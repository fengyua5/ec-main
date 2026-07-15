import logging
from sqlalchemy.orm import Session
from app.models.order import Order

logger = logging.getLogger(__name__)

SEED_ORDERS_DATA = [
    dict(order_no="ORD-PENDING-001", buyer_id=1, amount="199.00", status="pending_delivery"),
    dict(order_no="ORD-IN-DELIVERY-001", buyer_id=1, amount="299.00", status="in_delivery"),
    dict(order_no="ORD-DELIVERED-001", buyer_id=1, amount="399.00", status="delivered"),
]


def seed_orders(db: Session) -> None:
    existing = db.query(Order).count()
    if existing > 0:
        logger.info("种子数据: orders 表已有 %d 条记录，跳过", existing)
        return
    for data in SEED_ORDERS_DATA:
        db.add(Order(**data))
    db.commit()
    logger.info("种子数据: 已插入 %d 条订单", len(SEED_ORDERS_DATA))
