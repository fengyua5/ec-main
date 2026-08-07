from datetime import datetime
from pydantic import BaseModel


class OrderResponse(BaseModel):
    order_no: str
    buyer_id: int
    amount: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class OrderListResponse(BaseModel):
    items: list[OrderResponse]
    total: int
    page: int
    page_size: int


class OrderStatusUpdate(BaseModel):
    status: str


class OrderStatusUpdateResponse(BaseModel):
    order: OrderResponse
