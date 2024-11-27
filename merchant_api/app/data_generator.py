from merchant_api.app.config import settings

class DataGenerator:
    def __init__(self):
        self.NUM_MERCHANTS = settings.NUM_MERCHANTS
        
        # Late Night Trading Pattern
        self.LATE_NIGHT_CONFIG = {
            "time_window": (settings.LATE_NIGHT_START, settings.LATE_NIGHT_END),
            "volume_percentage": settings.LATE_NIGHT_VOLUME_THRESHOLD,
            "min_daily_transactions": settings.MIN_DAILY_TRANSACTIONS,
            "duration_days": settings.PATTERN_DURATION_DAYS
        }
        
        # Sudden Activity Spike Pattern
        self.SPIKE_CONFIG = {
            "normal_daily_txns": (settings.NORMAL_DAILY_MIN, settings.NORMAL_DAILY_MAX),
            "spike_daily_txns": (settings.SPIKE_THRESHOLD, settings.SPIKE_THRESHOLD + 100),
            "spike_duration": settings.SPIKE_DURATION_DAYS
        }
        
        # Split Transaction Pattern
        self.SPLIT_CONFIG = {
            "original_amount_range": (settings.SPLIT_AMOUNT_MIN, settings.SPLIT_AMOUNT_MAX),
            "split_count": settings.MIN_SPLITS,
            "time_window_minutes": settings.SPLIT_TIME_WINDOW
        }
        
        # Round Amount Pattern
        self.ROUND_CONFIG = {
            "amounts": settings.ROUND_AMOUNTS,
            "frequency": settings.ROUND_AMOUNT_THRESHOLD
        }
        
        # Customer Concentration Pattern
        self.CUSTOMER_CONCENTRATION_CONFIG = {
            "customer_count": settings.MIN_CUSTOMERS,
            "volume_concentration": settings.VOLUME_CONCENTRATION_THRESHOLD
        }