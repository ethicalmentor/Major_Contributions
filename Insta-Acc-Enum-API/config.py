import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    USERNAME = os.getenv('Your_Username')
    PASSWORD = os.getenv('Your_Password')
    CACHE_TTL = int(os.getenv('CACHE_TTL', 1800))
    MAX_WORKERS = int(os.getenv('MAX_WORKERS', 5))
