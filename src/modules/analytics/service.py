from collections import Counter, defaultdict
from datetime import date, datetime, time, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import BizException
from src.modules.analytics.schema import CostStats, EvaluationStats, UsageStats
from src.modules.conversation.model import Conversation
from src.modules.conversation.repository import ConversationRepository


def resolve_period(start_date: date | None, end_date: date | None) -> tuple[date, date]:
    end = end_date or date.today()
    start = start_date or (end - timedelta(days=6))
    if end < start:
        raise BizException(code=400, message="结束日期不能早于开始日期")
    if (end - start).days > 365:
        raise BizException(code=400, message="分析时间范围不能超过 366 天")
    return start, end


def _date_keys(start: date, end: date) -> list[date]:
    return [start + timedelta(days=index) for index in range((end - start).days + 1)]


def _group(items, key_fn):
    result = defaultdict(list)
    for item in items:
        result[key_fn(item)].append(item)
    return result


def _success_rate(items: list[Conversation]) -> float:
    return round(sum(item.status == "completed" for item in items) / len(items) * 100, 2) if items else 0


class AnalyticsService:
    def __init__(self, db: AsyncSession):
        self.repo = ConversationRepository(db)

    async def _load(self, start: date, end: date, agent_id: int | None, model_id: int | None):
        return await self.repo.list_between(
            datetime.combine(start, time.min),
            datetime.combine(end + timedelta(days=1), time.min),
            agent_id,
            model_id,
        )

    async def usage(self, start: date, end: date, agent_id: int | None, model_id: int | None) -> UsageStats:
        items = await self._load(start, end, agent_id, model_id)
        days = _date_keys(start, end)
        daily_groups = _group(items, lambda item: item.started_at.date())
        agent_groups = _group(items, lambda item: (item.agent_id, item.agent_name))
        model_groups = _group(items, lambda item: (item.model_id, item.model_name or "未配置模型"))
        user_groups = _group(items, lambda item: (item.user_id, item.user_name))
        total_cost = sum(float(item.cost) for item in items)
        return UsageStats.model_validate({
            "overview": {
                "totalCalls": len(items), "totalTokens": sum(item.token_usage for item in items),
                "totalCost": round(total_cost, 8),
                "avgResponseTime": round(sum(item.duration for item in items) / len(items), 3) if items else 0,
                "successRate": _success_rate(items), "period": f"{start.isoformat()}~{end.isoformat()}",
            },
            "daily": [{
                "date": day.isoformat(), "calls": len(group := daily_groups[day]),
                "tokens": sum(item.token_usage for item in group),
                "cost": round(sum(float(item.cost) for item in group), 8),
                "avgResponseTime": round(sum(item.duration for item in group) / len(group), 3) if group else 0,
                "successRate": _success_rate(group),
            } for day in days],
            "byAgent": [{
                "agentId": str(key[0]) if key[0] is not None else "deleted", "agentName": key[1],
                "calls": len(group), "tokens": sum(item.token_usage for item in group),
                "cost": round(sum(float(item.cost) for item in group), 8), "successRate": _success_rate(group),
            } for key, group in agent_groups.items()],
            "byModel": [{
                "modelId": str(key[0]) if key[0] is not None else "unconfigured", "modelName": key[1],
                "calls": len(group), "tokens": sum(item.token_usage for item in group),
                "cost": round(sum(float(item.cost) for item in group), 8),
                "avgResponseTime": round(sum(item.duration for item in group) / len(group), 3),
            } for key, group in model_groups.items()],
            "byUser": [{
                "userId": str(key[0]) if key[0] is not None else "deleted", "userName": key[1],
                "calls": len(group), "tokens": sum(item.token_usage for item in group),
                "cost": round(sum(float(item.cost) for item in group), 8),
                "avgSatisfaction": round(sum(item.satisfaction for item in group if item.satisfaction) / len([item for item in group if item.satisfaction]), 2) if any(item.satisfaction for item in group) else 0,
            } for key, group in user_groups.items()],
        })

    async def cost(self, start: date, end: date, agent_id: int | None, model_id: int | None) -> CostStats:
        items = await self._load(start, end, agent_id, model_id)
        days = _date_keys(start, end)
        daily_groups = _group(items, lambda item: item.started_at.date())
        model_groups = _group(items, lambda item: (item.model_id, item.model_name or "未配置模型"))
        agent_groups = _group(items, lambda item: (item.agent_id, item.agent_name))
        total = sum(float(item.cost) for item in items)
        span = len(days)
        previous_end = start - timedelta(days=1)
        previous_start = previous_end - timedelta(days=span - 1)
        previous_items = await self._load(previous_start, previous_end, agent_id, model_id)
        previous = sum(float(item.cost) for item in previous_items)
        change = (total - previous) / previous * 100 if previous else 0
        return CostStats.model_validate({
            "overview": {"totalCost": total, "modelCost": total, "toolCost": 0, "storageCost": 0, "otherCost": 0, "period": f"{start.isoformat()}~{end.isoformat()}"},
            "daily": [{"date": day.isoformat(), "total": value, "model": value, "tool": 0, "storage": 0, "other": 0} for day in days for value in [round(sum(float(item.cost) for item in daily_groups[day]), 8)]],
            "byModel": [{"modelId": str(key[0]) if key[0] is not None else "unconfigured", "modelName": key[1], "cost": value, "percentage": value / total * 100 if total else 0, "calls": len(group)} for key, group in model_groups.items() for value in [sum(float(item.cost) for item in group)]],
            "byAgent": [{"agentId": str(key[0]) if key[0] is not None else "deleted", "agentName": key[1], "cost": value, "percentage": value / total * 100 if total else 0} for key, group in agent_groups.items() for value in [sum(float(item.cost) for item in group)]],
            "byTool": [],
            "trend": {"current": total, "previous": previous, "change": change, "forecast": total / span * 30 if span else 0},
        })

    async def evaluation(self, start: date, end: date, agent_id: int | None) -> EvaluationStats:
        items = await self._load(start, end, agent_id, None)
        annotated = [item for item in items if item.annotation]
        days = _date_keys(start, end)
        daily_groups = _group(annotated, lambda item: item.annotation.annotated_at.date())
        agent_groups = _group(annotated, lambda item: (item.agent_id, item.agent_name))
        ratings = [item.annotation.rating for item in annotated]
        distribution = Counter(ratings)
        tags = Counter(tag for item in annotated for tag in item.annotation.tags)
        positive = sum(value >= 4 for value in ratings)
        negative = sum(value <= 2 for value in ratings)
        neutral = sum(value == 3 for value in ratings)
        count = len(ratings)
        return EvaluationStats.model_validate({
            "overview": {
                "avgSatisfaction": sum(ratings) / count / 5 * 100 if count else 0,
                "totalEvaluations": count, "positiveRate": positive / count * 100 if count else 0,
                "negativeRate": negative / count * 100 if count else 0,
                "neutralRate": neutral / count * 100 if count else 0,
                "period": f"{start.isoformat()}~{end.isoformat()}",
                "annotationCoverage": count / len(items) * 100 if items else 0,
                "avgRating": sum(ratings) / count if count else 0,
                "needsOptimization": negative,
            },
            "distribution": {f"score{score}": distribution[score] for score in range(1, 6)},
            "daily": [{
                "date": day.isoformat(), "avgScore": sum(values) / len(values) if values else 0,
                "evaluations": len(values), "positiveRate": sum(value >= 4 for value in values) / len(values) * 100 if values else 0,
            } for day in days for values in [[item.annotation.rating for item in daily_groups[day]]]],
            "byAgent": [{
                "agentId": str(key[0]) if key[0] is not None else "deleted", "agentName": key[1],
                "avgScore": sum(values) / len(values), "evaluations": len(values),
                "positiveRate": sum(value >= 4 for value in values) / len(values) * 100,
                "needsOptimization": sum(value <= 2 for value in values), "trend": "stable",
            } for key, group in agent_groups.items() for values in [[item.annotation.rating for item in group]]],
            "issues": [{"issue": tag, "count": value, "percentage": value / count * 100 if count else 0} for tag, value in tags.most_common()],
            "improvements": [],
        })
