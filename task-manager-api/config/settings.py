import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-only-change-me')
DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///tasks.db')
DEBUG = os.environ.get('DEBUG', 'false').lower() == 'true'

EMAIL_USER = os.environ.get('EMAIL_USER')
EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD')
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
