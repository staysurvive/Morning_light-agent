export interface AnalyticsOverview {
  totalCalls: number
  totalTokens: number
  totalCost: number
  avgLatency: number
  callsTrend: number
  tokensTrend: number
  costTrend: number
  latencyTrend: number
}

export interface DailyStats {
  date: string
  calls: number
  inputTokens: number
  outputTokens: number
  cost: number
  avgLatency: number
  successRate: number
}

export interface AgentAnalytics {
  agentId: string
  agentName: string
  calls: number
  tokens: number
  cost: number
  successRate: number
  avgLatency: number
}

export interface ModelAnalytics {
  modelId: string
  modelName: string
  calls: number
  inputTokens: number
  outputTokens: number
  cost: number
}

export interface CostAnalysis {
  monthCost: number
  dailyAvgCost: number
  projectedCost: number
  budgetRemaining: number
  costByModel: { model: string; cost: number }[]
  costByAgent: { agent: string; cost: number }[]
}

export interface Evaluation {
  avgSatisfaction: number
  annotationCoverage: number
  needsOptimization: number
  avgRating: number
  agentEvaluations: AgentEvaluation[]
  commonIssues: CommonIssue[]
}

export interface AgentEvaluation {
  agentId: string
  agentName: string
  satisfaction: number
  avgRating: number
  annotationCount: number
  needsOptimization: number
  trend: 'up' | 'down' | 'stable'
}

export interface CommonIssue {
  type: string
  count: number
  percentage: number
  trend: 'up' | 'down' | 'stable'
}

export interface UsageStats {
  overview: {
    totalCalls: number
    totalTokens: number
    totalCost: number
    avgResponseTime: number
    successRate: number
    period: string
  }
  daily: Array<{ date: string; calls: number; tokens: number; cost: number; avgResponseTime: number; successRate: number }>
  byAgent: Array<{ agentId: string; agentName: string; calls: number; tokens: number; cost: number; successRate: number }>
  byModel: Array<{ modelId: string; modelName: string; calls: number; tokens: number; cost: number; avgResponseTime: number }>
  byUser: Array<{ userId: string; userName: string; calls: number; tokens: number; cost: number; avgSatisfaction: number }>
}

export interface CostStats {
  overview: { totalCost: number; modelCost: number; toolCost: number; storageCost: number; otherCost: number; period: string }
  daily: Array<{ date: string; total: number; model: number; tool: number; storage: number; other: number }>
  byModel: Array<{ modelId: string; modelName: string; cost: number; percentage: number; calls: number }>
  byAgent: Array<{ agentId: string; agentName: string; cost: number; percentage: number }>
  byTool: Array<{ toolId: string; toolName: string; cost: number; calls: number }>
  trend: { current: number; previous: number; change: number; forecast: number }
}

export interface EvaluationStats {
  overview: {
    avgSatisfaction: number
    totalEvaluations: number
    positiveRate: number
    negativeRate: number
    neutralRate: number
    period: string
    annotationCoverage?: number
    avgRating?: number
    needsOptimization?: number
  }
  distribution: { score5: number; score4: number; score3: number; score2: number; score1: number }
  daily: Array<{ date: string; avgScore: number; evaluations: number; positiveRate: number }>
  byAgent: Array<{
    agentId: string
    agentName: string
    avgScore: number
    evaluations: number
    positiveRate: number
    needsOptimization: number
    trend: 'up' | 'down' | 'stable'
  }>
  issues: Array<{ issue: string; count: number; percentage: number }>
  improvements: Array<{ suggestion: string; priority: 'high' | 'medium' | 'low'; mentions: number }>
}
