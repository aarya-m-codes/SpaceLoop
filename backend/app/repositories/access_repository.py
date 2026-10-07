from models import AccessLog
from backend.app.repositories.base import BaseRepository
class AccessRepository(BaseRepository):
    def __init__(self):
        super().__init__(AccessLog)
