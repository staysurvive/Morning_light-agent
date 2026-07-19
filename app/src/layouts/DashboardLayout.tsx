import { useEffect, useState, type ComponentType } from 'react'
import { Link, Outlet, useLocation, useNavigate } from 'react-router-dom'
import {
  BarChart3,
  Bot,
  Brain,
  ChevronDown,
  ChevronRight,
  CircleCheck,
  CircleX,
  Database,
  FileText,
  Home,
  LayoutDashboard,
  LogOut,
  Menu,
  MessageSquare,
  Settings,
  User,
  Wrench,
} from 'lucide-react'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { Sheet, SheetContent, SheetTitle } from '@/components/ui/sheet'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip'
import { useAuthorization } from '@/hooks/useAuthorization'
import type { UserWithRolesRead } from '@/services/access'
import { authService } from '@/services/auth'
import { healthService } from '@/services/health'
import { PERMISSIONS, type PermissionCode } from '@/services/permissions'

interface MenuItem {
  path: string
  icon: ComponentType<{ className?: string }>
  label: string
  permission: PermissionCode
}

const menuItems: MenuItem[] = [
  { path: '/', icon: LayoutDashboard, label: '工作台', permission: PERMISSIONS.dashboardRead },
  { path: '/agents', icon: Bot, label: 'Agent管理', permission: PERMISSIONS.agentRead },
  { path: '/models', icon: Brain, label: '模型管理', permission: PERMISSIONS.modelRead },
  { path: '/prompts', icon: FileText, label: 'Prompt管理', permission: PERMISSIONS.promptRead },
  { path: '/knowledge', icon: Database, label: '知识库', permission: PERMISSIONS.knowledgeRead },
  { path: '/tools', icon: Wrench, label: '工具管理', permission: PERMISSIONS.toolRead },
  { path: '/conversations', icon: MessageSquare, label: '对话日志', permission: PERMISSIONS.conversationRead },
  { path: '/analytics', icon: BarChart3, label: '数据统计', permission: PERMISSIONS.analyticsRead },
]

const systemMenuItems = [
  { path: '/system/users', label: '用户管理', permission: PERMISSIONS.userRead },
  { path: '/system/roles', label: '角色管理', permission: PERMISSIONS.roleRead },
  { path: '/system/permissions', label: '权限管理', permission: PERMISSIONS.permissionRead },
  { path: '/system/api-keys', label: 'API Key', permission: PERMISSIONS.apiKeyRead },
  { path: '/system/audit', label: '审计日志', permission: PERMISSIONS.auditRead },
  { path: '/system/alerts', label: '告警管理', permission: PERMISSIONS.alertRead },
  { path: '/system/settings', label: '系统设置', permission: PERMISSIONS.settingsRead },
]

interface NavigationContentProps {
  currentUser: UserWithRolesRead | null
  can: (permission: PermissionCode) => boolean
  locationPath: string
  onLogout: () => void
  onNavigate: (path: string) => void
  onToggleSystem: () => void
  systemMenuOpen: boolean
}

