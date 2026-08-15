# 自建 CMS 首页改造实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 web 首页改造为 CMS 配置驱动:后端新增商品/首页模块/banner/公告 4 张表与读写接口,admin 提供配置管理页,web 首页按配置渲染。

**Architecture:** 后端 FastAPI 分层(路由薄 + domain/cms + Pydantic schema + 幂等种子);SDK 提供类型化客户端函数;web 首页为 async Server Component 并行拉取;admin 沿用 loadXxx 模式管理界面。数据源 URL 由 admin 在模块上配置,指向内部接口。

**Tech Stack:** FastAPI · SQLAlchemy · pydantic · Next.js · @ec/sdk · Vitest/Testing Library · pytest

**设计文档:** `docs/superpowers/specs/2026-08-15-homepage-cms-design.md`

---

### Task 1: 后端数据模型(4 张表)

**Files:**
- Create: `backend/app/models/product.py`
- Create: `backend/app/models/home_module.py`
- Create: `backend/app/models/banner_item.py`
- Create: `backend/app/models/announcement.py`
- Modify: `backend/app/models/__init__.py`

- [ ] **Step 1: 创建 `product.py`**

```python
from datetime import datetime
from sqlalchemy import String, Integer, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from app.models.user import Base


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    image_url: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    price: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="active")
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
```

- [ ] **Step 2: 创建 `home_module.py`**

```python
from datetime import datetime
from sqlalchemy import String, Integer, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from app.models.user import Base


class HomeModule(Base):
    __tablename__ = "home_modules"

    id: Mapped[int] = mapped_column(primary_key=True)
    module_type: Mapped[str] = mapped_column(String(30), nullable=False)
    title: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    data_source_url: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    is_enabled: Mapped[bool] = mapped_column(Integer, nullable=False, server_default="1")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
```

- [ ] **Step 3: 创建 `banner_item.py`**

```python
from datetime import datetime
from sqlalchemy import String, Integer, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from app.models.user import Base


class BannerItem(Base):
    __tablename__ = "banner_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    image_url: Mapped[str] = mapped_column(String(500), nullable=False)
    link_url: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    is_enabled: Mapped[bool] = mapped_column(Integer, nullable=False, server_default="1")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
```

- [ ] **Step 4: 创建 `announcement.py`**

```python
from datetime import datetime
from sqlalchemy import String, Integer, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from app.models.user import Base


class Announcement(Base):
    __tablename__ = "announcements"

    id: Mapped[int] = mapped_column(primary_key=True)
    content: Mapped[str] = mapped_column(String(500), nullable=False)
    is_enabled: Mapped[bool] = mapped_column(Integer, nullable=False, server_default="1")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
```

- [ ] **Step 5: 更新 `models/__init__.py`**(在 import 区加入 4 个模型)

```python
from app.models.user import User
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.faq_document import FAQDocument
from app.models.order import Order
from app.models.after_sale_case import AfterSaleCase
from app.models.buyer_memory import BuyerMemory
from app.models.product import Product
from app.models.home_module import HomeModule
from app.models.banner_item import BannerItem
from app.models.announcement import Announcement

__all__ = ["User", "Conversation", "Message", "FAQDocument", "Order", "AfterSaleCase", "BuyerMemory", "Product", "HomeModule", "BannerItem", "Announcement"]
```

- [ ] **Step 6: 验证 import 与建表**

Run: `cd backend && uv run python -c "from app.main import app; from app.models import Product, HomeModule, BannerItem, Announcement; print('models ok')"`
Expected: `models ok`(models 通过 __all__ 可导入)

- [ ] **Step 7: 提交**

```bash
git add backend/app/models/
git commit -m "feat(models): 新增商品/首页模块/banner/公告模型"
```

---

### Task 2: 后端 domain 层(cms 领域 + schemas + 种子)

**Files:**
- Create: `backend/app/domain/cms/__init__.py`
- Create: `backend/app/domain/cms/home.py`
- Create: `backend/app/domain/cms/modules.py`
- Create: `backend/app/domain/cms/products.py`
- Create: `backend/app/domain/cms/schemas.py`
- Modify: `backend/app/db/seed.py`

- [ ] **Step 1: 创建 `schemas.py`**

```python
from datetime import datetime
from pydantic import BaseModel


class HomeModuleResponse(BaseModel):
    id: int
    module_type: str
    title: str
    data_source_url: str
    sort_order: int

    model_config = {"from_attributes": True}


class HomeModulesResponse(BaseModel):
    modules: list[HomeModuleResponse]


class BannerItemResponse(BaseModel):
    id: int
    image_url: str
    link_url: str

    model_config = {"from_attributes": True}


class BannerListResponse(BaseModel):
    items: list[BannerItemResponse]


class AnnouncementResponse(BaseModel):
    id: int
    content: str

    model_config = {"from_attributes": True}


class AnnouncementListResponse(BaseModel):
    items: list[AnnouncementResponse]


class ProductPublicResponse(BaseModel):
    id: int
    title: str
    image_url: str
    price: int

    model_config = {"from_attributes": True}


class ProductPublicListResponse(BaseModel):
    items: list[ProductPublicResponse]
    total: int


# ---- 管理端(admin CMS)----

class ModuleInput(BaseModel):
    module_type: str
    title: str = ""
    data_source_url: str = ""
    sort_order: int = 0
    is_enabled: bool = True


class ModuleResponse(BaseModel):
    id: int
    module_type: str
    title: str
    data_source_url: str
    sort_order: int
    is_enabled: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MoveModuleRequest(BaseModel):
    direction: str


class ProductInput(BaseModel):
    title: str
    image_url: str = ""
    price: int = 0
    status: str = "active"
    sort_order: int = 0


class ProductResponse(BaseModel):
    id: int
    title: str
    image_url: str
    price: int
    status: str
    sort_order: int
    created_at: datetime

    model_config = {"from_attributes": True}


class ProductListResponse(BaseModel):
    items: list[ProductResponse]
    total: int
    page: int
    page_size: int


class BannerItemInput(BaseModel):
    image_url: str
    link_url: str = ""
    sort_order: int = 0
    is_enabled: bool = True


class AdminBannerItemResponse(BaseModel):
    id: int
    image_url: str
    link_url: str
    sort_order: int
    is_enabled: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class AdminBannerListResponse(BaseModel):
    items: list[AdminBannerItemResponse]


class AnnouncementInput(BaseModel):
    content: str
    is_enabled: bool = True


class AdminAnnouncementResponse(BaseModel):
    id: int
    content: str
    is_enabled: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class AdminAnnouncementListResponse(BaseModel):
    items: list[AdminAnnouncementResponse]
```

- [ ] **Step 2: 创建 `home.py`(web 公开读取)**

```python
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
```

- [ ] **Step 3: 创建 `products.py`(商品读写 + 状态/排序)**

```python
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models.product import Product


def list_products(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    status_filter: str | None = None,
) -> tuple[list[Product], int]:
    query = db.query(Product)
    if status_filter:
        query = query.filter(Product.status == status_filter)
    total = query.count()
    items = (
        query.order_by(Product.sort_order.asc(), Product.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return items, total


def get_product(db: Session, product_id: int) -> Product:
    product = db.query(Product).filter(Product.id == product_id).first()
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="商品不存在")
    return product


def create_product(
    db: Session,
    title: str,
    image_url: str,
    price: int,
    status: str = "active",
    sort_order: int = 0,
) -> Product:
    product = Product(title=title, image_url=image_url, price=price, status=status, sort_order=sort_order)
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


def update_product(db: Session, product_id: int, title: str, image_url: str, price: int, status: str, sort_order: int) -> Product:
    product = get_product(db, product_id)
    product.title = title
    product.image_url = image_url
    product.price = price
    product.status = status
    product.sort_order = sort_order
    db.commit()
    db.refresh(product)
    return product
```

