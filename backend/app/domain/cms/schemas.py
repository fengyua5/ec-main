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
