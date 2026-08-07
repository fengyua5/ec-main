import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models.user import Base
from app.models.order import Order
from app.db.session import engine, SessionLocal
from app.db.seed import seed_orders, SEED_ORDERS_DATA

Base.metadata.create_all(bind=engine)

client = TestClient(app)


@pytest.fixture(autouse=True)
def _clean_db() -> None:
    with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete())


def _insert_order(order_no: str, status: str, amount: str = "99.00", buyer_id: int = 1) -> None:
    db = SessionLocal()
    db.add(Order(order_no=order_no, buyer_id=buyer_id, amount=amount, status=status))
    db.commit()
    db.close()


def test_list_orders_empty() -> None:
    response = client.get("/api/v1/admin/orders")
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0


def test_list_orders_returns_seed() -> None:
    db = SessionLocal()
    seed_orders(db)
    db.close()

    response = client.get("/api/v1/admin/orders")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == len(SEED_ORDERS_DATA)
    assert len(data["items"]) == len(SEED_ORDERS_DATA)


def test_list_orders_status_filter() -> None:
    _insert_order("ORD-FILTER-001", status="pending_payment")
    _insert_order("ORD-FILTER-002", status="pending_delivery")
    _insert_order("ORD-FILTER-003", status="in_delivery")

    response = client.get("/api/v1/admin/orders", params={"status": "in_delivery"})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["order_no"] == "ORD-FILTER-003"


def test_list_orders_keyword_search() -> None:
    _insert_order("ORD-SEARCH-001", status="pending_delivery")
    _insert_order("ORD-SEARCH-002", status="pending_delivery")
    _insert_order("ORD-OTHER-001", status="pending_delivery")

    response = client.get("/api/v1/admin/orders", params={"keyword": "SEARCH"})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2


def test_list_orders_pagination() -> None:
    for i in range(5):
        _insert_order(f"ORD-PAGE-{i:03d}", status="pending_delivery")

    response = client.get("/api/v1/admin/orders", params={"page": 2, "page_size": 2})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 5
    assert len(data["items"]) == 2
    assert data["page"] == 2
    assert data["page_size"] == 2


def test_list_orders_invalid_page_size() -> None:
    response = client.get("/api/v1/admin/orders", params={"page_size": 101})
    assert response.status_code == 422


def test_order_detail_success() -> None:
    _insert_order("ORD-DETAIL-001", status="pending_payment", amount="199.00", buyer_id=7)

    response = client.get("/api/v1/admin/orders/ORD-DETAIL-001")
    assert response.status_code == 200
    data = response.json()
    assert data["order_no"] == "ORD-DETAIL-001"
    assert data["status"] == "pending_payment"
    assert data["amount"] == "199.00"
    assert data["buyer_id"] == 7


def test_order_detail_not_found() -> None:
    response = client.get("/api/v1/admin/orders/ORD-NOT-EXIST")
    assert response.status_code == 404


def test_update_status_success() -> None:
    _insert_order("ORD-UPDATE-001", status="pending_payment")

    response = client.patch(
        "/api/v1/admin/orders/ORD-UPDATE-001/status",
        json={"status": "pending_delivery"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["order"]["status"] == "pending_delivery"


def test_update_status_illegal_transition() -> None:
    _insert_order("ORD-UPDATE-002", status="pending_payment")

    response = client.patch(
        "/api/v1/admin/orders/ORD-UPDATE-002/status",
        json={"status": "in_delivery"},
    )
    assert response.status_code == 400


def test_update_status_terminal_state() -> None:
    _insert_order("ORD-UPDATE-003", status="delivered")

    response = client.patch(
        "/api/v1/admin/orders/ORD-UPDATE-003/status",
        json={"status": "pending_delivery"},
    )
    assert response.status_code == 400


def test_update_status_unknown_target() -> None:
    _insert_order("ORD-UPDATE-004", status="pending_payment")

    response = client.patch(
        "/api/v1/admin/orders/ORD-UPDATE-004/status",
        json={"status": "not_a_status"},
    )
    assert response.status_code == 400


def test_update_status_not_found() -> None:
    response = client.patch(
        "/api/v1/admin/orders/ORD-UPDATE-404/status",
        json={"status": "pending_delivery"},
    )
    assert response.status_code == 404
