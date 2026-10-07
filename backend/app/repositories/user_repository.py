from models import User
from backend.app.repositories.base import BaseRepository
class UserRepository(BaseRepository):
    def __init__(self):
        super().__init__(User)
    def find_by_email(self, email):
        return User.query.filter_by(email=email.lower().strip()).first()
