import { apiClient } from './client'
import type { PaginatedResponse } from '../types/common'
import type { AlertRule, ApiKey, AuditLog, SystemAlert, SystemSettings } from '../types/system'

// ---- 后端真实类型 ----
export interface BackendUser {
  id: number
  username: string
  email: string
  is_active: boolean
}

export interface BackendUserWithRoles extends BackendUser {
  roles: BackendRole[]
}

export interface BackendRole {
  id: number
  code: string
  name: string
  description: string | null
  permissions: BackendPermission[]
}

export interface BackendPermission {
  id: number
  code: string
  name: string
  description: string | null
}

export interface PageResult<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

export const apiSystemService = {
  // ---- 用户 ----
  async getUsers(params?: { page?: number; page_size?: number; keyword?: string }): Promise<PageResult<BackendUser>> {
    return apiClient.get('/users/search', { params: params as Record<string, unknown> })
  },

  async getUser(id: number): Promise<BackendUserWithRoles> {
    return apiClient.get(`/users/${id}`)
  },

  async createUser(data: { username: string; email: string; password: string }): Promise<BackendUser> {
    return apiClient.post('/users', data)
  },

  async deleteUser(id: number): Promise<void> {
    return apiClient.delete(`/users/${id}`)
  },

  async assignUserRoles(userId: number, roleIds: number[]): Promise<BackendUserWithRoles> {
    return apiClient.put(`/users/${userId}/roles`, { role_ids: roleIds })
  },

  async getCurrentUser(): Promise<BackendUser> {
    return apiClient.get('/users/me')
  },

  // ---- 角色 ----
  async getRoles(): Promise<BackendRole[]> {
    return apiClient.get('/roles/')
  },

  async searchRoles(params?: { page?: number; page_size?: number; keyword?: string }): Promise<PageResult<BackendRole>> {
    return apiClient.get('/roles/search', { params: params as Record<string, unknown> })
  },

  async getRole(id: number): Promise<BackendRole> {
    return apiClient.get(`/roles/${id}`)
  },

  async createRole(data: { code: string; name: string; description?: string }): Promise<BackendRole> {
    return apiClient.post('/roles', data)
  },

  async updateRole(id: number, data: { name?: string; description?: string }): Promise<BackendRole> {
    return apiClient.put(`/roles/${id}`, data)
  },

  async deleteRole(id: number): Promise<void> {
    return apiClient.delete(`/roles/${id}`)
  },

  async assignRolePermissions(roleId: number, permissionIds: number[]): Promise<BackendRole> {
    return apiClient.put(`/roles/${roleId}/permissions`, { permission_ids: permissionIds })
  },

  // ---- 权限 ----
  async getPermissions(): Promise<BackendPermission[]> {
    return apiClient.get('/permissions/')
  },

  async searchPermissions(params?: { page?: number; page_size?: number; keyword?: string }): Promise<PageResult<BackendPermission>> {
    return apiClient.get('/permissions/search', { params: params as Record<string, unknown> })
  },

  async createPermission(data: { code: string; name: string; description?: string }): Promise<BackendPermission> {
    return apiClient.post('/permissions', data)
  },

  async updatePermission(id: number, data: { name?: string; description?: string }): Promise<BackendPermission> {
    return apiClient.put(`/permissions/${id}`, data)
  },

  async deletePermission(id: number): Promise<void> {
    return apiClient.delete(`/permissions/${id}`)
  },

  // ---- API Key ----
  async getApiKeys(params?: { page?: number; pageSize?: number; status?: string }): Promise<PaginatedResponse<ApiKey>> {
    const result = await apiClient.get<PageResult<Omit<ApiKey, 'id'> & { id: number }>>('/system/api-keys', {
      params: { page: params?.page, page_size: params?.pageSize, status: params?.status },
    })
    return {
      data: result.items.map((item) => ({ ...item, id: String(item.id) })),
      total: result.total,
      page: result.page,
      pageSize: result.page_size,
    }
  },

  async createApiKey(data: { name: string; permissions?: string[]; rateLimit?: number; expiresAt?: string | null }): Promise<ApiKey> {
    const item = await apiClient.post<Omit<ApiKey, 'id'> & { id: number }>('/system/api-keys', {
      name: data.name,
      permissions: data.permissions ?? [],
      rate_limit: data.rateLimit ?? 100,
      expires_at: data.expiresAt ?? null,
    })
    return { ...item, id: String(item.id) }
  },

  async updateApiKey(id: string, data: { name?: string; permissions?: string[]; status?: string; rateLimit?: number; expiresAt?: string | null }): Promise<ApiKey> {
    const item = await apiClient.put<Omit<ApiKey, 'id'> & { id: number }>(`/system/api-keys/${id}`, {
      name: data.name,
      permissions: data.permissions,
      status: data.status,
      rate_limit: data.rateLimit,
      expires_at: data.expiresAt,
    })
    return { ...item, id: String(item.id) }
  },

  async rotateApiKey(id: string): Promise<ApiKey> {
    const item = await apiClient.post<Omit<ApiKey, 'id'> & { id: number }>(`/system/api-keys/${id}/rotate`)
    return { ...item, id: String(item.id) }
  },

  async deleteApiKey(id: string): Promise<void> {
    return apiClient.delete(`/system/api-keys/${id}`)
  },

  // ---- 审计 ----
  async getAuditLogs(params?: { page?: number; pageSize?: number; userId?: string; action?: string; module?: string; search?: string; startDate?: string; endDate?: string }): Promise<PaginatedResponse<AuditLog>> {
    const result = await apiClient.get<PageResult<AuditLog>>('/system/audit-logs', {
      params: {
        page: params?.page,
        page_size: params?.pageSize,
        user_id: params?.userId,
        action: params?.action,
        resource: params?.module,
        keyword: params?.search,
        start_date: params?.startDate,
        end_date: params?.endDate,
      },
    })
    return {
      data: result.items.map((item) => ({
        ...item,
        id: String(item.id),
        module: item.resource,
        detail: JSON.stringify(item.details),
        ipAddress: item.ip,
      })),
      total: result.total,
      page: result.page,
      pageSize: result.page_size,
    }
  },

  // ---- 告警与规则 ----
  async getSystemAlerts(params?: { status?: string; severity?: string }): Promise<SystemAlert[]> {
    const items = await apiClient.get<Array<Omit<SystemAlert, 'id'> & { id: number }>>('/system/alerts', { params })
    return items.map((item) => ({ ...item, id: String(item.id) }))
  },

  async createAlert(data: { type: string; title: string; message: string; source: string; severity: string }): Promise<SystemAlert> {
    const item = await apiClient.post<Omit<SystemAlert, 'id'> & { id: number }>('/system/alerts', data)
    return { ...item, id: String(item.id) }
  },

  async acknowledgeAlert(id: string): Promise<void> {
    await apiClient.post(`/system/alerts/${id}/acknowledge`)
  },

  async resolveAlert(id: string): Promise<void> {
    await apiClient.post(`/system/alerts/${id}/resolve`)
  },

  async deleteAlert(id: string): Promise<void> {
    await apiClient.delete(`/system/alerts/${id}`)
  },

  async getAlertRules(): Promise<AlertRule[]> {
    const items = await apiClient.get<Array<Omit<AlertRule, 'id'> & { id: number }>>('/system/alert-rules')
    return items.map((item) => ({ ...item, id: String(item.id) }))
  },

  async createAlertRule(data: Omit<AlertRule, 'id' | 'status' | 'createdBy' | 'createdAt' | 'updatedAt'>): Promise<AlertRule> {
    const item = await apiClient.post<Omit<AlertRule, 'id'> & { id: number }>('/system/alert-rules', data)
    return { ...item, id: String(item.id) }
  },

  async updateAlertRule(id: string, data: Partial<AlertRule>): Promise<AlertRule> {
    const item = await apiClient.put<Omit<AlertRule, 'id'> & { id: number }>(`/system/alert-rules/${id}`, data)
    return { ...item, id: String(item.id) }
  },

  async deleteAlertRule(id: string): Promise<void> {
    await apiClient.delete(`/system/alert-rules/${id}`)
  },

  // ---- 系统设置 ----
  async getSettings(): Promise<SystemSettings> {
    return apiClient.get('/system/settings')
  },

  async updateSettings(data: Partial<SystemSettings>): Promise<SystemSettings> {
    return apiClient.put('/system/settings', data)
  },
}
