from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.deps import get_db
from app.domain.auth.deps import get_current_user
from app.domain.users import list_users, get_user, set_user_active
from app.domain.users.schemas import (
    AdminUserResponse,
    UserListResponse,
    UserStatusUpdate,
    UserStatusUpdateResponse,
)
from app.models.user import User

router = APIRouter(prefix="/users")


@router.get("", response_model=UserListResponse)
def list_users_endpoint(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: str | None = Query(None),
    status: str | None = Query(None),
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    users, total = list_users(
        db,
        page=page,
        page_size=page_size,
        keyword=keyword,
        status_filter=status,
    )
    return UserListResponse(
        items=[AdminUserResponse.model_validate(u) for u in users],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{user_id}", response_model=AdminUserResponse)
def user_detail(
    user_id: int,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    return AdminUserResponse.model_validate(get_user(db, user_id))


@router.patch("/{user_id}/active", response_model=UserStatusUpdateResponse)
def change_user_active(
    user_id: int,
    payload: UserStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user = set_user_active(db, user_id, payload.is_active, actor=current_user)
    return UserStatusUpdateResponse(user=AdminUserResponse.model_validate(user))
