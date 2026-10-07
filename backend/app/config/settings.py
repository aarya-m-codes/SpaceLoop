import os
SECRET_KEY = os.getenv('SECRET_KEY', 'default-dev-secret')
DEBUG = os.getenv('FLASK_ENV') == 'development'
PORT = int(os.getenv('PORT', 5000))
