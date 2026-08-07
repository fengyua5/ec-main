import pytest
from app.models.after_sale_case import AfterSaleCase
from app.domain.after_sale import create_case, list_cases_by_buyer
from app.models.user import Base
from app.db.session import engine, SessionLocal

Base.metadata.create_all(bind=engine)


@pytest.fixture(autouse=True)
def _clean_db() -> None:
    with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete())


def test_create_case_persists() -> None:
    db = SessionLocal()
    try:
        case = create_case(
            db,
            order_no="ORD-CASE-001",
            buyer_id=7,
            case_type="refund",
            amount="199.00",
            reason="质量问题",
        )
        assert case.id is not None
        assert case.order_no == "ORD-CASE-001"
        assert case.buyer_id == 7
        assert case.case_type == "refund"
        assert case.amount == "199.00"
        assert case.reason == "质量问题"
        assert case.status == "processed"
        assert case.created_at is not None
    finally:
        db.close()


def test_create_case_minimal() -> None:
    db = SessionLocal()
    try:
        case = create_case(db, order_no="ORD-CASE-002", buyer_id=3, case_type="cancel")
        assert case.case_type == "cancel"
        assert case.amount is None
        assert case.reason is None
    finally:
        db.close()


def test_list_cases_by_buyer() -> None:
    db = SessionLocal()
    try:
        create_case(db, order_no="ORD-CASE-003", buyer_id=5, case_type="refund")
        create_case(db, order_no="ORD-CASE-004", buyer_id=5, case_type="cancel")
        create_case(db, order_no="ORD-CASE-005", buyer_id=9, case_type="refund")
        cases = list_cases_by_buyer(db, 5)
        assert len(cases) == 2
        assert {c.order_no for c in cases} == {"ORD-CASE-003", "ORD-CASE-004"}
    finally:
        db.close()
