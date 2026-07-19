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

class PageResult(BaseModel, Generic[T]):
    """分页结果包装"""
    items: list[T] = []
    total: int = 0
    page: int = 1
    page_size: int = 20

