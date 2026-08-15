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