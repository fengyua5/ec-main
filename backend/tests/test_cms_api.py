import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models.user import Base, User
from app.core.security import hash_password, create_access_token
from app.db.session import SessionLocal, engine

Base.metadata.create_all(bind=engine)

client = TestClient(app)

ADMIN_EMAIL = "cmstest@admin.com"


@pytest.fixture(autouse=True)
def _clean_db() -> None:
    with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete())


def _admin_headers() -> dict:
    db = SessionLocal()
    admin = db.query(User).filter(User.email == ADMIN_EMAIL).first()
    if admin is None:
        admin = User(email=ADMIN_EMAIL, username="cmstest", password_hash=hash_password("123456"), role="admin")
        db.add(admin)
        db.commit()
    token = create_access_token({"sub": str(admin.id)})
    db.close()
    return {"Cookie": f"token={token}"}


def test_modules_requires_auth() -> None:
    response = client.get("/api/v1/admin/cms/modules")
    assert response.status_code == 401


def test_create_and_update_module_description() -> None:
    headers = _admin_headers()
    response = client.post(
        "/api/v1/admin/cms/modules",
        json={"module_type": "banner", "title": "B1", "description": "原始描述", "data_source_url": "/api/v1/web/home/banner", "sort_order": 1, "is_enabled": True},
        headers=headers,
    )
    assert response.status_code == 201
    module_id = response.json()["id"]
    assert response.json()["description"] == "原始描述"

    updated = client.patch(
        f"/api/v1/admin/cms/modules/{module_id}",
        json={"module_type": "banner", "title": "B1", "description": "修改后的描述", "data_source_url": "/api/v1/web/home/banner", "sort_order": 1, "is_enabled": True},
        headers=headers,
    )
    assert updated.status_code == 200
    assert updated.json()["description"] == "修改后的描述"

    listed = client.get("/api/v1/admin/cms/modules", headers=headers)
    assert listed.status_code == 200
    by_id = {m["id"]: m["description"] for m in listed.json()}
    assert by_id[module_id] == "修改后的描述"


def test_create_and_move_module() -> None:
    headers = _admin_headers()
    response = client.post(
        "/api/v1/admin/cms/modules",
        json={"module_type": "banner", "title": "B1", "data_source_url": "/api/v1/web/home/banner", "sort_order": 1, "is_enabled": True},
        headers=headers,
    )
    assert response.status_code == 201
    module_id = response.json()["id"]

    # 再插入一个模块，使 move down 有相邻节点可交换，避免命中"已在边界"的 400
    client.post(
        "/api/v1/admin/cms/modules",
        json={"module_type": "product_recommend", "title": "P1", "data_source_url": "/api/v1/web/products?status=active", "sort_order": 2, "is_enabled": True},
        headers=headers,
    )

    moved = client.post(
        f"/api/v1/admin/cms/modules/{module_id}/move",
        json={"direction": "down"},
        headers=headers,
    )
    assert moved.status_code == 200
    by_id = {m["id"]: m["sort_order"] for m in moved.json()}
    assert by_id[module_id] == 2


def test_create_product() -> None:
    headers = _admin_headers()
    response = client.post(
        "/api/v1/admin/cms/products",
        json={"title": "新商品", "image_url": "", "price": 9800, "status": "active", "sort_order": 1},
        headers=headers,
    )
    assert response.status_code == 201
    assert response.json()["price"] == 9800


def test_create_banner() -> None:
    headers = _admin_headers()
    response = client.post(
        "/api/v1/admin/cms/banners",
        json={"image_url": "https://x/b.jpg", "link_url": "/p", "sort_order": 1, "is_enabled": True},
        headers=headers,
    )
    assert response.status_code == 201


def test_create_announcement() -> None:
    headers = _admin_headers()
    response = client.post(
        "/api/v1/admin/cms/announcements",
        json={"content": "测试公告", "is_enabled": True},
        headers=headers,
    )
    assert response.status_code == 201
