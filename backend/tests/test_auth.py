from fastapi.testclient import TestClient
from app.main import app
from app.models.user import Base
from app.db.session import engine

Base.metadata.create_all(bind=engine)

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
