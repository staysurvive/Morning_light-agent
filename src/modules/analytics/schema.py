from pydantic import BaseModel, Field


class UsageOverview(BaseModel):
    totalCalls: int
    totalTokens: int
    totalCost: float
    avgResponseTime: float
    successRate: float
    period: str


class UsageDaily(BaseModel):
    date: str
    calls: int
    tokens: int
    cost: float
    avgResponseTime: float
    successRate: float


class UsageByAgent(BaseModel):
    agentId: str
    agentName: str
    calls: int
    tokens: int
    cost: float
    successRate: float


class UsageByModel(BaseModel):
    modelId: str
    modelName: str
    calls: int
    tokens: int
    cost: float
    avgResponseTime: float


class UsageByUser(BaseModel):
    userId: str
    userName: str
    calls: int
    tokens: int
    cost: float
    avgSatisfaction: float


class UsageStats(BaseModel):
    overview: UsageOverview
    daily: list[UsageDaily]
    byAgent: list[UsageByAgent]
    byModel: list[UsageByModel]
    byUser: list[UsageByUser]


class CostOverview(BaseModel):
    totalCost: float
    modelCost: float
    toolCost: float
    storageCost: float
    otherCost: float
    period: str


class CostDaily(BaseModel):
    date: str
    total: float
    model: float
    tool: float
    storage: float
    other: float


class CostByModel(BaseModel):
    modelId: str
    modelName: str
    cost: float
    percentage: float
    calls: int


class CostByAgent(BaseModel):
    agentId: str
    agentName: str
    cost: float
    percentage: float


class CostByTool(BaseModel):
    toolId: str
    toolName: str
    cost: float
    calls: int


class CostTrend(BaseModel):
    current: float
    previous: float
    change: float
    forecast: float


class CostStats(BaseModel):
    overview: CostOverview
    daily: list[CostDaily]
    byModel: list[CostByModel]
    byAgent: list[CostByAgent]
    byTool: list[CostByTool]
    trend: CostTrend


class EvaluationOverview(BaseModel):
    avgSatisfaction: float
    totalEvaluations: int
    positiveRate: float
    negativeRate: float
    neutralRate: float
    period: str
    annotationCoverage: float
    avgRating: float
    needsOptimization: int


class EvaluationDistribution(BaseModel):
    score5: int = 0
    score4: int = 0
    score3: int = 0
    score2: int = 0
    score1: int = 0


class EvaluationDaily(BaseModel):
    date: str
    avgScore: float
    evaluations: int
    positiveRate: float


class EvaluationByAgent(BaseModel):
    agentId: str
    agentName: str
    avgScore: float
    evaluations: int
    positiveRate: float
    needsOptimization: int
    trend: str = "stable"


class EvaluationIssue(BaseModel):
    issue: str
    count: int
    percentage: float


class EvaluationImprovement(BaseModel):
    suggestion: str
    priority: str
    mentions: int


class EvaluationStats(BaseModel):
    overview: EvaluationOverview
    distribution: EvaluationDistribution
    daily: list[EvaluationDaily]
    byAgent: list[EvaluationByAgent]
    issues: list[EvaluationIssue]
    improvements: list[EvaluationImprovement]
