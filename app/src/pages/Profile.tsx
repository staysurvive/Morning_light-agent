import { Mail, ShieldCheck, UserRound } from 'lucide-react'
import InlineNotice from '@/components/InlineNotice'
import { useAuthorization } from '@/hooks/useAuthorization'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

export default function Profile() {
  const { currentUser: profile, error, loading } = useAuthorization()

  return (
    <div className="mx-auto max-w-4xl space-y-5 p-4 sm:p-6">
      <div>
        <h1 className="text-2xl font-semibold text-gray-950">个人资料</h1>
        <p className="mt-1 text-sm text-muted-foreground">当前登录身份及角色信息。</p>
      </div>

      {error && <InlineNotice kind="error" message={error} />}

      {loading && !error ? (
        <Card><CardContent className="py-16 text-center text-sm text-muted-foreground">正在加载个人资料...</CardContent></Card>
      ) : profile ? (
        <>
          <Card>
            <CardContent className="flex flex-col gap-5 pt-6 sm:flex-row sm:items-center">
              <Avatar className="h-20 w-20 border">
                <AvatarFallback className="bg-blue-600 text-2xl font-semibold text-white">
                  {profile.username.slice(0, 1).toUpperCase()}
                </AvatarFallback>
              </Avatar>
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center gap-2">
                  <h2 className="text-xl font-semibold">{profile.username}</h2>
                  <Badge variant={profile.is_active ? 'default' : 'secondary'}>{profile.is_active ? '账号启用' : '账号停用'}</Badge>
                </div>
                <p className="mt-1 break-all text-sm text-muted-foreground">{profile.email}</p>
                <p className="mt-2 text-xs text-muted-foreground">用户 ID：{profile.id}</p>
              </div>
            </CardContent>
          </Card>

          <div className="grid gap-4 md:grid-cols-2">
            <Card>
              <CardHeader><CardTitle className="flex items-center gap-2 text-base"><UserRound className="h-4 w-4" />身份信息</CardTitle></CardHeader>
              <CardContent>
                <dl className="grid grid-cols-[5rem_1fr] gap-x-4 gap-y-3 text-sm">
                  <dt className="text-muted-foreground">用户名</dt><dd className="font-medium">{profile.username}</dd>
                  <dt className="text-muted-foreground">邮箱</dt><dd className="flex min-w-0 items-center gap-2 break-all"><Mail className="h-4 w-4 shrink-0 text-muted-foreground" />{profile.email}</dd>
                  <dt className="text-muted-foreground">状态</dt><dd>{profile.is_active ? '启用' : '停用'}</dd>
                </dl>
              </CardContent>
            </Card>

            <Card>
              <CardHeader><CardTitle className="flex items-center gap-2 text-base"><ShieldCheck className="h-4 w-4" />角色</CardTitle></CardHeader>
              <CardContent>
                {profile.roles.length ? (
                  <div className="space-y-2">
                    {profile.roles.map((role) => (
                      <div className="rounded-md border px-3 py-2" key={role.id}>
                        <div className="flex items-center justify-between gap-3"><span className="text-sm font-medium">{role.name}</span><code className="text-xs text-muted-foreground">{role.code}</code></div>
                        <p className="mt-1 text-xs text-muted-foreground">{role.permissions.length} 项权限</p>
                      </div>
                    ))}
                  </div>
                ) : <p className="py-6 text-center text-sm text-muted-foreground">尚未分配角色</p>}
              </CardContent>
            </Card>
          </div>
        </>
      ) : null}
    </div>
  )
}
