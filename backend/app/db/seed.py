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


SEED_PRODUCTS = [
    dict(title="示例商品 A", image_url="https://placehold.co/400x300?text=Product+A", price=9900, status="active", sort_order=1),
    dict(title="示例商品 B", image_url="https://placehold.co/400x300?text=Product+B", price=12900, status="active", sort_order=2),
    dict(title="示例商品 C", image_url="https://placehold.co/400x300?text=Product+C", price=19900, status="active", sort_order=3),
]

SEED_ANNOUNCEMENTS = [
    dict(content="欢迎来到 EC Main,新用户首单享优惠。", is_enabled=True),
    dict(content="平台维护公告:每周三凌晨 2:00-4:00 例行维护。", is_enabled=True),
]


def seed_cms(db: Session) -> None:
    from app.models.home_module import HomeModule
    from app.models.banner_item import BannerItem
    from app.models.announcement import Announcement
    from app.models.product import Product

    if db.query(HomeModule).count() > 0:
        logger.info("种子数据: home_modules 已有记录，跳过")
        return

    db.add(HomeModule(
        module_type="banner",
        title="轮播 Banner",
        data_source_url="/api/v1/web/home/banner",
        sort_order=1,
        is_enabled=True,
    ))
    db.add(HomeModule(
        module_type="product_recommend",
        title="推荐商品",
        data_source_url="/api/v1/web/products?status=active",
        sort_order=2,
        is_enabled=True,
    ))
    db.add(HomeModule(
        module_type="announcement",
        title="平台公告",
        data_source_url="/api/v1/web/home/announcement",
        sort_order=3,
        is_enabled=True,
    ))
    db.add(BannerItem(
        image_url="https://placehold.co/800x300?text=Banner+1",
        link_url="https://example.com/1",
        sort_order=1,
        is_enabled=True,
    ))
    db.add(BannerItem(
        image_url="https://placehold.co/800x300?text=Banner+2",
        link_url="https://example.com/2",
        sort_order=2,
        is_enabled=True,
    ))
    for data in SEED_ANNOUNCEMENTS:
        db.add(Announcement(**data))
    for data in SEED_PRODUCTS:
        db.add(Product(**data))
    db.commit()
    logger.info("种子数据: 已初始化首页模块")
