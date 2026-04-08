from typing import Generic, TypeVar, List
from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


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
