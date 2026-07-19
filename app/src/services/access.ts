import { USE_MOCK } from './config'
import { apiAccessService } from './api/access'
import { mockAccessService } from './mock/access'

export const accessService = USE_MOCK ? mockAccessService : apiAccessService

export type {
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
} from './types/access'
