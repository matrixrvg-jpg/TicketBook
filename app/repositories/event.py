
from typing import Type

from app.repositories.base import BaseReadRepository, BaseWriteRepository
from app.models.event import Event



class GetEvents(BaseReadRepository[Event]):
    def __init__(self, db_session):
        super().__init__(Event, db_session)


class CreateEvent(BaseWriteRepository[Event]):
    def __init__(self, db_session):
        super().__init__(Event, db_session)
