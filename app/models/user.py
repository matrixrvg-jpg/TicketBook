from typing import TYPE_CHECKING

from sqlalchemy import String, Integer, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

if TYPE_CHECKING:
    from app.models.tenant import Tenant
    from app.models.ticket import Ticket

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=True)
    
    # RBAC Guardrail: e.g., "ORGANIZER", "ATTENDEE", "SUPER_ADMIN"
    role: Mapped[str] = mapped_column(String(50), server_default="ATTENDEE", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant")
    tickets:Mapped[list["Ticket"]]=relationship(
        "Ticket",
        back_populates="User",
        cascade="all, delete-orphan",
        passive_deletes=True
    )