from fastapi import HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session
from app.models.user import User


def list_users(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    keyword: str | None = None,
    status_filter: str | None = None,
) -> tuple[list[User], int]:
    query = db.query(User)
    if keyword:
        like = f"%{keyword}%"
        query = query.filter(or_(User.email.like(like), User.username.like(like)))
    if status_filter == "active":
        query = query.filter(User.is_active.is_(True))
    elif status_filter == "inactive":
        query = query.filter(User.is_active.is_(False))
    total = query.count()
    users = query.order_by(User.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return users, total


def get_user(db: Session, user_id: int) -> User:
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    return user


def set_user_active(db: Session, user_id: int, is_active: bool, actor: User) -> User:
    user = get_user(db, user_id)
    if user.id == actor.id and not is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能禁用当前登录的管理员账号",
        )
    user.is_active = is_active
    db.commit()
    db.refresh(user)
    return user
