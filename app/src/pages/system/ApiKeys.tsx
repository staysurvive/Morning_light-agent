import { useCallback, useEffect, useState } from 'react'
import { Copy, KeyRound, Plus, RefreshCw, Trash2 } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import InlineNotice from '@/components/InlineNotice'
import Modal from '@/components/Modal'
import Pagination from '@/components/Pagination'
import { useAuthorization } from '@/hooks/useAuthorization'
import { accessService, type PermissionRead } from '@/services/access'
import { PERMISSIONS } from '@/services/permissions'
import { systemService } from '@/services/system'
import type { ApiKey } from '@/services/types/system'

export default function SystemApiKeys() {
  const { can } = useAuthorization()
  const [apiKeys, setApiKeys] = useState<ApiKey[]>([])
  const [permissions, setPermissions] = useState<PermissionRead[]>([])
  const [loading, setLoading] = useState(true)
  const [status, setStatus] = useState('all')
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(10)
  const [total, setTotal] = useState(0)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [createOpen, setCreateOpen] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [issuedKey, setIssuedKey] = useState<ApiKey | null>(null)
  const [form, setForm] = useState({ name: '', rateLimit: 100, expiresAt: '', permissions: [] as string[] })

  const loadApiKeys = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const response = await systemService.getApiKeys({ page, pageSize, status: status === 'all' ? undefined : status })
      setApiKeys(response.data)
      setTotal(response.total)
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : '加载 API Key 失败')
    } finally {
      setLoading(false)
    }
  }, [page, pageSize, status])

  useEffect(() => { loadApiKeys() }, [loadApiKeys])
  useEffect(() => { setPage(1) }, [status])

  const openCreate = async () => {
    setError('')
    try {
      setPermissions(await accessService.listPermissions())
      setForm({ name: '', rateLimit: 100, expiresAt: '', permissions: [] })
      setCreateOpen(true)
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : '加载权限列表失败')
    }
  }

  const createKey = async () => {
    if (!form.name.trim()) return
    setSubmitting(true)
    setError('')
    try {
      const created = await systemService.createApiKey({
        name: form.name.trim(), permissions: form.permissions, rateLimit: form.rateLimit,
        expiresAt: form.expiresAt ? new Date(form.expiresAt).toISOString() : null,
      })
      setCreateOpen(false)
      setIssuedKey(created)
      await loadApiKeys()
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : '创建 API Key 失败')
    } finally {
      setSubmitting(false)
    }
  }

  const updateStatus = async (item: ApiKey) => {
    try {
      await systemService.updateApiKey(item.id, { status: item.status === 'active' ? 'disabled' : 'active' })
      setNotice(item.status === 'active' ? 'API Key 已停用' : 'API Key 已启用')
      await loadApiKeys()
    } catch (caught) { setError(caught instanceof Error ? caught.message : '更新失败') }
  }

  const rotate = async (item: ApiKey) => {
    if (!window.confirm(`轮换“${item.name}”后，旧密钥会立即失效。继续吗？`)) return
    try {
      setIssuedKey(await systemService.rotateApiKey(item.id))
      await loadApiKeys()
    } catch (caught) { setError(caught instanceof Error ? caught.message : '轮换失败') }
  }

  const remove = async (item: ApiKey) => {
    if (!window.confirm(`确定删除“${item.name}”吗？`)) return
    try {
      await systemService.deleteApiKey(item.id)
      setNotice('API Key 已删除')
      if (apiKeys.length === 1 && page > 1) setPage(page - 1)
      else await loadApiKeys()
    } catch (caught) { setError(caught instanceof Error ? caught.message : '删除失败') }
  }

  const statusBadge = (value: ApiKey['status']) => {
    const label = { active: '活跃', disabled: '已停用', expired: '已过期' }[value]
    return <Badge variant={value === 'active' ? 'default' : value === 'expired' ? 'destructive' : 'secondary'}>{label}</Badge>
  }

  return (
    <div className="space-y-6 p-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div><h1 className="text-3xl font-bold">API Key 管理</h1><p className="mt-1 text-muted-foreground">签发和撤销平台访问凭证</p></div>
        {can(PERMISSIONS.apiKeyCreate) && <Button onClick={openCreate}><Plus className="mr-2 h-4 w-4" />创建 API Key</Button>}
      </div>
      {error && <InlineNotice kind="error" message={error} />}
      {notice && <InlineNotice kind="success" message={notice} />}

      <Card>
        <CardHeader><div className="flex items-center justify-between gap-3"><CardTitle>密钥列表</CardTitle><Select value={status} onValueChange={setStatus}><SelectTrigger className="w-36"><SelectValue /></SelectTrigger><SelectContent><SelectItem value="all">全部状态</SelectItem><SelectItem value="active">活跃</SelectItem><SelectItem value="disabled">已停用</SelectItem><SelectItem value="expired">已过期</SelectItem></SelectContent></Select></div></CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <Table><TableHeader><TableRow><TableHead>名称</TableHead><TableHead>密钥</TableHead><TableHead>权限数</TableHead><TableHead>每分钟限额</TableHead><TableHead>状态</TableHead><TableHead>最后使用</TableHead><TableHead>过期时间</TableHead><TableHead className="text-right">操作</TableHead></TableRow></TableHeader>
              <TableBody>{loading ? <TableRow><TableCell colSpan={8} className="text-center">加载中...</TableCell></TableRow> : apiKeys.length === 0 ? <TableRow><TableCell colSpan={8} className="text-center">暂无 API Key</TableCell></TableRow> : apiKeys.map((item) => <TableRow key={item.id}>
                <TableCell className="font-medium">{item.name}</TableCell><TableCell><code className="rounded bg-muted px-2 py-1 text-xs">{item.key}</code></TableCell><TableCell>{item.permissions.length}</TableCell><TableCell>{item.rateLimit}</TableCell><TableCell>{statusBadge(item.status)}</TableCell><TableCell>{item.lastUsedAt ? new Date(item.lastUsedAt).toLocaleString('zh-CN') : '从未使用'}</TableCell><TableCell>{item.expiresAt ? new Date(item.expiresAt).toLocaleDateString('zh-CN') : '永不过期'}</TableCell>
                <TableCell><div className="flex justify-end gap-1">{can(PERMISSIONS.apiKeyUpdate) && <><Button size="sm" variant="outline" onClick={() => updateStatus(item)}>{item.status === 'active' ? '停用' : '启用'}</Button><Button size="icon" variant="ghost" title="轮换" onClick={() => rotate(item)}><RefreshCw className="h-4 w-4" /></Button></>}{can(PERMISSIONS.apiKeyDelete) && <Button size="icon" variant="ghost" title="删除" onClick={() => remove(item)}><Trash2 className="h-4 w-4 text-destructive" /></Button>}</div></TableCell>
              </TableRow>)}</TableBody></Table>
          </div>
          <Pagination page={page} total={total} pageSize={pageSize} disabled={loading} onChange={setPage} onPageSizeChange={(value) => { setPageSize(value); setPage(1) }} />
        </CardContent>
      </Card>

      {createOpen && <Modal title="创建 API Key" description="完整密钥只显示一次" onClose={() => setCreateOpen(false)} footer={<div className="flex justify-end gap-2"><Button variant="outline" onClick={() => setCreateOpen(false)}>取消</Button><Button disabled={submitting || !form.name.trim()} onClick={createKey}>{submitting ? '创建中...' : '创建'}</Button></div>}>
        <div className="space-y-4"><div className="space-y-2"><Label>名称</Label><Input value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} /></div><div className="grid grid-cols-2 gap-4"><div className="space-y-2"><Label>每分钟限额</Label><Input min={1} type="number" value={form.rateLimit} onChange={(event) => setForm({ ...form, rateLimit: Number(event.target.value) })} /></div><div className="space-y-2"><Label>过期时间</Label><Input type="datetime-local" value={form.expiresAt} onChange={(event) => setForm({ ...form, expiresAt: event.target.value })} /></div></div><div className="space-y-2"><Label>权限</Label><div className="max-h-56 space-y-2 overflow-y-auto rounded border p-3">{permissions.map((permission) => <label className="flex items-center gap-2 text-sm" key={permission.id}><input className="h-4 w-4" type="checkbox" checked={form.permissions.includes(permission.code)} onChange={(event) => setForm({ ...form, permissions: event.target.checked ? [...form.permissions, permission.code] : form.permissions.filter((code) => code !== permission.code) })} /><span>{permission.name}</span><code className="ml-auto text-xs text-muted-foreground">{permission.code}</code></label>)}</div></div></div>
      </Modal>}

      {issuedKey && <Modal title="保存新密钥" description="关闭后无法再次查看完整内容" onClose={() => setIssuedKey(null)} footer={<div className="flex justify-end"><Button onClick={() => setIssuedKey(null)}>我已保存</Button></div>}><div className="space-y-3"><InlineNotice kind="success" message="密钥已签发，旧密钥（如有）已失效。" /><div className="flex items-center gap-2 rounded border bg-muted p-3"><KeyRound className="h-4 w-4 shrink-0" /><code className="min-w-0 flex-1 break-all text-sm">{issuedKey.key}</code><Button size="icon" variant="outline" onClick={() => navigator.clipboard.writeText(issuedKey.key)} title="复制"><Copy className="h-4 w-4" /></Button></div></div></Modal>}
    </div>
  )
}
