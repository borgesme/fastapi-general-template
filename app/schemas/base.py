from typing import Generic, TypeVar, List
from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """统一响应包装：code=0 表示成功，其他为业务错误码"""
    model_config = ConfigDict(from_attributes=True)

    code: int = 0
    msg: str = "success"
    data: T | None = None


class PageResponse(BaseModel, Generic[T]):
    model_config = ConfigDict(from_attributes=True)

    items: List[T]
    total: int
    page: int
    page_size: int
    pages: int


class PageParams(BaseModel):
    page: int = 1
    page_size: int = 20

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
