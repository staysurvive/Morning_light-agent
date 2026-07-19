export interface User {
  id: string
  username: string
  name: string
  email: string
  avatar?: string
  role: string
  status: 'active' | 'inactive'
  department: string
  lastLoginAt: string
  createdAt: string
}

export interface Role {
  id: string
  name: string
  displayName: string
  description: string
  permissions: string[]
  userCount: number
  createdAt: string
  updatedAt: string
}

export interface Permission {
  id: string
  code: string
  name: string
  description: string | null
}

export interface ApiKey {
  id: string
  name: string
  key: string
  permissions: string[]
  status: 'active' | 'disabled' | 'expired'
  rateLimit: number
  usageCount: number
  lastUsedAt: string | null
  expiresAt: string | null
  createdBy: string
  createdAt: string
}

export interface AuditLog {
  id: string
  userId: string
  userName: string
  action: string
  resource: string
  resourceName: string
  details: Record<string, unknown>
  ip: string
  userAgent: string
  status: 'success' | 'failed'
  timestamp: string
  module?: string
  detail?: string
  ipAddress?: string
}

export interface AlertRule {
  id: string
  name: string
  description: string | null
  notifications: string[]
  condition: {
    metric: string
    operator: 'gt' | 'lt' | 'eq' | 'gte' | 'lte'
    threshold: number
    duration: number
  }
  status: 'enabled' | 'disabled'
  createdBy: string
  createdAt: string
  updatedAt: string
}

export interface ActiveAlert {
  id: string
  ruleId: string
  ruleName: string
  level: 'info' | 'warning' | 'error' | 'critical'
  message: string
  triggeredAt: string
  duration: string
  status: 'active' | 'acknowledged' | 'resolved'
}

export interface SystemAlert {
  id: string
  type: 'error' | 'warning' | 'info'
  title: string
  message: string
  source: string
  severity: 'low' | 'medium' | 'high' | 'critical'
  status: 'active' | 'acknowledged' | 'resolved'
  count: number
  firstOccurredAt: string
  lastOccurredAt: string
  acknowledgedBy: string | null
  acknowledgedAt?: string
  resolvedAt?: string
}

export interface SystemSettings {
  systemName: string
  systemDescription: string
  defaultLanguage: string
  defaultModel: string
  defaultTemperature: number
  defaultMaxTokens: number
  smtpServer: string
  smtpPort: number
  senderEmail: string
}