function NavigationContent({
  currentUser,
  can,
  locationPath,
  onLogout,
  onNavigate,
  onToggleSystem,
  systemMenuOpen,
}: NavigationContentProps) {
  const isSystemPath = locationPath.startsWith('/system')
  const visibleSystemMenuItems = systemMenuItems.filter((item) => can(item.permission))

  return (
    <>
      <div className="flex h-16 items-center border-b border-gray-200 px-6">
        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-md bg-blue-600 shadow-sm">
            <Bot className="h-5 w-5 text-white" />
          </div>
          <div>
            <div className="text-base font-semibold text-gray-950">辰光 Agent</div>
            <div className="text-xs text-gray-500">Enterprise</div>
          </div>
        </div>
      </div>

      <nav className="flex-1 space-y-1 overflow-y-auto px-3 py-4">
        <div className="mb-2 px-3 text-xs font-semibold text-gray-400">平台功能</div>
        {menuItems.filter((item) => can(item.permission)).map((item) => {
          const Icon = item.icon
          const isActive = locationPath === item.path || (item.path !== '/' && locationPath.startsWith(item.path))
          return (
            <Link
              className={`relative flex items-center gap-3 rounded-md px-3 py-2.5 text-sm font-medium transition-colors ${isActive ? 'bg-blue-600 text-white' : 'text-gray-700 hover:bg-gray-100'}`}
              key={item.path}
              onClick={() => onNavigate(item.path)}
              to={item.path}
            >
              <Icon className="h-5 w-5 shrink-0" />
              <span>{item.label}</span>
            </Link>
          )
        })}

        {visibleSystemMenuItems.length > 0 && (
          <div className="pt-4">
            <div className="mb-2 px-3 text-xs font-semibold text-gray-400">访问控制</div>
            <button
              className={`flex w-full items-center gap-3 rounded-md px-3 py-2.5 text-sm font-medium transition-colors ${isSystemPath ? 'bg-blue-600 text-white' : 'text-gray-700 hover:bg-gray-100'}`}
              onClick={onToggleSystem}
              type="button"
            >
              <Settings className="h-5 w-5 shrink-0" />
              <span className="flex-1 text-left">系统管理</span>
              {systemMenuOpen ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
            </button>
            {systemMenuOpen && (
              <div className="ml-8 mt-1 space-y-1">
                {visibleSystemMenuItems.map((item) => (
                  <Link
                    className={`block rounded-md px-3 py-2 text-sm transition-colors ${locationPath === item.path ? 'bg-blue-600 text-white' : 'text-gray-600 hover:bg-gray-100'}`}
                    key={item.path}
                    onClick={() => onNavigate(item.path)}
                    to={item.path}
                  >
                    {item.label}
                  </Link>
                ))}
              </div>
            )}
          </div>
        )}
      </nav>

      <div className="border-t border-gray-200 p-3">
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button className="flex w-full items-center gap-3 rounded-md px-3 py-2.5 text-left transition-colors hover:bg-gray-100" type="button">
              <Avatar className="h-9 w-9 border-2 border-gray-200">
                <AvatarFallback className="bg-blue-600 text-white">
                  {(currentUser?.username ?? 'U').slice(0, 1).toUpperCase()}
                </AvatarFallback>
              </Avatar>
              <span className="min-w-0 flex-1">
                <span className="block truncate text-sm font-medium text-gray-950">{currentUser?.username ?? '当前用户'}</span>
                <span className="block truncate text-xs text-gray-500">{currentUser?.email ?? '正在读取身份...'}</span>
              </span>
              <ChevronRight className="h-4 w-4 text-gray-400" />
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-56">
            <DropdownMenuLabel>我的账户</DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={() => onNavigate('/profile')}><User className="mr-2 h-4 w-4" />个人资料</DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem className="text-red-600" onClick={onLogout}><LogOut className="mr-2 h-4 w-4" />退出登录</DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </>
  )
}

export default function DashboardLayout() {
  const location = useLocation()
  const navigate = useNavigate()
  const { can, currentUser } = useAuthorization()
  const [systemMenuOpen, setSystemMenuOpen] = useState(() => location.pathname.startsWith('/system'))
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [health, setHealth] = useState<'checking' | 'mock' | 'api' | 'error'>('checking')

  useEffect(() => {
    let active = true
    healthService.check()
      .then((result) => { if (active) setHealth(result.source) })
      .catch(() => { if (active) setHealth('error') })
    return () => { active = false }
  }, [])

  const breadcrumbs = [{ label: '首页', path: '/' }]
  let currentPath = ''
  location.pathname.split('/').filter(Boolean).forEach((path, index, paths) => {
    currentPath += `/${path}`
    const menuItem = menuItems.find((item) => item.path === currentPath)
    const systemItem = systemMenuItems.find((item) => item.path === currentPath)
    if (menuItem) breadcrumbs.push({ label: menuItem.label, path: currentPath })
    else if (systemItem) {
      if (breadcrumbs[breadcrumbs.length - 1].label !== '系统管理') breadcrumbs.push({ label: '系统管理', path: '/system/users' })
      breadcrumbs.push({ label: systemItem.label, path: currentPath })
    } else if (index === paths.length - 1) breadcrumbs.push({ label: path, path: currentPath })
  })

  const handleNavigate = (path: string) => {
    setMobileMenuOpen(false)
    if (location.pathname !== path) navigate(path)
  }

  const handleLogout = () => {
    authService.logout()
    navigate('/login')
  }

  const navigationProps: NavigationContentProps = {
    can,
    currentUser,
    locationPath: location.pathname,
    onLogout: handleLogout,
    onNavigate: handleNavigate,
    onToggleSystem: () => setSystemMenuOpen((open) => !open),
    systemMenuOpen,
  }

  return (
    <div className="flex h-screen bg-gray-50">
      <aside className="hidden w-64 shrink-0 flex-col border-r border-gray-200 bg-white lg:flex">
        <NavigationContent {...navigationProps} />
      </aside>

      <Sheet onOpenChange={setMobileMenuOpen} open={mobileMenuOpen}>
        <SheetContent className="w-72 gap-0 p-0" side="left">
          <SheetTitle className="sr-only">主导航</SheetTitle>
          <NavigationContent {...navigationProps} />
        </SheetContent>
      </Sheet>

      <div className="flex min-w-0 flex-1 flex-col overflow-hidden">
        <header className="flex h-16 shrink-0 items-center justify-between gap-3 border-b border-gray-200 bg-white px-4 sm:px-6">
          <div className="flex min-w-0 items-center gap-3">
            <Button aria-label="打开主导航" className="lg:hidden" onClick={() => setMobileMenuOpen(true)} size="icon" variant="outline"><Menu className="h-4 w-4" /></Button>
            <div className="flex min-w-0 items-center gap-2 overflow-hidden text-sm">
              {breadcrumbs.map((crumb, index) => (
                <div className={`items-center gap-2 ${index < breadcrumbs.length - 2 ? 'hidden sm:flex' : 'flex'}`} key={`${crumb.path}-${index}`}>
                  {index > 0 && <ChevronRight className="h-4 w-4 shrink-0 text-gray-400" />}
                  {index === breadcrumbs.length - 1 ? <span className="truncate font-medium text-gray-950">{crumb.label}</span> : <Link className="truncate text-gray-500 transition-colors hover:text-gray-950" to={crumb.path}>{index === 0 ? <Home className="h-4 w-4" /> : crumb.label}</Link>}
                </div>
              ))}
            </div>
          </div>
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <div aria-label="后端状态" className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md border bg-white">
                  {health === 'api' ? <CircleCheck className="h-4 w-4 text-emerald-600" /> : health === 'mock' ? <CircleCheck className="h-4 w-4 text-blue-600" /> : health === 'error' ? <CircleX className="h-4 w-4 text-red-600" /> : <span className="h-2 w-2 animate-pulse rounded-full bg-gray-400" />}
                </div>
              </TooltipTrigger>
              <TooltipContent>{health === 'api' ? '后端连接正常' : health === 'mock' ? '当前使用 Mock 数据' : health === 'error' ? '后端连接异常' : '正在检查后端'}</TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </header>
        <main className="flex-1 overflow-auto bg-gray-50"><Outlet /></main>
      </div>
    </div>
  )
}
