export interface Conversation {
  id: string
  agentId: string
  agentName: string
  userId: string
  userName: string
  status: 'active' | 'completed' | 'failed'
  turnCount: number
  tokenUsage: number
  cost: number
  duration: number
  satisfaction?: number
  startedAt: string
  endedAt?: string
  tags?: string[]
  errorMessage?: string
}

export interface ConversationDetail extends Conversation {
  turns: ConversationTurn[]
  annotation?: ConversationAnnotation
}

export interface ConversationTurn {
  id: string
  conversationId: string
  role: 'user' | 'assistant'
  content: string
  timestamp: string
  tokenCount: number
  toolCalls?: Array<{
    toolId: string
    toolName: string
    input: Record<string, unknown>
    output: Record<string, unknown>
    duration: number
    status: 'success' | 'failed'
  }>
  trace?: TurnTrace
}

export interface TurnTrace {
  steps: TraceStep[]
  inputTokens: number
  outputTokens: number
  totalDuration: number
  model: string
}

export interface TraceStep {
  id: string
  turnId: string
  type: 'llm' | 'retrieval' | 'tool'
  name: string
  input: unknown
  output: unknown
  startTime: string
  endTime: string
  duration: number
  status: 'success' | 'failed'
  tokenUsage?: { prompt: number; completion: number; total: number }
  metadata?: {
    knowledgeBaseId?: string
    topK?: number
    toolId?: string
    toolName?: string
  }
}

export interface ConversationAnnotation {
  rating: number
  tags: string[]
  notes: string
  annotatedBy: string
  annotatedAt: string
}
