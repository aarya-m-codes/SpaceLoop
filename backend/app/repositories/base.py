class BaseRepository:
    def __init__(self, model):
        self.model = model
    def get_by_id(self, item_id):
        return self.model.query.get(item_id)
    def all(self):
        return self.model.query.all()
