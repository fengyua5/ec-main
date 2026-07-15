from datetime import datetime
from sqlalchemy import String, Integer, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from app.models.user import Base


class Order(Base):
    __tablename__ = "orders"

    order_no: Mapped[str] = mapped_column(String(50), primary_key=True)
    buyer_id: Mapped[int] = mapped_column(Integer, nullable=False)
    amount: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending_delivery")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
