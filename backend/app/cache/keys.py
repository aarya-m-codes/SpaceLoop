def booking_lock_key(booking_id):
    return f"lock:booking:{booking_id}"
