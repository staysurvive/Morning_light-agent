import { useState, useEffect } from 'react';
import { Plus, Bell, BellOff, Check, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Switch } from '@/components/ui/switch';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import Modal from '@/components/Modal';
import InlineNotice from '@/components/InlineNotice';
import { useAuthorization } from '@/hooks/useAuthorization';
import { PERMISSIONS } from '@/services/permissions';
import { systemService } from '@/services/system';
import type { AlertRule, SystemAlert } from '@/services/types/system';

export default function SystemAlerts() {
  const { can } = useAuthorization();
  const [alerts, setAlerts] = useState<SystemAlert[]>([]);
  const [rules, setRules] = useState<AlertRule[]>([]);
  const [ruleOpen, setRuleOpen] = useState(false);
  const [error, setError] = useState('');
  const [ruleForm, setRuleForm] = useState({ name: '', metric: '', operator: 'gt', threshold: 0, duration: 0 });

  const loadAlerts = () => {
    Promise.all([systemService.getSystemAlerts(), systemService.getAlertRules()])
      .then(([alertItems, ruleItems]) => { setAlerts(alertItems); setRules(ruleItems); })
      .catch((error: unknown) => console.error('加载告警失败:', error));
  };

  useEffect(() => {
    loadAlerts();
  }, []);

  const createRule = async () => {
    try {
      await systemService.createAlertRule({
        name: ruleForm.name,
        description: null,
        condition: { metric: ruleForm.metric, operator: ruleForm.operator as 'gt', threshold: ruleForm.threshold, duration: ruleForm.duration },
        notifications: [],
      });
      setRuleOpen(false);
      setRuleForm({ name: '', metric: '', operator: 'gt', threshold: 0, duration: 0 });
      loadAlerts();
    } catch (caught) { setError(caught instanceof Error ? caught.message : '创建规则失败'); }
  };

  const toggleRule = async (rule: AlertRule) => {
    try {
      await systemService.updateAlertRule(rule.id, { status: rule.status === 'enabled' ? 'disabled' : 'enabled' });
      loadAlerts();
    } catch (caught) { setError(caught instanceof Error ? caught.message : '更新规则失败'); }
  };

  const deleteRule = async (rule: AlertRule) => {
    if (!window.confirm(`确定删除“${rule.name}”吗？`)) return;
    try { await systemService.deleteAlertRule(rule.id); loadAlerts(); }
    catch (caught) { setError(caught instanceof Error ? caught.message : '删除规则失败'); }
  };

  const handleAcknowledge = async (id: string) => {
    try {
      await systemService.acknowledgeAlert(id);
      loadAlerts();
    } catch (error) {
      console.error('确认告警失败:', error);
    }
  };

  const handleResolve = async (id: string) => {
    try {
      await systemService.resolveAlert(id);
      loadAlerts();
    } catch (error) {
      console.error('解决告警失败:', error);
    }
  };

  const getSeverityBadge = (severity: string) => {
    const variants: Record<string, 'default' | 'destructive' | 'secondary'> = {
      high: 'destructive',
      critical: 'destructive',
      medium: 'default',
      low: 'secondary',
    };
    const labels: Record<string, string> = {
      high: '高',
      critical: '严重',
      medium: '中',
      low: '低',
    };
    return <Badge variant={variants[severity]}>{labels[severity]}</Badge>;
  };

  const getTypeIcon = (type: string) => {
    const colors: Record<string, string> = {
      error: 'text-red-500',
      warning: 'text-yellow-500',
      info: 'text-blue-500',
    };
    return <Bell className={`h-5 w-5 ${colors[type] || 'text-gray-500'}`} />;
  };

  const activeAlerts = alerts.filter((a) => a.status === 'active');
  const acknowledgedAlerts = alerts.filter((a) => a.status === 'acknowledged');
  const resolvedAlerts = alerts.filter((a) => a.status === 'resolved');

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">告警管理</h1>
          <p className="text-muted-foreground mt-1">管理系统告警和规则</p>
        </div>
        {can(PERMISSIONS.alertCreate) && <Button onClick={() => setRuleOpen(true)}>
          <Plus className="h-4 w-4 mr-2" />
          创建告警规则
        </Button>}
      </div>
      {error && <InlineNotice kind="error" message={error} />}

      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">活跃告警</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-500">{activeAlerts.length}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">已确认</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-yellow-500">{acknowledgedAlerts.length}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">已解决</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-500">{resolvedAlerts.length}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">告警总数</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{alerts.length}</div>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="active" className="space-y-4">
        <TabsList>
          <TabsTrigger value="active">
            活跃告警 ({activeAlerts.length})
          </TabsTrigger>
          <TabsTrigger value="rules">告警规则</TabsTrigger>
          <TabsTrigger value="history">历史记录</TabsTrigger>
        </TabsList>

        <TabsContent value="active" className="space-y-4">
          {activeAlerts.length === 0 ? (
            <Card>
              <CardContent className="py-12 text-center text-muted-foreground">
                <BellOff className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>暂无活跃告警</p>
              </CardContent>
            </Card>
          ) : (
            activeAlerts.map((alert) => (
              <Card key={alert.id} className="border-l-4 border-l-red-500">
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div className="flex items-start gap-3">
                      {getTypeIcon(alert.type)}
                      <div>
                        <div className="flex items-center gap-2">
                          <h3 className="font-semibold">{alert.title}</h3>
                          {getSeverityBadge(alert.severity)}
                        </div>
                        <p className="text-sm text-muted-foreground mt-1">{alert.message}</p>
                        <div className="flex items-center gap-4 mt-2 text-xs text-muted-foreground">
                          <span>来源: {alert.source}</span>
                          <span>首次: {new Date(alert.firstOccurredAt).toLocaleString('zh-CN')}</span>
                          <span>最近: {new Date(alert.lastOccurredAt).toLocaleString('zh-CN')}</span>
                          {alert.count > 1 && <Badge variant="outline">出现 {alert.count} 次</Badge>}
                        </div>
                      </div>
                    </div>
                    {can(PERMISSIONS.alertHandle) && <div className="flex items-center gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleAcknowledge(alert.id)}
                      >
                        <Check className="h-4 w-4 mr-2" />
                        确认
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleResolve(alert.id)}
                      >
                        <X className="h-4 w-4 mr-2" />
                        解决
                      </Button>
                    </div>}
                  </div>
                </CardHeader>
              </Card>
            ))
          )}
        </TabsContent>

        <TabsContent value="rules" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>告警规则列表</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {rules.length === 0 ? <p className="py-8 text-center text-sm text-muted-foreground">暂无告警规则</p> : rules.map((rule) => (
                  <div
                    key={rule.id}
                    className="flex items-center justify-between p-4 border rounded-lg"
                  >
                    <div className="flex-1">
                      <div className="font-medium">{rule.name}</div>
                      <div className="text-sm text-muted-foreground mt-1">
                        条件: {rule.condition.metric} {rule.condition.operator} {rule.condition.threshold}，持续 {rule.condition.duration} 分钟
                      </div>
                      <div className="text-sm text-muted-foreground">
                        通知: {rule.notifications.length ? rule.notifications.join(' + ') : '未配置'}
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      {can(PERMISSIONS.alertUpdate) && <Switch checked={rule.status === 'enabled'} onCheckedChange={() => toggleRule(rule)} />}
                      {can(PERMISSIONS.alertDelete) && <Button variant="outline" size="sm" onClick={() => deleteRule(rule)}>删除</Button>}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="history" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>历史告警</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {[...acknowledgedAlerts, ...resolvedAlerts].map((alert) => (
                  <div key={alert.id} className="flex items-start gap-3 p-3 border rounded-lg">
                    {getTypeIcon(alert.type)}
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className="font-medium">{alert.title}</span>
                        {getSeverityBadge(alert.severity)}
                        <Badge variant={alert.status === 'resolved' ? 'default' : 'secondary'}>
                          {alert.status === 'resolved' ? '已解决' : '已确认'}
                        </Badge>
                      </div>
                      <p className="text-sm text-muted-foreground mt-1">{alert.message}</p>
                      <div className="text-xs text-muted-foreground mt-2">
                        {alert.status === 'resolved' && alert.resolvedAt && (
                          <span>解决时间: {new Date(alert.resolvedAt).toLocaleString('zh-CN')}</span>
                        )}
                        {alert.status === 'acknowledged' && alert.acknowledgedAt && (
                          <span>确认时间: {new Date(alert.acknowledgedAt).toLocaleString('zh-CN')}</span>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
      {ruleOpen && <Modal title="创建告警规则" description="规则仅保存配置，需接入指标采集器后才会自动评估" onClose={() => setRuleOpen(false)} footer={<div className="flex justify-end gap-2"><Button variant="outline" onClick={() => setRuleOpen(false)}>取消</Button><Button disabled={!ruleForm.name.trim() || !ruleForm.metric.trim()} onClick={createRule}>创建</Button></div>}>
        <div className="space-y-4"><div className="space-y-2"><Label>规则名称</Label><Input value={ruleForm.name} onChange={(e) => setRuleForm({ ...ruleForm, name: e.target.value })} /></div><div className="space-y-2"><Label>指标</Label><Input value={ruleForm.metric} onChange={(e) => setRuleForm({ ...ruleForm, metric: e.target.value })} placeholder="例如 error_rate" /></div><div className="grid grid-cols-3 gap-3"><div className="space-y-2"><Label>运算符</Label><Select value={ruleForm.operator} onValueChange={(value) => setRuleForm({ ...ruleForm, operator: value })}><SelectTrigger><SelectValue /></SelectTrigger><SelectContent><SelectItem value="gt">大于</SelectItem><SelectItem value="gte">大于等于</SelectItem><SelectItem value="lt">小于</SelectItem><SelectItem value="lte">小于等于</SelectItem><SelectItem value="eq">等于</SelectItem></SelectContent></Select></div><div className="space-y-2"><Label>阈值</Label><Input type="number" value={ruleForm.threshold} onChange={(e) => setRuleForm({ ...ruleForm, threshold: Number(e.target.value) })} /></div><div className="space-y-2"><Label>持续分钟</Label><Input type="number" min={0} value={ruleForm.duration} onChange={(e) => setRuleForm({ ...ruleForm, duration: Number(e.target.value) })} /></div></div></div>
      </Modal>}
    </div>
  );
}
