from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models.order import Order

ORDER_STATUSES = [
    "pending_payment",
    "pending_delivery",
    "in_delivery",
    "delivered",
    "cancelled",
    "refunded",
]

VALID_TRANSITIONS: dict[str, set[str]] = {
    "pending_payment": {"pending_delivery", "cancelled"},
    "pending_delivery": {"in_delivery", "cancelled", "refunded"},
    "in_delivery": {"delivered"},
    "delivered": set(),
    "cancelled": set(),
    "refunded": set(),
}

STATUS_LABELS: dict[str, str] = {
    "pending_payment": "待付款",
    "pending_delivery": "待发货",
    "in_delivery": "配送中",
    "delivered": "已送达",
    "cancelled": "已取消",
    "refunded": "已退款",
}


def get_next_statuses(current: str) -> list[str]:
    """返回某状态所有合法的目标状态，按状态集合顺序排列。"""
    if current not in VALID_TRANSITIONS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="无效的订单状态")
    allowed = VALID_TRANSITIONS[current]
    return [s for s in ORDER_STATUSES if s in allowed]


def validate_transition(current: str, target: str) -> None:
    """校验 current → target 是否合法，非法流转抛出 400。"""
    if target not in ORDER_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的订单状态",
        )
    if target not in VALID_TRANSITIONS.get(current, set()):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"订单状态不允许从 {STATUS_LABELS.get(current, current)} 变更为 {STATUS_LABELS.get(target, target)}",
        )


def list_orders(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    status_filter: str | None = None,
    keyword: str | None = None,
) -> tuple[list[Order], int]:
    query = db.query(Order)
    if status_filter:
        query = query.filter(Order.status == status_filter)
    if keyword:
        query = query.filter(Order.order_no.like(f"%{keyword}%"))
    total = query.count()
    orders = query.order_by(Order.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return orders, total


def get_order(db: Session, order_no: str) -> Order:
    order = db.query(Order).filter(Order.order_no == order_no).first()
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="订单不存在")
    return order


def update_order_status(db: Session, order_no: str, target_status: str) -> Order:
    order = get_order(db, order_no)
    validate_transition(order.status, target_status)
    order.status = target_status
    db.commit()
    db.refresh(order)
    return order
