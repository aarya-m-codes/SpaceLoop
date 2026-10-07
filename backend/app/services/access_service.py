from backend.modules.bookings.service import BookingService

class AccessService:
    @staticmethod
    def checkin(booking_id, current_user, pin=None, qr_token=None, lat=None, lng=None, photos=None):
        return BookingService.check_in_booking(
            booking_id=booking_id,
            current_user=current_user,
            lat=lat,
            lng=lng,
            photos=photos,
            arrival_pin=pin,
            qr_token=qr_token
        )
