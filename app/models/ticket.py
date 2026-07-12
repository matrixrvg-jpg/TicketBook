import datetime
from typing import TYPE_CHECKING # Avoids circular imports at runtime
from sqlalchemy import String, Integer, ForeignKey, DateTime , Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

if TYPE_CHECKING:
    from app.models.event import Event

from app.models.user import User 

class Ticket(Base):
    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    event_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("events.id", ondelete="CASCADE"), 
        nullable=False,
        index=True
    )
    user_id:Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,  # Nullable because a ticket may not be reserved yet
        index=True
    )
    #sitting locations
    location: Mapped[str | None] = mapped_column(String(100), nullable=True)
    section: Mapped[str | None] = mapped_column(String(50), nullable=True)
    row: Mapped[str | None] = mapped_column(String(20), nullable=True)
    seat_number: Mapped[str | None] = mapped_column(String(20), nullable=True)
    
    # State Engine Transition Matrix: AVAILABLE -> RESERVED -> CONFIRMED
    status: Mapped[str] = mapped_column(String(20), server_default="AVAILABLE", nullable=False, index=True)
    reserved_at: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False,index=True)

    
    # HIGH-CONCURRENCY ANCHOR: The OCC Version Tracking Token
    # Every update statement must explicitly verify that version_id matches the read state.
    version_id: Mapped[int] = mapped_column(Integer, server_default="1", nullable=False)

    # Relationships
    event: Mapped["Event"] = relationship("Event", back_populates="tickets")
    User: Mapped["User"] = relationship("User", back_populates="tickets")
