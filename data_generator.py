import random
from datetime import datetime, timedelta
import uuid
from typing import List, Dict, Tuple
import json
from sqlalchemy.orm import Session
from merchant_api.app.models import Merchant, Transaction
import logging
from merchant_api.app.config import settings
from merchant_api.app.db import SessionLocal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataGenerator:
    def __init__(self):
        # Existing business configurations
        self.BUSINESS_TYPES = ["Electronics", "Fashion", "Grocery", "Furniture", "Automotive"]
        self.BUSINESS_MODELS = ["Online", "Offline", "Hybrid"]
        self.PRODUCT_CATEGORIES = ["Electronics", "Clothing", "Food", "Home", "Auto Parts"]
        self.CITIES = ["Mumbai", "Delhi", "Bangalore", "Chennai", "Kolkata"]
        self.STATES = ["Maharashtra", "Delhi", "Karnataka", "Tamil Nadu", "West Bengal"]
        self.BANKS = ["SBI", "HDFC", "ICICI", "Axis", "PNB"]
        self.PAYMENT_METHODS = ["Credit Card", "Debit Card", "UPI", "Net Banking", "Wallet"]
        self.PLATFORMS = ["Web", "Mobile App", "POS"]
        self.TRANSACTION_STATUS = ["completed", "failed", "refunded"]
        self.DEVICE_TYPES = ["Android", "iOS", "Windows", "MacOS", "Linux"]
        self.LOCATIONS = ["Mumbai", "Delhi", "Bangalore", "Chennai", "Kolkata"]

        # Date range
        self.end_date = datetime.now()
        self.start_date = self.end_date - timedelta(days=30)

        # Import settings
        from merchant_api.app.config import settings

        # Basic settings
        self.NUM_MERCHANTS = settings.NUM_MERCHANTS
        self.FRAUD_MERCHANT_PERCENTAGE = settings.FRAUD_MERCHANT_PERCENTAGE
        self.BATCH_SIZE = settings.BATCH_SIZE

        # Late Night Trading Pattern
        self.LATE_NIGHT_CONFIG = {
            "start_hour": settings.LATE_NIGHT_START,
            "end_hour": settings.LATE_NIGHT_END,
            "volume_threshold": settings.LATE_NIGHT_VOLUME_THRESHOLD,
            "min_daily_txns": settings.MIN_DAILY_TRANSACTIONS,
            "pattern_duration": settings.PATTERN_DURATION_DAYS
        }
        
        # Sudden Activity Spike Pattern
        self.SPIKE_CONFIG = {
            "normal_daily_min": settings.NORMAL_DAILY_MIN,
            "normal_daily_max": settings.NORMAL_DAILY_MAX,
            "spike_threshold": settings.SPIKE_THRESHOLD,
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
            "volume_concentration": settings.VOLUME_CONCENTRATION_THRESHOLD,
            "time_window": settings.CONCENTRATION_TIME_WINDOW
        }

    def generate_merchant_id(self) -> str:
        """Generate merchant ID in format M1XXXXXX"""
        return f"M1{str(random.randint(0, 999999)).zfill(6)}"

    def generate_pan_number(self) -> str:
        """Generate a valid format PAN number"""
        alphabets = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=5))
        numbers = ''.join(random.choices('0123456789', k=4))
        return f"{alphabets}{numbers}{''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=1))}"

    def generate_bank_account(self) -> str:
        """Generate a bank account number"""
        return ''.join(random.choices('0123456789', k=12))

    def generate_merchant_profile(self) -> Dict:
        """Generate a single merchant profile"""
        merchant_id = f"M{random.randint(1000000, 9999999)}"
        return {
            "merchant_id": merchant_id,
            "business_name": f"Business_{merchant_id}",
            "business_type": random.choice(self.BUSINESS_TYPES),
            "business_model": random.choice(self.BUSINESS_MODELS),
            "registration_date": self.start_date - timedelta(days=random.randint(30, 365)),
            "city": random.choice(self.CITIES),
            "state": random.choice(self.STATES),
            "bank_name": random.choice(self.BANKS),
            "account_number": f"ACC{random.randint(10000000, 99999999)}",
            "status": "active"
        }

    def generate_merchant_name(self) -> str:
        """Generate a realistic business name"""
        prefixes = ["Global", "Prime", "Elite", "Star", "Royal", "Indian", "Metro"]
        suffixes = ["Trading", "Enterprises", "Solutions", "Services", "Mart", "Store", "Retail"]
        middle = ["Business", "Commercial", "Retail", "Market"]
        
        # 50% chance to include middle name
        if random.random() < 0.5:
            return f"{random.choice(prefixes)} {random.choice(middle)} {random.choice(suffixes)}"
        return f"{random.choice(prefixes)} {random.choice(suffixes)}"

    def generate_transaction_id(self, timestamp: datetime) -> str:
        """Generate a unique transaction ID using timestamp and UUID"""
        # Use uuid4 to generate a random UUID and take first 8 chars
        uuid_suffix = str(uuid.uuid4())[:8]
        return f"TXN{timestamp.strftime('%Y%m%d')}{uuid_suffix}"

    def generate_device_id(self) -> str:
        """Generate device ID"""
        return f"DEV-{''.join(random.choices('0123456789ABCDEF', k=12))}"

    def generate_normal_transaction(self, merchant_id: str, product_category: str) -> Dict:
        """Generate a normal transaction pattern"""
        # Normal business hours (9 AM to 9 PM)
        timestamp = self.start_date + timedelta(
            days=random.randint(0, 30),
            hours=random.randint(9, 21),
            minutes=random.randint(0, 59)
        )
        
        amount = random.uniform(100, 1000)
        device_id = self.generate_device_id()
        customer_location = random.choice(self.LOCATIONS)
        
        # Calculate risk flags
        velocity_flag = False
        amount_flag = amount > 800  # Flag high amounts
        time_flag = False  # Normal business hours
        device_flag = random.random() < 0.05  # 5% chance of device flag
        
        return {
            # Basic Transaction Info
            "transaction_id": self.generate_transaction_id(timestamp),
            "merchant_id": merchant_id,
            "timestamp": timestamp,
            "amount": amount,
            
            # Customer Info
            "customer_id": str(uuid.uuid4()),
            "device_id": device_id,
            "customer_location": customer_location,
            
            # Transaction Details
            "payment_method": random.choice(self.PAYMENT_METHODS),
            "status": "completed",  # Most normal transactions complete
            "product_category": product_category,
            "platform": random.choice(self.PLATFORMS),
            
            # Risk Indicators
            "velocity_flag": velocity_flag,
            "amount_flag": amount_flag,
            "time_flag": time_flag,
            "device_flag": device_flag
        }

    def generate_fraudulent_transactions(self, merchant_id: str, product_category: str) -> List[Dict]:
        """Generate transactions with fraud patterns"""
        transactions = []
        fraud_type = random.choice(["late_night", "high_velocity", "customer_concentration"])
        
        if fraud_type == "late_night":
            # Generate late night transactions (11 PM to 4 AM)
            for _ in range(random.randint(3, 7)):
                timestamp = self.start_date + timedelta(
                    days=random.randint(0, 30),
                    hours=random.randint(23, 24) if random.random() < 0.5 else random.randint(0, 4),
                    minutes=random.randint(0, 59)
                )
                
                amount = random.uniform(1000, 5000)
                device_id = self.generate_device_id()
                
                transactions.append({
                    # Basic Transaction Info
                    "transaction_id": self.generate_transaction_id(timestamp),
                    "merchant_id": merchant_id,
                    "timestamp": timestamp,
                    "amount": amount,
                    
                    # Customer Info
                    "customer_id": str(uuid.uuid4()),
                    "device_id": device_id,
                    "customer_location": random.choice(self.LOCATIONS),
                    
                    # Transaction Details
                    "payment_method": random.choice(self.PAYMENT_METHODS),
                    "status": "completed",
                    "product_category": product_category,
                    "platform": random.choice(self.PLATFORMS),
                    
                    # Risk Indicators
                    "velocity_flag": False,
                    "amount_flag": amount > 800,
                    "time_flag": True,  # Late night flag
                    "device_flag": random.random() < 0.20  # Higher chance of device flag
                })
                
        elif fraud_type == "high_velocity":
            # Generate multiple transactions within a short time window
            base_date = self.start_date + timedelta(days=random.randint(0, 30))
            device_id = self.generate_device_id()  # Same device for velocity
            customer_id = str(uuid.uuid4())  # Same customer for velocity
            
            for i in range(random.randint(5, 8)):
                timestamp = base_date + timedelta(minutes=i*2)  # Transactions 2 minutes apart
                amount = random.uniform(500, 2000)
                
                transactions.append({
                    # Basic Transaction Info
                    "transaction_id": self.generate_transaction_id(timestamp),
                    "merchant_id": merchant_id,
                    "timestamp": timestamp,
                    "amount": amount,
                    
                    # Customer Info
                    "customer_id": customer_id,
                    "device_id": device_id,
                    "customer_location": random.choice(self.LOCATIONS),
                    
                    # Transaction Details
                    "payment_method": random.choice(self.PAYMENT_METHODS),
                    "status": "completed",
                    "product_category": product_category,
                    "platform": random.choice(self.PLATFORMS),
                    
                    # Risk Indicators
                    "velocity_flag": True,
                    "amount_flag": amount > 800,
                    "time_flag": False,
                    "device_flag": True
                })
                
        else:  # customer_concentration
            # Generate multiple transactions from same customer
            customer_id = "ConcentratedCustomer"
            device_id = self.generate_device_id()
            base_date = self.start_date + timedelta(days=random.randint(0, 30))
            
            for i in range(random.randint(8, 12)):
                timestamp = base_date + timedelta(hours=random.randint(0, 23))
                amount = random.uniform(2000, 6000)
                
                transactions.append({
                    # Basic Transaction Info
                    "transaction_id": self.generate_transaction_id(timestamp),
                    "merchant_id": merchant_id,
                    "timestamp": timestamp,
                    "amount": amount,
                    
                    # Customer Info
                    "customer_id": customer_id,
                    "device_id": device_id,
                    "customer_location": random.choice(self.LOCATIONS),
                    
                    # Transaction Details
                    "payment_method": random.choice(self.PAYMENT_METHODS),
                    "status": "completed",
                    "product_category": product_category,
                    "platform": random.choice(self.PLATFORMS),
                    
                    # Risk Indicators
                    "velocity_flag": True,
                    "amount_flag": True,
                    "time_flag": False,
                    "device_flag": True
                })
                
        return transactions

    def generate_dataset(self) -> Tuple[List[Dict], List[Dict]]:
        """Generate complete dataset with mix of normal and fraudulent transactions"""
        session = SessionLocal()
        try:
            # 1. Generate merchants first
            merchants = []
            for _ in range(self.NUM_MERCHANTS):
                merchant = self.generate_merchant_profile()
                merchants.append(merchant)
                
            # 2. Save merchants to database first
            for merchant in merchants:
                merchant_obj = Merchant(**merchant)
                session.add(merchant_obj)
            session.commit()
            
            # 3. Generate transactions
            all_transactions = []
            fraud_count = int(len(merchants) * self.FRAUD_MERCHANT_PERCENTAGE)
            fraud_merchants = random.sample(merchants, fraud_count)
            
            for merchant in merchants:
                if merchant in fraud_merchants:
                    # Generate fraudulent transactions with random pattern
                    pattern = random.choice([
                        self._generate_late_night_pattern,
                        self._generate_spike_pattern,
                        self._generate_split_pattern,
                        self._generate_round_amount_pattern,
                        self._generate_concentration_pattern
                    ])
                    txns = pattern(merchant)
                else:
                    txns = self.generate_normal_transactions(merchant)
                all_transactions.extend(txns)
            
            # 4. Save transactions in batches
            for i in range(0, len(all_transactions), self.BATCH_SIZE):
                batch = all_transactions[i:i + self.BATCH_SIZE]
                transaction_objs = [Transaction(**txn) for txn in batch]
                session.bulk_save_objects(transaction_objs)
                session.commit()
            
            return merchants, all_transactions
            
        except Exception as e:
            logger.error(f"Error generating data: {str(e)}")
            session.rollback()
            raise
        finally:
            session.close()

    def _generate_late_night_pattern(self, merchant: Dict) -> List[Dict]:
        transactions = []
        current_date = self.start_date
        
        for _ in range(self.LATE_NIGHT_CONFIG["pattern_duration"]):
            # Generate daily transactions
            daily_txn_count = max(self.LATE_NIGHT_CONFIG["min_daily_txns"], 
                                random.randint(20, 40))
            
            # Calculate how many should be late night
            night_txn_count = int(daily_txn_count * self.LATE_NIGHT_CONFIG["volume_threshold"])
            
            # Generate late night transactions
            for _ in range(night_txn_count):
                hour = random.choice([23, 0, 1, 2, 3, 4])
                timestamp = current_date.replace(
                    hour=hour,
                    minute=random.randint(0, 59)
                )
                
                transactions.append(self.generate_transaction(
                    merchant["merchant_id"],
                    timestamp,
                    amount=random.uniform(1000, 5000)  # Higher amounts at night
                ))
            
            # Generate regular transactions
            for _ in range(daily_txn_count - night_txn_count):
                hour = random.randint(9, 22)
                timestamp = current_date.replace(
                    hour=hour,
                    minute=random.randint(0, 59)
                )
                
                transactions.append(self.generate_transaction(
                    merchant["merchant_id"],
                    timestamp
                ))
            
            current_date += timedelta(days=1)
        
        return transactions

    def _generate_spike_pattern(self, merchant: Dict) -> List[Dict]:
        """Generate sudden activity spike pattern"""
        transactions = []
        current_date = self.start_date
        days_until_spike = random.randint(5, 10)
        
        while current_date <= self.end_date:
            if days_until_spike == 0:
                # Generate spike
                for _ in range(self.SPIKE_CONFIG["spike_threshold"]):
                    timestamp = current_date + timedelta(
                        minutes=random.randint(0, 1440)  # Throughout the day
                    )
                    transactions.append(self.generate_transaction(
                        merchant["merchant_id"],
                        timestamp
                    ))
                days_until_spike = 14  # Reset spike counter
            else:
                # Normal day - use min and max from config
                normal_txns = random.randint(
                    self.SPIKE_CONFIG["normal_daily_min"],
                    self.SPIKE_CONFIG["normal_daily_max"]
                )
                for _ in range(normal_txns):
                    timestamp = current_date + timedelta(
                        minutes=random.randint(0, 1440)
                    )
                    transactions.append(self.generate_transaction(
                        merchant["merchant_id"],
                        timestamp
                    ))
            
            current_date += timedelta(days=1)
            days_until_spike -= 1
        
        return transactions

    def _generate_split_pattern(self, merchant: Dict) -> List[Dict]:
        """Generate split transaction pattern"""
        transactions = []
        current_date = self.start_date
        
        while current_date <= self.end_date:
            # Randomly decide if we'll generate splits today
            if random.random() < 0.3:  # 30% chance of split transactions per day
                # Generate original large amount
                original_amount = random.uniform(
                    self.SPLIT_CONFIG["original_amount_range"][0],
                    self.SPLIT_CONFIG["original_amount_range"][1]
                )
                
                # Split into smaller transactions
                split_count = self.SPLIT_CONFIG["split_count"]
                split_amount = original_amount / split_count
                
                # Generate splits within time window
                base_time = current_date.replace(
                    hour=random.randint(9, 17),
                    minute=random.randint(0, 59)
                )
                
                customer_id = f"CUST{random.randint(1000, 9999)}"
                
                for i in range(split_count):
                    timestamp = base_time + timedelta(
                        minutes=random.randint(1, self.SPLIT_CONFIG["time_window_minutes"])
                    )
                    
                    transactions.append(self.generate_transaction(
                        merchant["merchant_id"],
                        timestamp,
                        amount=split_amount,
                        customer_id=customer_id  # Same customer for splits
                    ))
            
            # Generate some normal transactions too
            for _ in range(random.randint(5, 15)):
                hour = random.randint(9, 20)
                timestamp = current_date.replace(
                    hour=hour,
                    minute=random.randint(0, 59)
                )
                transactions.append(self.generate_transaction(
                    merchant["merchant_id"],
                    timestamp
                ))
            
            current_date += timedelta(days=1)
        
        return transactions

    def _generate_round_amount_pattern(self, merchant: Dict) -> List[Dict]:
        """Generate round amount pattern"""
        transactions = []
        current_date = self.start_date
        
        while current_date <= self.end_date:
            daily_txn_count = random.randint(10, 30)
            round_txn_count = int(daily_txn_count * self.ROUND_CONFIG["frequency"])
            
            # Generate round amount transactions
            for _ in range(round_txn_count):
                amount = random.choice(self.ROUND_CONFIG["amounts"])
                hour = random.randint(9, 20)
                timestamp = current_date.replace(
                    hour=hour,
                    minute=random.randint(0, 59)
                )
                transactions.append(self.generate_transaction(
                    merchant["merchant_id"],
                    timestamp,
                    amount=amount
                ))
            
            # Generate normal transactions
            for _ in range(daily_txn_count - round_txn_count):
                hour = random.randint(9, 20)
                timestamp = current_date.replace(
                    hour=hour,
                    minute=random.randint(0, 59)
                )
                transactions.append(self.generate_transaction(
                    merchant["merchant_id"],
                    timestamp
                ))
            
            current_date += timedelta(days=1)
        
        return transactions

    def _generate_concentration_pattern(self, merchant: Dict) -> List[Dict]:
        """Generate customer concentration pattern"""
        transactions = []
        current_date = self.start_date
        
        # Generate a small set of concentrated customers
        concentrated_customers = [
            f"CUST{random.randint(1000, 9999)}"
            for _ in range(self.CUSTOMER_CONCENTRATION_CONFIG["customer_count"])
        ]
        
        while current_date <= self.end_date:
            daily_txn_count = random.randint(20, 40)
            concentrated_txn_count = int(daily_txn_count * 
                                       self.CUSTOMER_CONCENTRATION_CONFIG["volume_concentration"])
            
            # Generate transactions for concentrated customers
            for _ in range(concentrated_txn_count):
                customer_id = random.choice(concentrated_customers)
                hour = random.randint(9, 20)
                timestamp = current_date.replace(
                    hour=hour,
                    minute=random.randint(0, 59)
                )
                transactions.append(self.generate_transaction(
                    merchant["merchant_id"],
                    timestamp,
                    amount=random.uniform(1000, 5000),  # Higher amounts for concentrated customers
                    customer_id=customer_id
                ))
            
            # Generate normal transactions
            for _ in range(daily_txn_count - concentrated_txn_count):
                hour = random.randint(9, 20)
                timestamp = current_date.replace(
                    hour=hour,
                    minute=random.randint(0, 59)
                )
                transactions.append(self.generate_transaction(
                    merchant["merchant_id"],
                    timestamp
                ))
            
            current_date += timedelta(days=1)
        
        return transactions

    def generate_transaction(
        self,
        merchant_id: str,
        timestamp: datetime,
        amount: float = None,
        customer_id: str = None
    ) -> Dict:
        """Generate a single transaction with optional overrides"""
        if amount is None:
            amount = random.uniform(100, 3000)
        
        if customer_id is None:
            customer_id = f"CUST{random.randint(1000, 9999)}"
        
        return {
            "transaction_id": self.generate_transaction_id(timestamp),
            "merchant_id": merchant_id,
            "timestamp": timestamp,
            "amount": amount,
            "customer_id": customer_id,
            "device_id": f"DEV{random.randint(1000, 9999)}",
            "customer_location": random.choice(self.CITIES),
            "payment_method": random.choice(self.PAYMENT_METHODS),
            "status": "completed",
            "product_category": random.choice(self.PRODUCT_CATEGORIES),
            "platform": random.choice(self.PLATFORMS)
        }

    def generate_normal_transactions(self, merchant: Dict) -> List[Dict]:
        transactions = []
        current_date = self.start_date
        
        while current_date <= self.end_date:
            daily_txn_count = random.randint(5, 15)
            
            for _ in range(daily_txn_count):
                hour = random.randint(9, 20)  # Business hours
                timestamp = current_date.replace(
                    hour=hour,
                    minute=random.randint(0, 59)
                )
                
                transactions.append(self.generate_transaction(
                    merchant["merchant_id"],
                    timestamp
                ))
            
            current_date += timedelta(days=1)
        
        return transactions

def generate_test_data(db: Session):
    """Wrapper function to generate test data"""
    generator = DataGenerator()
    generator.generate_dataset()

if __name__ == "__main__":
    from merchant_api.app.db import SessionLocal
    db = SessionLocal()
    generate_test_data(db)
    db.close()
