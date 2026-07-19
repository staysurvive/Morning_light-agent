import type { LoginRequest, TokenResponse, CaptchaResponse } from '../api/auth'
import { tokenStorage } from '../api/client'

const MOCK_ACCOUNTS = {
  admin: {
    password: 'Admin123!',
    user: { id: 1, username: 'admin', email: 'admin@example.com', is_active: true, is_superuser: false },
  },
  operator: {
    password: 'Operator123!',
    user: { id: 2, username: 'operator', email: 'operator@example.com', is_active: true, is_superuser: false },
  },
} as const

// Mock 验证码由登录页生成和校验，这里只保留与真实服务一致的接口形状。
export const mockAuthService = {
  async getCaptcha(): Promise<CaptchaResponse> {
    await new Promise((r) => setTimeout(r, 200))
    return { key: 'mock-captcha-key', image: '' }
  },

  async verifyCaptcha(_key: string, code: string): Promise<boolean> {
    await new Promise((resolve) => setTimeout(resolve, 120))
    return Boolean(code.trim())
  },

  async login(data: LoginRequest): Promise<TokenResponse> {
    await new Promise((r) => setTimeout(r, 800))
    const username = data.username.trim() as keyof typeof MOCK_ACCOUNTS
    const account = MOCK_ACCOUNTS[username]
    if (!account || account.password !== data.password) throw new Error('用户名或密码错误')

    const token = 'mock-token-' + Date.now()
    tokenStorage.set(token)
    localStorage.setItem('user', JSON.stringify(account.user))
    return { access_token: token, token_type: 'bearer' }
  },

  logout() {
    tokenStorage.remove()
    localStorage.removeItem('user')
  },

  isLoggedIn(): boolean {
    return tokenStorage.get()?.startsWith('mock-token-') ?? false
  },
}