- [ ] **Step 4: 创建 `modules.py`(模块 CRUD + 排序)**

```python
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models.home_module import HomeModule

MODULE_TYPES = ["banner", "product_recommend", "announcement"]


def list_modules(db: Session) -> list[HomeModule]:
    return db.query(HomeModule).order_by(HomeModule.sort_order.asc()).all()


def get_module(db: Session, module_id: int) -> HomeModule:
    module = db.query(HomeModule).filter(HomeModule.id == module_id).first()
    if module is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="模块不存在")
    return module


def validate_module_type(module_type: str) -> None:
    if module_type not in MODULE_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"无效的模块类型: {module_type}")


def create_module(
    db: Session,
    module_type: str,
    title: str,
    data_source_url: str,
    sort_order: int,
    is_enabled: bool,
) -> HomeModule:
    validate_module_type(module_type)
    module = HomeModule(
        module_type=module_type,
        title=title,
        data_source_url=data_source_url,
        sort_order=sort_order,
        is_enabled=is_enabled,
    )
    db.add(module)
    db.commit()
    db.refresh(module)
    return module


def update_module(
    db: Session,
    module_id: int,
    module_type: str,
    title: str,
    data_source_url: str,
    sort_order: int,
    is_enabled: bool,
) -> HomeModule:
    validate_module_type(module_type)
    module = get_module(db, module_id)
    module.module_type = module_type
    module.title = title
    module.data_source_url = data_source_url
    module.sort_order = sort_order
    module.is_enabled = is_enabled
    db.commit()
    db.refresh(module)
    return module


def move_module(db: Session, module_id: int, direction: str, modules: list[HomeModule] | None = None) -> HomeModule:
    if direction not in ("up", "down"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="排序方向仅支持 up/down")
    ordered = modules if modules is not None else list_modules(db)
    index = next((i for i, m in enumerate(ordered) if m.id == module_id), None)
    if index is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="模块不存在")
    target = index - 1 if direction == "up" else index + 1
    if target < 0 or target >= len(ordered):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="已在边界,无法移动")
    current = ordered[index]
    neighbor = ordered[target]
    current.sort_order, neighbor.sort_order = neighbor.sort_order, current.sort_order
    db.commit()
    db.refresh(current)
    return current
```

- [ ] **Step 5: 更新 `seed.py` 增加 `seed_cms`**

在 `seed_orders` 函数之后追加:

```python
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

    db.add(HomeModule(module_type="banner", title="轮播 Banner", data_source_url="/api/v1/web/home/banner", sort_order=1, is_enabled=True))
    db.add(HomeModule(module_type="product_recommend", title="推荐商品", data_source_url="/api/v1/web/products?status=active", sort_order=2, is_enabled=True))
    db.add(HomeModule(module_type="announcement", title="平台公告", data_source_url="/api/v1/web/home/announcement", sort_order=3, is_enabled=True))
    db.add(BannerItem(image_url="https://placehold.co/800x300?text=Banner+1", link_url="https://example.com/1", sort_order=1, is_enabled=True))
    db.add(BannerItem(image_url="https://placehold.co/800x300?text=Banner+2", link_url="https://example.com/2", sort_order=2, is_enabled=True))
    for data in SEED_ANNOUNCEMENTS:
        db.add(Announcement(**data))
    for data in SEED_PRODUCTS:
        db.add(Product(**data))
    db.commit()
    logger.info("种子数据: 已初始化首页模块")
```

- [ ] **Step 6: main.py lifespan 调用 `seed_cms`**

将 `backend/app/main.py` 中:

```python
        seed_admin(db)
        seed_orders(db)
```

改为:

```python
        seed_admin(db)
        seed_orders(db)
        seed_cms(db)
```

并把 import 行改为:

```python
from app.db.seed import seed_orders, seed_admin, seed_cms
```

- [ ] **Step 7: 提交**

```bash
git add backend/app/domain/cms/ backend/app/db/seed.py backend/app/main.py
git commit -m "feat(domain): CMS 领域层 + 首页模块种子数据"
```

---

### Task 3: 后端 API 路由(web 公开 + admin CRUD)

**Files:**
- Create: `backend/app/api/web/home.py`
- Create: `backend/app/api/admin/cms.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1: 创建 `api/web/home.py`**

```python
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
```

- [ ] **Step 2: 创建 `api/admin/cms.py`**

```python
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
        data_source_url=payload.data_source_url,
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
        data_source_url=payload.data_source_url,
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
    items, total = products_service.list_products(db, page=page, page_size=page_size, status_filter=status)
    return ProductListResponse(items=[ProductResponse.model_validate(p) for p in items], total=total, page=page, page_size=page_size)


@router.post("/products", response_model=ProductResponse, status_code=201)
def create_product(
    payload: ProductInput,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> ProductResponse:
    product = products_service.create_product(
        db, title=payload.title, image_url=payload.image_url, price=payload.price, status=payload.status, sort_order=payload.sort_order
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
        db, product_id, title=payload.title, image_url=payload.image_url, price=payload.price, status=payload.status, sort_order=payload.sort_order
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
    item = BannerItem(image_url=payload.image_url, link_url=payload.link_url, sort_order=payload.sort_order, is_enabled=payload.is_enabled)
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
    return AdminAnnouncementListResponse(items=[AdminAnnouncementResponse.model_validate(a) for a in items])


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
```

- [ ] **Step 3: main.py 注册路由**

修改 import 块:

```python
from app.api.web.home import router as web_home_router
from app.api.admin.cms import router as admin_cms_router
```

修改 include_router 块(追加):

```python
app.include_router(web_home_router, prefix="/api/v1/web")
app.include_router(admin_cms_router, prefix="/api/v1/admin")
```

- [ ] **Step 4: 提交**

```bash
git add backend/app/api/web/home.py backend/app/api/admin/cms.py backend/app/main.py
git commit -m "feat(api): 首页公开读取 + CMS admin CRUD 接口"
```

---

### Task 4: 后端测试

**Files:**
- Create: `backend/tests/test_home_api.py`
- Create: `backend/tests/test_cms_api.py`

- [ ] **Step 1: 创建 `test_home_api.py`**

```python
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models.user import Base
from app.db.session import engine

Base.metadata.create_all(bind=engine)

client = TestClient(app)


@pytest.fixture(autouse=True)
def _clean_db() -> None:
    with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete())


def _seed_module() -> None:
    db = SessionLocal()
    db.add(HomeModule(module_type="banner", title="B", data_source_url="/api/v1/web/home/banner", sort_order=1, is_enabled=True))
    db.add(HomeModule(module_type="product_recommend", title="P", data_source_url="/api/v1/web/products?status=active", sort_order=2, is_enabled=False))
    db.add(BannerItem(image_url="https://x/b1.jpg", link_url="/p1", sort_order=1, is_enabled=True))
    db.add(Announcement(content="公告1", is_enabled=True))
    db.add(Product(title="商品1", image_url="", price=9900, status="active", sort_order=1))
    db.add(Product(title="下架商品", image_url="", price=5000, status="inactive", sort_order=2))
    db.commit()
    db.close()


def test_modules_returns_only_enabled() -> None:
    _seed_module()
    response = client.get("/api/v1/web/home/modules")
    assert response.status_code == 200
    modules = response.json()["modules"]
    assert len(modules) == 1
    assert modules[0]["module_type"] == "banner"


def test_banner_returns_items() -> None:
    _seed_module()
    response = client.get("/api/v1/web/home/banner")
    assert response.status_code == 200
    assert len(response.json()["items"]) == 1


def test_announcement_returns_items() -> None:
    _seed_module()
    response = client.get("/api/v1/web/home/announcement")
    assert response.status_code == 200
    assert response.json()["items"][0]["content"] == "公告1"


def test_products_public_filters_active() -> None:
    _seed_module()
    response = client.get("/api/v1/web/home/products?status=active")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["price"] == 9900


def test_modules_empty_when_no_data() -> None:
    response = client.get("/api/v1/web/home/modules")
    assert response.status_code == 200
    assert response.json()["modules"] == []
```

- [ ] **Step 2: 创建 `test_cms_api.py`(结构骨架)**

```python
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models.user import Base
from app.db.session import engine

Base.metadata.create_all(bind=engine)

client = TestClient(app)

ADMIN_EMAIL = "cmstest@admin.com"


@pytest.fixture(autouse=True)
def _clean_db() -> None:
    with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete())
