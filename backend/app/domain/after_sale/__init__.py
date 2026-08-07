from sqlalchemy.orm import Session

from app.models.after_sale_case import AfterSaleCase


def create_case(
    db: Session,
    *,
    order_no: str,
    buyer_id: int,
    case_type: str,
    amount: str | None = None,
    reason: str | None = None,
) -> AfterSaleCase:
    case = AfterSaleCase(
        order_no=order_no,
        buyer_id=buyer_id,
        case_type=case_type,
        amount=amount,
        reason=reason,
        status="processed",
    )
    db.add(case)
    db.commit()
    db.refresh(case)
    return case


def list_cases_by_buyer(db: Session, buyer_id: int) -> list[AfterSaleCase]:
    return db.query(AfterSaleCase).filter(
        AfterSaleCase.buyer_id == buyer_id,
    ).order_by(
        AfterSaleCase.created_at.desc(),
    ).all()
