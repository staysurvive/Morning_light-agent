import { BrowserRouter, Navigate, Routes, Route } from 'react-router-dom'
import DashboardLayout from './layouts/DashboardLayout'
import AuthGuard from './components/AuthGuard'
import PermissionGuard from './components/PermissionGuard'
import AuthorizationProvider from './contexts/AuthorizationProvider'
import { PERMISSIONS } from './services/permissions'
import Dashboard from './pages/Dashboard'
import Login from './pages/Login'
import Profile from './pages/Profile'
import { AgentList, AgentCreate, AgentDetail, AgentVersions } from './pages/agent'
import { ModelList, ModelProviders, ModelCreate } from './pages/model'
import { PromptList, PromptCreate, PromptVersions } from './pages/prompt'
import { KnowledgeList, KnowledgeCreate, KnowledgeDetail, KnowledgeDocuments, KnowledgeSegments, KnowledgeTest } from './pages/knowledge'
import { ToolList, ToolCreate, ToolDetail } from './pages/tool'
import { ConversationList, ConversationDetail } from './pages/conversation'
import { AnalyticsUsage, AnalyticsCosts, AnalyticsEvaluation } from './pages/analytics'
import { SystemUsers, SystemRoles, SystemPermissions, SystemApiKeys, SystemAudit, SystemAlerts, SystemSettings } from './pages/system'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Login Route - Outside DashboardLayout */}
        <Route path="/login" element={<Login />} />
        
        {/* Main App Routes - Inside DashboardLayout, protected by AuthGuard */}
        <Route path="/" element={<AuthGuard><AuthorizationProvider><DashboardLayout /></AuthorizationProvider></AuthGuard>}>
          <Route index element={<PermissionGuard permission={PERMISSIONS.dashboardRead}><Dashboard /></PermissionGuard>} />
          
          {/* User Routes */}
          <Route path="profile" element={<Profile />} />
          <Route path="settings" element={<Navigate replace to="/profile" />} />
          
          {/* Agent Routes */}
          <Route path="agents" element={<PermissionGuard permission={PERMISSIONS.agentRead}><AgentList /></PermissionGuard>} />
          <Route path="agents/create" element={<PermissionGuard permission={PERMISSIONS.agentCreate}><AgentCreate /></PermissionGuard>} />
          <Route path="agents/:id" element={<PermissionGuard permission={PERMISSIONS.agentRead}><AgentDetail /></PermissionGuard>} />
          <Route path="agents/:id/edit" element={<PermissionGuard permission={PERMISSIONS.agentUpdate}><AgentCreate /></PermissionGuard>} />
          <Route path="agents/:id/versions" element={<PermissionGuard permission={PERMISSIONS.agentRead}><AgentVersions /></PermissionGuard>} />
          
          {/* Model Routes */}
          <Route path="models" element={<PermissionGuard permission={PERMISSIONS.modelRead}><ModelList /></PermissionGuard>} />
          <Route path="models/create" element={<PermissionGuard permission={PERMISSIONS.modelCreate}><ModelCreate /></PermissionGuard>} />
          <Route path="models/:id/edit" element={<PermissionGuard permission={PERMISSIONS.modelUpdate}><ModelCreate /></PermissionGuard>} />
          <Route path="models/providers" element={<PermissionGuard permission={PERMISSIONS.providerRead}><ModelProviders /></PermissionGuard>} />
          
          {/* Prompt Routes */}
          <Route path="prompts" element={<PermissionGuard permission={PERMISSIONS.promptRead}><PromptList /></PermissionGuard>} />
          <Route path="prompts/create" element={<PermissionGuard permission={PERMISSIONS.promptCreate}><PromptCreate /></PermissionGuard>} />
          <Route path="prompts/:id/edit" element={<PermissionGuard permission={PERMISSIONS.promptUpdate}><PromptCreate /></PermissionGuard>} />
          <Route path="prompts/:id/versions" element={<PermissionGuard permission={PERMISSIONS.promptRead}><PromptVersions /></PermissionGuard>} />
          
          {/* Knowledge Routes */}
          <Route path="knowledge" element={<PermissionGuard permission={PERMISSIONS.knowledgeRead}><KnowledgeList /></PermissionGuard>} />
          <Route path="knowledge/create" element={<PermissionGuard permission={PERMISSIONS.knowledgeCreate}><KnowledgeCreate /></PermissionGuard>} />
          <Route path="knowledge/:id" element={<PermissionGuard permission={PERMISSIONS.knowledgeRead}><KnowledgeDetail /></PermissionGuard>} />
          <Route path="knowledge/:id/documents" element={<PermissionGuard permission={PERMISSIONS.knowledgeRead}><KnowledgeDocuments /></PermissionGuard>} />
          <Route path="knowledge/:id/segments" element={<PermissionGuard permission={PERMISSIONS.knowledgeRead}><KnowledgeSegments /></PermissionGuard>} />
          <Route path="knowledge/:id/test" element={<PermissionGuard permission={PERMISSIONS.knowledgeRetrieve}><KnowledgeTest /></PermissionGuard>} />
          
          {/* Tool Routes */}
          <Route path="tools" element={<PermissionGuard permission={PERMISSIONS.toolRead}><ToolList /></PermissionGuard>} />
          <Route path="tools/create" element={<PermissionGuard permission={PERMISSIONS.toolCreate}><ToolCreate /></PermissionGuard>} />
          <Route path="tools/:id" element={<PermissionGuard permission={PERMISSIONS.toolRead}><ToolDetail /></PermissionGuard>} />
          <Route path="tools/:id/edit" element={<PermissionGuard permission={PERMISSIONS.toolUpdate}><ToolCreate /></PermissionGuard>} />
          
          {/* Conversation Routes */}
          <Route path="conversations" element={<PermissionGuard permission={PERMISSIONS.conversationRead}><ConversationList /></PermissionGuard>} />
          <Route path="conversations/:id" element={<PermissionGuard permission={PERMISSIONS.conversationRead}><ConversationDetail /></PermissionGuard>} />
          
          {/* Analytics Routes */}
          <Route path="analytics" element={<PermissionGuard permission={PERMISSIONS.analyticsRead}><AnalyticsUsage /></PermissionGuard>} />
          <Route path="analytics/costs" element={<PermissionGuard permission={PERMISSIONS.analyticsRead}><AnalyticsCosts /></PermissionGuard>} />
          <Route path="analytics/evaluation" element={<PermissionGuard permission={PERMISSIONS.analyticsRead}><AnalyticsEvaluation /></PermissionGuard>} />
          
          {/* System Routes */}
          <Route path="system/users" element={<PermissionGuard permission={PERMISSIONS.userRead}><SystemUsers /></PermissionGuard>} />
          <Route path="system/roles" element={<PermissionGuard permission={PERMISSIONS.roleRead}><SystemRoles /></PermissionGuard>} />
          <Route path="system/permissions" element={<PermissionGuard permission={PERMISSIONS.permissionRead}><SystemPermissions /></PermissionGuard>} />
          <Route path="system/api-keys" element={<PermissionGuard permission={PERMISSIONS.apiKeyRead}><SystemApiKeys /></PermissionGuard>} />
          <Route path="system/audit" element={<PermissionGuard permission={PERMISSIONS.auditRead}><SystemAudit /></PermissionGuard>} />
          <Route path="system/alerts" element={<PermissionGuard permission={PERMISSIONS.alertRead}><SystemAlerts /></PermissionGuard>} />
          <Route path="system/settings" element={<PermissionGuard permission={PERMISSIONS.settingsRead}><SystemSettings /></PermissionGuard>} />
          <Route path="*" element={<div className="p-6 text-center text-muted-foreground">页面开发中...</div>} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
