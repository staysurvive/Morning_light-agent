export interface PageQuery {
  page?: number
  page_size?: number
  keyword?: string
}

export interface PageResult<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

export interface PermissionRead {
  id: number
  code: string
  name: string
  description: string | null
}

export interface PermissionCreate {
  code: string
  name: string
  description?: string | null
}

export interface PermissionUpdate {
  name?: string | null
  description?: string | null
}

export interface RoleRead {
  id: number
  code: string
  name: string
  description: string | null
  permissions: PermissionRead[]
}

export interface RoleCreate {
  code: string
  name: string
  description?: string | null
}

export interface RoleUpdate {
  name?: string | null
  description?: string | null
}

export interface UserRead {
  id: number
  username: string
  email: string
  is_active: boolean
  is_superuser: boolean
}

export interface UserWithRolesRead extends UserRead {
  roles: RoleRead[]
}

export interface UserCreate {
  username: string
  email: string
  password: string
}

export interface AccessService {
  listUsers(params?: { offset?: number; limit?: number }): Promise<UserRead[]>
  searchUsers(params?: PageQuery): Promise<PageResult<UserRead>>
  getCurrentUser(): Promise<UserWithRolesRead>
  getUser(id: number): Promise<UserWithRolesRead>
  getUserRoles(id: number): Promise<UserWithRolesRead[]>
  createUser(data: UserCreate): Promise<UserRead>
  deleteUser(id: number): Promise<void>
  assignUserRoles(userId: number, roleIds: number[]): Promise<UserWithRolesRead>

  listRoles(): Promise<RoleRead[]>
  searchRoles(params?: PageQuery): Promise<PageResult<RoleRead>>
  getRole(id: number): Promise<RoleRead>
  createRole(data: RoleCreate): Promise<RoleRead>
  updateRole(id: number, data: RoleUpdate): Promise<RoleRead>
  deleteRole(id: number): Promise<void>
  assignRolePermissions(roleId: number, permissionIds: number[]): Promise<RoleRead>

  listPermissions(): Promise<PermissionRead[]>
  searchPermissions(params?: PageQuery): Promise<PageResult<PermissionRead>>
  getPermission(id: number): Promise<PermissionRead>
  createPermission(data: PermissionCreate): Promise<PermissionRead>
  updatePermission(id: number, data: PermissionUpdate): Promise<PermissionRead>
  deletePermission(id: number): Promise<void>
}
