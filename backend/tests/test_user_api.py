import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models.user import Base, User
from app.db.session import engine, SessionLocal

Base.metadata.create_all(bind=engine)

client = TestClient(app)


@pytest.fixture(autouse=True)
def _clean_db() -> None:
    with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete())


def _create_user(email: str, role: str = "buyer", password: str = "password123", is_active: bool = True) -> int:
    from app.core.security import hash_password
    db = SessionLocal()
    user = User(email=email, password_hash=hash_password(password), role=role, is_active=is_active)
    db.add(user)
    db.commit()
    db.refresh(user)
    db.close()
    return user.id


def _login_admin() -> None:
    _create_user("admin@admin.com", role="admin", password="admin123")
    response = client.post("/api/v1/admin/auth/login", json={
        "email": "admin@admin.com", "password": "admin123",
    })
    assert response.status_code == 200


def test_list_users_requires_auth() -> None:
    response = client.get("/api/v1/admin/users")
    assert response.status_code == 401


def test_list_users_returns_all() -> None:
    _login_admin()
    _create_user("buyer1@example.com")
    _create_user("buyer2@example.com")

    response = client.get("/api/v1/admin/users")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    roles = {u["email"]: u["role"] for u in data["items"]}
    assert roles["admin@admin.com"] == "admin"
    assert roles["buyer1@example.com"] == "buyer"


def test_list_users_keyword() -> None:
    _login_admin()
    _create_user("alice@example.com")
    _create_user("bob@example.com")

    response = client.get("/api/v1/admin/users", params={"keyword": "alice"})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["email"] == "alice@example.com"


def test_user_detail_success() -> None:
    _login_admin()
    user_id = _create_user("detail@example.com")

    response = client.get(f"/api/v1/admin/users/{user_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "detail@example.com"
    assert data["is_active"] is True


def test_user_detail_not_found() -> None:
    _login_admin()
    response = client.get("/api/v1/admin/users/999")
    assert response.status_code == 404


def test_disable_user() -> None:
    _login_admin()
    user_id = _create_user("disable@example.com")

    response = client.patch(f"/api/v1/admin/users/{user_id}/active", json={"is_active": False})
    assert response.status_code == 200
    assert response.json()["user"]["is_active"] is False


def test_enable_user() -> None:
    _login_admin()
    user_id = _create_user("enable@example.com", is_active=False)

    response = client.patch(f"/api/v1/admin/users/{user_id}/active", json={"is_active": True})
    assert response.status_code == 200
    assert response.json()["user"]["is_active"] is True


def test_cannot_disable_self() -> None:
    _login_admin()
    admin = client.get("/api/v1/admin/auth/me").json()

    response = client.patch(f"/api/v1/admin/users/{admin['id']}/active", json={"is_active": False})
    assert response.status_code == 400


def test_disabled_user_cannot_login() -> None:
    _create_user("blocked@example.com", is_active=False)

    response = client.post("/api/v1/web/auth/login", json={
        "email": "blocked@example.com", "password": "password123",
    })
    assert response.status_code == 403
    assert response.json()["detail"] == "账号已被禁用"
