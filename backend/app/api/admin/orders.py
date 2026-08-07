from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.deps import get_db
from app.domain.orders import (
    list_orders,
    get_order,
    update_order_status,
)
from app.domain.orders.schemas import (
    OrderListResponse,
    OrderResponse,
    OrderStatusUpdate,
    OrderStatusUpdateResponse,
)

router = APIRouter(prefix="/orders")


@router.get("", response_model=OrderListResponse)
def list_orders_endpoint(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str | None = Query(None),
    keyword: str | None = Query(None),
    db: Session = Depends(get_db),
):
    orders, total = list_orders(
        db,
        page=page,
        page_size=page_size,
        status_filter=status,
        keyword=keyword,
    )
    return OrderListResponse(
        items=[OrderResponse.model_validate(o) for o in orders],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{order_no}", response_model=OrderResponse)
def order_detail(order_no: str, db: Session = Depends(get_db)):
    return OrderResponse.model_validate(get_order(db, order_no))


@router.patch("/{order_no}/status", response_model=OrderStatusUpdateResponse)
def change_order_status(
    order_no: str,
    payload: OrderStatusUpdate,
    db: Session = Depends(get_db),
):
    order = update_order_status(db, order_no, payload.status)
    return OrderStatusUpdateResponse(order=OrderResponse.model_validate(order))
