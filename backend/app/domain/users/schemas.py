from datetime import datetime
from pydantic import BaseModel


class AdminUserResponse(BaseModel):
    id: int
    username: str | None = None
    email: str
    role: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UserListResponse(BaseModel):
    items: list[AdminUserResponse]
    total: int
    page: int
    page_size: int


class UserStatusUpdate(BaseModel):
    is_active: bool


class UserStatusUpdateResponse(BaseModel):
    user: AdminUserResponse
