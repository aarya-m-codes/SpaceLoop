import os
STORAGE_BACKEND = os.getenv('STORAGE_BACKEND', 'local')
UPLOAD_DIR = os.getenv('STORAGE_LOCAL_DIR', 'uploads')
