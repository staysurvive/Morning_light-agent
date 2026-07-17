import base64
import hashlib
import hmac
import secrets
from io import BytesIO
from random import SystemRandom

from PIL import Image, ImageDraw, ImageFont
from redis.asyncio import Redis
from redis.exceptions import RedisError

from src.core.exceptions import BizException
from src.modules.captcha.schema import CaptchaRead, CaptchaVerifyRequest


class CaptchaService:
    CAPTCHA_EXPIRE = 5 * 60
    CAPTCHA_KEY_PREFIX = "captcha:"
    CAPTCHA_LENGTH = 4
    # Exclude 0/O, 1/I/L and 5/S, which are easy to confuse in an image.
    CAPTCHA_ALPHABET = "2346789ABCDEFGHJKMNPQRTUVWXYZ"

    def __init__(self, redis_client: Redis):
        self.redis = redis_client
        self._random = SystemRandom()

    def random_code(self) -> str:
        return "".join(
            secrets.choice(self.CAPTCHA_ALPHABET)
            for _ in range(self.CAPTCHA_LENGTH)
        )

    async def create_captcha(self) -> CaptchaRead:
        code = self.random_code()
        captcha_id = secrets.token_urlsafe(24)
        try:
            await self.redis.setex(
                self._redis_key(captcha_id),
                self.CAPTCHA_EXPIRE,
                self._hash_code(code),
            )
        except RedisError as exc:
            raise BizException(code=503, message="验证码服务暂不可用") from exc

        encoded_image = self._render_image(code)
        return CaptchaRead(
            key=captcha_id,
            image=f"data:image/png;base64,{encoded_image}",
        )

    async def verify_captcha(self, captcha: CaptchaVerifyRequest) -> bool:
        try:
            stored_hash = await self._consume_captcha(captcha.key)
        except RedisError as exc:
            raise BizException(code=503, message="验证码服务暂不可用") from exc

        if stored_hash is None:
            raise BizException(code=10001, message="验证码不存在、已过期或已使用")
        if isinstance(stored_hash, bytes):
            stored_hash = stored_hash.decode("utf-8")

        submitted_hash = self._hash_code(captcha.code.strip().upper())
        if not hmac.compare_digest(str(stored_hash), submitted_hash):
            raise BizException(code=10002, message="验证码错误")
        return True

    async def _consume_captcha(self, captcha_id: str) -> str | bytes | None:
        """Read and delete a captcha atomically, so every attempt consumes it."""
        key = self._redis_key(captcha_id)
        getdel = getattr(self.redis, "getdel", None)
        if getdel is not None:
            return await getdel(key)

        # Compatibility path for older Redis clients/servers. A transaction keeps
        # the read and deletion together even though GETDEL is unavailable.
        pipeline = self.redis.pipeline(transaction=True)
        pipeline.get(key)
        pipeline.delete(key)
        result = await pipeline.execute()
        return result[0]

    @classmethod
    def _redis_key(cls, captcha_id: str) -> str:
        return f"{cls.CAPTCHA_KEY_PREFIX}{captcha_id}"

    @staticmethod
    def _hash_code(code: str) -> str:
        return hashlib.sha256(code.encode("utf-8")).hexdigest()

    def _render_image(self, code: str) -> str:
        """Draw a small noisy PNG without relying on the incompatible captcha package."""
        width, height = 162, 54
        image = Image.new("RGB", (width, height), (248, 250, 252))
        draw = ImageDraw.Draw(image)

        for _ in range(6):
            draw.line(
                (
                    self._random.randrange(width),
                    self._random.randrange(height),
                    self._random.randrange(width),
                    self._random.randrange(height),
                ),
                fill=(self._random.randrange(150, 210), self._random.randrange(150, 210), self._random.randrange(150, 210)),
                width=1,
            )
        for _ in range(80):
            x, y = self._random.randrange(width), self._random.randrange(height)
            draw.point((x, y), fill=(self._random.randrange(160, 225), self._random.randrange(160, 225), self._random.randrange(160, 225)))

        font = ImageFont.load_default(size=30)
        bbox = draw.textbbox((0, 0), code, font=font)
        text_width, text_height = bbox[2] - bbox[0], bbox[3] - bbox[1]
        draw.text(
            ((width - text_width) // 2, (height - text_height) // 2 - bbox[1]),
            code,
            font=font,
            fill=(20, 50, 115),
        )

        image_bytes = BytesIO()
        image.save(image_bytes, format="PNG")
        return base64.b64encode(image_bytes.getvalue()).decode("ascii")
