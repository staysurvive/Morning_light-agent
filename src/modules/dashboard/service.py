import asyncio
from datetime import date, datetime, time, timedelta

from loguru import logger
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.infra.minio_client import get_bucket_usage
from src.modules.agent.model import Agent
from src.modules.conversation.model import Conversation
from src.modules.knowledge.model import Document
from src.modules.model.model import LLMModel
from src.modules.system.model import SystemAlert


def _trend(current:float,previous:float)->float:
    return round((current-previous)/previous*100,2) if previous else 0


class DashboardService:
    def __init__(self,db:AsyncSession): self.db=db

    async def stats(self):
        today=datetime.combine(date.today(),time.min); tomorrow=today+timedelta(days=1); yesterday=today-timedelta(days=1)
        async def aggregate(start,end):
            row=(await self.db.execute(select(func.count(Conversation.id),func.coalesce(func.sum(Conversation.input_tokens+Conversation.output_tokens),0),func.coalesce(func.sum(Conversation.cost),0)).where(Conversation.started_at>=start,Conversation.started_at<end))).one(); return int(row[0]),int(row[1]),float(row[2])
        current=await aggregate(today,tomorrow); previous=await aggregate(yesterday,today)
        total_agents=int(await self.db.scalar(select(func.count(Agent.id))) or 0); active=int(await self.db.scalar(select(func.count(Agent.id)).where(Agent.status=='active')) or 0)
        return {"todayCalls":current[0],"todayCallsTrend":_trend(current[0],previous[0]),"tokenUsage":current[1],"tokenUsageTrend":_trend(current[1],previous[1]),"cost":current[2],"costTrend":_trend(current[2],previous[2]),"activeAgents":active,"totalAgents":total_agents,"activeAgentsTrend":0}

    async def trends(self):
        days=[date.today()-timedelta(days=i) for i in reversed(range(7))]; result=[]
        for day in days:
            start=datetime.combine(day,time.min); end=start+timedelta(days=1)
            row=(await self.db.execute(select(func.count(Conversation.id),func.coalesce(func.sum(Conversation.input_tokens+Conversation.output_tokens),0)).where(Conversation.started_at>=start,Conversation.started_at<end))).one()
            result.append({"date":day.isoformat(),"calls":int(row[0]),"tokens":int(row[1])})
        return result

    async def top_agents(self):
        since=datetime.now()-timedelta(days=7)
        rows=(await self.db.execute(select(Agent.id,Agent.name,func.count(Conversation.id),func.coalesce(func.sum(Conversation.status=='completed'),0),func.coalesce(func.avg(Conversation.duration),0)).outerjoin(Conversation,((Conversation.agent_id==Agent.id)&(Conversation.started_at>=since))).group_by(Agent.id,Agent.name).order_by(func.count(Conversation.id).desc()).limit(5))).all()
        return [{"agentId":str(r[0]),"agentName":r[1],"calls":int(r[2]),"successRate":round(int(r[3])/int(r[2])*100,2) if r[2] else 0,"avgLatency":round(float(r[4]),3)} for r in rows]

    async def alerts(self):
        rows=(await self.db.execute(select(SystemAlert).order_by(SystemAlert.last_occurred_at.desc()).limit(5))).scalars().all()
        level={"low":"info","medium":"warning","high":"error","critical":"critical"}
        return [{"id":str(i.id),"level":level.get(i.severity,"info"),"message":i.title,"time":i.last_occurred_at.isoformat(),"status":i.status} for i in rows]

    async def resources(self):
        total_models=int(await self.db.scalar(select(func.count(LLMModel.id))) or 0); available=int(await self.db.scalar(select(func.count(LLMModel.id)).where(LLMModel.status=='available')) or 0)
        document_count=int(await self.db.scalar(select(func.count(Document.id))) or 0)
        try:
            bucket_usage=await asyncio.to_thread(get_bucket_usage)
            object_count=bucket_usage.object_count
        except Exception as exc:
            logger.warning(f"读取 MinIO 资源用量失败: {exc}")
            object_count=0
        return [
            {"name":"可用模型","used":available,"total":total_models,"percentage":round(available/total_models*100,2) if total_models else 0,"unit":"个"},
            {"name":"MinIO 文档对象","used":object_count,"total":document_count,"percentage":round(min(object_count/document_count,1)*100,2) if document_count else 0,"unit":"个"},
        ]
