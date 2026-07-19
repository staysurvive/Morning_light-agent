from fastapi import APIRouter,Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.base_schema import ResponseSchema
from src.core.deps import require_permission
from src.core.permissions import DASHBOARD_READ
from src.infra.database import get_db
from src.modules.dashboard.schema import AgentRanking,DashboardAlert,DashboardStats,ResourceUsage,TrendData
from src.modules.dashboard.service import DashboardService

router=APIRouter(prefix='/dashboard',tags=['Dashboard'],dependencies=[Depends(require_permission(DASHBOARD_READ))])
def get_service(db:AsyncSession=Depends(get_db,scope='function')): return DashboardService(db)
@router.get('/stats',response_model=ResponseSchema[DashboardStats])
async def stats(service:DashboardService=Depends(get_service)): return ResponseSchema(data=DashboardStats.model_validate(await service.stats()))
@router.get('/trends',response_model=ResponseSchema[list[TrendData]])
async def trends(service:DashboardService=Depends(get_service)): return ResponseSchema(data=[TrendData.model_validate(i) for i in await service.trends()])
@router.get('/top-agents',response_model=ResponseSchema[list[AgentRanking]])
async def top_agents(service:DashboardService=Depends(get_service)): return ResponseSchema(data=[AgentRanking.model_validate(i) for i in await service.top_agents()])
@router.get('/recent-alerts',response_model=ResponseSchema[list[DashboardAlert]])
async def alerts(service:DashboardService=Depends(get_service)): return ResponseSchema(data=[DashboardAlert.model_validate(i) for i in await service.alerts()])
@router.get('/resource-usage',response_model=ResponseSchema[list[ResourceUsage]])
async def resources(service:DashboardService=Depends(get_service)): return ResponseSchema(data=[ResourceUsage.model_validate(i) for i in await service.resources()])
