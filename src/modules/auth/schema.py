# 
# {
#   "username": "testuser",
#   "password": "123456",
#   "captcha_key": "550e8400-e29b-41d4-a716-446655440000",
#   "captcha_code": "A3BX"
# }


from pydantic import BaseModel,Field
# 登录请求
class AuthLoginRequest(BaseModel):
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")
    captcha_key: str = Field(..., description="验证码key")
    captcha_code: str = Field(..., description="验证码")


# 登录响应
class TokenResponse(BaseModel):
    access_token: str = Field(..., description="登录token")
    token_type: str = "Bearer"
