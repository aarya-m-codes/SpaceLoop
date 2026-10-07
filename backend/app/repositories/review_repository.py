from models import Review
from backend.app.repositories.base import BaseRepository
class ReviewRepository(BaseRepository):
    def __init__(self):
        super().__init__(Review)
