import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv('SECRET_KEY', 'dev-only-insecure-key-change-in-production')
FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
PORT = int(os.getenv('PORT', 5000))
DATABASE_PATH = os.getenv('DATABASE_PATH', 'loja.db')

VALID_CATEGORIES = ['informatica', 'moveis', 'vestuario', 'geral', 'eletronicos', 'livros']
VALID_ORDER_STATUSES = ['pendente', 'aprovado', 'enviado', 'entregue', 'cancelado']

DISCOUNT_TIER_HIGH = 10000
DISCOUNT_TIER_MID = 5000
DISCOUNT_TIER_LOW = 1000
DISCOUNT_RATE_HIGH = 0.10
DISCOUNT_RATE_MID = 0.05
DISCOUNT_RATE_LOW = 0.02