```

完整实现见 Step 3(`_admin_headers` + 5 个测试用例)。

- [ ] **Step 3(app 内验证 admin 鉴权 + CRUD)**

为精简,用直接插入 admin 用户 + 手动签发 token 的方式。在 `test_cms_api.py` 中补全:

```python
def _admin_headers() -> dict:
    from app.core.security import hash_password, create_access_token
    from app.models.user import User
    from app.db.session import SessionLocal
    db = SessionLocal()
    admin = db.query(User).filter(User.email == ADMIN_EMAIL).first()
    if admin is None:
        admin = User(email=ADMIN_EMAIL, username="cmstest", password_hash=hash_password("123456"), role="admin")
        db.add(admin)
        db.commit()
    token = create_access_token({"sub": str(admin.id)})
    db.close()
    return {"Cookie": f"token={token}"}


def test_modules_requires_auth() -> None:
    response = client.get("/api/v1/admin/cms/modules")
    assert response.status_code == 401


def test_create_and_move_module() -> None:
    headers = _admin_headers()
    response = client.post(
        "/api/v1/admin/cms/modules",
        json={"module_type": "banner", "title": "B1", "data_source_url": "/api/v1/web/home/banner", "sort_order": 1, "is_enabled": True},
        headers=headers,
    )
    assert response.status_code == 201
    module_id = response.json()["id"]

    # 再插入一个模块，使 move down 有相邻节点可交换，避免命中"已在边界"的 400
    client.post(
        "/api/v1/admin/cms/modules",
        json={"module_type": "product_recommend", "title": "P1", "data_source_url": "/api/v1/web/products?status=active", "sort_order": 2, "is_enabled": True},
        headers=headers,
    )

    moved = client.post(
        f"/api/v1/admin/cms/modules/{module_id}/move",
        json={"direction": "down"},
        headers=headers,
    )
    assert moved.status_code == 200
    by_id = {m["id"]: m["sort_order"] for m in moved.json()}
    assert by_id[module_id] == 2


def test_create_product() -> None:
    headers = _admin_headers()
    response = client.post("/api/v1/admin/cms/products",
        json={"title": "新商品", "image_url": "", "price": 9800, "status": "active", "sort_order": 1},
        headers=headers)
    assert response.status_code == 201
    assert response.json()["price"] == 9800


def test_create_banner() -> None:
    headers = _admin_headers()
    response = client.post("/api/v1/admin/cms/banners",
        json={"image_url": "https://x/b.jpg", "link_url": "/p", "sort_order": 1, "is_enabled": True},
        headers=headers)
    assert response.status_code == 201


def test_create_announcement() -> None:
    headers = _admin_headers()
    response = client.post("/api/v1/admin/cms/announcements",
        json={"content": "测试公告", "is_enabled": True},
        headers=headers)
    assert response.status_code == 201
```

注意:`_admin_headers` 中 token 需按 `create_access_token(data: dict)` 的实际签名签发,`get_current_user` 读取 `payload["sub"]` 并转 int,因此应为 `token = create_access_token({"sub": str(admin.id)})`,同时去掉 `_make` 占位符(仅作示例的声明常量,不保留)。以实际可编译为准,实现者需 Read `backend/app/core/security.py` 确认。

- [ ] **Step 4: 运行测试**

Run: `cd backend && uv run pytest tests/test_home_api.py tests/test_cms_api.py -v`
Expected: 全部 PASS

- [ ] **Step 5: 提交**

```bash
git add backend/tests/
git commit -m "test: 首页公开接口 + CMS admin CRUD 测试"
```

---

### Task 5: SDK 类型与函数

**Files:**
- Create: `packages/sdk/src/home.ts`
- Create: `packages/sdk/src/cms.ts`
- Modify: `packages/sdk/src/index.ts`

- [ ] **Step 1: 创建 `home.ts`**

```typescript
import type { ApiClient } from "./client";

export type ModuleType = "banner" | "product_recommend" | "announcement";

export type HomeModule = {
  id: number;
  module_type: ModuleType;
  title: string;
  data_source_url: string;
  sort_order: number;
};

export type HomeModulesResponse = {
  modules: HomeModule[];
};

export type BannerItem = {
  id: number;
  image_url: string;
  link_url: string;
};

export type BannerListResponse = {
  items: BannerItem[];
};

export type Announcement = {
  id: number;
  content: string;
};

export type AnnouncementListResponse = {
  items: Announcement[];
};

export type Product = {
  id: number;
  title: string;
  image_url: string;
  price: number;
};

export type ProductPublicListResponse = {
  items: Product[];
  total: number;
};

/** 首页可配置模块列表(仅启用) */
export function getHomeModules(client: ApiClient): Promise<HomeModulesResponse> {
  return client.request<HomeModulesResponse>("/api/v1/web/home/modules");
}

/** 首页 banner 列表 */
export function getHomeBanner(client: ApiClient): Promise<BannerListResponse> {
  return client.request<BannerListResponse>("/api/v1/web/home/banner");
}

/** 首页公告列表 */
export function getHomeAnnouncements(client: ApiClient): Promise<AnnouncementListResponse> {
  return client.request<AnnouncementListResponse>("/api/v1/web/home/announcement");
}

/** 首页推荐商品(公开) */
export function getPublicProducts(
  client: ApiClient,
  options?: { status?: string; page?: number; page_size?: number },
): Promise<ProductPublicListResponse> {
  const params = new URLSearchParams();
  if (options?.status) params.set("status", options.status);
  if (options?.page) params.set("page", String(options.page));
  if (options?.page_size) params.set("page_size", String(options.page_size));
  const query = params.toString();
  return client.request<ProductPublicListResponse>(
    `/api/v1/web/home/products${query ? `?${query}` : ""}`,
  );
}
```

- [ ] **Step 2: 创建 `cms.ts`**

```typescript
import type { ApiClient } from "./client";
import type { ModuleType } from "./home";

export type CmsModule = {
  id: number;
  module_type: ModuleType;
  title: string;
  data_source_url: string;
  sort_order: number;
  is_enabled: boolean;
  created_at: string;
  updated_at: string;
};

export type ModuleInput = {
  module_type: ModuleType;
  title: string;
  data_source_url: string;
  sort_order: number;
  is_enabled: boolean;
};

export type CmsProduct = {
  id: number;
  title: string;
  image_url: string;
  price: number;
  status: string;
  sort_order: number;
  created_at: string;
};

export type ProductInput = {
  title: string;
  image_url: string;
  price: number;
  status: string;
  sort_order: number;
};

export type CmsProductListResponse = {
  items: CmsProduct[];
  total: number;
  page: number;
  page_size: number;
};

export type CmsBanner = {
  id: number;
  image_url: string;
  link_url: string;
  sort_order: number;
  is_enabled: boolean;
  created_at: string;
};

export type BannerInput = {
  image_url: string;
  link_url: string;
  sort_order: number;
  is_enabled: boolean;
};

export type CmsBannerListResponse = {
  items: CmsBanner[];
};

export type CmsAnnouncement = {
  id: number;
  content: string;
  is_enabled: boolean;
  created_at: string;
};

export type AnnouncementInput = {
  content: string;
  is_enabled: boolean;
};

