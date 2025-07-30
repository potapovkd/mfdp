"""ORM модели для пользователей."""

from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from products.adapters.orm import ProductORM

from sqlalchemy import DateTime, String, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from base.orm import Base


class UserORM(Base):
    """Модель пользователя в БД."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True)
    username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    balance: Mapped[float] = mapped_column(Numeric(10, 2), default=0.00)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    products: Mapped[list["ProductORM"]] = relationship(
        back_populates="user", lazy="selectin"
    )
