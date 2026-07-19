import { apiClient } from './client'
import type { PaginatedResponse } from '../types/common'
import type { Conversation, ConversationTurn, TraceStep } from '../types/conversation'

interface ConversationQuery {
  page?: number
  pageSize?: number
  search?: string
  agentId?: string
  userId?: string
  status?: string
  startDate?: string
  endDate?: string
}

interface BackendPage<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

interface BackendConversation {
  id: number
  agent_id: number | null
  agent_name: string
  user_id: number | null
  user_name: string
  status: Conversation['status']
  turn_count: number
  token_usage: number
  cost: number
  duration: number
  satisfaction: number | null
  started_at: string
  ended_at: string | null
  tags: string[]
  error_message: string | null
}

interface BackendTurn {
  id: number
  conversation_id: number
  role: ConversationTurn['role'] | 'system'
  content: string
  timestamp: string
  token_count: number
  tool_calls: ConversationTurn['toolCalls']
}

interface BackendTrace {
  id: number
  turn_id: number
  type: TraceStep['type']
  name: string
  input: unknown
  output: unknown
  start_time: string
  end_time: string
  duration: number
  status: TraceStep['status']
  prompt_tokens: number
  completion_tokens: number
  total_tokens: number
  metadata: Record<string, unknown>
}

const mapConversation = (item: BackendConversation): Conversation => ({
  id: String(item.id),
  agentId: item.agent_id === null ? '' : String(item.agent_id),
  agentName: item.agent_name,
  userId: item.user_id === null ? '' : String(item.user_id),
  userName: item.user_name,
  status: item.status,
  turnCount: item.turn_count,
  tokenUsage: item.token_usage,
  cost: item.cost,
  duration: item.duration,
  satisfaction: item.satisfaction ?? undefined,
  startedAt: item.started_at,
  endedAt: item.ended_at ?? undefined,
  tags: item.tags,
  errorMessage: item.error_message ?? undefined,
})

const mapTurn = (item: BackendTurn): ConversationTurn => ({
  id: String(item.id),
  conversationId: String(item.conversation_id),
  role: item.role === 'system' ? 'assistant' : item.role,
  content: item.content,
  timestamp: item.timestamp,
  tokenCount: item.token_count,
  toolCalls: item.tool_calls ?? undefined,
})

const mapTrace = (item: BackendTrace): TraceStep => {
  const metadata = item.metadata ?? {}
  return {
    id: String(item.id),
    turnId: String(item.turn_id),
    type: item.type,
    name: item.name,
    input: item.input,
    output: item.output,
    startTime: item.start_time,
    endTime: item.end_time,
    duration: item.duration,
    status: item.status,
    tokenUsage: item.total_tokens > 0
      ? { prompt: item.prompt_tokens, completion: item.completion_tokens, total: item.total_tokens }
      : undefined,
    metadata: {
      knowledgeBaseId: String(metadata.knowledgeBaseId ?? metadata.knowledge_base_id ?? ''),
      topK: Number(metadata.topK ?? metadata.top_k ?? 0),
      toolId: String(metadata.toolId ?? metadata.tool_id ?? ''),
      toolName: String(metadata.toolName ?? metadata.tool_name ?? ''),
    },
  }
}

export const apiConversationService = {
  async getConversations(params?: ConversationQuery): Promise<PaginatedResponse<Conversation>> {
    const page = await apiClient.get<BackendPage<BackendConversation>>('/conversations', {
      params: {
        page: params?.page,
        page_size: params?.pageSize,
        keyword: params?.search,
        agent_id: params?.agentId,
        user_id: params?.userId,
        status: params?.status,
        start_date: params?.startDate,
        end_date: params?.endDate,
      },
    })
    return { data: page.items.map(mapConversation), total: page.total, page: page.page, pageSize: page.page_size }
  },

  async getConversation(id: string): Promise<Conversation> {
    return mapConversation(await apiClient.get<BackendConversation>(`/conversations/${id}`))
  },

  async getConversationTurns(conversationId: string): Promise<ConversationTurn[]> {
    const items = await apiClient.get<BackendTurn[]>(`/conversations/${conversationId}/turns`)
    return items.map(mapTurn)
  },

  async getTraceSteps(turnId: string): Promise<TraceStep[]> {
    const items = await apiClient.get<BackendTrace[]>(`/turns/${turnId}/trace`)
    return items.map(mapTrace)
  },

  async exportConversation(id: string, format: 'json' | 'txt'): Promise<Blob> {
    return apiClient.getBlob(`/conversations/${id}/export`, { params: { format } })
  },
}
