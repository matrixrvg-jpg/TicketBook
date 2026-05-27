import datetime
from xmlrpc.client import Boolean
from sqlalchemy import String, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from typing import TYPE_CHECKING # Avoids circular imports at runtime

if TYPE_CHECKING:
    from app.models.tenant import Tenant  
    from app.models.ticket import Ticket

class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    tenant_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("tenants.id", ondelete="CASCADE"), 
        nullable=False,
        index=True
    )
    category:Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    date: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    base_price:Mapped[int] = mapped_column(Integer,nullable=False)
    start_time :Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time:Mapped[datetime.datetime]= mapped_column(DateTime(timezone=True),nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False,index=True)

    
    # OCP Guardrail: Stores dynamic fields (e.g., {"github_url": "string", "tshirt_size": "enum"})
    custom_form_schema: Mapped[dict] = mapped_column(JSONB, server_default="{}", nullable=False)

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="events")
    tickets: Mapped[list["Ticket"]] = relationship(
        "Ticket", 
        back_populates="event", 
        cascade="all, delete-orphan",
        passive_deletes=True
    )