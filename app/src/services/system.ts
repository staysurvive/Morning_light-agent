import { USE_MOCK } from './config'
import { mockSystemService } from './mock/system'
import { apiSystemService } from './api/system'

export const systemService = USE_MOCK ? mockSystemService : apiSystemService

// 导出真实后端类型，供页面在非 mock 模式下使用
export type {
  BackendUser,
  BackendUserWithRoles,
  BackendRole,
  BackendPermission,
  PageResult,
} from './api/system'
