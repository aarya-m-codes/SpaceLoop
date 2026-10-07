from models import Space
from backend.app.repositories.base import BaseRepository
class SpaceRepository(BaseRepository):
    def __init__(self):
        super().__init__(Space)
