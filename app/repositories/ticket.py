
from app.repositories.base import BaseReadRepository
from app.models.ticket import Ticket # Import the Ticket model

class TicketRepository(BaseReadRepository[Ticket]): # Bind to Ticket
    def __init__(self, db_session):
        super().__init__(model=Ticket, db_session=db_session)

    # get_by_id is already here, ready to use!


        

