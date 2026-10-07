from backend.modules.bookings.service import BookingService
class AccessService:
    @staticmethod
    def checkin_pin(booking_id, user_id, pin, lat, lng):
        return BookingService.checkin_with_pin(booking_id, user_id, pin, lat, lng)
