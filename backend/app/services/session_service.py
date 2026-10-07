class SessionService:
    @staticmethod
    def get_session_info(session_id):
        return {'session_id': session_id, 'status': 'ACTIVE'}
