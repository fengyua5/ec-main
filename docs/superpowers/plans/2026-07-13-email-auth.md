---
change: add-email-auth
design-doc: docs/superpowers/specs/2026-07-13-email-auth-design.md
base-ref: 49b3c9a3fb4a4148b6a68d52aae048db2f0d37de
archived-with: 2026-07-15-add-email-auth
---

# Email Auth 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 为 EC Main 平台的买家端（Web）和 Admin 后台分别提供邮箱+密码的登录注册能力。

**Architecture:** domain 层（`domain/auth/`）封装业务逻辑和认证依赖，API 层（`api/web/` 和 `api/admin/`）隔离挂载。最终路由：`/api/v1/web/auth/*` 和 `/api/v1/admin/auth/*`。

**Tech Stack:** FastAPI + SQLAlchemy + SQLite, passlib+bcrypt, python-jose, Next.js + React 19, Tailwind v4

archived-with: 2026-07-15-add-email-auth
---

## 目录结构

```
backend/app/
├── api/
│   ├── web/
│   │   ├── __init__.py
│   │   └── auth.py            # Web 端路由（/api/v1/web/auth/*）
│   └── admin/
│       ├── __init__.py
│       └── auth.py            # Admin 端路由（/api/v1/admin/auth/*）
├── core/
│   ├── config.py              # + jwt_secret
│   └── security.py            # bcrypt + JWT + cookie 工具
├── db/
│   ├── session.py             # + Base import
│   └── deps.py                # get_db 依赖
├── domain/
│   └── auth/
│       ├── __init__.py         # register_user, authenticate_user
│       ├── schemas.py          # Pydantic 请求/响应模型
│       └── deps.py             # get_current_user 认证依赖
└── models/
    ├── __init__.py
    └── user.py                 # User SQLAlchemy 模型
```

archived-with: 2026-07-15-add-email-auth
---

## 1. 后端认证基础设施

### Task 1.1: 安装 Python 依赖

**Files:**
- Modify: `backend/pyproject.toml`

- [x] **Step 1: 添加依赖**

向 `backend/pyproject.toml` 的 `[project.dependencies]` 新增：

```toml
python-jose>=3.3.0
passlib>=1.7.4
bcrypt>=4.0.0
pydantic[email]>=2.0.0
```

- [x] **Step 2: 安装依赖**

```bash
cd backend && uv sync
```

- [x] **Step 3: 提交**

```bash
git add backend/pyproject.toml backend/uv.lock
git commit -m "chore: add python-jose passlib bcrypt pydantic[email] dependencies"
```

### Task 1.2: 创建 User SQLAlchemy 模型 + 自动建表

**Files:**
- Create: `backend/app/models/__init__.py`
- Create: `backend/app/models/user.py`
- Modify: `backend/app/db/session.py`
- Modify: `backend/app/main.py`

- [x] **Step 1: 创建 models 包**

`backend/app/models/__init__.py`:
```python
from app.models.user import User

__all__ = ["User"]
```

`backend/app/models/user.py`:
```python
from datetime import datetime
from sqlalchemy import String, DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
```

- [x] **Step 2: 修改 db/session.py 导入 Base**

`backend/app/db/session.py`:
```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.user import Base

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False}
    if settings.database_url.startswith("sqlite")
    else {},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
```

- [x] **Step 3: 在 main.py 添加启动建表**

`backend/app/main.py`:
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.web.auth import router as web_auth_router
from app.api.admin.auth import router as admin_auth_router
from app.core.config import settings
from app.models.user import Base
from app.db.session import engine

app = FastAPI(title="EC Main API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "ec-backend"}


app.include_router(web_auth_router, prefix="/api/v1/web")
app.include_router(admin_auth_router, prefix="/api/v1/admin")
```

- [x] **Step 4: 验证模型导入**

```bash
cd backend && uv run python -c "from app.models.user import User; print('OK')"
```

Expected: `OK`

- [x] **Step 5: 提交**

```bash
git add backend/app/models/ backend/app/db/session.py backend/app/main.py
git commit -m "feat: add User model with SQLAlchemy Base and auto table creation"
```

### Task 1.3: 创建密码哈希 + JWT + Cookie 工具

**Files:**
- Create: `backend/app/core/security.py`
- Modify: `backend/app/core/config.py`

- [x] **Step 1: 在 config.py 添加 jwt_secret**

`backend/app/core/config.py`:
```python
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "sqlite:///./.data/ec-main.sqlite3"
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:3001"]
    jwt_secret: str = "dev-secret-key-change-in-production"
    model_config = SettingsConfigDict(env_file=".env", env_prefix="")


settings = Settings()
```

- [x] **Step 2: 创建 security.py**

`backend/app/core/security.py`:
```python
from datetime import datetime, timedelta, timezone
from fastapi import Response
from jose import jwt, JWTError
from passlib.context import CryptContext
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"])

SECRET_KEY = settings.jwt_secret
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None


def set_auth_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key="token",
        value=token,
        httponly=True,
        samesite="lax",
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )


