from models import FraudEvent
from backend.app.repositories.base import BaseRepository
class FraudRepository(BaseRepository):
    def __init__(self):
        super().__init__(FraudEvent)
