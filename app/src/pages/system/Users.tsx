import { useEffect, useState, type FormEvent } from 'react'
import { Eye, Plus, Search, ShieldCheck, Trash2, UserRoundCheck, UsersRound } from 'lucide-react'
import Modal from '@/components/Modal'
import InlineNotice from '@/components/InlineNotice'
import Pagination from '@/components/Pagination'
import { useAuthorization } from '@/hooks/useAuthorization'
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from '@/components/ui/alert-dialog'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { accessService, type RoleRead, type UserRead, type UserWithRolesRead } from '@/services/access'
import { PERMISSIONS } from '@/services/permissions'

const DEFAULT_PAGE_SIZE = 10

interface UserCreateModalProps {
  onClose: () => void
  onSaved: (message: string) => void
}

function UserCreateModal({ onClose, onSaved }: UserCreateModalProps) {
  const [form, setForm] = useState({ username: '', email: '', password: '' })
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault()
    if (!form.username.trim() || !form.email.trim() || !form.password) {
      setError('请填写用户名、邮箱和初始密码')
      return
    }

    setSubmitting(true)
    setError('')
    try {
      await accessService.createUser({
        username: form.username.trim(),
        email: form.email.trim(),
        password: form.password,
      })
      onSaved(`用户“${form.username.trim()}”已创建`)
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : '创建用户失败')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <Modal
      title="创建用户"
      description="新用户创建后默认启用，角色可在用户列表中单独分配。"
      onClose={onClose}
      footer={
        <div className="flex justify-end gap-2">
          <Button disabled={submitting} onClick={onClose} variant="outline">取消</Button>
          <Button disabled={submitting} form="create-user-form" type="submit">
            {submitting ? '创建中...' : '创建用户'}
          </Button>
        </div>
      }
    >
      <form className="space-y-4" id="create-user-form" onSubmit={handleSubmit}>
        <div className="space-y-2">
          <Label htmlFor="new-username">用户名</Label>
          <Input
            autoComplete="off"
            id="new-username"
            onChange={(event) => setForm((current) => ({ ...current, username: event.target.value }))}
            placeholder="例如：zhangsan"
            value={form.username}
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="new-email">邮箱</Label>
          <Input
            autoComplete="off"
            id="new-email"
            onChange={(event) => setForm((current) => ({ ...current, email: event.target.value }))}
            placeholder="name@example.com"
            type="email"
            value={form.email}
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="new-password">初始密码</Label>
          <Input
            autoComplete="new-password"
            id="new-password"
            onChange={(event) => setForm((current) => ({ ...current, password: event.target.value }))}
            type="password"
            value={form.password}
          />
        </div>
        {error && <InlineNotice kind="error" message={error} />}
      </form>
    </Modal>
  )
}

function UserDetailModal({ userId, onClose }: { userId: number; onClose: () => void }) {
  const [user, setUser] = useState<UserWithRolesRead | null>(null)
  const [roles, setRoles] = useState<RoleRead[]>([])
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true
    Promise.all([accessService.getUser(userId), accessService.getUserRoles(userId)])
      .then(([detail, assignments]) => {
        if (!active) return
        setUser(detail)
        setRoles(assignments[0]?.roles ?? detail.roles)
      })
      .catch((caught: unknown) => {
        if (active) setError(caught instanceof Error ? caught.message : '加载用户详情失败')
      })
    return () => {
      active = false
    }
  }, [userId])

  return (
    <Modal title="用户详情" description={`用户 ID：${userId}`} onClose={onClose} width="sm">
      {error ? (
        <InlineNotice kind="error" message={error} />
      ) : !user ? (
        <p className="py-8 text-center text-sm text-muted-foreground">正在加载用户信息...</p>
      ) : (
        <div className="space-y-5">
          <dl className="grid grid-cols-[6rem_1fr] gap-x-4 gap-y-3 text-sm">
            <dt className="text-muted-foreground">用户名</dt>
            <dd className="font-medium">{user.username}</dd>
            <dt className="text-muted-foreground">邮箱</dt>
            <dd className="break-all">{user.email}</dd>
            <dt className="text-muted-foreground">状态</dt>
            <dd><Badge variant={user.is_active ? 'default' : 'secondary'}>{user.is_active ? '启用' : '停用'}</Badge></dd>
          </dl>
          <div>
            <h3 className="mb-2 text-sm font-medium">已分配角色</h3>
            <div className="flex flex-wrap gap-2">
              {roles.length > 0 ? roles.map((role) => (
                <Badge key={role.id} variant="outline">{role.name} · {role.code}</Badge>
              )) : <span className="text-sm text-muted-foreground">尚未分配角色</span>}
            </div>
          </div>
        </div>
      )}
    </Modal>
  )
}

interface AssignRolesModalProps {
  user: UserRead
  onClose: () => void
  onSaved: (message: string) => void
}

