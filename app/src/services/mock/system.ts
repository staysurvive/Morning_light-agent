import type { PaginatedResponse } from '../types/common';
import type { User, Role, ApiKey, AuditLog, SystemAlert, SystemSettings, AlertRule } from '../types/system';
import { mockUsers, mockRoles, mockApiKeys, mockAuditLogs, mockSystemAlerts, mockSystemSettings, mockPermissions } from './data/system';

const mockAlertRules: AlertRule[] = [];

export const mockSystemService = {
  // 用户管理
  async getUsers(params?: {
    page?: number;
    pageSize?: number;
    search?: string;
    role?: string;
    status?: string;
  }): Promise<PaginatedResponse<User>> {
    let filtered = [...mockUsers];

    if (params?.search) {
      const search = params.search.toLowerCase();
      filtered = filtered.filter(
        (u) =>
          u.username.toLowerCase().includes(search) ||
          u.name.toLowerCase().includes(search) ||
          u.email.toLowerCase().includes(search)
      );
    }

    if (params?.role) {
      filtered = filtered.filter((u) => u.role === params.role);
    }

    if (params?.status) {
      filtered = filtered.filter((u) => u.status === params.status);
    }

    const page = params?.page || 1;
    const pageSize = params?.pageSize || 10;
    const start = (page - 1) * pageSize;
    const end = start + pageSize;

    return {
      data: filtered.slice(start, end),
      total: filtered.length,
      page,
      pageSize,
    };
  },

  async getUser(id: string): Promise<User> {
    const user = mockUsers.find((u) => u.id === id);
    if (!user) throw new Error('用户不存在');
    return user;
  },

  async createUser(data: Partial<User>): Promise<User> {
    const newUser: User = {
      id: `user-${Date.now()}`,
      username: data.username || '',
      email: data.email || '',
      name: data.name || '',
      avatar: data.avatar || '',
      role: data.role || 'viewer',
      status: 'active',
      department: data.department || '',
      lastLoginAt: new Date().toISOString(),
      createdAt: new Date().toISOString(),
    };
    return newUser;
  },

  async updateUser(id: string, data: Partial<User>): Promise<User> {
    const user = await this.getUser(id);
    return { ...user, ...data };
  },

  async deleteUser(id: string): Promise<void> {
    void id
    await new Promise((resolve) => setTimeout(resolve, 500));
  },

  // 角色管理
  async getRoles(): Promise<Role[]> {
    return mockRoles;
  },

  async getRolesPaged(params?: { page?: number; pageSize?: number; keyword?: string }): Promise<PaginatedResponse<Role>> {
    let filtered = [...mockRoles];
    if (params?.keyword) {
      const kw = params.keyword.toLowerCase();
      filtered = filtered.filter(r =>
        r.name.toLowerCase().includes(kw) ||
        (r as unknown as { displayName?: string }).displayName?.toLowerCase().includes(kw) ||
        r.description?.toLowerCase().includes(kw)
      );
    }
    const page = params?.page || 1;
    const pageSize = params?.pageSize || 10;
    const start = (page - 1) * pageSize;
    return { data: filtered.slice(start, start + pageSize), total: filtered.length, page, pageSize };
  },

  async getRole(id: string): Promise<Role> {
    const role = mockRoles.find((r) => r.id === id);
    if (!role) throw new Error('角色不存在');
    return role;
  },

  async createRole(data: Partial<Role>): Promise<Role> {
    const newRole: Role = {
      id: `role-${Date.now()}`,
      name: data.name || '',
      displayName: data.displayName || '',
      description: data.description || '',
      permissions: data.permissions || [],
      userCount: 0,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };
    return newRole;
  },

  async updateRole(id: string, data: Partial<Role>): Promise<Role> {
    const role = await this.getRole(id);
    return { ...role, ...data, updatedAt: new Date().toISOString() };
  },

  async deleteRole(id: string): Promise<void> {
    void id
    await new Promise((resolve) => setTimeout(resolve, 500));
  },

  // API密钥管理
  async getApiKeys(params?: {
    page?: number;
    pageSize?: number;
    status?: string;
  }): Promise<PaginatedResponse<ApiKey>> {
    let filtered = [...mockApiKeys];

    if (params?.status) {
      filtered = filtered.filter((k) => k.status === params.status);
    }

    const page = params?.page || 1;
    const pageSize = params?.pageSize || 10;
    const start = (page - 1) * pageSize;
    const end = start + pageSize;

    return {
      data: filtered.slice(start, end),
      total: filtered.length,
      page,
      pageSize,
    };
  },

  async createApiKey(data: Partial<ApiKey>): Promise<ApiKey> {
    const newKey: ApiKey = {
      id: `key-${Date.now()}`,
      name: data.name || '',
      key: `sk-${Math.random().toString(36).substring(2, 15)}`,
      status: 'active',
      permissions: data.permissions || [],
      rateLimit: data.rateLimit || 100,
      usageCount: 0,
      lastUsedAt: new Date().toISOString(),
      expiresAt: new Date(Date.now() + 365 * 24 * 60 * 60 * 1000).toISOString(),
      createdAt: new Date().toISOString(),
      createdBy: 'current-user',
    };
    return newKey;
  },

  async updateApiKey(id: string, data: Partial<ApiKey>): Promise<ApiKey> {
    const item = mockApiKeys.find((key) => key.id === id);
    if (!item) throw new Error('API Key 不存在');
    Object.assign(item, data);
    return { ...item };
  },

  async rotateApiKey(id: string): Promise<ApiKey> {
    const item = mockApiKeys.find((key) => key.id === id);
    if (!item) throw new Error('API Key 不存在');
    item.key = `sk-mock-${Math.random().toString(36).slice(2)}`;
    item.status = 'active';
    return { ...item };
  },

  async deleteApiKey(id: string): Promise<void> {
    void id
    await new Promise((resolve) => setTimeout(resolve, 500));
  },

  // 审计日志
  async getAuditLogs(params?: {
    page?: number;
    pageSize?: number;
    userId?: string;
    action?: string;
    search?: string;
    startDate?: string;
    endDate?: string;
  }): Promise<PaginatedResponse<AuditLog>> {
    let filtered = [...mockAuditLogs];

    if (params?.userId) {
      filtered = filtered.filter((l) => l.userId === params.userId);
    }

    if (params?.action) {
      filtered = filtered.filter((l) => l.action.includes(params.action!));
    }
    if (params?.search) {
      const keyword = params.search.toLowerCase();
      filtered = filtered.filter((item) => item.userName.toLowerCase().includes(keyword) || item.resourceName.toLowerCase().includes(keyword));
    }

    const page = params?.page || 1;
    const pageSize = params?.pageSize || 10;
    const start = (page - 1) * pageSize;
    const end = start + pageSize;

    return {
      data: filtered.slice(start, end),
      total: filtered.length,
      page,
      pageSize,
    };
  },

  // 系统告警
  async getSystemAlerts(params?: {
    status?: string;
    severity?: string;
  }): Promise<SystemAlert[]> {
    let filtered = [...mockSystemAlerts];

    if (params?.status) {
      filtered = filtered.filter((a) => a.status === params.status);
    }

    if (params?.severity) {
      filtered = filtered.filter((a) => a.severity === params.severity);
    }

    return filtered;
  },

  async createAlert(data: Pick<SystemAlert, 'type' | 'title' | 'message' | 'source' | 'severity'>): Promise<SystemAlert> {
    const item: SystemAlert = { ...data, id: `alert-${Date.now()}`, status: 'active', count: 1, firstOccurredAt: new Date().toISOString(), lastOccurredAt: new Date().toISOString(), acknowledgedBy: null };
    mockSystemAlerts.push(item);
    return item;
  },

  async acknowledgeAlert(id: string): Promise<void> {
    const item = mockSystemAlerts.find((alert) => alert.id === id);
    if (item) { item.status = 'acknowledged'; item.acknowledgedBy = 'admin'; item.acknowledgedAt = new Date().toISOString(); }
    await new Promise((resolve) => setTimeout(resolve, 500));
  },

  async resolveAlert(id: string): Promise<void> {
    const item = mockSystemAlerts.find((alert) => alert.id === id);
    if (item) { item.status = 'resolved'; item.resolvedAt = new Date().toISOString(); }
    await new Promise((resolve) => setTimeout(resolve, 500));
  },

  async deleteAlert(id: string): Promise<void> {
    const index = mockSystemAlerts.findIndex((alert) => alert.id === id);
    if (index >= 0) mockSystemAlerts.splice(index, 1);
  },

  async getAlertRules(): Promise<AlertRule[]> {
    return [...mockAlertRules];
  },

  async createAlertRule(data: Omit<AlertRule, 'id' | 'status' | 'createdBy' | 'createdAt' | 'updatedAt'>): Promise<AlertRule> {
    const now = new Date().toISOString();
    const item: AlertRule = { ...data, id: `rule-${Date.now()}`, status: 'enabled', createdBy: 'admin', createdAt: now, updatedAt: now };
    mockAlertRules.push(item);
    return item;
  },

  async updateAlertRule(id: string, data: Partial<AlertRule>): Promise<AlertRule> {
    const index = mockAlertRules.findIndex((rule) => rule.id === id);
    if (index < 0) throw new Error('告警规则不存在');
    mockAlertRules[index] = { ...mockAlertRules[index], ...data, updatedAt: new Date().toISOString() };
    return mockAlertRules[index];
  },

  async deleteAlertRule(id: string): Promise<void> {
    const index = mockAlertRules.findIndex((rule) => rule.id === id);
    if (index >= 0) mockAlertRules.splice(index, 1);
  },

  // 系统设置
  async getSettings(): Promise<SystemSettings> {
    return mockSystemSettings;
  },

  async updateSettings(data: Partial<SystemSettings>): Promise<SystemSettings> {
    await new Promise((resolve) => setTimeout(resolve, 500));
    return { ...mockSystemSettings, ...data };
  },

  // 权限管理
  async getPermissions(): Promise<{ id: string; code: string; name: string; description: string | null }[]> {
    return mockPermissions;
  },

  async getPermissionsPaged(params?: { page?: number; pageSize?: number; keyword?: string }) {
    let filtered = [...mockPermissions];
    if (params?.keyword) {
      const kw = params.keyword.toLowerCase();
      filtered = filtered.filter(p =>
        p.code.toLowerCase().includes(kw) || p.name.toLowerCase().includes(kw)
      );
    }
    const page = params?.page || 1;
    const pageSize = params?.pageSize || 10;
    const start = (page - 1) * pageSize;
    return { data: filtered.slice(start, start + pageSize), total: filtered.length, page, pageSize };
  },

  async createPermission(data: { code: string; name: string; description?: string }) {
    await new Promise(r => setTimeout(r, 300));
    return { id: `perm-${Date.now()}`, code: data.code, name: data.name, description: data.description || null };
  },

  async updatePermission(id: string, data: { name?: string; description?: string }) {
    await new Promise(r => setTimeout(r, 300));
    const perm = mockPermissions.find(p => p.id === id);
    if (!perm) throw new Error('权限不存在');
    return { ...perm, ...data };
  },

  async deletePermission(id: string): Promise<void> {
    void id
    await new Promise(r => setTimeout(r, 300));
  },
};
