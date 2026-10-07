from models import EscrowTransaction
from backend.app.repositories.base import BaseRepository
class PaymentRepository(BaseRepository):
    def __init__(self):
        super().__init__(EscrowTransaction)
