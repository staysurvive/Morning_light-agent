import { useEffect, useState, type FormEvent } from 'react'
import { Edit, Eye, KeyRound, Plus, Search, Shield, Trash2 } from 'lucide-react'
import InlineNotice from '@/components/InlineNotice'
import Modal from '@/components/Modal'
import Pagination from '@/components/Pagination'
import { useAuthorization } from '@/hooks/useAuthorization'
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from '@/components/ui/alert-dialog'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { accessService, type PermissionRead, type RoleRead } from '@/services/access'
import { PERMISSIONS } from '@/services/permissions'

const DEFAULT_PAGE_SIZE = 10

interface RoleFormModalProps {
  role?: RoleRead
  onClose: () => void
  onSaved: (message: string) => void
}

function RoleFormModal({ role, onClose, onSaved }: RoleFormModalProps) {
  const [form, setForm] = useState({ code: role?.code ?? '', name: role?.name ?? '', description: role?.description ?? '' })
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault()
    if (!form.code.trim() || !form.name.trim()) {
      setError('请填写角色编码和名称')
      return
    }
    setSubmitting(true)
    setError('')
    try {
      if (role) {
        await accessService.updateRole(role.id, { name: form.name.trim(), description: form.description.trim() || null })
        onSaved(`角色“${form.name.trim()}”已更新`)
      } else {
        await accessService.createRole({ code: form.code.trim(), name: form.name.trim(), description: form.description.trim() || null })
        onSaved(`角色“${form.name.trim()}”已创建`)
      }
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : '保存角色失败')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <Modal
      title={role ? '编辑角色' : '创建角色'}
      description={role ? '角色编码创建后不可修改。' : '角色用于聚合一组权限，并分配给用户。'}
      onClose={onClose}
      footer={<div className="flex justify-end gap-2"><Button disabled={submitting} onClick={onClose} variant="outline">取消</Button><Button disabled={submitting} form="role-form" type="submit">{submitting ? '保存中...' : '保存角色'}</Button></div>}
    >
      <form className="space-y-4" id="role-form" onSubmit={handleSubmit}>
        <div className="space-y-2"><Label htmlFor="role-code">角色编码</Label><Input disabled={Boolean(role)} id="role-code" onChange={(event) => setForm((current) => ({ ...current, code: event.target.value }))} placeholder="例如：admin" value={form.code} /></div>
        <div className="space-y-2"><Label htmlFor="role-name">角色名称</Label><Input id="role-name" onChange={(event) => setForm((current) => ({ ...current, name: event.target.value }))} placeholder="例如：平台管理员" value={form.name} /></div>
        <div className="space-y-2"><Label htmlFor="role-description">描述</Label><Input id="role-description" onChange={(event) => setForm((current) => ({ ...current, description: event.target.value }))} placeholder="说明角色的职责范围" value={form.description} /></div>
        {error && <InlineNotice kind="error" message={error} />}
      </form>
    </Modal>
  )
}

function RoleDetailModal({ roleId, onClose }: { roleId: number; onClose: () => void }) {
  const [role, setRole] = useState<RoleRead | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true
    accessService.getRole(roleId)
      .then((result) => { if (active) setRole(result) })
      .catch((caught: unknown) => { if (active) setError(caught instanceof Error ? caught.message : '加载角色详情失败') })
    return () => { active = false }
  }, [roleId])

  return (
    <Modal title="角色详情" description={`角色 ID：${roleId}`} onClose={onClose}>
      {error ? <InlineNotice kind="error" message={error} /> : !role ? <p className="py-8 text-center text-sm text-muted-foreground">正在加载角色...</p> : (
        <div className="space-y-5">
          <dl className="grid grid-cols-[6rem_1fr] gap-x-4 gap-y-3 text-sm"><dt className="text-muted-foreground">角色名称</dt><dd className="font-medium">{role.name}</dd><dt className="text-muted-foreground">角色编码</dt><dd><code className="rounded bg-gray-100 px-1.5 py-0.5 text-xs">{role.code}</code></dd><dt className="text-muted-foreground">描述</dt><dd>{role.description || '无描述'}</dd></dl>
          <div><h3 className="mb-2 text-sm font-medium">权限集合（{role.permissions.length}）</h3><div className="flex flex-wrap gap-2">{role.permissions.length ? role.permissions.map((permission) => <Badge key={permission.id} variant="outline">{permission.name} · {permission.code}</Badge>) : <span className="text-sm text-muted-foreground">尚未分配权限</span>}</div></div>
        </div>
      )}
    </Modal>
  )
}

interface AssignPermissionsModalProps {
  role: RoleRead
  onClose: () => void
  onSaved: (message: string) => void
}

