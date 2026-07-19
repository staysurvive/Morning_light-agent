import { useEffect, useState, type FormEvent } from 'react'
import { Edit, Eye, KeyRound, Layers3, Plus, Search, Trash2 } from 'lucide-react'
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
import { accessService, type PermissionRead } from '@/services/access'
import { PERMISSIONS } from '@/services/permissions'

const DEFAULT_PAGE_SIZE = 10

const getModule = (code: string) => code.split(/[:_]/)[0] || 'other'

interface PermissionFormModalProps {
  permission?: PermissionRead
  onClose: () => void
  onSaved: (message: string) => void
}

function PermissionFormModal({ permission, onClose, onSaved }: PermissionFormModalProps) {
  const [form, setForm] = useState({ code: permission?.code ?? '', name: permission?.name ?? '', description: permission?.description ?? '' })
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault()
    if (!form.code.trim() || !form.name.trim()) {
      setError('请填写权限编码和名称')
      return
    }
    setSubmitting(true)
    setError('')
    try {
      if (permission) {
        await accessService.updatePermission(permission.id, { name: form.name.trim(), description: form.description.trim() || null })
        onSaved(`权限“${form.name.trim()}”已更新`)
      } else {
        await accessService.createPermission({ code: form.code.trim(), name: form.name.trim(), description: form.description.trim() || null })
        onSaved(`权限“${form.name.trim()}”已创建`)
      }
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : '保存权限失败')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <Modal title={permission ? '编辑权限' : '创建权限'} description="权限编码采用“资源_动作”，创建后不可修改。" onClose={onClose} footer={<div className="flex justify-end gap-2"><Button disabled={submitting} onClick={onClose} variant="outline">取消</Button><Button disabled={submitting} form="permission-form" type="submit">{submitting ? '保存中...' : '保存权限'}</Button></div>}>
      <form className="space-y-4" id="permission-form" onSubmit={handleSubmit}>
        <div className="space-y-2"><Label htmlFor="permission-code">权限编码</Label><Input disabled={Boolean(permission)} id="permission-code" onChange={(event) => setForm((current) => ({ ...current, code: event.target.value }))} placeholder="例如：agent_read" value={form.code} /></div>
        <div className="space-y-2"><Label htmlFor="permission-name">权限名称</Label><Input id="permission-name" onChange={(event) => setForm((current) => ({ ...current, name: event.target.value }))} placeholder="例如：查看 Agent" value={form.name} /></div>
        <div className="space-y-2"><Label htmlFor="permission-description">描述</Label><Input id="permission-description" onChange={(event) => setForm((current) => ({ ...current, description: event.target.value }))} placeholder="说明权限允许的操作" value={form.description} /></div>
        {error && <InlineNotice kind="error" message={error} />}
      </form>
    </Modal>
  )
}

function PermissionDetailModal({ permissionId, onClose }: { permissionId: number; onClose: () => void }) {
  const [permission, setPermission] = useState<PermissionRead | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true
    accessService.getPermission(permissionId)
      .then((result) => { if (active) setPermission(result) })
      .catch((caught: unknown) => { if (active) setError(caught instanceof Error ? caught.message : '加载权限详情失败') })
    return () => { active = false }
  }, [permissionId])

  return (
    <Modal title="权限详情" description={`权限 ID：${permissionId}`} onClose={onClose} width="sm">
      {error ? <InlineNotice kind="error" message={error} /> : !permission ? <p className="py-8 text-center text-sm text-muted-foreground">正在加载权限...</p> : <dl className="grid grid-cols-[6rem_1fr] gap-x-4 gap-y-3 text-sm"><dt className="text-muted-foreground">权限名称</dt><dd className="font-medium">{permission.name}</dd><dt className="text-muted-foreground">权限编码</dt><dd><code className="rounded bg-gray-100 px-1.5 py-0.5 text-xs">{permission.code}</code></dd><dt className="text-muted-foreground">所属模块</dt><dd><Badge variant="outline">{getModule(permission.code)}</Badge></dd><dt className="text-muted-foreground">描述</dt><dd>{permission.description || '无描述'}</dd></dl>}
    </Modal>
  )
}

