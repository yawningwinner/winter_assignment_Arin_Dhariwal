from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # Database settings
    DATABASE_URL: str = "postgresql://merchant_user:merchant_pass@localhost:5432/merchant_db"
    
    # Late Night Trading Pattern
    LATE_NIGHT_START: int = 23
    LATE_NIGHT_END: int = 4
    LATE_NIGHT_VOLUME_THRESHOLD: float = 0.70
    MIN_DAILY_TRANSACTIONS: int = 20
    PATTERN_DURATION_DAYS: int = 14
    
    # Sudden Activity Spike Pattern
    NORMAL_DAILY_MIN: int = 10
    NORMAL_DAILY_MAX: int = 20
    SPIKE_THRESHOLD: int = 200
    SPIKE_DURATION_DAYS: int = 3
    
    # Split Transaction Pattern
    SPLIT_AMOUNT_MIN: float = 50000.0
    SPLIT_AMOUNT_MAX: float = 100000.0
    MIN_SPLITS: int = 5
    SPLIT_TIME_WINDOW: int = 30
    
    # Round Amount Pattern
    ROUND_AMOUNTS: List[int] = [9999, 19999, 29999]
    ROUND_AMOUNT_THRESHOLD: float = 0.70
    
    # Customer Concentration Pattern
    MIN_CUSTOMERS: int = 5
    MAX_CUSTOMERS: int = 10
    VOLUME_CONCENTRATION_THRESHOLD: float = 0.80
    CONCENTRATION_TIME_WINDOW: int = 24
    
    # Data Generation
    FRAUD_MERCHANT_PERCENTAGE: float = 0.20
    NUM_MERCHANTS: int = 100
    
    # Processing
    BATCH_SIZE: int = 1000
    
    class Config:
        env_file = ".env"

settings = Settings() 