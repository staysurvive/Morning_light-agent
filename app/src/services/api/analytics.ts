import { apiClient } from './client';
import type { UsageStats, CostStats, EvaluationStats } from '../types/analytics';

const mapParams = (params?: Record<string, string>) => ({
  start_date: params?.startDate,
  end_date: params?.endDate,
  agent_id: params?.agentId,
  model_id: params?.modelId,
})

export const apiAnalyticsService = {
  async getUsageStats(params?: Record<string, string>): Promise<UsageStats> {
    return apiClient.get('/analytics/usage', { params: mapParams(params) });
  },

  async getCostStats(params?: Record<string, string>): Promise<CostStats> {
    return apiClient.get('/analytics/cost', { params: mapParams(params) });
  },

  async getEvaluationStats(params?: Record<string, string>): Promise<EvaluationStats> {
    return apiClient.get('/analytics/evaluation', { params: mapParams(params) });
  },

  async exportReport(type: string, format: string): Promise<Blob> {
    return apiClient.getBlob(`/analytics/${type}/export`, { params: { format } });
  },
};
