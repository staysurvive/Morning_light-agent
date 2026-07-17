from fastapi import APIRouter, Depends
from redis.asyncio import Redis

from src.core.base_schema import ResponseSchema
from src.infra.redis_cache import get_redis_client
from src.modules.captcha.schema import CaptchaRead, CaptchaVerifyRequest
from src.modules.captcha.service import CaptchaService

router = APIRouter(prefix="/captcha", tags=["验证码"])


def get_captcha_service(
    redis_client: Redis = Depends(get_redis_client),
) -> CaptchaService:
    return CaptchaService(redis_client)


@router.get("", response_model=ResponseSchema[CaptchaRead], summary="获取验证码")
async def get_captcha(
    svc: CaptchaService = Depends(get_captcha_service),
) -> ResponseSchema[CaptchaRead]:
    return ResponseSchema(data=await svc.create_captcha())


@router.post("", response_model=ResponseSchema[bool], summary="验证验证码")
async def verify_captcha(
    captcha: CaptchaVerifyRequest,
    svc: CaptchaService = Depends(get_captcha_service),
) -> ResponseSchema[bool]:
    return ResponseSchema(data=await svc.verify_captcha(captcha))
