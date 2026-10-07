from backend.app.api.v1.auth import auth_bp
from backend.app.api.v1.spaces import spaces_bp
from backend.app.api.v1.bookings import bookings_bp
from backend.app.api.v1.escrow import escrow_bp
from backend.app.api.v1.ai import ai_bp
from backend.app.api.v1.trust_safety import trust_safety_bp
from backend.app.api.v1.fraud import fraud_bp
from backend.app.api.v1.verification import verification_bp
from backend.app.api.v1.admin import admin_bp

def register_all_blueprints(app):
    app.register_blueprint(auth_bp, url_prefix='/api/v1/auth')
    app.register_blueprint(admin_bp, url_prefix='/api/v1/admin')
    app.register_blueprint(spaces_bp, url_prefix='/api/v1/spaces')
    app.register_blueprint(bookings_bp, url_prefix='/api/v1/bookings')
    app.register_blueprint(escrow_bp, url_prefix='/api/v1/escrow')
    app.register_blueprint(ai_bp, url_prefix='/api/v1/ai')
    app.register_blueprint(trust_safety_bp, url_prefix='/api/v1/trust-safety')
    app.register_blueprint(fraud_bp, url_prefix='/api/v1/fraud')
    app.register_blueprint(verification_bp, url_prefix='/api/v1/verify')
