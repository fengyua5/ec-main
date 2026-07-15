import pytest
from app.models.user import Base
from app.models.order import Order
from app.db.session import engine, SessionLocal
from app.db.seed import seed_orders, SEED_ORDERS_DATA

Base.metadata.create_all(bind=engine)


@pytest.fixture(autouse=True)
def _clean_db() -> None:
    with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete())


def test_seed_creates_orders() -> None:
    db = SessionLocal()
    seed_orders(db)
    db.close()

    db = SessionLocal()
    orders = db.query(Order).all()
    db.close()

    assert len(orders) == 3


def test_seed_skips_if_exists() -> None:
    db = SessionLocal()
    seed_orders(db)
    seed_orders(db)
    db.close()

    db = SessionLocal()
    count = db.query(Order).count()
    db.close()

    assert count == 3


def test_create_order() -> None:
    db = SessionLocal()
    order = Order(
        order_no="ORD-TEST-001",
        buyer_id=2,
        amount="99.50",
        status="pending_delivery",
    )
    db.add(order)
    db.commit()
    db.close()

    db = SessionLocal()
    saved = db.query(Order).filter(Order.order_no == "ORD-TEST-001").first()
    db.close()

    assert saved is not None
    assert saved.buyer_id == 2
    assert saved.amount == "99.50"
    assert saved.status == "pending_delivery"
    assert saved.created_at is not None


def test_default_status() -> None:
    db = SessionLocal()
    order = Order(
        order_no="ORD-DEFAULT-001",
        buyer_id=1,
        amount="10.00",
    )
    db.add(order)
    db.commit()
    db.close()

    db = SessionLocal()
    saved = db.query(Order).filter(Order.order_no == "ORD-DEFAULT-001").first()
    db.close()

    assert saved is not None
    assert saved.status == "pending_delivery"
