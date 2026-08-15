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
