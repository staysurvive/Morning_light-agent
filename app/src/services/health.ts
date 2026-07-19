import { API_ORIGIN, USE_MOCK } from './config'

export interface HealthResult {
  status: 'ok'
  source: 'mock' | 'api'
}

export const healthService = {
  async check(): Promise<HealthResult> {
    if (USE_MOCK) return { status: 'ok', source: 'mock' }

    const response = await fetch(`${API_ORIGIN}/health`)
    if (!response.ok) throw new Error(`健康检查失败（HTTP ${response.status}）`)
    const data = (await response.json()) as { status?: string }
    if (data.status !== 'ok') throw new Error('后端未返回健康状态')
    return { status: 'ok', source: 'api' }
  },
}