def clear_auth_cookie(response: Response) -> None:
    response.delete_cookie(key="token", path="/")
```

- [x] **Step 3: 验证 JWT 工具**

```bash
cd backend && uv run python -c "
from app.core.security import create_access_token, decode_access_token
token = create_access_token({'sub': '1', 'email': 'a@b.com', 'role': 'buyer'})
payload = decode_access_token(token)
assert payload is not None and payload['sub'] == '1' and payload['email'] == 'a@b.com'
assert decode_access_token('invalid') is None
print('OK')
"
```

- [x] **Step 4: 提交**

```bash
git add backend/app/core/security.py backend/app/core/config.py
git commit -m "feat: add password hashing, JWT creation/verification, and cookie utilities"
```

archived-with: 2026-07-15-add-email-auth
---

## 2. Domain 层（共享业务逻辑）

### Task 2.1: 创建 get_db 数据库依赖

**Files:**
- Create: `backend/app/db/deps.py`

- [x] **Step 1: 创建 deps.py**

`backend/app/db/deps.py`:
```python
from collections.abc import Generator
from sqlalchemy.orm import Session
from app.db.session import SessionLocal


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

- [x] **Step 2: 提交**

```bash
git add backend/app/db/deps.py
git commit -m "feat: add get_db dependency for SQLAlchemy session injection"
```

### Task 2.2: 创建 domain/auth 业务逻辑

**Files:**
- Create: `backend/app/domain/__init__.py`
- Create: `backend/app/domain/auth/__init__.py`
- Create: `backend/app/domain/auth/schemas.py`
- Create: `backend/app/domain/auth/deps.py`

- [x] **Step 1: 创建 domain/auth/\_\_init\_\_.py — 注册/登录业务逻辑**

`backend/app/domain/__init__.py`:
```python
```

`backend/app/domain/auth/__init__.py`:
```python
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.user import User
from app.core.security import hash_password, verify_password


def register_user(db: Session, email: str, password: str, role: str) -> User:
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="该邮箱已被注册",
        )
    user = User(
        email=email,
        password_hash=hash_password(password),
        role=role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str) -> User:
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="邮箱或密码不正确",
        )
    return user
```

- [x] **Step 2: 创建 Pydantic schemas**

`backend/app/domain/auth/schemas.py`:
```python
from datetime import datetime
from pydantic import BaseModel, EmailStr


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    email: str
    role: str
    created_at: datetime

    model_config = {"from_attributes": True}


class AuthResponse(BaseModel):
    user: UserResponse
```

- [x] **Step 3: 创建认证依赖 deps.py**

`backend/app/domain/auth/deps.py`:
```python
from fastapi import Depends, Request, HTTPException, status
from sqlalchemy.orm import Session
from app.db.deps import get_db
from app.core.security import decode_access_token
from app.models.user import User


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    token = request.cookies.get("token")
    if not token:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="未登录")
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的认证凭证")
    user = db.query(User).filter(User.id == int(payload["sub"])).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户不存在")
    return user
```

- [x] **Step 4: 提交**

```bash
git add backend/app/domain/
git commit -m "feat: add auth domain layer with business logic, schemas, and auth dependency"
```

archived-with: 2026-07-15-add-email-auth
---

## 3. API 路由（Web + Admin 隔离）

### Task 3.1: 创建 Web auth 路由

**Files:**
- Create: `backend/app/api/web/__init__.py`
- Create: `backend/app/api/web/auth.py`

- [x] **Step 1: 创建 Web auth 路由文件**

`backend/app/api/__init__.py`:
```python
```

`backend/app/api/web/__init__.py`:
```python
```

`backend/app/api/web/auth.py`:
```python
from fastapi import APIRouter, Depends, Response
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
    user = register_user(db, req.email, req.password, role="buyer")
    token = create_access_token({"sub": str(user.id), "email": user.email, "role": user.role})
    set_auth_cookie(response, token)
    return AuthResponse(user=UserResponse.model_validate(user))


@router.post("/login", response_model=AuthResponse)
def login(req: LoginRequest, response: Response, db: Session = Depends(get_db)):
    user = authenticate_user(db, req.email, req.password)
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
```

