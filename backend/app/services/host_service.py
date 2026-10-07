from models import Space, Booking
class HostService:
    @staticmethod
    def get_host_metrics(host_id):
        listings = Space.query.filter_by(host_id=host_id).all()
        return {'listings_count': len(listings)}