function AssignRolesModal({ user, onClose, onSaved }: AssignRolesModalProps) {
  const [roles, setRoles] = useState<RoleRead[]>([])
  const [selectedIds, setSelectedIds] = useState<number[]>([])
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true
    Promise.all([accessService.listRoles(), accessService.getUserRoles(user.id)])
      .then(([allRoles, assignments]) => {
        if (!active) return
        setRoles(allRoles)
        setSelectedIds((assignments[0]?.roles ?? []).map((role) => role.id))
      })
      .catch((caught: unknown) => {
        if (active) setError(caught instanceof Error ? caught.message : '加载角色失败')
      })
      .finally(() => {
        if (active) setLoading(false)
      })
    return () => {
      active = false
    }
  }, [user.id])

  const handleSave = async () => {
    setSubmitting(true)
    setError('')
    try {
      await accessService.assignUserRoles(user.id, selectedIds)
      onSaved(`用户“${user.username}”的角色已更新`)
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : '保存角色失败')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <Modal
      title="分配角色"
      description={`为用户“${user.username}”整体替换角色集合。`}
      onClose={onClose}
      footer={
        <div className="flex justify-end gap-2">
          <Button disabled={submitting} onClick={onClose} variant="outline">取消</Button>
          <Button disabled={loading || submitting} onClick={handleSave}>
            {submitting ? '保存中...' : '保存角色'}
          </Button>
        </div>
      }
    >
      {error && <div className="mb-4"><InlineNotice kind="error" message={error} /></div>}
      {loading ? (
        <p className="py-8 text-center text-sm text-muted-foreground">正在加载角色...</p>
      ) : roles.length === 0 ? (
        <p className="py-8 text-center text-sm text-muted-foreground">暂无可分配角色</p>
      ) : (
        <div className="space-y-2">
          {roles.map((role) => (
            <label className="flex cursor-pointer items-start gap-3 rounded-md border p-3 hover:bg-gray-50" key={role.id}>
              <input
                checked={selectedIds.includes(role.id)}
                className="mt-1 h-4 w-4"
                onChange={() => setSelectedIds((current) =>
                  current.includes(role.id)
                    ? current.filter((id) => id !== role.id)
                    : [...current, role.id],
                )}
                type="checkbox"
              />
              <span className="min-w-0">
                <span className="block text-sm font-medium">{role.name}</span>
                <span className="block text-xs text-muted-foreground">{role.code} · {role.description || '无描述'}</span>
              </span>
            </label>
          ))}
        </div>
      )}
    </Modal>
  )
}