function AssignPermissionsModal({ role, onClose, onSaved }: AssignPermissionsModalProps) {
  const [permissions, setPermissions] = useState<PermissionRead[]>([])
  const [selectedIds, setSelectedIds] = useState<number[]>([])
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true
    Promise.all([accessService.listPermissions(), accessService.getRole(role.id)])
      .then(([allPermissions, detail]) => { if (active) { setPermissions(allPermissions); setSelectedIds(detail.permissions.map((permission) => permission.id)) } })
      .catch((caught: unknown) => { if (active) setError(caught instanceof Error ? caught.message : '加载权限失败') })
      .finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [role.id])

  const handleSave = async () => {
    setSubmitting(true)
    setError('')
    try {
      await accessService.assignRolePermissions(role.id, selectedIds)
      onSaved(`角色“${role.name}”的权限已更新`)
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : '保存权限失败')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <Modal title="分配权限" description={`为角色“${role.name}”整体替换权限集合。`} onClose={onClose} width="lg" footer={<div className="flex justify-end gap-2"><Button disabled={submitting} onClick={onClose} variant="outline">取消</Button><Button disabled={loading || submitting} onClick={handleSave}>{submitting ? '保存中...' : '保存权限'}</Button></div>}>
      {error && <div className="mb-4"><InlineNotice kind="error" message={error} /></div>}
      {loading ? <p className="py-8 text-center text-sm text-muted-foreground">正在加载权限...</p> : permissions.length === 0 ? <p className="py-8 text-center text-sm text-muted-foreground">暂无可分配权限</p> : (
        <div className="grid gap-2 sm:grid-cols-2">
          {permissions.map((permission) => <label className="flex cursor-pointer items-start gap-3 rounded-md border p-3 hover:bg-gray-50" key={permission.id}><input checked={selectedIds.includes(permission.id)} className="mt-1 h-4 w-4" onChange={() => setSelectedIds((current) => current.includes(permission.id) ? current.filter((id) => id !== permission.id) : [...current, permission.id])} type="checkbox" /><span className="min-w-0"><span className="block text-sm font-medium">{permission.name}</span><code className="block truncate text-xs text-muted-foreground">{permission.code}</code></span></label>)}
        </div>
      )}
    </Modal>
  )
}

