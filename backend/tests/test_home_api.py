import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models.user import Base
from app.db.session import engine

Base.metadata.create_all(bind=engine)

client = TestClient(app)


@pytest.fixture(autouse=True)
def _clean_db() -> None:
    with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete())


def _seed_module(db_session) -> None:
    from app.db.session import SessionLocal
    db = SessionLocal()
    from app.models.home_module import HomeModule
    from app.models.banner_item import BannerItem
    from app.models.announcement import Announcement
    from app.models.product import Product
    db.add(HomeModule(module_type="banner", title="B", data_source_url="/api/v1/web/home/banner", sort_order=1, is_enabled=True))
    db.add(HomeModule(module_type="product_recommend", title="P", data_source_url="/api/v1/web/products?status=active", sort_order=2, is_enabled=False))
    db.add(BannerItem(image_url="https://x/b1.jpg", link_url="/p1", sort_order=1, is_enabled=True))
    db.add(Announcement(content="公告1", is_enabled=True))
    db.add(Product(title="商品1", image_url="", price=9900, status="active", sort_order=1))
    db.commit()
    db.close()


def test_modules_returns_only_enabled() -> None:
    _seed_module(None)
    response = client.get("/api/v1/web/home/modules")
    assert response.status_code == 200
    modules = response.json()["modules"]
    assert len(modules) == 1
    assert modules[0]["module_type"] == "banner"


def test_banner_returns_items() -> None:
    _seed_module(None)
    response = client.get("/api/v1/web/home/banner")
    assert response.status_code == 200
    assert len(response.json()["items"]) == 1


def test_announcement_returns_items() -> None:
    _seed_module(None)
    response = client.get("/api/v1/web/home/announcement")
    assert response.status_code == 200
    assert response.json()["items"][0]["content"] == "公告1"


def test_products_public_filters_active() -> None:
    _seed_module(None)
    response = client.get("/api/v1/web/home/products?status=active")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["price"] == 9900


def test_modules_empty_when_no_data() -> None:
    response = client.get("/api/v1/web/home/modules")
    assert response.status_code == 200
    assert response.json()["modules"] == []