import { createContext } from 'react'
import type { UserWithRolesRead } from '@/services/access'
import type { PermissionCode } from '@/services/permissions'

export interface AuthorizationValue {
  currentUser: UserWithRolesRead | null
  error: string
  loading: boolean
  can: (permission: PermissionCode) => boolean
  canAll: (...permissions: PermissionCode[]) => boolean
}

export const AuthorizationContext = createContext<AuthorizationValue | null>(null)