export default function SystemPermissions() {
  const { can } = useAuthorization()
  const [permissions, setPermissions] = useState<PermissionRead[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(DEFAULT_PAGE_SIZE)
  const [keyword, setKeyword] = useState('')
  const [searchInput, setSearchInput] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [refreshKey, setRefreshKey] = useState(0)
  const [formPermission, setFormPermission] = useState<PermissionRead | 'new' | null>(null)
  const [detailPermissionId, setDetailPermissionId] = useState<number | null>(null)
  const [deletePermission, setDeletePermission] = useState<PermissionRead | null>(null)
  const [deleting, setDeleting] = useState(false)

  useEffect(() => {
    let active = true
    accessService.searchPermissions({ page, page_size: pageSize, keyword: keyword || undefined })
      .then((result) => { if (active) { setPermissions(result.items); setTotal(result.total); setError('') } })
      .catch((caught: unknown) => { if (active) setError(caught instanceof Error ? caught.message : '加载权限失败') })
      .finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [keyword, page, pageSize, refreshKey])

  const refresh = (message: string) => {
    setFormPermission(null)
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
    if (!deletePermission) return
    setDeleting(true)
    setError('')
    setSuccess('')
    try {
      await accessService.deletePermission(deletePermission.id)
      const moveToPreviousPage = permissions.length === 1 && page > 1
      setDeletePermission(null)
      setSuccess(`权限“${deletePermission.name}”已删除`)
      setLoading(true)
      if (moveToPreviousPage) setPage((current) => current - 1)
      else setRefreshKey((current) => current + 1)
    } catch (caught) {
      setDeletePermission(null)
      setError(caught instanceof Error ? caught.message : '删除权限失败')
    } finally {
      setDeleting(false)
    }
  }

  const moduleCount = new Set(permissions.map((permission) => getModule(permission.code))).size

  return (
    <div className="space-y-5 p-4 sm:p-6">
      <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-center"><div><h1 className="text-2xl font-semibold text-gray-950">权限管理</h1><p className="mt-1 text-sm text-muted-foreground">维护可分配给角色的原子权限。</p></div>{can(PERMISSIONS.permissionCreate) && <Button onClick={() => setFormPermission('new')}><Plus className="h-4 w-4" />创建权限</Button>}</div>
      {success && <InlineNotice kind="success" message={success} />}{error && <InlineNotice kind="error" message={error} />}
      <div className="grid gap-3 sm:grid-cols-3"><Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">权限总数</CardTitle></CardHeader><CardContent className="flex items-center justify-between"><span className="text-2xl font-semibold">{total}</span><KeyRound className="h-5 w-5 text-blue-600" /></CardContent></Card><Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">本页模块数</CardTitle></CardHeader><CardContent className="flex items-center justify-between"><span className="text-2xl font-semibold">{moduleCount}</span><Layers3 className="h-5 w-5 text-emerald-600" /></CardContent></Card><Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">当前页</CardTitle></CardHeader><CardContent><span className="text-2xl font-semibold">{page}</span></CardContent></Card></div>
      <Card><CardHeader className="pb-3"><form className="flex max-w-lg flex-col gap-2 sm:flex-row" onSubmit={handleSearch}><div className="relative flex-1"><Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" /><Input className="pl-9" onChange={(event) => setSearchInput(event.target.value)} placeholder="搜索权限编码或名称" value={searchInput} /></div><Button type="submit" variant="outline">搜索</Button></form></CardHeader><CardContent><div className="overflow-x-auto"><Table><TableHeader><TableRow><TableHead className="w-20">ID</TableHead><TableHead className="w-28">模块</TableHead><TableHead>权限</TableHead><TableHead>描述</TableHead><TableHead className="w-36 text-right">操作</TableHead></TableRow></TableHeader><TableBody>{loading ? <TableRow><TableCell className="h-28 text-center text-muted-foreground" colSpan={5}>正在加载权限...</TableCell></TableRow> : permissions.length === 0 ? <TableRow><TableCell className="h-28 text-center text-muted-foreground" colSpan={5}>没有符合条件的权限</TableCell></TableRow> : permissions.map((permission) => <TableRow key={permission.id}><TableCell className="text-muted-foreground">{permission.id}</TableCell><TableCell><Badge variant="outline">{getModule(permission.code)}</Badge></TableCell><TableCell><div className="font-medium">{permission.name}</div><code className="text-xs text-muted-foreground">{permission.code}</code></TableCell><TableCell className="max-w-sm text-sm text-muted-foreground">{permission.description || '无描述'}</TableCell><TableCell><div className="flex justify-end gap-1"><Button aria-label={`查看 ${permission.name}`} onClick={() => setDetailPermissionId(permission.id)} size="icon" title="查看详情" variant="ghost"><Eye className="h-4 w-4" /></Button>{can(PERMISSIONS.permissionUpdate) && <Button aria-label={`编辑 ${permission.name}`} onClick={() => setFormPermission(permission)} size="icon" title="编辑权限" variant="ghost"><Edit className="h-4 w-4" /></Button>}{can(PERMISSIONS.permissionDelete) && <Button aria-label={`删除 ${permission.name}`} onClick={() => setDeletePermission(permission)} size="icon" title="删除权限" variant="ghost"><Trash2 className="h-4 w-4 text-red-600" /></Button>}</div></TableCell></TableRow>)}</TableBody></Table></div><Pagination disabled={loading} onChange={handlePageChange} onPageSizeChange={handlePageSizeChange} page={page} pageSize={pageSize} total={total} /></CardContent></Card>
      {formPermission && <PermissionFormModal permission={formPermission === 'new' ? undefined : formPermission} onClose={() => setFormPermission(null)} onSaved={refresh} />}
      {detailPermissionId !== null && <PermissionDetailModal permissionId={detailPermissionId} onClose={() => setDetailPermissionId(null)} />}
      <AlertDialog open={Boolean(deletePermission)} onOpenChange={(open) => { if (!open) setDeletePermission(null) }}><AlertDialogContent><AlertDialogHeader><AlertDialogTitle>删除权限</AlertDialogTitle><AlertDialogDescription>确定删除权限“{deletePermission?.name}（{deletePermission?.code}）”吗？已分配该权限的角色将失去对应能力。</AlertDialogDescription></AlertDialogHeader><AlertDialogFooter><AlertDialogCancel disabled={deleting}>取消</AlertDialogCancel><AlertDialogAction className="bg-red-600 text-white hover:bg-red-700" disabled={deleting} onClick={handleDelete}>{deleting ? '删除中...' : '确认删除'}</AlertDialogAction></AlertDialogFooter></AlertDialogContent></AlertDialog>
    </div>
  )
}
