"""ORM модели для товаров и предсказаний цен."""

from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from users.adapters.orm import UserORM

from sqlalchemy import Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from base.config import TaskStatus
from base.orm import Base


class ProductORM(Base):
    """Модель товара."""

    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    brand_name: Mapped[str] = mapped_column(String(255), default="Unknown")
    category_name: Mapped[str] = mapped_column(String(255), default="Other")
    item_description: Mapped[str] = mapped_column(Text, default="")
    item_condition_id: Mapped[int] = mapped_column(Integer, default=1)
    shipping: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(default=func.now(), nullable=False)

    price_predictions: Mapped[list["PricePredictionORM"]] = relationship(
        back_populates="product", lazy="selectin"
    )
    tasks: Mapped[list["TaskORM"]] = relationship(
        back_populates="product", lazy="selectin"
    )
    user: Mapped["UserORM"] = relationship(back_populates="products", lazy="selectin")


class PricePredictionORM(Base):
    """Модель прогноза цены."""

    __tablename__ = "price_predictions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
    )
    predicted_price: Mapped[float] = mapped_column(Float, nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0)
    model_version: Mapped[str] = mapped_column(String(50), default="1.0")
    created_at: Mapped[datetime] = mapped_column(default=func.now(), nullable=False)

    product: Mapped["ProductORM"] = relationship(back_populates="price_predictions")


class TaskORM(Base):
    """Модель задачи ML."""

    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
    )
    status: Mapped[TaskStatus] = mapped_column(default=TaskStatus.NEW)
    type: Mapped[str] = mapped_column(String(50), default="pricing")
    input_data: Mapped[dict] = mapped_column(Text, default="{}")
    result: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        default=func.now(), onupdate=func.now(), nullable=False
    )

    product: Mapped["ProductORM"] = relationship(
        back_populates="tasks", lazy="selectin"
    )


# All deprecated ORM models removed after migration
