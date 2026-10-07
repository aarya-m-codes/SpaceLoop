from backend.core.database import db
def get_session():
    return db.session
