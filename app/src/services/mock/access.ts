import type {
  AccessService,
  PageQuery,
  PageResult,
  PermissionCreate,
  PermissionRead,
  PermissionUpdate,
  RoleCreate,
  RoleRead,
  RoleUpdate,
  UserCreate,
  UserRead,
  UserWithRolesRead,
} from '../types/access'

interface MockUser extends UserRead {
  roleIds: number[]
}

interface MockRole extends Omit<RoleRead, 'permissions'> {
  permissionIds: number[]
}

let permissions: PermissionRead[] = [
  { id: 1, code: 'user_read', name: '查看用户', description: '查看用户列表、详情和角色' },
  { id: 2, code: 'user_create', name: '创建用户', description: '创建平台用户' },
  { id: 3, code: 'user_delete', name: '删除用户', description: '删除平台用户' },
  { id: 4, code: 'user_assign_roles', name: '分配用户角色', description: '调整用户拥有的角色' },
  { id: 5, code: 'role_read', name: '查看角色', description: '查看角色列表、详情和权限' },
  { id: 6, code: 'role_create', name: '创建角色', description: '创建平台角色' },
  { id: 7, code: 'role_update', name: '更新角色', description: '修改角色名称和描述' },
  { id: 8, code: 'role_delete', name: '删除角色', description: '删除平台角色' },
  { id: 9, code: 'role_assign_permissions', name: '分配角色权限', description: '调整角色拥有的权限' },
  { id: 10, code: 'permission_read', name: '查看权限', description: '查看权限列表和详情' },
  { id: 11, code: 'permission_create', name: '创建权限', description: '创建权限定义' },
  { id: 12, code: 'permission_update', name: '更新权限', description: '修改权限名称和描述' },
  { id: 13, code: 'permission_delete', name: '删除权限', description: '删除权限定义' },
  { id: 14, code: 'agent_read', name: '查看 Agent', description: '查看 Agent 配置和状态' },
  { id: 15, code: 'agent_publish', name: '发布 Agent', description: '发布或回滚 Agent 版本' },
  { id: 16, code: 'model_manage', name: '管理模型', description: '维护模型和供应商配置' },
  { id: 17, code: 'audit_read', name: '查看审计', description: '查看平台审计记录' },
]

let roles: MockRole[] = [
  {
    id: 1,
    code: 'admin',
    name: '平台管理员',
    description: '负责平台配置和访问控制',
    permissionIds: permissions.map((permission) => permission.id),
  },
  {
    id: 2,
    code: 'operator',
    name: 'Agent 运营',
    description: '负责 Agent 配置、测试和发布',
    permissionIds: [14, 15, 16],
  },
  {
    id: 3,
    code: 'viewer',
    name: '只读成员',
    description: '只读查看平台资源',
    permissionIds: [14],
  },
]

let users: MockUser[] = [
  { id: 1, username: 'admin', email: 'admin@example.com', is_active: true, is_superuser: false, roleIds: [1] },
  { id: 2, username: 'operator', email: 'operator@example.com', is_active: true, is_superuser: false, roleIds: [2] },
  { id: 3, username: 'lisi', email: 'lisi@example.com', is_active: true, is_superuser: false, roleIds: [2] },
  { id: 4, username: 'wangwu', email: 'wangwu@example.com', is_active: false, is_superuser: false, roleIds: [3] },
  { id: 5, username: 'zhaoliu', email: 'zhaoliu@example.com', is_active: true, is_superuser: false, roleIds: [3] },
  { id: 6, username: 'sunqi', email: 'sunqi@example.com', is_active: true, is_superuser: false, roleIds: [] },
]

const delay = () => new Promise((resolve) => setTimeout(resolve, 180))

const nextId = (items: { id: number }[]) => Math.max(0, ...items.map((item) => item.id)) + 1

const toRole = (role: MockRole): RoleRead => ({
  id: role.id,
  code: role.code,
  name: role.name,
  description: role.description,
  permissions: permissions.filter((permission) => role.permissionIds.includes(permission.id)),
})

const toUser = (user: MockUser): UserWithRolesRead => ({
  id: user.id,
  username: user.username,
  email: user.email,
  is_active: user.is_active,
  is_superuser: user.is_superuser,
  roles: roles.filter((role) => user.roleIds.includes(role.id)).map(toRole),
})

const toUserRead = (user: MockUser): UserRead => ({
  id: user.id,
  username: user.username,
  email: user.email,
  is_active: user.is_active,
  is_superuser: user.is_superuser,
})

const getStoredUser = (): Partial<UserRead> | null => {
  const stored = localStorage.getItem('user')
  if (!stored) return null
  try {
    return JSON.parse(stored) as Partial<UserRead>
  } catch {
    return null
  }
}

const paginate = <T>(items: T[], params?: PageQuery): PageResult<T> => {
  const page = params?.page ?? 1
  const pageSize = params?.page_size ?? 10
  const start = (page - 1) * pageSize
  return {
    items: items.slice(start, start + pageSize),
    total: items.length,
    page,
    page_size: pageSize,
  }
}

export const mockAccessService: AccessService = {
  async listUsers(params) {
    await delay()
    const offset = params?.offset ?? 0
    const limit = params?.limit ?? 100
    return users.slice(offset, offset + limit).map(toUserRead)
  },

  async searchUsers(params) {
    await delay()
    const keyword = params?.keyword?.trim().toLowerCase()
    const filtered = keyword
      ? users.filter(
          (user) =>
            user.username.toLowerCase().includes(keyword) ||
            user.email.toLowerCase().includes(keyword),
        )
      : users
    return paginate(
      filtered.map(toUserRead),
      params,
    )
  },

  async getCurrentUser() {
    await delay()
    const parsed = getStoredUser()
    const matched = users.find((user) => user.id === parsed?.id) ?? users[0]
    const current = toUser(matched)
    return parsed
      ? {
          ...current,
          username: parsed.username ?? current.username,
          email: parsed.email ?? current.email,
          is_active: parsed.is_active ?? current.is_active,
          is_superuser: parsed.is_superuser ?? current.is_superuser,
        }
      : current
  },

  async getUser(id) {
    await delay()
    const user = users.find((item) => item.id === id)
    if (!user) throw new Error('用户不存在')
    const detail = toUser(user)
    const stored = getStoredUser()
    return stored?.id === id
      ? {
          ...detail,
          username: stored.username ?? detail.username,
          email: stored.email ?? detail.email,
          is_active: stored.is_active ?? detail.is_active,
        }
      : detail
  },

  async getUserRoles(id) {
    return [await this.getUser(id)]
  },

  async createUser(data: UserCreate) {
    await delay()
    if (users.some((user) => user.username === data.username)) throw new Error('用户名已存在')
    if (users.some((user) => user.email === data.email)) throw new Error('邮箱已存在')
    const user: MockUser = {
      id: nextId(users),
      username: data.username,
      email: data.email,
      is_active: true,
      is_superuser: false,
      roleIds: [],
    }
    users = [user, ...users]
    return toUserRead(user)
  },

  async deleteUser(id) {
    await delay()
    if (!users.some((user) => user.id === id)) throw new Error('用户不存在')
    users = users.filter((user) => user.id !== id)
    if (getStoredUser()?.id === id) {
      localStorage.removeItem('access_token')
      localStorage.removeItem('user')
    }
  },

  async assignUserRoles(userId, roleIds) {
    await delay()
    const user = users.find((item) => item.id === userId)
    if (!user) throw new Error('用户不存在')
    if (roleIds.some((id) => !roles.some((role) => role.id === id))) throw new Error('角色不存在')
    user.roleIds = [...roleIds]
    return toUser(user)
  },

  async listRoles() {
    await delay()
    return roles.map(toRole)
  },

  async searchRoles(params) {
    await delay()
    const keyword = params?.keyword?.trim().toLowerCase()
    const filtered = keyword
      ? roles.filter(
          (role) =>
            role.code.toLowerCase().includes(keyword) ||
            role.name.toLowerCase().includes(keyword),
        )
      : roles
    return paginate(filtered.map(toRole), params)
  },

  async getRole(id) {
    await delay()
    const role = roles.find((item) => item.id === id)
    if (!role) throw new Error('角色不存在')
    return toRole(role)
  },

  async createRole(data: RoleCreate) {
    await delay()
    if (roles.some((role) => role.code === data.code)) throw new Error('角色编码已存在')
    const role: MockRole = {
      id: nextId(roles),
      code: data.code,
      name: data.name,
      description: data.description ?? null,
      permissionIds: [],
    }
    roles = [role, ...roles]
    return toRole(role)
  },

  async updateRole(id, data: RoleUpdate) {
    await delay()
    const role = roles.find((item) => item.id === id)
    if (!role) throw new Error('角色不存在')
    if (data.name !== undefined && data.name !== null) role.name = data.name
    if (data.description !== undefined) role.description = data.description
    return toRole(role)
  },

  async deleteRole(id) {
    await delay()
    if (!roles.some((role) => role.id === id)) throw new Error('角色不存在')
    roles = roles.filter((role) => role.id !== id)
    users.forEach((user) => {
      user.roleIds = user.roleIds.filter((roleId) => roleId !== id)
    })
  },

  async assignRolePermissions(roleId, permissionIds) {
    await delay()
    const role = roles.find((item) => item.id === roleId)
    if (!role) throw new Error('角色不存在')
    if (permissionIds.some((id) => !permissions.some((permission) => permission.id === id))) {
      throw new Error('权限不存在')
    }
    role.permissionIds = [...permissionIds]
    return toRole(role)
  },

  async listPermissions() {
    await delay()
    return [...permissions]
  },

  async searchPermissions(params) {
    await delay()
    const keyword = params?.keyword?.trim().toLowerCase()
    const filtered = keyword
      ? permissions.filter(
          (permission) =>
            permission.code.toLowerCase().includes(keyword) ||
            permission.name.toLowerCase().includes(keyword),
        )
      : permissions
    return paginate(filtered, params)
  },

  async getPermission(id) {
    await delay()
    const permission = permissions.find((item) => item.id === id)
    if (!permission) throw new Error('权限不存在')
    return permission
  },

  async createPermission(data: PermissionCreate) {
    await delay()
    if (permissions.some((permission) => permission.code === data.code)) {
      throw new Error('权限编码已存在')
    }
    const permission: PermissionRead = {
      id: nextId(permissions),
      code: data.code,
      name: data.name,
      description: data.description ?? null,
    }
    permissions = [permission, ...permissions]
    return permission
  },

  async updatePermission(id, data: PermissionUpdate) {
    await delay()
    const permission = permissions.find((item) => item.id === id)
    if (!permission) throw new Error('权限不存在')
    if (data.name !== undefined && data.name !== null) permission.name = data.name
    if (data.description !== undefined) permission.description = data.description
    return permission
  },

  async deletePermission(id) {
    await delay()
    if (!permissions.some((permission) => permission.id === id)) throw new Error('权限不存在')
    permissions = permissions.filter((permission) => permission.id !== id)
    roles.forEach((role) => {
      role.permissionIds = role.permissionIds.filter((permissionId) => permissionId !== id)
    })
  },
}
