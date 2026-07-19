import csv
import io
from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.base_schema import ResponseSchema
from src.core.deps import require_permission
from src.core.permissions import ANALYTICS_EXPORT, ANALYTICS_READ
from src.infra.database import get_db
from src.modules.analytics.schema import CostStats, EvaluationStats, UsageStats
from src.modules.analytics.service import AnalyticsService, resolve_period

router = APIRouter(prefix="/analytics", tags=["Analytics"])


def get_analytics_service(db: AsyncSession = Depends(get_db, scope="function")) -> AnalyticsService:
    return AnalyticsService(db)


@router.get("/usage", response_model=ResponseSchema[UsageStats], dependencies=[Depends(require_permission(ANALYTICS_READ))])
async def usage_stats(
    start_date: date | None = Query(default=None), end_date: date | None = Query(default=None),
    agent_id: int | None = Query(default=None, ge=1), model_id: int | None = Query(default=None, ge=1),
    service: AnalyticsService = Depends(get_analytics_service),
):
    start, end = resolve_period(start_date, end_date)
    return ResponseSchema(data=await service.usage(start, end, agent_id, model_id))


@router.get("/cost", response_model=ResponseSchema[CostStats], dependencies=[Depends(require_permission(ANALYTICS_READ))])
async def cost_stats(
    start_date: date | None = Query(default=None), end_date: date | None = Query(default=None),
    agent_id: int | None = Query(default=None, ge=1), model_id: int | None = Query(default=None, ge=1),
    service: AnalyticsService = Depends(get_analytics_service),
):
    start, end = resolve_period(start_date, end_date)
    return ResponseSchema(data=await service.cost(start, end, agent_id, model_id))


@router.get("/evaluation", response_model=ResponseSchema[EvaluationStats], dependencies=[Depends(require_permission(ANALYTICS_READ))])
async def evaluation_stats(
    start_date: date | None = Query(default=None), end_date: date | None = Query(default=None),
    agent_id: int | None = Query(default=None, ge=1), service: AnalyticsService = Depends(get_analytics_service),
):
    start, end = resolve_period(start_date, end_date)
    return ResponseSchema(data=await service.evaluation(start, end, agent_id))


@router.get("/{report_type}/export", dependencies=[Depends(require_permission(ANALYTICS_EXPORT))])
async def export_analytics(
    report_type: Literal["usage", "cost", "evaluation"],
    format: Literal["csv"] = Query(default="csv"),
    start_date: date | None = Query(default=None), end_date: date | None = Query(default=None),
    service: AnalyticsService = Depends(get_analytics_service),
):
    start, end = resolve_period(start_date, end_date)
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    if report_type == "usage":
        data = await service.usage(start, end, None, None)
        writer.writerow(["date", "calls", "tokens", "cost", "avg_response_time", "success_rate"])
        for item in data.daily:
            writer.writerow([item.date, item.calls, item.tokens, item.cost, item.avgResponseTime, item.successRate])
    elif report_type == "cost":
        data = await service.cost(start, end, None, None)
        writer.writerow(["date", "total", "model", "tool", "storage", "other"])
        for item in data.daily:
            writer.writerow([item.date, item.total, item.model, item.tool, item.storage, item.other])
    else:
        data = await service.evaluation(start, end, None)
        writer.writerow(["date", "avg_score", "evaluations", "positive_rate"])
        for item in data.daily:
            writer.writerow([item.date, item.avgScore, item.evaluations, item.positiveRate])
    content = ("\ufeff" + buffer.getvalue()).encode("utf-8")
    return Response(
        content=content, media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="analytics-{report_type}.csv"'},
    )
