import { API_BASE } from '../config'

interface ApiEnvelope<T> {
  code?: number
  message?: string
  data?: T
}

interface ValidationIssue {
  loc?: Array<string | number>
  msg?: string
}

export class ApiError extends Error {
  status: number
  code?: number

  constructor(message: string, status: number, code?: number) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
  }
}

// Token 管理
export const tokenStorage = {
  get: () => localStorage.getItem('access_token'),
  set: (token: string) => localStorage.setItem('access_token', token),
  remove: () => localStorage.removeItem('access_token'),
}

class ApiClient {
  private baseUrl: string

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl
  }

  private getHeaders(): Record<string, string> {
    const headers: Record<string, string> = { 'Content-Type': 'application/json' }
    const token = tokenStorage.get()
    if (token) headers['Authorization'] = `Bearer ${token}`
    return headers
  }

  private async handleResponse<T>(res: Response): Promise<T> {
    const contentType = res.headers.get('content-type') ?? ''
    const json = contentType.includes('application/json')
      ? ((await res.json()) as ApiEnvelope<T> & { detail?: ValidationIssue[] | string })
      : null

    const businessCode = json?.code
    if (res.status === 401 || businessCode === 401) {
      tokenStorage.remove()
      if (window.location.pathname !== '/login') window.location.assign('/login')
      throw new ApiError(json?.message || '登录已过期，请重新登录', res.status, businessCode)
    }

    if (!res.ok) {
      const detail = Array.isArray(json?.detail)
        ? json.detail.map((issue) => issue.msg).filter(Boolean).join('；')
        : json?.detail
      throw new ApiError(detail || json?.message || `请求失败（HTTP ${res.status}）`, res.status, businessCode)
    }

    if (businessCode !== undefined && businessCode !== 200 && businessCode !== 0) {
      throw new ApiError(json?.message || '请求失败', res.status, businessCode)
    }

    if (json) return (json.data !== undefined ? json.data : json) as T
    return undefined as T
  }

  async get<T>(path: string, options?: { params?: object }): Promise<T> {
    const url = new URL(`${this.baseUrl}${path}`)
    if (options?.params) {
      Object.entries(options.params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          url.searchParams.set(key, String(value))
        }
      })
    }
    const res = await fetch(url.toString(), { headers: this.getHeaders() })
    return this.handleResponse<T>(res)
  }

  async getBlob(path: string, options?: { params?: object }): Promise<Blob> {
    const url = new URL(`${this.baseUrl}${path}`)
    if (options?.params) {
      Object.entries(options.params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) url.searchParams.set(key, String(value))
      })
    }
    const res = await fetch(url.toString(), { headers: this.getHeaders() })
    if (!res.ok || (res.headers.get('content-type') ?? '').includes('application/json')) {
      return this.handleResponse<Blob>(res)
    }
    return res.blob()
  }

  async post<T>(path: string, body?: unknown): Promise<T> {
    const isFormData = body instanceof FormData
    const headers = this.getHeaders()
    if (isFormData) delete headers['Content-Type'] // let browser set multipart boundary
    const res = await fetch(`${this.baseUrl}${path}`, {
      method: 'POST',
      headers,
      body: isFormData ? body : body ? JSON.stringify(body) : undefined,
    })
    return this.handleResponse<T>(res)
  }

  async put<T>(path: string, body?: unknown): Promise<T> {
    const res = await fetch(`${this.baseUrl}${path}`, {
      method: 'PUT',
      headers: this.getHeaders(),
      body: body ? JSON.stringify(body) : undefined,
    })
    return this.handleResponse<T>(res)
  }

  async delete<T>(path: string): Promise<T> {
    const res = await fetch(`${this.baseUrl}${path}`, {
      method: 'DELETE',
      headers: this.getHeaders(),
    })
    return this.handleResponse<T>(res)
  }
}

export const apiClient = new ApiClient(API_BASE)
