import logging
from sqlalchemy.orm import Session
from app.models.order import Order
from app.models.user import User
from app.core.security import hash_password

logger = logging.getLogger(__name__)

SEED_ORDERS_DATA = [
    dict(order_no="ORD-PENDING-001", buyer_id=1, amount="199.00", status="pending_delivery"),
    dict(order_no="ORD-IN-DELIVERY-001", buyer_id=1, amount="299.00", status="in_delivery"),
    dict(order_no="ORD-DELIVERED-001", buyer_id=1, amount="399.00", status="delivered"),
]

DEFAULT_ADMIN_EMAIL = "admin@admin.com"
DEFAULT_ADMIN_PASSWORD = "123456"


def seed_admin(db: Session) -> None:
    existing = db.query(User).filter(User.email == DEFAULT_ADMIN_EMAIL).first()
    if existing:
        logger.info("种子数据: admin 用户已存在，跳过")
        return
    db.add(User(
        email=DEFAULT_ADMIN_EMAIL,
        username="admin",
        password_hash=hash_password(DEFAULT_ADMIN_PASSWORD),
        role="admin",
    ))
    db.commit()
    logger.info("种子数据: 已创建默认管理员 %s", DEFAULT_ADMIN_EMAIL)


def seed_orders(db: Session) -> None:
    existing = db.query(Order).count()
    if existing > 0:
        logger.info("种子数据: orders 表已有 %d 条记录，跳过", existing)
        return
    for data in SEED_ORDERS_DATA:
        db.add(Order(**data))
    db.commit()
    logger.info("种子数据: 已插入 %d 条订单", len(SEED_ORDERS_DATA))
