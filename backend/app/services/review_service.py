from models import Review
class ReviewService:
    @staticmethod
    def get_reviews_for_space(space_id):
        return Review.query.filter_by(space_id=space_id).all()
