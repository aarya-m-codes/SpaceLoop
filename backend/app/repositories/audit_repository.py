from models import AuditLog
from backend.app.repositories.base import BaseRepository
class AuditRepository(BaseRepository):
    def __init__(self):
        super().__init__(AuditLog)
