from models import User, Space, Booking, EscrowTransaction
class AdminService:
    @staticmethod
    def get_overview_metrics():
        return {
            'users_count': User.query.count(),
            'spaces_count': Space.query.count(),
            'bookings_count': Booking.query.count()
        }
