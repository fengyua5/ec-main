from datetime import datetime
from sqlalchemy import String, Integer, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from app.models.user import Base


class AfterSaleCase(Base):
    __tablename__ = "after_sale_cases"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    order_no: Mapped[str] = mapped_column(String(50), nullable=False)
    buyer_id: Mapped[int] = mapped_column(Integer, nullable=False)
    case_type: Mapped[str] = mapped_column(String(20), nullable=False)
    amount: Mapped[str | None] = mapped_column(String(20), nullable=True)
    reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="processed")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