export default function SystemUsers() {
  const { can, canAll } = useAuthorization()
  const [users, setUsers] = useState<UserRead[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(DEFAULT_PAGE_SIZE)
  const [keyword, setKeyword] = useState('')
  const [searchInput, setSearchInput] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [refreshKey, setRefreshKey] = useState(0)
  const [createOpen, setCreateOpen] = useState(false)
  const [detailUserId, setDetailUserId] = useState<number | null>(null)
  const [assignUser, setAssignUser] = useState<UserRead | null>(null)
  const [deleteUser, setDeleteUser] = useState<UserRead | null>(null)
  const [deleting, setDeleting] = useState(false)

  useEffect(() => {
    let active = true
    accessService.searchUsers({ page, page_size: pageSize, keyword: keyword || undefined })
      .then((result) => {
        if (!active) return
        setUsers(result.items)
        setTotal(result.total)
        setError('')
      })
      .catch((caught: unknown) => {
        if (active) setError(caught instanceof Error ? caught.message : '加载用户失败')
      })
      .finally(() => {
        if (active) setLoading(false)
      })
    return () => {
      active = false
    }
  }, [keyword, page, pageSize, refreshKey])

  const refresh = (message: string) => {
    setCreateOpen(false)
    setAssignUser(null)
    setSuccess(message)
    setLoading(true)
    setRefreshKey((current) => current + 1)
  }

  const handleSearch = (event: FormEvent) => {
    event.preventDefault()
    setSuccess('')
    setLoading(true)
    setKeyword(searchInput.trim())
    setPage(1)
    setRefreshKey((current) => current + 1)
  }

  const handlePageChange = (nextPage: number) => {
    setLoading(true)
    setPage(nextPage)
  }

  const handlePageSizeChange = (nextPageSize: number) => {
    setLoading(true)
    setPageSize(nextPageSize)
    setPage(1)
  }

  const handleDelete = async () => {
    if (!deleteUser) return
    setDeleting(true)
    setError('')
    setSuccess('')
    try {
      await accessService.deleteUser(deleteUser.id)
      const moveToPreviousPage = users.length === 1 && page > 1
      setDeleteUser(null)
      setSuccess(`用户“${deleteUser.username}”已删除`)
      setLoading(true)
      if (moveToPreviousPage) setPage((current) => current - 1)
      else setRefreshKey((current) => current + 1)
    } catch (caught) {
      setDeleteUser(null)
      setError(caught instanceof Error ? caught.message : '删除用户失败')
    } finally {
      setDeleting(false)
    }
  }

  const currentPageActive = users.filter((user) => user.is_active).length
  const totalPages = Math.max(1, Math.ceil(total / pageSize))

  return (
    <div className="space-y-5 p-4 sm:p-6">
      <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-center">
        <div>
          <h1 className="text-2xl font-semibold text-gray-950">用户管理</h1>
          <p className="mt-1 text-sm text-muted-foreground">创建用户、查看身份状态并分配角色。</p>
        </div>
        {can(PERMISSIONS.userCreate) && <Button onClick={() => setCreateOpen(true)}><Plus className="h-4 w-4" />创建用户</Button>}
      </div>

      {success && <InlineNotice kind="success" message={success} />}
      {error && <InlineNotice kind="error" message={error} />}

      <div className="grid gap-3 sm:grid-cols-3">
        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-sm font-medium">用户总数</CardTitle></CardHeader>
          <CardContent className="flex items-center justify-between"><span className="text-2xl font-semibold">{total}</span><UsersRound className="h-5 w-5 text-blue-600" /></CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-sm font-medium">本页启用</CardTitle></CardHeader>
          <CardContent className="flex items-center justify-between"><span className="text-2xl font-semibold">{currentPageActive}</span><UserRoundCheck className="h-5 w-5 text-emerald-600" /></CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-sm font-medium">分页</CardTitle></CardHeader>
          <CardContent className="flex items-center justify-between"><span className="text-2xl font-semibold">{page}/{totalPages}</span><span className="text-xs text-muted-foreground">每页 {pageSize} 条</span></CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader className="pb-3">
          <form className="flex max-w-lg flex-col gap-2 sm:flex-row" onSubmit={handleSearch}>
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input className="pl-9" onChange={(event) => setSearchInput(event.target.value)} placeholder="搜索用户名或邮箱" value={searchInput} />
            </div>
            <Button type="submit" variant="outline">搜索</Button>
          </form>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <Table>
              <TableHeader><TableRow><TableHead className="w-20">ID</TableHead><TableHead>用户名</TableHead><TableHead>邮箱</TableHead><TableHead className="w-24">状态</TableHead><TableHead className="w-36 text-right">操作</TableHead></TableRow></TableHeader>
              <TableBody>
                {loading ? (
                  <TableRow><TableCell className="h-28 text-center text-muted-foreground" colSpan={5}>正在加载用户...</TableCell></TableRow>
                ) : users.length === 0 ? (
                  <TableRow><TableCell className="h-28 text-center text-muted-foreground" colSpan={5}>没有符合条件的用户</TableCell></TableRow>
                ) : users.map((user) => (
                  <TableRow key={user.id}>
                    <TableCell className="text-muted-foreground">{user.id}</TableCell>
                    <TableCell className="font-medium">{user.username}</TableCell>
                    <TableCell>{user.email}</TableCell>
                    <TableCell><Badge variant={user.is_active ? 'default' : 'secondary'}>{user.is_active ? '启用' : '停用'}</Badge></TableCell>
                    <TableCell>
                      <div className="flex justify-end gap-1">
                        <Button aria-label={`查看 ${user.username}`} onClick={() => setDetailUserId(user.id)} size="icon" title="查看详情" variant="ghost"><Eye className="h-4 w-4" /></Button>
                        {canAll(PERMISSIONS.userAssignRoles, PERMISSIONS.roleRead) && <Button aria-label={`为 ${user.username} 分配角色`} onClick={() => setAssignUser(user)} size="icon" title="分配角色" variant="ghost"><ShieldCheck className="h-4 w-4" /></Button>}
                        {can(PERMISSIONS.userDelete) && <Button aria-label={`删除 ${user.username}`} onClick={() => setDeleteUser(user)} size="icon" title="删除用户" variant="ghost"><Trash2 className="h-4 w-4 text-red-600" /></Button>}
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
          <Pagination disabled={loading} onChange={handlePageChange} onPageSizeChange={handlePageSizeChange} page={page} pageSize={pageSize} total={total} />
        </CardContent>
      </Card>

      {createOpen && <UserCreateModal onClose={() => setCreateOpen(false)} onSaved={refresh} />}
      {detailUserId !== null && <UserDetailModal userId={detailUserId} onClose={() => setDetailUserId(null)} />}
      {assignUser && <AssignRolesModal user={assignUser} onClose={() => setAssignUser(null)} onSaved={refresh} />}
      <AlertDialog open={Boolean(deleteUser)} onOpenChange={(open) => { if (!open) setDeleteUser(null) }}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>删除用户</AlertDialogTitle>
            <AlertDialogDescription>确定删除用户“{deleteUser?.username}”吗？该用户的角色关联也会一并移除，此操作无法撤销。</AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={deleting}>取消</AlertDialogCancel>
            <AlertDialogAction className="bg-red-600 text-white hover:bg-red-700" disabled={deleting} onClick={handleDelete}>{deleting ? '删除中...' : '确认删除'}</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}
