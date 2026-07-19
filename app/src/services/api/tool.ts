import { apiClient } from './client';

export interface ToolRead {
  id: number;
  name: string;
  description: string | null;
  type: string;
  status: string;
  config: Record<string, unknown> | null;
  function_definition: Record<string, unknown> | null;
  call_count_7d: number;
  success_rate: number;
  avg_latency: number;
  created_by: string | null;
  created_at?: string;
  updated_at?: string;
}

export interface PageResult<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

export const apiToolService = {
  async getTools(params?: { page?: number; page_size?: number; keyword?: string }): Promise<PageResult<ToolRead>> {
    return apiClient.get('/tools', { params });
  },

  async getTool(id: number): Promise<ToolRead> {
    return apiClient.get(`/tools/${id}`);
  },

  async createTool(data: { name: string; description?: string; type: 'builtin' | 'http_api' | 'custom_function'; config?: Record<string, unknown>; function_definition?: Record<string, unknown> }): Promise<ToolRead> {
    return apiClient.post('/tools', data);
  },

  async updateTool(id: number, data: Partial<{ name: string; description: string; type: 'builtin' | 'http_api' | 'custom_function'; config: Record<string, unknown>; function_definition: Record<string, unknown> }>): Promise<ToolRead> {
    return apiClient.put(`/tools/${id}`, data);
  },

  async deleteTool(id: number): Promise<void> {
    return apiClient.delete(`/tools/${id}`);
  },

  async enableTool(id: number): Promise<ToolRead> {
    return apiClient.post(`/tools/${id}/enable`);
  },

  async disableTool(id: number): Promise<ToolRead> {
    return apiClient.post(`/tools/${id}/disable`);
  },

  async testTool(id: number, input: Record<string, unknown>): Promise<{ success: boolean; output: unknown; error: string | null; latency_ms: number }> {
    return apiClient.post(`/tools/${id}/test`, { input });
  },
};
