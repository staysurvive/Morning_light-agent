export interface ApiResponse<T> {
  code: 0
  message: 'success'
  data: T
}

export interface ApiErrorResponse {
  code: number
  message: string
  detail?: string
}

export interface PaginatedResponse<T> {
  data: T[]
  total: number
  page: number
  pageSize: number
}

export interface PaginationParams {
  page?: number
  pageSize?: number
}

export interface SortParams {
  sortBy?: string
  sortOrder?: 'asc' | 'desc'
}

export interface SearchParams {
  keyword?: string
}
