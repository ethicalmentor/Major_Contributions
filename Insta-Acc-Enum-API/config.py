import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    USERNAME = os.getenv('_mystrical_guy')
    PASSWORD = os.getenv('Sample@2025')
    CACHE_TTL = int(os.getenv('CACHE_TTL', 1800))
    MAX_WORKERS = int(os.getenv('MAX_WORKERS', 5))
