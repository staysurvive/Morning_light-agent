import { useEffect, useState, type ReactNode } from 'react'
import { AuthorizationContext } from '@/contexts/authorization-context'
import { accessService, type UserWithRolesRead } from '@/services/access'
import { hasPermission, type PermissionCode } from '@/services/permissions'

export default function AuthorizationProvider({ children }: { children: ReactNode }) {
  const [currentUser, setCurrentUser] = useState<UserWithRolesRead | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true
    accessService.getCurrentUser()
      .then((user) => {
        if (active) {
          setCurrentUser(user)
          setError('')
        }
      })
      .catch((caught: unknown) => {
        if (active) setError(caught instanceof Error ? caught.message : '读取当前用户权限失败')
      })
      .finally(() => {
        if (active) setLoading(false)
      })
    return () => {
      active = false
    }
  }, [])

  const can = (permission: PermissionCode) => hasPermission(currentUser, permission)
  const canAll = (...permissions: PermissionCode[]) => permissions.every(can)

  return (
    <AuthorizationContext.Provider value={{ currentUser, error, loading, can, canAll }}>
      {children}
    </AuthorizationContext.Provider>
  )
}
