from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.db.deps import get_db
from app.domain.auth.deps import get_current_user
from app.domain.cms import modules as modules_service
from app.domain.cms import products as products_service
from app.domain.cms.schemas import (
    AdminAnnouncementListResponse,
    AdminAnnouncementResponse,
    AdminBannerItemResponse,
    AdminBannerListResponse,
    AnnouncementInput,
    BannerItemInput,
    ModuleInput,
    ModuleResponse,
    MoveModuleRequest,
    ProductInput,
    ProductListResponse,
    ProductResponse,
)
from app.models.user import User
from app.models.banner_item import BannerItem
from app.models.announcement import Announcement

router = APIRouter(prefix="/cms")


def _modules_for_move(db: Session):
    return modules_service.list_modules(db)


# ---- 模块 ----

@router.get("/modules", response_model=list[ModuleResponse])
def list_modules(
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> list[ModuleResponse]:
    modules = modules_service.list_modules(db)
    return [ModuleResponse.model_validate(m) for m in modules]


@router.post("/modules", response_model=ModuleResponse, status_code=201)
def create_module(
    payload: ModuleInput,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> ModuleResponse:
    module = modules_service.create_module(
        db,
        module_type=payload.module_type,
        title=payload.title,
        description=payload.description,
        data_source_url=payload.data_source_url,
        is_static=payload.is_static,
        sort_order=payload.sort_order,
        is_enabled=payload.is_enabled,
    )
    return ModuleResponse.model_validate(module)


@router.patch("/modules/{module_id}", response_model=ModuleResponse)
def update_module(
    module_id: int,
    payload: ModuleInput,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> ModuleResponse:
    module = modules_service.update_module(
        db,
        module_id,
        module_type=payload.module_type,
        title=payload.title,
        description=payload.description,
        data_source_url=payload.data_source_url,
        is_static=payload.is_static,
        sort_order=payload.sort_order,
        is_enabled=payload.is_enabled,
    )
    return ModuleResponse.model_validate(module)


@router.delete("/modules/{module_id}", status_code=204)
def delete_module(
    module_id: int,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> None:
    module = modules_service.get_module(db, module_id)
    db.delete(module)
    db.commit()


@router.post("/modules/{module_id}/move", response_model=list[ModuleResponse])
def move_module(
    module_id: int,
    payload: MoveModuleRequest,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> list[ModuleResponse]:
    ordered = _modules_for_move(db)
    modules_service.move_module(db, module_id, payload.direction, modules=ordered)
    return [ModuleResponse.model_validate(m) for m in ordered]


# ---- 商品 ----

@router.get("/products", response_model=ProductListResponse)
def list_products(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str | None = Query(None),
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> ProductListResponse:
    items, total = products_service.list_products(
        db,
        page=page,
        page_size=page_size,
        status_filter=status,
    )
    return ProductListResponse(
        items=[ProductResponse.model_validate(p) for p in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/products", response_model=ProductResponse, status_code=201)
def create_product(
    payload: ProductInput,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> ProductResponse:
    product = products_service.create_product(
        db,
        title=payload.title,
        image_url=payload.image_url,
        price=payload.price,
        status=payload.status,
        sort_order=payload.sort_order,
    )
    return ProductResponse.model_validate(product)


@router.patch("/products/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int,
    payload: ProductInput,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> ProductResponse:
    product = products_service.update_product(
        db,
        product_id,
        title=payload.title,
        image_url=payload.image_url,
        price=payload.price,
        status=payload.status,
        sort_order=payload.sort_order,
    )
    return ProductResponse.model_validate(product)


@router.delete("/products/{product_id}", status_code=204)
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> None:
    product = products_service.get_product(db, product_id)
    db.delete(product)
    db.commit()


# ---- banner ----

@router.get("/banners", response_model=AdminBannerListResponse)
def list_banners(
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> AdminBannerListResponse:
    items = db.query(BannerItem).order_by(BannerItem.sort_order.asc()).all()
    return AdminBannerListResponse(items=[AdminBannerItemResponse.model_validate(b) for b in items])


@router.post("/banners", response_model=AdminBannerItemResponse, status_code=201)
def create_banner(
    payload: BannerItemInput,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> AdminBannerItemResponse:
    item = BannerItem(
        image_url=payload.image_url,
        description=payload.description,
        link_url=payload.link_url,
        sort_order=payload.sort_order,
        is_enabled=payload.is_enabled,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return AdminBannerItemResponse.model_validate(item)


@router.patch("/banners/{banner_id}", response_model=AdminBannerItemResponse)
def update_banner(
    banner_id: int,
    payload: BannerItemInput,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> AdminBannerItemResponse:
    item = db.query(BannerItem).filter(BannerItem.id == banner_id).first()
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Banner不存在")
    item.image_url = payload.image_url
    item.description = payload.description
    item.link_url = payload.link_url
    item.sort_order = payload.sort_order
    item.is_enabled = payload.is_enabled
    db.commit()
    db.refresh(item)
    return AdminBannerItemResponse.model_validate(item)


@router.delete("/banners/{banner_id}", status_code=204)
def delete_banner(
    banner_id: int,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> None:
    item = db.query(BannerItem).filter(BannerItem.id == banner_id).first()
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Banner不存在")
    db.delete(item)
    db.commit()


# ---- 公告 ----

@router.get("/announcements", response_model=AdminAnnouncementListResponse)
def list_announcements(
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> AdminAnnouncementListResponse:
    items = db.query(Announcement).order_by(Announcement.created_at.desc()).all()
    return AdminAnnouncementListResponse(
        items=[AdminAnnouncementResponse.model_validate(a) for a in items],
    )


@router.post("/announcements", response_model=AdminAnnouncementResponse, status_code=201)
def create_announcement(
    payload: AnnouncementInput,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> AdminAnnouncementResponse:
    item = Announcement(content=payload.content, is_enabled=payload.is_enabled)
    db.add(item)
    db.commit()
    db.refresh(item)
    return AdminAnnouncementResponse.model_validate(item)


@router.patch("/announcements/{announcement_id}", response_model=AdminAnnouncementResponse)
def update_announcement(
    announcement_id: int,
    payload: AnnouncementInput,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> AdminAnnouncementResponse:
    item = db.query(Announcement).filter(Announcement.id == announcement_id).first()
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="公告不存在")
    item.content = payload.content
    item.is_enabled = payload.is_enabled
    db.commit()
    db.refresh(item)
    return AdminAnnouncementResponse.model_validate(item)


@router.delete("/announcements/{announcement_id}", status_code=204)
def delete_announcement(
    announcement_id: int,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> None:
    item = db.query(Announcement).filter(Announcement.id == announcement_id).first()
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="公告不存在")
    db.delete(item)
    db.commit()
