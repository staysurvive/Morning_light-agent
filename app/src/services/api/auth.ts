import { apiClient, tokenStorage } from './client'

export interface LoginRequest {
  username: string
  password: string
  captcha_key: string
  captcha_code: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
}

export interface CaptchaResponse {
  key: string
  image: string // base64
}

export const apiAuthService = {
  async getCaptcha(): Promise<CaptchaResponse> {
    return apiClient.get<CaptchaResponse>('/captcha')
  },

  async verifyCaptcha(key: string, code: string): Promise<boolean> {
    return apiClient.post<boolean>('/captcha', { key, code })
  },

  async login(data: LoginRequest): Promise<TokenResponse> {
    const result = await apiClient.post<TokenResponse>('/auth/login', data)
    tokenStorage.set(result.access_token)
    return result
  },

  logout() {
    tokenStorage.remove()
    localStorage.removeItem('user')
  },

  isLoggedIn(): boolean {
    const token = tokenStorage.get()
    return Boolean(token && !token.startsWith('mock-token-'))
  },
}
