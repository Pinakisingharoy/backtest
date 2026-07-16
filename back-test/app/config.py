import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

class Config:
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/backtest")
    API_VERSION = "v1"
    API_TITLE = "Trading Analytics API"
    API_DESCRIPTION = "API for trading analytics and strategy backtesting"
    ALLOWED_ORIGINS = ["http://localhost:3000", "http://localhost:3001"]
    TOP_N_SYMBOLS = 10
    TIMEZONE = "Asia/Kolkata"
    MAX_UPLOAD_SIZE = 10 * 1024 * 1024
    BASE_DIR = Path(__file__).resolve().parent
    OUTPUT_DATA_DIR = BASE_DIR / "exports"

config = Config()