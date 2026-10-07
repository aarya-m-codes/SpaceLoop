from models import Space, db
class ListingService:
    @staticmethod
    def get_active_listings():
        return Space.query.filter_by(is_active=True).all()
