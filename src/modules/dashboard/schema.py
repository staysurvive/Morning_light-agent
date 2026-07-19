from pydantic import BaseModel


class DashboardStats(BaseModel):
    todayCalls:int; todayCallsTrend:float; tokenUsage:int; tokenUsageTrend:float; cost:float; costTrend:float
    activeAgents:int; totalAgents:int; activeAgentsTrend:float


class TrendData(BaseModel): date:str; calls:int; tokens:int
class AgentRanking(BaseModel): agentId:str; agentName:str; calls:int; successRate:float; avgLatency:float
class DashboardAlert(BaseModel): id:str; level:str; message:str; time:str; status:str
class ResourceUsage(BaseModel): name:str; used:float; total:float; percentage:float; unit:str
