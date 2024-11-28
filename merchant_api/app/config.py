from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database settings
    DATABASE_URL: str = "postgresql://merchant_user@localhost:5432/merchant_db"
    
    # Data generation settings
    NUM_MERCHANTS: int = 100
    NUM_TRANSACTIONS_PER_MERCHANT: int = 1000
    FRAUD_RATIO: float = 0.03  # 3% fraud transactions
    FRAUD_MERCHANT_PERCENTAGE: float = 0.10  # 10% of merchants will be fraudulent
    BATCH_SIZE: int = 100  # Number of transactions to generate in batch
    
    # Transaction amount ranges
    MIN_TRANSACTION_AMOUNT: float = 10.0
    MAX_TRANSACTION_AMOUNT: float = 5000.0
    FRAUD_AMOUNT_MULTIPLIER: float = 5.0  # Fraudulent transactions will be 5x normal max
    SPLIT_AMOUNT_MIN: float = 2000.0  # Minimum amount for split transactions
    SPLIT_AMOUNT_MAX: float = 10000.0  # Maximum amount for split transactions
    MIN_SPLITS: int = 2  # Minimum number of split transactions
    MAX_SPLITS: int = 5  # Maximum number of split transactions
    SPLIT_TIME_WINDOW: int = 30  # Minutes within which split transactions occur
    
    # Rounding patterns
    ROUND_AMOUNTS: list[int] = [100, 500, 1000, 2000, 5000]  # Common round amounts
    ROUND_AMOUNT_THRESHOLD: float = 0.7  # Probability of rounding amounts
    
    # Time-based settings
    DAYS_OF_HISTORY: int = 90  # Generate 90 days of transaction history
    BUSINESS_HOURS_START: int = 8  # 8 AM
    BUSINESS_HOURS_END: int = 18   # 6 PM
    PATTERN_DURATION_DAYS: int = 7  # Duration of fraud patterns
    SPIKE_DURATION_DAYS: int = 3   # Duration of volume spikes
    
    # Late night patterns
    LATE_NIGHT_START: int = 23  # 11 PM
    LATE_NIGHT_END: int = 4    # 4 AM
    LATE_NIGHT_VOLUME_THRESHOLD: int = 5  # Number of transactions to trigger volume alert
    MIN_DAILY_TRANSACTIONS: int = 5
    
    # Volume and concentration patterns
    MIN_CUSTOMERS: int = 3  # Minimum number of unique customers
    VOLUME_CONCENTRATION_THRESHOLD: float = 0.7  # Threshold for customer concentration
    CONCENTRATION_TIME_WINDOW: int = 24  # Hours for concentration window
    
    # Normal transaction patterns
    NORMAL_DAILY_MIN: int = 3
    NORMAL_DAILY_MAX: int = 15
    SPIKE_THRESHOLD: int = 50  # Transactions to consider a spike
    
    # API settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Merchant API"
    
    class Config:
        env_file = ".env"

settings = Settings() 