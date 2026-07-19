import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken

from src.core.config import get_settings


def _fernet() -> Fernet:
    digest = hashlib.sha256(get_settings().APP_SECRET_KEY.encode("utf-8")).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


def encrypt_secret(value: str) -> str:
    return _fernet().encrypt(value.encode("utf-8")).decode("ascii")


def decrypt_secret(value: str | None) -> str | None:
    if not value:
        return None
    try:
        return _fernet().decrypt(value.encode("ascii")).decode("utf-8")
    except InvalidToken as exc:
        raise ValueError("密钥解密失败，请检查 APP_SECRET_KEY") from exc
