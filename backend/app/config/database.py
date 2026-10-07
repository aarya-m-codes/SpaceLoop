import os
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///instance/spaceloop_dev.db')
SQLALCHEMY_TRACK_MODIFICATIONS = False
