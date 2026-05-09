"""Common base schemas."""
from datetime import datetime
from typing import Generic, TypeVar, List, Optional
from pydantic import BaseModel, Field

T = TypeVar("T")


class BaseSchema(BaseModel):
    model_config = {"from_attributes": True}


class MessageResponse(BaseSchema):
    message: str
    success: bool = True


class TokenPair(BaseSchema):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class PaginatedResponse(BaseSchema, Generic[T]):
    items: List[T]
    total: int
    page: int
    page_size: int
    has_next: bool


class PageParams(BaseModel):
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)
