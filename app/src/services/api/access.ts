import { apiClient } from './client'
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

const normalizePermission = (permission: PermissionRead): PermissionRead => ({
  ...permission,
  description: permission.description ?? null,
})

const normalizeRole = (role: RoleRead): RoleRead => ({
  ...role,
  description: role.description ?? null,
  permissions: (role.permissions ?? []).map(normalizePermission),
})

const normalizeUser = (user: UserWithRolesRead): UserWithRolesRead => ({
  ...user,
  roles: (user.roles ?? []).map(normalizeRole),
})

export const apiAccessService: AccessService = {
  listUsers(params) {
    return apiClient.get<UserRead[]>('/users', { params })
  },

  searchUsers(params?: PageQuery) {
    return apiClient.get<PageResult<UserRead>>('/users/search', { params })
  },

  async getCurrentUser() {
    return normalizeUser(await apiClient.get<UserWithRolesRead>('/users/me'))
  },

  async getUser(id) {
    return normalizeUser(await apiClient.get<UserWithRolesRead>(`/users/${id}`))
  },

  async getUserRoles(id) {
    const users = await apiClient.get<UserWithRolesRead[]>(`/users/${id}/roles`)
    return users.map(normalizeUser)
  },

  createUser(data: UserCreate) {
    return apiClient.post<UserRead>('/users', data)
  },

  deleteUser(id) {
    return apiClient.delete<void>(`/users/${id}`)
  },

  async assignUserRoles(userId, roleIds) {
    return normalizeUser(
      await apiClient.put<UserWithRolesRead>(`/users/${userId}/roles`, { role_ids: roleIds }),
    )
  },

  async listRoles() {
    const roles = await apiClient.get<RoleRead[]>('/roles')
    return roles.map(normalizeRole)
  },

  async searchRoles(params?: PageQuery) {
    const result = await apiClient.get<PageResult<RoleRead>>('/roles/search', { params })
    return { ...result, items: result.items.map(normalizeRole) }
  },

  async getRole(id) {
    return normalizeRole(await apiClient.get<RoleRead>(`/roles/${id}`))
  },

  async createRole(data: RoleCreate) {
    return normalizeRole(await apiClient.post<RoleRead>('/roles', data))
  },

  async updateRole(id, data: RoleUpdate) {
    return normalizeRole(await apiClient.put<RoleRead>(`/roles/${id}`, data))
  },

  deleteRole(id) {
    return apiClient.delete<void>(`/roles/${id}`)
  },

  async assignRolePermissions(roleId, permissionIds) {
    return normalizeRole(
      await apiClient.put<RoleRead>(`/roles/${roleId}/permissions`, {
        permission_ids: permissionIds,
      }),
    )
  },

  async listPermissions() {
    const permissions = await apiClient.get<PermissionRead[]>('/permissions/')
    return permissions.map(normalizePermission)
  },

  async searchPermissions(params?: PageQuery) {
    const result = await apiClient.get<PageResult<PermissionRead>>('/permissions/search', { params })
    return { ...result, items: result.items.map(normalizePermission) }
  },

  async getPermission(id) {
    return normalizePermission(await apiClient.get<PermissionRead>(`/permissions/${id}`))
  },

  async createPermission(data: PermissionCreate) {
    return normalizePermission(await apiClient.post<PermissionRead>('/permissions/', data))
  },

  async updatePermission(id, data: PermissionUpdate) {
    return normalizePermission(
      await apiClient.put<PermissionRead>(`/permissions/${id}`, data),
    )
  },

  deletePermission(id) {
    return apiClient.delete<void>(`/permissions/${id}`)
  },
}