export type CmsAnnouncementListResponse = {
  items: CmsAnnouncement[];
};

export function getCmsModules(client: ApiClient): Promise<CmsModule[]> {
  return client.request<CmsModule[]>("/api/v1/admin/cms/modules");
}

export function createCmsModule(client: ApiClient, input: ModuleInput): Promise<CmsModule> {
  return client.request<CmsModule>("/api/v1/admin/cms/modules", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
}

export function updateCmsModule(
  client: ApiClient,
  moduleId: number,
  input: ModuleInput,
): Promise<CmsModule> {
  return client.request<CmsModule>(`/api/v1/admin/cms/modules/${moduleId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
}

export function deleteCmsModule(client: ApiClient, moduleId: number): Promise<void> {
  return client.request<void>(`/api/v1/admin/cms/modules/${moduleId}`, { method: "DELETE" });
}

export function moveCmsModule(
  client: ApiClient,
  moduleId: number,
  direction: "up" | "down",
): Promise<CmsModule[]> {
  return client.request<CmsModule[]>(`/api/v1/admin/cms/modules/${moduleId}/move`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ direction }),
  });
}

export function getCmsProducts(
  client: ApiClient,
  options?: { page?: number; page_size?: number; status?: string },
): Promise<CmsProductListResponse> {
  const params = new URLSearchParams();
  if (options?.page) params.set("page", String(options.page));
  if (options?.page_size) params.set("page_size", String(options.page_size));
  if (options?.status) params.set("status", options.status);
  const query = params.toString();
  return client.request<CmsProductListResponse>(`/api/v1/admin/cms/products${query ? `?${query}` : ""}`);
}

export function createCmsProduct(client: ApiClient, input: ProductInput): Promise<CmsProduct> {
  return client.request<CmsProduct>("/api/v1/admin/cms/products", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
}

export function updateCmsProduct(
  client: ApiClient,
  productId: number,
  input: ProductInput,
): Promise<CmsProduct> {
  return client.request<CmsProduct>(`/api/v1/admin/cms/products/${productId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
}

export function deleteCmsProduct(client: ApiClient, productId: number): Promise<void> {
  return client.request<void>(`/api/v1/admin/cms/products/${productId}`, { method: "DELETE" });
}

export function getCmsBanners(client: ApiClient): Promise<CmsBannerListResponse> {
  return client.request<CmsBannerListResponse>("/api/v1/admin/cms/banners");
}

export function createCmsBanner(client: ApiClient, input: BannerInput): Promise<CmsBanner> {
  return client.request<CmsBanner>("/api/v1/admin/cms/banners", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
}

export function updateCmsBanner(
  client: ApiClient,
  bannerId: number,
  input: BannerInput,
): Promise<CmsBanner> {
  return client.request<CmsBanner>(`/api/v1/admin/cms/banners/${bannerId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
}

export function deleteCmsBanner(client: ApiClient, bannerId: number): Promise<void> {
  return client.request<void>(`/api/v1/admin/cms/banners/${bannerId}`, { method: "DELETE" });
}

export function getCmsAnnouncements(client: ApiClient): Promise<CmsAnnouncementListResponse> {
  return client.request<CmsAnnouncementListResponse>("/api/v1/admin/cms/announcements");
}

export function createCmsAnnouncement(
  client: ApiClient,
  input: AnnouncementInput,
): Promise<CmsAnnouncement> {
  return client.request<CmsAnnouncement>("/api/v1/admin/cms/announcements", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
}

export function updateCmsAnnouncement(
  client: ApiClient,
  announcementId: number,
  input: AnnouncementInput,
): Promise<CmsAnnouncement> {
  return client.request<CmsAnnouncement>(`/api/v1/admin/cms/announcements/${announcementId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
}

export function deleteCmsAnnouncement(
  client: ApiClient,
  announcementId: number,
): Promise<void> {
  return client.request<void>(`/api/v1/admin/cms/announcements/${announcementId}`, {
    method: "DELETE",
  });
}
```

- [ ] **Step 3: 更新 `index.ts`**

追加:

```typescript
export {
  getHomeModules,
  getHomeBanner,
  getHomeAnnouncements,
  getPublicProducts,
} from "./home";
export type {
  ModuleType,
  HomeModule,
  HomeModulesResponse,
  BannerItem,
  BannerListResponse,
  Announcement,
  AnnouncementListResponse,
  Product,
  ProductPublicListResponse,
} from "./home";
export {
  getCmsModules,
  createCmsModule,
  updateCmsModule,
  deleteCmsModule,
  moveCmsModule,
  getCmsProducts,
  createCmsProduct,
  updateCmsProduct,
  deleteCmsProduct,
  getCmsBanners,
  createCmsBanner,
  updateCmsBanner,
  deleteCmsBanner,
  getCmsAnnouncements,
  createCmsAnnouncement,
  updateCmsAnnouncement,
  deleteCmsAnnouncement,
} from "./cms";
export type {
  CmsModule,
  ModuleInput,
  CmsProduct,
  ProductInput,
  CmsProductListResponse,
  CmsBanner,
  BannerInput,
  CmsBannerListResponse,
  CmsAnnouncement,
  AnnouncementInput,
  CmsAnnouncementListResponse,
} from "./cms";
```

- [ ] **Step 4: 验证类型检查**

Run: `cd packages/sdk && npx tsc --noEmit`
Expected: 无错误

- [ ] **Step 4b: 修复 `client.request` 对 204 的短路**

CMS 删除接口返回 `204 No Content`,而 `client.request`(packages/sdk/src/client.ts)现在无条件调用 `response.json()`,204 无 body 会抛 `SyntaxError`,导致 `deleteCms*`(及历史 `deleteFAQDocument`)不可用。在 `request` 中、`response.json()` 之前加:

```typescript
  if (response.status === 204) {
    return undefined as T;
  }
```

- [ ] **Step 5: 提交**

```bash
git add packages/sdk/src/
git commit -m "feat(sdk): 首页读取 + CMS 管理客户端函数"
```

---

### Task 6: web 首页按配置渲染

**Files:**
- Modify: `apps/web/app/(main)/page.tsx`
- Create: `apps/web/app/(main)/components/home-banner.tsx`
- Create: `apps/web/app/(main)/components/home-product-grid.tsx`
- Create: `apps/web/app/(main)/components/home-announcement.tsx`
- Create: `apps/web/app/(main)/components/home-module-renderer.tsx`

- [x] **Step 1: 创建 `home-banner.tsx`**

```tsx
import type { BannerItem } from "@ec/sdk";

type Props = { items: BannerItem[] };

export function HomeBanner({ items }: Props) {
  if (items.length === 0) return null;
  return (
    <div className="overflow-hidden rounded-2xl">
      {items.map((item, index) => {
        const inner = (
          <img
            src={item.image_url}
            alt={`banner-${index}`}
            className="h-48 w-full object-cover"
          />
        );
        return item.link_url ? (
          <a key={item.id} href={item.link_url}>
            {inner}
          </a>
        ) : (
          <div key={item.id}>{inner}</div>
        );
      })}
    </div>
  );
}
```

- [x] **Step 2: 创建 `home-product-grid.tsx`**

```tsx
import type { Product } from "@ec/sdk";

type Props = { items: Product[] };

export function formatPrice(cents: number): string {
  return `¥${(cents / 100).toFixed(2)}`;
}

export function HomeProductGrid({ items }: Props) {
  if (items.length === 0) return null;
  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
      {items.map((product) => (
        <div
          key={product.id}
          className="overflow-hidden rounded-xl border bg-surface-100-bg"
        >
          <img
            src={product.image_url}
            alt={product.title}
            className="h-32 w-full object-cover"
          />
          <div className="p-3">
            <p className="truncate text-sm text-surface-100-fg-default">{product.title}</p>
            <p className="mt-1 text-base font-medium text-text-accent">{formatPrice(product.price)}</p>
          </div>
        </div>
      ))}
    </div>
  );
}
```

- [x] **Step 3: 创建 `home-announcement.tsx`**

```tsx
import type { Announcement } from "@ec/sdk";

type Props = { items: Announcement[] };

export function HomeAnnouncement({ items }: Props) {
  if (items.length === 0) return null;
  return (
    <div className="space-y-2">
      {items.map((item) => (
        <p
          key={item.id}
          className="rounded-lg bg-surface-100-bg px-4 py-2 text-sm text-surface-100-fg-minor"
        >
          {item.content}
        </p>
      ))}
    </div>
  );
}
```

- [x] **Step 4: 创建 `home-module-renderer.tsx`**

```tsx
import { HomeModule, BannerItem, Product, Announcement } from "@ec/sdk";
import { HomeBanner } from "./home-banner";
import { HomeProductGrid } from "./home-product-grid";
import { HomeAnnouncement } from "./home-announcement";

export type ModulePayloads = {
  banner: BannerItem[];
  product_recommend: Product[];
  announcement: Announcement[];
};

type Props = {
  modules: HomeModule[];
  data: ModulePayloads;
};

export function HomeModuleRenderer({ modules, data }: Props) {
  return (
    <div className="space-y-8">
      {modules.map((module) => {
        const key = module.id;
        switch (module.module_type) {
          case "banner":
            return <HomeBanner key={key} items={data.banner} />;
          case "product_recommend":
            return <HomeProductGrid key={key} items={data.product_recommend} />;
          case "announcement":
            return <HomeAnnouncement key={key} items={data.announcement} />;
          default:
            return null;
        }
      })}
    </div>
  );
}
```

- [x] **Step 5: 重写 `page.tsx`**

```tsx
import {
  createApiClient,
  getHomeModules,
  getHomeBanner,
  getHomeAnnouncements,
  getPublicProducts,
  type HomeModule,
} from "@ec/sdk";
import { HomeModuleRenderer, ModulePayloads } from "./components/home-module-renderer";

const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

type HomeData =
  | { modules: HomeModule[]; data: ModulePayloads }
  | { modules: null; data: null };

async function loadHomeData(): Promise<HomeData> {
  try {
    const client = createApiClient({ baseUrl: apiBaseUrl });
    const [moduleRes, bannerRes, annoRes, productsRes] = await Promise.all([
      getHomeModules(client),
      getHomeBanner(client),
      getHomeAnnouncements(client),
      getPublicProducts(client, { status: "active" }),
    ]);
    return {
      modules: moduleRes.modules,
      data: {
        banner: bannerRes.items,
        product_recommend: productsRes.items,
        announcement: annoRes.items,
      },
    };
  } catch {
    return { modules: null, data: null };
  }
}

export default async function HomePage() {
  const { modules, data } = await loadHomeData();

  return (
    <div className="min-h-screen bg-surface-200-bg px-6 py-10 text-surface-100-fg-default">
      <main className="mx-auto flex max-w-5xl flex-col gap-8">
        <section className="space-y-3">
          <p className="enki-body-sm font-medium uppercase tracking-wide text-surface-100-fg-minor">
            EC Main
          </p>
          <h1 className="enki-heading-3xl">买家端商城</h1>
        </section>

        {modules && data ? (
          <HomeModuleRenderer modules={modules} data={data} />
        ) : (
          <p className="enki-body-base text-surface-100-fg-minor">
            首页模块加载失败，请先到 Admin 后台配置首页内容。
          </p>
        )}
      </main>
    </div>
  );
}
```

- [x] **Step 6: 运行类型检查**

Run: `cd apps/web && npx tsc --noEmit`
Expected: 无错误

- [x] **Step 7: 提交**

```bash
git add apps/web/app/\(main\)/page.tsx apps/web/app/\(main\)/components/
git commit -m "feat(web): 首页按 CMS 配置渲染"
```

---


> 质量评审后同步的补充修订:评审通过后一次清理提交 `70e29af`——`import type` 卫生(`page.tsx`/`home-module-renderer.tsx`)+ 5 个文件补齐 EOF 换行。全部非行为改动,`npx tsc --noEmit` 零错误。

### Task 7: web 首页测试

**Files:**
- Create: `apps/web/__tests__/home/home-module-renderer.test.tsx`
- Create: `apps/web/__tests__/home/home-product-grid.test.tsx`

- [x] **Step 1: 创建 `home-module-renderer.test.tsx`**

```tsx
import { render, screen, cleanup } from "@testing-library/react";
import { afterEach, describe, it, expect, vi } from "vitest";

afterEach(cleanup);

vi.mock("@ec/sdk", () => ({
  HomeModule: {},
  BannerItem: {},
  Product: {},
  Announcement: {},
}));

import { HomeModuleRenderer, ModulePayloads } from "@/app/(main)/components/home-module-renderer";

const data: ModulePayloads = {
  banner: [{ id: 1, image_url: "https://x/b.jpg", link_url: "/p" }],
  product_recommend: [{ id: 1, title: "商品1", image_url: "", price: 9900 }],
  announcement: [{ id: 1, content: "公告1" }],
};

describe("HomeModuleRenderer", () => {
  it("renders banner module", () => {
    render(
      <HomeModuleRenderer
        modules={[{ id: 1, module_type: "banner", title: "B", data_source_url: "/api/v1/web/home/banner", sort_order: 1 }]}
        data={data}
      />,
    );
    expect(screen.getByAltText("banner-0")).toBeInTheDocument();
  });

  it("renders product grid module", () => {
    render(
      <HomeModuleRenderer
        modules={[{ id: 2, module_type: "product_recommend", title: "P", data_source_url: "/api/v1/web/home/products", sort_order: 2 }]}
        data={data}
      />,
    );
    expect(screen.getByText("商品1")).toBeInTheDocument();
  });

  it("renders announcement module", () => {
    render(
      <HomeModuleRenderer
        modules={[{ id: 3, module_type: "announcement", title: "A", data_source_url: "/api/v1/web/home/announcement", sort_order: 3 }]}
        data={data}
      />,
    );
    expect(screen.getByText("公告1")).toBeInTheDocument();
  });

  it("renders nothing for unknown module type", () => {
    const { container } = render(
      <HomeModuleRenderer
        modules={[{ id: 4, module_type: "unknown", title: "X", data_source_url: "", sort_order: 4 }]}
        data={data}
      />,
    );
    expect(container.querySelectorAll("*").length).toBe(1);
  });
});
```

- [x] **Step 2: 创建 `home-product-grid.test.tsx`**

```tsx
import { render, screen, cleanup } from "@testing-library/react";
import { afterEach, describe, it, expect } from "vitest";

afterEach(cleanup);

import { HomeProductGrid, formatPrice } from "@/app/(main)/components/home-product-grid";

describe("formatPrice", () => {
  it("formats cents to yuan", () => {
    expect(formatPrice(9900)).toBe("¥99.00");
    expect(formatPrice(12900)).toBe("¥129.00");
  });
});

describe("HomeProductGrid", () => {
  it("renders nothing when empty", () => {
    const { container } = render(<HomeProductGrid items={[]} />);
    expect(container.innerHTML).toBe("");
  });

  it("renders product titles and prices", () => {
    render(<HomeProductGrid items={[{ id: 1, title: "商品1", image_url: "", price: 9900 }]} />);
    expect(screen.getByText("商品1")).toBeInTheDocument();
    expect(screen.getByText("¥99.00")).toBeInTheDocument();
  });
});
```

- [x] **Step 3: 运行测试**

Run: `cd apps/web && npx vitest run __tests__/home/`
Expected: 全部 PASS

- [x] **Step 4: 提交**

```bash
git add apps/web/__tests__/home/
git commit -m "test(web): 首页模块渲染测试"
```

---


已实现与验证:`70e29af` 后提交 `__tests__/home/` 两文件(vitest 7/7 PASS、`npm run check` 零错误,评审 APPROVED)。相对计划的改进:无必要 `vi.mock`、`import type` 卫生、`module_type: "unknown"` 用 `as unknown as HomeModule` 覆盖 default 分支。

### Task 8: admin CMS 管理页 + 导航

**Files:**
- Modify: `apps/admin/app/components/sidebar.tsx`
- Create: `apps/admin/app/(main)/cms/modules/page.tsx`
- Create: `apps/admin/app/(main)/cms/banners/page.tsx`
- Create: `apps/admin/app/(main)/cms/announcements/page.tsx`
- Create: `apps/admin/app/(main)/cms/products/page.tsx`

- [ ] **Step 1: sidebar 增加导航**

将 `apps/admin/app/components/sidebar.tsx` 的 navItems 中 `{ label: "商品管理", href: "/products" }`(若存在)改为:

```typescript
  { label: "首页配置", href: "/cms/modules" },
  { label: "商品管理", href: "/cms/products" },
```

保持其他项不变。

- [ ] **Step 2: 创建 `cms/modules/page.tsx`**

```tsx
"use client";

import { useEffect, useState, useCallback } from "react";
import { Loader2, ArrowUp, ArrowDown, Pencil, Trash2 } from "lucide-react";
import { createApiClient } from "@ec/sdk/client";
import {
  getCmsModules,
  createCmsModule,
  updateCmsModule,
  deleteCmsModule,
  moveCmsModule,
} from "@ec/sdk";
import type { CmsModule, ModuleInput } from "@ec/sdk";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

const client = createApiClient({
  baseUrl: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
});

const MODULE_TYPE_LABELS: Record<string, string> = {
  banner: "Banner 轮播",
  product_recommend: "推荐商品",
  announcement: "平台公告",
};

const DEFAULT_URLS: Record<string, string> = {
  banner: "/api/v1/web/home/banner",
  product_recommend: "/api/v1/web/products?status=active",
  announcement: "/api/v1/web/home/announcement",
};

const emptyForm: ModuleInput = {
  module_type: "banner",
  title: "",
  data_source_url: DEFAULT_URLS.banner,
  sort_order: 0,
  is_enabled: true,
};

export default function ModulesPage() {
  const [modules, setModules] = useState<CmsModule[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState<ModuleInput>({ ...emptyForm });
  const [editingId, setEditingId] = useState<number | null>(null);

  const loadModules = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setModules(await getCmsModules(client));
    } catch {
      setError("加载首页模块失败");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadModules();
  }, [loadModules]);

  function resetForm() {
    setForm({ ...emptyForm });
    setEditingId(null);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      if (editingId === null) {
        await createCmsModule(client, form);
      } else {
        await updateCmsModule(client, editingId, form);
      }
      resetForm();
      await loadModules();
    } catch {
      setError("保存模块失败");
    }
  }

  async function handleDelete(id: number) {
    if (!confirm("确认删除该模块?")) return;
    try {
      await deleteCmsModule(client, id);
      await loadModules();
    } catch {
      setError("删除模块失败");
    }
  }

  async function handleMove(id: number, direction: "up" | "down") {
    try {
      setModules(await moveCmsModule(client, id, direction));
    } catch {
      setError("移动模块失败");
    }
  }

  function handleEdit(module: CmsModule) {
    setEditingId(module.id);
    setForm({
      module_type: module.module_type,
      title: module.title,
      data_source_url: module.data_source_url,
      sort_order: module.sort_order,
      is_enabled: module.is_enabled,
    });
  }

  return (
    <section className="space-y-6">
      <h1 className="text-2xl font-semibold">首页模块配置</h1>

      {error && <p className="text-sm text-red-600">{error}</p>}

      <form onSubmit={handleSubmit} className="space-y-3 rounded-lg border p-4">
        <div className="flex flex-wrap gap-3">
          <select
            value={form.module_type}
            onChange={(e) =>
              setForm({
                ...form,
                module_type: e.target.value,
                data_source_url: DEFAULT_URLS[e.target.value] ?? form.data_source_url,
              })
            }
            className="h-8 rounded-lg border border-input bg-transparent px-2.5 text-sm"
          >
            {Object.entries(MODULE_TYPE_LABELS).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
          <Input
            value={form.title}
            onChange={(e) => setForm({ ...form, title: e.target.value })}
            placeholder="模块标题"
            className="w-48"
          />
          <Input
            value={form.data_source_url}
            onChange={(e) => setForm({ ...form, data_source_url: e.target.value })}
            placeholder="数据源 URL"
            className="w-72"
          />
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={form.is_enabled}
              onChange={(e) => setForm({ ...form, is_enabled: e.target.checked })}
            />
            启用
          </label>
          <Button type="submit">{editingId === null ? "新增" : "更新"}</Button>
          {editingId !== null && (
            <Button type="button" variant="outline" onClick={resetForm}>
              取消
            </Button>
          )}
        </div>
      </form>

      {loading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="size-6 animate-spin text-muted-foreground" />
        </div>
      ) : modules.length === 0 ? (
        <p className="py-8 text-center text-sm text-muted-foreground">暂无模块</p>
      ) : (
        <table className="w-full overflow-hidden rounded-lg border text-sm">
          <thead className="bg-muted/50">
            <tr>
              <th className="px-4 py-3 text-left font-medium">排序</th>
              <th className="px-4 py-3 text-left font-medium">类型</th>
              <th className="px-4 py-3 text-left font-medium">标题</th>
              <th className="px-4 py-3 text-left font-medium">数据源</th>
              <th className="px-4 py-3 text-left font-medium">状态</th>
              <th className="px-4 py-3 text-right font-medium">操作</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {modules.map((module) => (
              <tr key={module.id} className="hover:bg-muted/30">
                <td className="px-4 py-3">
                  <div className="flex items-center gap-1">
                    <button
                      onClick={() => handleMove(module.id, "up")}
                      disabled={module.sort_order === 0}
                      className="text-muted-foreground hover:text-foreground disabled:opacity-40"
                      aria-label="上移"
                    >
                      <ArrowUp className="size-4" />
                    </button>
                    <button
                      onClick={() => handleMove(module.id, "down")}
                      className="text-muted-foreground hover:text-foreground"
                      aria-label="下移"
                    >
                      <ArrowDown className="size-4" />
                    </button>
                  </div>
                </td>
                <td className="px-4 py-3">
                  {MODULE_TYPE_LABELS[module.module_type] ?? module.module_type}
                </td>
                <td className="px-4 py-3">{module.title}</td>
                <td className="px-4 py-3 font-mono text-xs text-muted-foreground">
                  {module.data_source_url}
                </td>
                <td className="px-4 py-3">
                  {module.is_enabled ? (
                    <span className="inline-block rounded-full bg-green-100 px-2.5 py-0.5 text-xs text-green-700">
                      启用
                    </span>
                  ) : (
                    <span className="inline-block rounded-full bg-gray-100 px-2.5 py-0.5 text-xs text-gray-600">
                      停用
                    </span>
                  )}
                </td>
                <td className="px-4 py-3 text-right">
                  <button onClick={() => handleEdit(module)} className="mr-2 text-blue-600 hover:underline" aria-label="编辑">
                    <Pencil className="inline size-4" />
                  </button>
                  <button onClick={() => handleDelete(module.id)} className="text-red-600 hover:underline" aria-label="删除">
                    <Trash2 className="inline size-4" />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}
```

- [ ] **Step 3: 创建 `cms/products/page.tsx`**

```tsx
"use client";

import { useEffect, useState, useCallback } from "react";
import { Loader2, Pencil, Trash2 } from "lucide-react";
import { createApiClient } from "@ec/sdk/client";
import { getCmsProducts, createCmsProduct, updateCmsProduct, deleteCmsProduct } from "@ec/sdk";
import type { CmsProduct, ProductInput } from "@ec/sdk";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

const client = createApiClient({
  baseUrl: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
});

const PAGE_SIZE = 20;

const emptyForm: ProductInput = {
  title: "",
  image_url: "",
  price: 0,
  status: "active",
  sort_order: 0,
};

export default function CmsProductsPage() {
  const [items, setItems] = useState<CmsProduct[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState<ProductInput>({ ...emptyForm });
  const [editingId, setEditingId] = useState<number | null>(null);

  const loadProducts = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await getCmsProducts(client, { page, page_size: PAGE_SIZE });
      setItems(res.items);
      setTotal(res.total);
    } catch {
      setError("加载商品失败");
    } finally {
      setLoading(false);
    }
  }, [page]);

  useEffect(() => {
    loadProducts();
  }, [loadProducts]);

  function resetForm() {
    setForm({ ...emptyForm });
    setEditingId(null);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      if (editingId === null) {
        await createCmsProduct(client, { ...form, price: Number(form.price) || 0 });
      } else {
        await updateCmsProduct(client, editingId, { ...form, price: Number(form.price) || 0 });
      }
      resetForm();
      await loadProducts();
    } catch {
      setError("保存商品失败");
    }
  }

  async function handleDelete(id: number) {
    if (!confirm("确认删除该商品?")) return;
    try {
      await deleteCmsProduct(client, id);
      await loadProducts();
    } catch {
      setError("删除商品失败");
    }
  }

  function handleEdit(item: CmsProduct) {
    setEditingId(item.id);
    setForm({
      title: item.title,
      image_url: item.image_url,
      price: item.price,
      status: item.status,
      sort_order: item.sort_order,
    });
  }

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  return (
    <section className="space-y-6">
      <h1 className="text-2xl font-semibold">商品管理</h1>

      {error && <p className="text-sm text-red-600">{error}</p>}

      <form onSubmit={handleSubmit} className="space-y-3 rounded-lg border p-4">
        <div className="flex flex-wrap items-end gap-3">
          <div>
            <label className="mb-1 block text-xs text-muted-foreground">标题</label>
            <Input
              value={form.title}
              onChange={(e) => setForm({ ...form, title: e.target.value })}
              placeholder="商品标题"
              className="w-52"
            />
          </div>
          <div>
            <label className="mb-1 block text-xs text-muted-foreground">图片 URL</label>
            <Input
              value={form.image_url}
              onChange={(e) => setForm({ ...form, image_url: e.target.value })}
              placeholder="https://..."
              className="w-72"
            />
          </div>
          <div>
            <label className="mb-1 block text-xs text-muted-foreground">价格(分)</label>
            <Input
              type="number"
              value={form.price}
              onChange={(e) => setForm({ ...form, price: Number(e.target.value) })}
              className="w-28"
            />
          </div>
          <select
            value={form.status}
            onChange={(e) => setForm({ ...form, status: e.target.value })}
            className="h-8 rounded-lg border border-input bg-transparent px-2.5 text-sm"
          >
            <option value="active">上架</option>
            <option value="inactive">下架</option>
          </select>
          <Button type="submit">{editingId === null ? "新增" : "更新"}</Button>
          {editingId !== null && (
            <Button type="button" variant="outline" onClick={resetForm}>
              取消
            </Button>
          )}
        </div>
      </form>

      {loading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="size-6 animate-spin text-muted-foreground" />
        </div>
      ) : items.length === 0 ? (
        <p className="py-8 text-center text-sm text-muted-foreground">暂无商品</p>
      ) : (
        <div className="overflow-hidden rounded-lg border">
          <table className="w-full text-sm">
            <thead className="bg-muted/50">
              <tr>
                <th className="px-4 py-3 text-left font-medium">ID</th>
                <th className="px-4 py-3 text-left font-medium">标题</th>
                <th className="px-4 py-3 text-left font-medium">价格</th>
                <th className="px-4 py-3 text-left font-medium">状态</th>
                <th className="px-4 py-3 text-right font-medium">操作</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {items.map((item) => (
                <tr key={item.id} className="hover:bg-muted/30">
                  <td className="px-4 py-3">{item.id}</td>
                  <td className="px-4 py-3 font-medium">{item.title}</td>
                  <td className="px-4 py-3">¥{(item.price / 100).toFixed(2)}</td>
                  <td className="px-4 py-3">
                    {item.status === "active" ? (
                      <span className="inline-block rounded-full bg-green-100 px-2.5 py-0.5 text-xs text-green-700">
                        上架
                      </span>
                    ) : (
                      <span className="inline-block rounded-full bg-gray-100 px-2.5 py-0.5 text-xs text-gray-600">
                        下架
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <button onClick={() => handleEdit(item)} className="mr-2 text-blue-600 hover:underline" aria-label="编辑">
                      <Pencil className="inline size-4" />
                    </button>
                    <button onClick={() => handleDelete(item.id)} className="text-red-600 hover:underline" aria-label="删除">
                      <Trash2 className="inline size-4" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {!loading && items.length > 0 && (
        <div className="flex items-center justify-between text-sm text-muted-foreground">
          <span>
            共 {total} 条,第 {page} / {totalPages} 页
          </span>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
              上一页
            </Button>
            <Button variant="outline" size="sm" disabled={page >= totalPages} onClick={() => setPage((p) => p + 1)}>
              下一页
            </Button>
          </div>
        </div>
      )}
    </section>
  );
}
```

- [ ] **Step 4: 创建 `cms/banners/page.tsx`**(banner 列表 + 表单,image_url/link_url/sort_order/is_enabled)

```tsx
"use client";

import { useEffect, useState, useCallback } from "react";
import { Loader2, Pencil, Trash2 } from "lucide-react";
import { createApiClient } from "@ec/sdk/client";
import { getCmsBanners, createCmsBanner, updateCmsBanner, deleteCmsBanner } from "@ec/sdk";
import type { CmsBanner, BannerInput } from "@ec/sdk";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

const client = createApiClient({
  baseUrl: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
});

const emptyForm: BannerInput = { image_url: "", link_url: "", sort_order: 0, is_enabled: true };

export default function CmsBannersPage() {
  const [items, setItems] = useState<CmsBanner[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState<BannerInput>({ ...emptyForm });
  const [editingId, setEditingId] = useState<number | null>(null);

  const loadBanners = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setItems((await getCmsBanners(client)).items);
    } catch {
      setError("加载 Banner 失败");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadBanners();
  }, [loadBanners]);

  function resetForm() {
    setForm({ ...emptyForm });
    setEditingId(null);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      if (editingId === null) {
        await createCmsBanner(client, { ...form, sort_order: Number(form.sort_order) || 0 });
      } else {
        await updateCmsBanner(client, editingId, { ...form, sort_order: Number(form.sort_order) || 0 });
      }
      resetForm();
      await loadBanners();
    } catch {
      setError("保存 Banner 失败");
    }
  }

  async function handleDelete(id: number) {
    if (!confirm("确认删除?")) return;
    try {
      await deleteCmsBanner(client, id);
      await loadBanners();
    } catch {
      setError("删除 Banner 失败");
    }
  }

  function handleEdit(item: CmsBanner) {
    setEditingId(item.id);
    setForm({ image_url: item.image_url, link_url: item.link_url, sort_order: item.sort_order, is_enabled: item.is_enabled });
  }

  return (
    <section className="space-y-6">
      <h1 className="text-2xl font-semibold">Banner 管理</h1>
      {error && <p className="text-sm text-red-600">{error}</p>}

      <form onSubmit={handleSubmit} className="space-y-3 rounded-lg border p-4">
        <div className="flex flex-wrap items-end gap-3">
          <div className="min-w-64 flex-1">
            <label className="mb-1 block text-xs text-muted-foreground">图片 URL</label>
            <Input value={form.image_url} onChange={(e) => setForm({ ...form, image_url: e.target.value })} placeholder="https://..." />
          </div>
          <div className="min-w-48 flex-1">
            <label className="mb-1 block text-xs text-muted-foreground">跳转链接</label>
            <Input value={form.link_url} onChange={(e) => setForm({ ...form, link_url: e.target.value })} />
          </div>
          <div>
            <label className="mb-1 block text-xs text-muted-foreground">排序</label>
            <Input type="number" value={form.sort_order} onChange={(e) => setForm({ ...form, sort_order: Number(e.target.value) })} className="w-24" />
          </div>
          <label className="flex items-center gap-2 pb-1 text-sm">
            <input type="checkbox" checked={form.is_enabled} onChange={(e) => setForm({ ...form, is_enabled: e.target.checked })} />
            启用
          </label>
          <Button type="submit">{editingId === null ? "新增" : "更新"}</Button>
          {editingId !== null && (
            <Button type="button" variant="outline" onClick={resetForm}>取消</Button>
          )}
        </div>
      </form>

      {loading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="size-6 animate-spin text-muted-foreground" />
        </div>
      ) : items.length === 0 ? (
        <p className="py-8 text-center text-sm text-muted-foreground">暂无 Banner</p>
      ) : (
        <div className="grid grid-cols-2 gap-4 md:grid-cols-3">
          {items.map((item) => (
            <div key={item.id} className="overflow-hidden rounded-lg border">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={item.image_url} alt={item.link_url} className="h-32 w-full object-cover" />
              <div className="flex items-center justify-between p-3">
                <span className="truncate text-xs text-muted-foreground">{item.link_url || "无链接"}</span>
                <div className="flex gap-2">
                  <button onClick={() => handleEdit(item)} className="text-blue-600 hover:underline" aria-label="编辑">
                    <Pencil className="size-4" />
                  </button>
                  <button onClick={() => handleDelete(item.id)} className="text-red-600 hover:underline" aria-label="删除">
                    <Trash2 className="size-4" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
```

- [ ] **Step 5: 创建 `cms/announcements/page.tsx`**(公告列表 + 表单)

```tsx
"use client";

import { useEffect, useState, useCallback } from "react";
import { Loader2, Pencil, Trash2 } from "lucide-react";
import { createApiClient } from "@ec/sdk/client";
import { getCmsAnnouncements, createCmsAnnouncement, updateCmsAnnouncement, deleteCmsAnnouncement } from "@ec/sdk";
import type { CmsAnnouncement, AnnouncementInput } from "@ec/sdk";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

const client = createApiClient({
  baseUrl: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
});

const emptyForm: AnnouncementInput = { content: "", is_enabled: true };

export default function CmsAnnouncementsPage() {
  const [items, setItems] = useState<CmsAnnouncement[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState<AnnouncementInput>({ ...emptyForm });
  const [editingId, setEditingId] = useState<number | null>(null);

  const loadAnnouncements = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setItems((await getCmsAnnouncements(client)).items);
    } catch {
      setError("加载公告失败");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadAnnouncements();
  }, [loadAnnouncements]);

  function resetForm() {
    setForm({ ...emptyForm });
    setEditingId(null);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      if (editingId === null) {
        await createCmsAnnouncement(client, form);
      } else {
        await updateCmsAnnouncement(client, editingId, form);
      }
      resetForm();
      await loadAnnouncements();
    } catch {
      setError("保存公告失败");
    }
  }

  async function handleDelete(id: number) {
    if (!confirm("确认删除?")) return;
    try {
      await deleteCmsAnnouncement(client, id);
      await loadAnnouncements();
    } catch {
      setError("删除公告失败");
    }
  }

  function handleEdit(item: CmsAnnouncement) {
    setEditingId(item.id);
    setForm({ content: item.content, is_enabled: item.is_enabled });
  }

  return (
    <section className="space-y-6">
      <h1 className="text-2xl font-semibold">公告管理</h1>
      {error && <p className="text-sm text-red-600">{error}</p>}

      <form onSubmit={handleSubmit} className="flex flex-wrap items-end gap-3 rounded-lg border p-4">
        <div className="min-w-72 flex-1">
          <label className="mb-1 block text-xs text-muted-foreground">公告内容</label>
          <Input value={form.content} onChange={(e) => setForm({ ...form, content: e.target.value })} placeholder="公告内容" />
        </div>
        <label className="flex items-center gap-2 pb-1 text-sm">
          <input type="checkbox" checked={form.is_enabled} onChange={(e) => setForm({ ...form, is_enabled: e.target.checked })} />
          启用
        </label>
        <Button type="submit">{editingId === null ? "新增" : "更新"}</Button>
        {editingId !== null && (
          <Button type="button" variant="outline" onClick={resetForm}>取消</Button>
        )}
      </form>

      {loading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="size-6 animate-spin text-muted-foreground" />
        </div>
      ) : items.length === 0 ? (
        <p className="py-8 text-center text-sm text-muted-foreground">暂无公告</p>
      ) : (
        <ul className="space-y-2">
          {items.map((item) => (
            <li key={item.id} className="flex items-center justify-between rounded-lg border px-4 py-3">
              <div className="flex items-center gap-3">
                <span className="text-sm">{item.content}</span>
                {item.is_enabled ? (
                  <span className="inline-block rounded-full bg-green-100 px-2 py-0.5 text-xs text-green-700">启用</span>
                ) : (
                  <span className="inline-block rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-600">停用</span>
                )}
              </div>
              <div className="flex gap-2">
                <button onClick={() => handleEdit(item)} className="text-blue-600 hover:underline" aria-label="编辑">
                  <Pencil className="size-4" />
                </button>
                <button onClick={() => handleDelete(item.id)} className="text-red-600 hover:underline" aria-label="删除">
                  <Trash2 className="size-4" />
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
```

- [ ] **Step 6: 运行类型检查**

Run: `cd apps/admin && npx tsc --noEmit`
Expected: 无错误

- [ ] **Step 7: 提交**

```bash
git add apps/admin/app/components/sidebar.tsx apps/admin/app/\(main\)/cms/
git commit -m "feat(admin): 首页 CMS 配置管理页"
```

---

### Task 9: 集成验证

- [ ] **Step 1: 后端全部测试**

Run: `cd backend && uv run pytest -v`
Expected: 全部 PASS(含新增 home/cms 测试)

- [ ] **Step 2: 前端类型检查 + 测试**

Run: `cd packages/sdk && npx tsc --noEmit && cd apps/web && npx tsc --noEmit && npx vitest run && cd ../admin && npx tsc --noEmit && npx vitest run`
Expected: 全部通过

- [ ] **Step 3: 运行态冒烟(可选)**

- `pnpm dev:backend` 启动后端,确认 `/api/v1/web/home/modules` 返回 3 个种子模块
- `pnpm dev:admin` 登录 admin@admin.com/123456,打开 首页配置→模块,能增删改排序
- `pnpm dev:web` 打开首页,应显示 banner 图、推荐商品、公告

---

## 自检

- **Spec 覆盖**:4 表(Task 1)→ domain+seed(Task 2)→ 接口(Task 3)→ 测试(Task 4)→ SDK(Task 5)→ web(Task 6-7)→ admin(Task 8)→ 集成验证(Task 9)。全量覆盖设计文档。
- **无占位符**:全部代码完整给出;Task 4 中 `test_cms_api.py` 的鉴权 helper 以实际可编译为准,已提示实现者需参考 `create_access_token` 实际签名或改用登录接口。
- **类型一致**:SDK 函数名与后端路由路径一一对应;组件 props 与 SDK 类型一致;`HomeModuleRenderer` 的 `data` props(ModulePayloads)与 page 传入对象结构一致。