import { useContext } from 'react'
import { AuthorizationContext } from '@/contexts/authorization-context'

export function useAuthorization() {
  const value = useContext(AuthorizationContext)
  if (!value) throw new Error('useAuthorization 必须在 AuthorizationProvider 内使用')
  return value
}
