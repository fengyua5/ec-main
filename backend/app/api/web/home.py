from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.deps import get_db
from app.domain.cms import home as home_service
from app.domain.cms import products as products_service
from app.domain.cms.schemas import (
    HomeModulesResponse,
    HomeModuleResponse,
    BannerListResponse,
    BannerItemResponse,
    AnnouncementListResponse,
    AnnouncementResponse,
    ProductPublicListResponse,
    ProductPublicResponse,
)

router = APIRouter(prefix="/home")


@router.get("/modules", response_model=HomeModulesResponse)
def get_home_modules(db: Session = Depends(get_db)) -> HomeModulesResponse:
    modules = home_service.list_enabled_modules(db)
    return HomeModulesResponse(modules=[HomeModuleResponse.model_validate(m) for m in modules])


@router.get("/banner", response_model=BannerListResponse)
def get_home_banner(db: Session = Depends(get_db)) -> BannerListResponse:
    items = home_service.list_enabled_banners(db)
    return BannerListResponse(items=[BannerItemResponse.model_validate(b) for b in items])


@router.get("/announcement", response_model=AnnouncementListResponse)
def get_home_announcement(db: Session = Depends(get_db)) -> AnnouncementListResponse:
    items = home_service.list_enabled_announcements(db)
    return AnnouncementListResponse(items=[AnnouncementResponse.model_validate(a) for a in items])


@router.get("/products", response_model=ProductPublicListResponse)
def list_products_public(
    status: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> ProductPublicListResponse:
    items, total = products_service.list_products(db, page=page, page_size=page_size, status_filter=status)
    return ProductPublicListResponse(items=[ProductPublicResponse.model_validate(p) for p in items], total=total)