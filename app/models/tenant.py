from sqlalchemy import String, Integer, Boolean
from typing import TYPE_CHECKING # Avoids circular imports at runtime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

if TYPE_CHECKING:
    from app.models.event import Event
    from app.models.user import User


class Tenant(Base):
    __tablename__ = "tenants"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    business_email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False,index=True)

    # 1:M Relationship back-reference compiled at runtime wrapper
    events: Mapped[list["Event"]] = relationship(
        "Event", 
        back_populates="tenant", 
        cascade="all, delete-orphan",
        passive_deletes=True
    )