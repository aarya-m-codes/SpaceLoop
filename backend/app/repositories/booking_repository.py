from models import Booking
from backend.app.repositories.base import BaseRepository
class BookingRepository(BaseRepository):
    def __init__(self):
        super().__init__(Booking)
