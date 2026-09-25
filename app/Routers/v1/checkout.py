from fastapi import APIRouter, Depends, status, HTTPException, Request, Response
from fastapi_limiter.depends import RateLimiter
from fastapi_limiter import FastAPILimiter
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies import get_db, get_current_user
from app.models.user import User
from app.schemas.checkout import TicketReserveRequest, TicketReserveResponse, TicketRandomReserveRequest, TicketConfirmRequest
from app.services.checkout import CheckoutService

router = APIRouter(prefix="/checkout", tags=["Checkout (Resume Flex)"])

async def optional_rate_limiter(request: Request, response: Response):
    """Bypasses rate limiting if Redis is not running locally."""
    if getattr(FastAPILimiter, "redis", None):
        limiter = RateLimiter(times=5, seconds=10)
        return await limiter(request, response)
    return None

@router.post("/reserve", status_code=status.HTTP_200_OK, response_model=TicketReserveResponse, dependencies=[Depends(optional_rate_limiter)])
async def reserve_ticket_endpoint(
    payload: TicketReserveRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    The Core Flex: Reserves a specific VIP ticket using Optimistic Concurrency Control.
    safely handles massive parallel requests and locks the ticket for 2 minutes.
    """
    service = CheckoutService(db_session=db)
    
    try:
        ticket = await service.reserve_ticket(
            ticket_id=payload.ticket_id,
            user_id=current_user.id
        )
        return TicketReserveResponse(
            status="success",
            message="Ticket successfully reserved for 2 minutes pending confirmation.",
            ticket_id=ticket.id,
            reserved_at=str(ticket.reserved_at),
            expires_at=str(ticket.expires_at)
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

@router.post("/reserve-random", status_code=status.HTTP_200_OK, response_model=TicketReserveResponse, dependencies=[Depends(optional_rate_limiter)])
async def reserve_random_ticket_endpoint(
    payload: TicketRandomReserveRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    The General Admission Flow: Reserves any available GA ticket using PostgreSQL SKIP LOCKED.
    Locks the ticket for 1 minute.
    """
    service = CheckoutService(db_session=db)
    
    try:
        ticket = await service.reserve_random_ticket(
            event_id=payload.event_id,
            user_id=current_user.id
        )
        return TicketReserveResponse(
            status="success",
            message="General Admission Ticket successfully reserved for 1 minute pending confirmation.",
            ticket_id=ticket.id,
            reserved_at=str(ticket.reserved_at),
            expires_at=str(ticket.expires_at)
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
async def confirm_ticket_endpoint(
    payload: TicketConfirmRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Final Checkout: Confirms the ticket if the cart timer has not expired.
    Requires attendee details for VIPs, optional for GA.
    """
    service = CheckoutService(db_session=db)
    
    try:
        ticket = await service.confirm_ticket(
            ticket_id=payload.ticket_id,
            user_id=current_user.id,
            attendee_name=payload.attendee_name,
            attendee_age=payload.attendee_age
        )
        return {
            "status": "success", 
            "message": f"Ticket {ticket.id} permanently CONFIRMED for {payload.attendee_name or current_user.email}!"
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )
