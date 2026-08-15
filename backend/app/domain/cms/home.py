from sqlalchemy.orm import Session
from app.models.home_module import HomeModule
from app.models.banner_item import BannerItem
from app.models.announcement import Announcement


def list_enabled_modules(db: Session) -> list[HomeModule]:
    return (
        db.query(HomeModule)
        .filter(HomeModule.is_enabled.is_(True))
        .order_by(HomeModule.sort_order.asc())
        .all()
    )


def list_enabled_banners(db: Session) -> list[BannerItem]:
    return (
        db.query(BannerItem)
        .filter(BannerItem.is_enabled.is_(True))
        .order_by(BannerItem.sort_order.asc())
        .all()
    )


def list_enabled_announcements(db: Session) -> list[Announcement]:
    return (
        db.query(Announcement)
        .filter(Announcement.is_enabled.is_(True))
        .order_by(Announcement.created_at.desc())
        .all()
    )