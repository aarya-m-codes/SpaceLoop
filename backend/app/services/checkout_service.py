from backend.modules.bookings.pricing import PricingEngine
class CheckoutService:
    @staticmethod
    def calculate(base_rate, days=1, hours=0, student_discount=False):
        return PricingEngine.calculate_breakdown(base_rate, days, hours, student_discount)