- [x] **Step 2: 提交**

```bash
git add backend/app/api/web/
git commit -m "feat: add web auth routes (register/login/logout/me)"
```

### Task 3.2: 创建 Admin auth 路由

**Files:**
- Create: `backend/app/api/admin/__init__.py`
- Create: `backend/app/api/admin/auth.py`

- [x] **Step 1: 创建 Admin auth 路由文件**

`backend/app/api/admin/__init__.py`:
```python
```

`backend/app/api/admin/auth.py`:
```python
from fastapi import APIRouter, Depends, Response
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
```

- [x] **Step 2: 提交**

```bash
git add backend/app/api/admin/
git commit -m "feat: add admin auth routes (register/login/logout/me)"
```

### Task 3.3: 编写 auth API 测试

**Files:**
- Create: `backend/tests/test_auth.py`

- [x] **Step 1: 创建测试文件**

`backend/tests/test_auth.py`:
```python
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_register_success() -> None:
    response = client.post("/api/v1/web/auth/register", json={
        "email": "test@example.com",
        "password": "password123",
    })
    assert response.status_code == 200
    data = response.json()
    assert data["user"]["email"] == "test@example.com"
    assert data["user"]["role"] == "buyer"
    assert "token" in response.cookies


def test_register_duplicate_email() -> None:
    response = client.post("/api/v1/web/auth/register", json={
        "email": "dup@example.com",
        "password": "password123",
    })
    assert response.status_code == 200
    response = client.post("/api/v1/web/auth/register", json={
        "email": "dup@example.com",
        "password": "password456",
    })
    assert response.status_code == 409


def test_login_success() -> None:
    email = "login-test@example.com"
    client.post("/api/v1/web/auth/register", json={
        "email": email, "password": "password123",
    })
    response = client.post("/api/v1/web/auth/login", json={
        "email": email, "password": "password123",
    })
    assert response.status_code == 200
    assert response.json()["user"]["email"] == email


def test_login_wrong_password() -> None:
    response = client.post("/api/v1/web/auth/login", json={
        "email": "login-test@example.com",
        "password": "wrong-password",
    })
    assert response.status_code == 401


def test_login_nonexistent_email() -> None:
    response = client.post("/api/v1/web/auth/login", json={
        "email": "nonexistent@example.com",
        "password": "password123",
    })
    assert response.status_code == 401


def test_logout() -> None:
    client.post("/api/v1/web/auth/register", json={
        "email": "logout-test@example.com",
        "password": "password123",
    })
    response = client.post("/api/v1/web/auth/logout")
    assert response.status_code == 200


def test_me_unauthenticated() -> None:
    response = client.get("/api/v1/web/auth/me")
    assert response.status_code == 401


def test_me_authenticated() -> None:
    email = "me-test@example.com"
    client.post("/api/v1/web/auth/register", json={
        "email": email, "password": "password123",
    })
    response = client.get("/api/v1/web/auth/me")
    assert response.status_code == 200
    assert response.json()["email"] == email


def test_admin_register() -> None:
    response = client.post("/api/v1/admin/auth/register", json={
        "email": "admin@example.com",
        "password": "admin123",
    })
    assert response.status_code == 200
    assert response.json()["user"]["role"] == "admin"


def test_admin_login() -> None:
    response = client.post("/api/v1/admin/auth/login", json={
        "email": "admin@example.com",
        "password": "admin123",
    })
    assert response.status_code == 200
    assert response.json()["user"]["role"] == "admin"


def test_invalid_email() -> None:
    response = client.post("/api/v1/web/auth/register", json={
        "email": "not-an-email",
        "password": "password123",
    })
    assert response.status_code == 422
```

- [x] **Step 2: 运行测试**

```bash
cd backend && rm -f .data/ec-main.sqlite3 && uv run pytest tests/ -v
```

Expected: ALL PASS (test_health + test_auth)

- [x] **Step 3: 提交**

```bash
git add backend/tests/test_auth.py
git commit -m "test: add auth API tests covering register, login, logout, me, error cases"
```

archived-with: 2026-07-15-add-email-auth
---

## 4. SDK Auth 方法

### Task 4.1: SDK 新增 auth 方法

**Files:**
- Create: `packages/sdk/src/auth.ts`
- Modify: `packages/sdk/src/index.ts`

