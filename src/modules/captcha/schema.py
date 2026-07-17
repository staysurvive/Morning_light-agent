from pydantic import BaseModel, Field


class CaptchaRead(BaseModel):
    """A newly generated captcha image and its verification key."""

    key: str
    image: str = Field(description="A data:image/png;base64 URL")


class CaptchaVerifyRequest(BaseModel):
    """Payload used to verify a captcha."""

    key: str = Field(min_length=1, max_length=128)
    code: str = Field(min_length=1, max_length=16)


class CaptchaVerifyResult(BaseModel):
    """Captcha verification result."""

    valid: bool
