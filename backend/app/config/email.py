import os
EMAIL_PROVIDER = os.getenv('EMAIL_PROVIDER', 'memory')
RESEND_API_KEY = os.getenv('RESEND_API_KEY', '')
BREVO_API_KEY = os.getenv('BREVO_API_KEY', '')
SMTP_HOST = os.getenv('SMTP_HOST', 'localhost')
SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