- [x] **Step 1: 创建 auth.ts**

`packages/sdk/src/auth.ts`:
```typescript
import type { ApiClient } from "./client";

export type UserResponse = {
  id: number;
  email: string;
  role: "buyer" | "admin";
  created_at: string;
};

export type AuthResponse = {
  user: UserResponse;
};

export type RegisterRequest = {
  email: string;
  password: string;
};

export type LoginRequest = {
  email: string;
  password: string;
};

export function register(
  client: ApiClient,
  path: "/web" | "/admin",
  data: RegisterRequest,
): Promise<AuthResponse> {
  return client.request<AuthResponse>(`/api/v1${path}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}

export function login(
  client: ApiClient,
  path: "/web" | "/admin",
  data: LoginRequest,
): Promise<AuthResponse> {
  return client.request<AuthResponse>(`/api/v1${path}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}

export function logout(
  client: ApiClient,
  path: "/web" | "/admin",
): Promise<{ message: string }> {
  return client.request<{ message: string }>(`/api/v1${path}/auth/logout`, {
    method: "POST",
  });
}

export function getMe(
  client: ApiClient,
  path: "/web" | "/admin",
): Promise<UserResponse> {
  return client.request<UserResponse>(`/api/v1${path}/auth/me`, {
    method: "GET",
  });
}
```

- [x] **Step 2: 在 index.ts 导出**

`packages/sdk/src/index.ts`:
```typescript
export { createApiClient } from "./client";
export type { ApiClient } from "./client";
export { checkHealth } from "./health";
export type { HealthResponse } from "./health";
export { register, login, logout, getMe } from "./auth";
export type { UserResponse, AuthResponse, RegisterRequest, LoginRequest } from "./auth";
```

- [x] **Step 3: TypeScript 编译检查**

```bash
pnpm exec tsc --noEmit -p packages/sdk/tsconfig.json
```

Expected: No errors

- [x] **Step 4: 提交**

```bash
git add packages/sdk/src/auth.ts packages/sdk/src/index.ts
git commit -m "feat: add auth methods to SDK"
```

archived-with: 2026-07-15-add-email-auth
---

## 5. 前端登录注册页面

### Task 5.1: Web 端注册页面

**Files:**
- Create: `apps/web/app/register/page.tsx`

- [x] **Step 1: 创建注册页面**

`apps/web/app/register/page.tsx`:
```typescript
"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { createApiClient, register } from "@ec/sdk";
import { Button } from "@ec/ui";

const client = createApiClient({
  baseUrl: process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000",
});

export default function RegisterPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await register(client, "/web", { email, password });
      router.push("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "注册失败");
    }
  }

  return (
    <div className="mx-auto mt-16 max-w-md">
      <h1 className="mb-6 text-2xl font-bold">注册买家账号</h1>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="mb-1 block text-sm font-medium">邮箱</label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            className="w-full rounded border px-3 py-2"
          />
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium">密码</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            className="w-full rounded border px-3 py-2"
          />
        </div>
        {error && <p className="text-sm text-red-600">{error}</p>}
        <Button type="submit" variant="primary" className="w-full">
          注册
        </Button>
        <p className="text-sm text-gray-500">
          已有账号？<a href="/login" className="text-blue-600 hover:underline">去登录</a>
        </p>
      </form>
    </div>
  );
}
```

- [x] **Step 2: 提交**

```bash
git add apps/web/app/register/page.tsx
git commit -m "feat: add web buyer registration page"
```

### Task 5.2: Web 端登录页面

**Files:**
- Create: `apps/web/app/login/page.tsx`

- [x] **Step 1: 创建登录页面**

`apps/web/app/login/page.tsx`:
```typescript
"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { createApiClient, login } from "@ec/sdk";
import { Button } from "@ec/ui";

const client = createApiClient({
  baseUrl: process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000",
});

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await login(client, "/web", { email, password });
      router.push("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "登录失败");
    }
  }

  return (
    <div className="mx-auto mt-16 max-w-md">
      <h1 className="mb-6 text-2xl font-bold">买家登录</h1>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="mb-1 block text-sm font-medium">邮箱</label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            className="w-full rounded border px-3 py-2"
          />
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium">密码</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            className="w-full rounded border px-3 py-2"
          />
        </div>
        {error && <p className="text-sm text-red-600">{error}</p>}
        <Button type="submit" variant="primary" className="w-full">
          登录
        </Button>
        <p className="text-sm text-gray-500">
          没有账号？<a href="/register" className="text-blue-600 hover:underline">去注册</a>
        </p>
      </form>
    </div>
  );
}
```

- [x] **Step 2: 提交**

```bash
git add apps/web/app/login/page.tsx
git commit -m "feat: add web buyer login page"
```

### Task 5.3: Admin 端注册页面

**Files:**
- Create: `apps/admin/app/register/page.tsx`

- [x] **Step 1: 创建注册页面**

`apps/admin/app/register/page.tsx`:
```typescript
"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { createApiClient, register } from "@ec/sdk";
import { Button } from "@ec/ui";

const client = createApiClient({
  baseUrl: process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000",
});

export default function AdminRegisterPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await register(client, "/admin", { email, password });
      router.push("/admin");
    } catch (err) {
      setError(err instanceof Error ? err.message : "注册失败");
    }
  }

  return (
    <div className="mx-auto mt-16 max-w-md">
      <h1 className="mb-6 text-2xl font-bold">注册管理员账号</h1>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="mb-1 block text-sm font-medium">邮箱</label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            className="w-full rounded border px-3 py-2"
          />
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium">密码</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            className="w-full rounded border px-3 py-2"
          />
        </div>
        {error && <p className="text-sm text-red-600">{error}</p>}
        <Button type="submit" variant="primary" className="w-full">
          注册
        </Button>
        <p className="text-sm text-gray-500">
          已有账号？<a href="/login" className="text-blue-600 hover:underline">去登录</a>
        </p>
      </form>
    </div>
  );
}
```

- [x] **Step 2: 提交**

```bash
git add apps/admin/app/register/page.tsx
git commit -m "feat: add admin registration page"
```

### Task 5.4: Admin 端登录页面

**Files:**
- Create: `apps/admin/app/login/page.tsx`

- [x] **Step 1: 创建登录页面**

`apps/admin/app/login/page.tsx`:
```typescript
"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { createApiClient, login } from "@ec/sdk";
import { Button } from "@ec/ui";

const client = createApiClient({
  baseUrl: process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000",
});

export default function AdminLoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await login(client, "/admin", { email, password });
      router.push("/admin");
    } catch (err) {
      setError(err instanceof Error ? err.message : "登录失败");
    }
  }

  return (
    <div className="mx-auto mt-16 max-w-md">
      <h1 className="mb-6 text-2xl font-bold">管理员登录</h1>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="mb-1 block text-sm font-medium">邮箱</label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            className="w-full rounded border px-3 py-2"
          />
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium">密码</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            className="w-full rounded border px-3 py-2"
          />
        </div>
        {error && <p className="text-sm text-red-600">{error}</p>}
        <Button type="submit" variant="primary" className="w-full">
          登录
        </Button>
        <p className="text-sm text-gray-500">
          没有账号？<a href="/register" className="text-blue-600 hover:underline">去注册</a>
        </p>
      </form>
    </div>
  );
}
```

- [x] **Step 2: 提交**

```bash
git add apps/admin/app/login/page.tsx
git commit -m "feat: add admin login page"
```

### Task 5.5: 前端编译验证

- [x] **Step 1: TypeScript 编译检查**

```bash
pnpm exec tsc --noEmit -p apps/web/tsconfig.json && pnpm exec tsc --noEmit -p apps/admin/tsconfig.json
```

Expected: No errors

- [x] **Step 2: 确认已提交前端代码**

```bash
git status
```

archived-with: 2026-07-15-add-email-auth
---

## 6. 验证

### Task 6.1: 全量后端测试

- [x] **Step 1: 运行全部测试**

```bash
cd backend && rm -f .data/ec-main.sqlite3 && uv run pytest tests/ -v
```

Expected: ALL PASS

### Task 6.2: 端到端验证

- [x] **Step 1: 启动后端并手动验证**

```bash
cd backend && uv run uvicorn app.main:app --port 8000 &
```

```bash
# 注册 buyer
curl -X POST http://localhost:8000/api/v1/web/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"e2e@test.com","password":"test123"}' -v

# 登录 buyer
curl -X POST http://localhost:8000/api/v1/web/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"e2e@test.com","password":"test123"}' -v

# me
curl http://localhost:8000/api/v1/web/auth/me -v

# logout
curl -X POST http://localhost:8000/api/v1/web/auth/logout -v

# 注册 admin
curl -X POST http://localhost:8000/api/v1/admin/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"admin-e2e@test.com","password":"admin123"}' -v
```
