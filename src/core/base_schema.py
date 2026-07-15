from typing import TypeVar, Generic, Optional
from pydantic import BaseModel
# 响应模型基类
# 所有响应模型都继承自此基类
# 包含 code, message, data 字段
T = TypeVar("T")


class ResponseSchema(BaseModel, Generic[T]):
    code: int = 200
    message: str = "success"
    data: Optional[T] = None