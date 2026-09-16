from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies import get_db, get_current_user
from app.models.user import User
from app.schemas.checkout import TicketReserveRequest, TicketReserveResponse
from app.services.checkout import CheckoutService

router = APIRouter(prefix="/checkout", tags=["Checkout (Resume Flex)"])

@router.post("/reserve", status_code=status.HTTP_200_OK, response_model=TicketReserveResponse)
async def reserve_ticket_endpoint(
    payload: TicketReserveRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    The Core Flex: Reserves a ticket using Optimistic Concurrency Control.
    Safely handles massive parallel requests for the same event.
    """
    service = CheckoutService(db_session=db)
    
    try:
        ticket = await service.reserve_ticket(
            ticket_id=payload.ticket_id,
            user_id=current_user.id
        )
        return TicketReserveResponse(
            status="success",
            message="Ticket successfully reserved for 10 minutes pending payment.",
            ticket_id=ticket.id,
            reserved_at=str(ticket.reserved_at)
        )
    except ValueError as e:
        # A controlled error (e.g., Sold Out, or Concurrency Limit Reached)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except Exception as e:
        # Prevent leaking raw DB errors in prod, but expose for debugging now
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )

from app.schemas.checkout import TicketRandomReserveRequest

@router.post("/reserve-random", status_code=status.HTTP_200_OK, response_model=TicketReserveResponse)
async def reserve_random_ticket_endpoint(
    payload: TicketRandomReserveRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    The General Admission Flow: Reserves any available ticket using PostgreSQL SKIP LOCKED.
    """
    service = CheckoutService(db_session=db)
    
    try:
        ticket = await service.reserve_random_ticket(
            event_id=payload.event_id,
            user_id=current_user.id
        )
        return TicketReserveResponse(
            status="success",
            message="General Admission Ticket successfully reserved for 10 minutes pending payment.",
            ticket_id=ticket.id,
            reserved_at=str(ticket.reserved_at)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )

@router.post("/confirm", status_code=status.HTTP_200_OK)
async def mock_stripe_webhook(
    ticket_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Mocks a successful payment webhook from Stripe.
    """
    from app.models.ticket import Ticket
    from sqlalchemy import select, update
    
    # Simple direct update for the mock
    stmt = (
        update(Ticket)
        .where(Ticket.id == ticket_id)
        .values(status="CONFIRMED")
    )
    await db.execute(stmt)
    await db.commit()
    
    return {"status": "success", "message": f"Ticket {ticket_id} confirmed via mock payment."}
