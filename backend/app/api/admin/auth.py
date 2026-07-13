from fastapi import APIRouter, Depends, Response, HTTPException, status
from sqlalchemy.orm import Session
from app.db.deps import get_db
from app.domain.auth import register_user, authenticate_user
from app.domain.auth.schemas import RegisterRequest, LoginRequest, AuthResponse, UserResponse
from app.core.security import create_access_token, set_auth_cookie, clear_auth_cookie
from app.domain.auth.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/auth")


@router.post("/register", response_model=AuthResponse)
def register(req: RegisterRequest, response: Response, db: Session = Depends(get_db)):
    user = register_user(db, req.email, req.password, role="admin")
    token = create_access_token({"sub": str(user.id), "email": user.email, "role": user.role})
    set_auth_cookie(response, token)
    return AuthResponse(user=UserResponse.model_validate(user))


@router.post("/login", response_model=AuthResponse)
def login(req: LoginRequest, response: Response, db: Session = Depends(get_db)):
    user = authenticate_user(db, req.email, req.password)
    if user.role != "admin":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无权访问管理后台")
    token = create_access_token({"sub": str(user.id), "email": user.email, "role": user.role})
    set_auth_cookie(response, token)
    return AuthResponse(user=UserResponse.model_validate(user))


@router.post("/logout")
def logout(response: Response, current_user: User = Depends(get_current_user)):
    clear_auth_cookie(response)
    return {"message": "已登出"}


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)):
    return UserResponse.model_validate(current_user)
