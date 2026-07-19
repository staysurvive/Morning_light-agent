import { ShieldX } from 'lucide-react'
import InlineNotice from '@/components/InlineNotice'
import { useAuthorization } from '@/hooks/useAuthorization'
import type { PermissionCode } from '@/services/permissions'

export default function PermissionGuard({ children, permission }: { children: React.ReactNode; permission: PermissionCode }) {
  const { can, error, loading } = useAuthorization()

  if (loading) return <p className="p-6 text-sm text-muted-foreground">正在校验访问权限...</p>
  if (error) return <div className="p-6"><InlineNotice kind="error" message={error} /></div>
  if (!can(permission)) {
    return (
      <div className="flex min-h-[60vh] flex-col items-center justify-center gap-3 p-6 text-center">
        <ShieldX className="h-10 w-10 text-red-600" />
        <h1 className="text-xl font-semibold text-gray-950">无权访问</h1>
        <p className="text-sm text-muted-foreground">当前账号没有访问此页面所需的权限。</p>
      </div>
    )
  }
  return <>{children}</>
}