export default function SystemRoles() {
  const { can, canAll } = useAuthorization()
  const [roles, setRoles] = useState<RoleRead[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(DEFAULT_PAGE_SIZE)
  const [keyword, setKeyword] = useState('')
  const [searchInput, setSearchInput] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [refreshKey, setRefreshKey] = useState(0)
  const [formRole, setFormRole] = useState<RoleRead | 'new' | null>(null)
  const [detailRoleId, setDetailRoleId] = useState<number | null>(null)
  const [permissionsRole, setPermissionsRole] = useState<RoleRead | null>(null)
  const [deleteRole, setDeleteRole] = useState<RoleRead | null>(null)
  const [deleting, setDeleting] = useState(false)

  useEffect(() => {
    let active = true
    accessService.searchRoles({ page, page_size: pageSize, keyword: keyword || undefined })
      .then((result) => { if (active) { setRoles(result.items); setTotal(result.total); setError('') } })
      .catch((caught: unknown) => { if (active) setError(caught instanceof Error ? caught.message : '加载角色失败') })
      .finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [keyword, page, pageSize, refreshKey])

  const refresh = (message: string) => {
    setFormRole(null)
    setPermissionsRole(null)
    setSuccess(message)
    setLoading(true)
    setRefreshKey((current) => current + 1)
  }

  const handleSearch = (event: FormEvent) => {
    event.preventDefault()
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
    if (!deleteRole) return
    setDeleting(true)
    setError('')
    setSuccess('')
    try {
      await accessService.deleteRole(deleteRole.id)
      const moveToPreviousPage = roles.length === 1 && page > 1
      setDeleteRole(null)
      setSuccess(`角色“${deleteRole.name}”已删除`)
      setLoading(true)
      if (moveToPreviousPage) setPage((current) => current - 1)
      else setRefreshKey((current) => current + 1)
    } catch (caught) {
      setDeleteRole(null)
      setError(caught instanceof Error ? caught.message : '删除角色失败')
    } finally {
      setDeleting(false)
    }
  }

  const permissionCount = roles.reduce((count, role) => count + role.permissions.length, 0)

  return (
    <div className="space-y-5 p-4 sm:p-6">
      <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-center"><div><h1 className="text-2xl font-semibold text-gray-950">角色管理</h1><p className="mt-1 text-sm text-muted-foreground">维护角色定义，并为角色分配权限。</p></div>{can(PERMISSIONS.roleCreate) && <Button onClick={() => setFormRole('new')}><Plus className="h-4 w-4" />创建角色</Button>}</div>
      {success && <InlineNotice kind="success" message={success} />}{error && <InlineNotice kind="error" message={error} />}
      <div className="grid gap-3 sm:grid-cols-3"><Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">角色总数</CardTitle></CardHeader><CardContent className="flex items-center justify-between"><span className="text-2xl font-semibold">{total}</span><Shield className="h-5 w-5 text-blue-600" /></CardContent></Card><Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">本页权限关联</CardTitle></CardHeader><CardContent className="flex items-center justify-between"><span className="text-2xl font-semibold">{permissionCount}</span><KeyRound className="h-5 w-5 text-emerald-600" /></CardContent></Card><Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">当前页</CardTitle></CardHeader><CardContent><span className="text-2xl font-semibold">{page}</span></CardContent></Card></div>
      <Card><CardHeader className="pb-3"><form className="flex max-w-lg flex-col gap-2 sm:flex-row" onSubmit={handleSearch}><div className="relative flex-1"><Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" /><Input className="pl-9" onChange={(event) => setSearchInput(event.target.value)} placeholder="搜索角色编码或名称" value={searchInput} /></div><Button type="submit" variant="outline">搜索</Button></form></CardHeader><CardContent><div className="overflow-x-auto"><Table><TableHeader><TableRow><TableHead className="w-20">ID</TableHead><TableHead>角色</TableHead><TableHead>描述</TableHead><TableHead className="w-28">权限数</TableHead><TableHead className="w-44 text-right">操作</TableHead></TableRow></TableHeader><TableBody>{loading ? <TableRow><TableCell className="h-28 text-center text-muted-foreground" colSpan={5}>正在加载角色...</TableCell></TableRow> : roles.length === 0 ? <TableRow><TableCell className="h-28 text-center text-muted-foreground" colSpan={5}>没有符合条件的角色</TableCell></TableRow> : roles.map((role) => <TableRow key={role.id}><TableCell className="text-muted-foreground">{role.id}</TableCell><TableCell><div className="font-medium">{role.name}</div><code className="text-xs text-muted-foreground">{role.code}</code></TableCell><TableCell className="max-w-sm text-sm text-muted-foreground">{role.description || '无描述'}</TableCell><TableCell><Badge variant="secondary">{role.permissions.length}</Badge></TableCell><TableCell><div className="flex justify-end gap-1"><Button aria-label={`查看 ${role.name}`} onClick={() => setDetailRoleId(role.id)} size="icon" title="查看详情" variant="ghost"><Eye className="h-4 w-4" /></Button>{can(PERMISSIONS.roleUpdate) && <Button aria-label={`编辑 ${role.name}`} onClick={() => setFormRole(role)} size="icon" title="编辑角色" variant="ghost"><Edit className="h-4 w-4" /></Button>}{canAll(PERMISSIONS.roleAssignPermissions, PERMISSIONS.permissionRead) && <Button aria-label={`为 ${role.name} 分配权限`} onClick={() => setPermissionsRole(role)} size="icon" title="分配权限" variant="ghost"><KeyRound className="h-4 w-4" /></Button>}{can(PERMISSIONS.roleDelete) && <Button aria-label={`删除 ${role.name}`} onClick={() => setDeleteRole(role)} size="icon" title="删除角色" variant="ghost"><Trash2 className="h-4 w-4 text-red-600" /></Button>}</div></TableCell></TableRow>)}</TableBody></Table></div><Pagination disabled={loading} onChange={handlePageChange} onPageSizeChange={handlePageSizeChange} page={page} pageSize={pageSize} total={total} /></CardContent></Card>
      {formRole && <RoleFormModal role={formRole === 'new' ? undefined : formRole} onClose={() => setFormRole(null)} onSaved={refresh} />}
      {detailRoleId !== null && <RoleDetailModal roleId={detailRoleId} onClose={() => setDetailRoleId(null)} />}
      {permissionsRole && <AssignPermissionsModal role={permissionsRole} onClose={() => setPermissionsRole(null)} onSaved={refresh} />}
      <AlertDialog open={Boolean(deleteRole)} onOpenChange={(open) => { if (!open) setDeleteRole(null) }}><AlertDialogContent><AlertDialogHeader><AlertDialogTitle>删除角色</AlertDialogTitle><AlertDialogDescription>确定删除角色“{deleteRole?.name}”吗？用户与该角色的关联也将失效。</AlertDialogDescription></AlertDialogHeader><AlertDialogFooter><AlertDialogCancel disabled={deleting}>取消</AlertDialogCancel><AlertDialogAction className="bg-red-600 text-white hover:bg-red-700" disabled={deleting} onClick={handleDelete}>{deleting ? '删除中...' : '确认删除'}</AlertDialogAction></AlertDialogFooter></AlertDialogContent></AlertDialog>
    </div>
  )
}
