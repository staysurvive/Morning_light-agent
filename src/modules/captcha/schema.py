from pydantic import BaseModel

class CaptchaRead(BaseModel):
    """验证码读取体"""
    key: str
    image: str  # data:image/png;base64,...

class CaptchaVerifyRequest(BaseModel):
    """验证码验证请求体"""
    key: str
    code: str
