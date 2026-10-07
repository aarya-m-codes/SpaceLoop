from backend.core.database import db

class BaseRepository:
    def __init__(self, model):
        self.model = model
    def get_by_id(self, item_id):
        return db.session.get(self.model, item_id)
    def all(self):
        return self.model.query.all()

