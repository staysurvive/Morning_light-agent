from datetime import datetime, timedelta, timezone
import jwt

SECRET_KEY = "17bfb8d274f91b4bf09f55d0c2d086319c251859c7a0edf1aef823e4c3c5adea"
ALGORITHM = "HS256"

# 配置OAuth2 Bearer 模式
from fastapi.security import OAuth2PasswordBearer
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

def encode_jwt(payload: dict) -> str:
    payload_copy = payload.copy()
    # 更新过期时间为30分钟后。注意使用 utc 时间
    payload_copy["exp"] = datetime.now(timezone.utc) + timedelta(minutes=30)
    payload_copy["iat"] = datetime.now(timezone.utc)

    token = jwt.encode(payload_copy, key =SECRET_KEY, algorithm=ALGORITHM)
    return token

def verify_jwt(token: str) -> dict:
    try:
        payload = jwt.decode(token, key=SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise Exception("token已经过期")
    except jwt.InvalidTokenError:
        raise Exception("非法token")
    except Exception as e:
        raise Exception(f"token校验失败: {str(e)}")
