import random
from datetime import datetime, timedelta
import uuid
from typing import List, Dict
import json
from sqlalchemy.orm import Session
from merchant_api.app.models import Merchant, Transaction
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataGenerator:
    def __init__(self):
        # Configuration
        self.BUSINESS_TYPES = ["Retail", "Restaurant", "E-commerce", "Services", "Wholesale"]
        self.GST_STATUSES = ["Active", "Suspended", "Pending"]
        self.NUM_MERCHANTS = 100
        self.TRANSACTIONS_PER_MERCHANT = 200
        self.FRAUD_MERCHANT_PERCENTAGE = 0.20  # 20% merchants will have fraud patterns
        
        # Time range for transactions (last 30 days)
        self.end_date = datetime.now()
        self.start_date = self.end_date - timedelta(days=30)

    def generate_merchant_id(self) -> str:
        """Generate merchant ID in format M-XXXXX"""
        return f"M-{str(random.randint(0, 99999)).zfill(5)}"

    def generate_merchant_name(self) -> str:
        """Generate a realistic business name"""
        prefixes = ["Global", "Prime", "Elite", "Star", "Royal"]
        suffixes = ["Trading", "Enterprises", "Solutions", "Services", "Mart"]
        return f"{random.choice(prefixes)} {random.choice(suffixes)}"

    def generate_merchant_profile(self) -> Dict:
        """Generate a complete merchant profile"""
        return {
            "merchant_id": self.generate_merchant_id(),
            "name": self.generate_merchant_name(),
            "business_type": random.choice(self.BUSINESS_TYPES),
            "registration_date": self.start_date - timedelta(days=random.randint(1, 365)),
            "gst_status": random.choice(self.GST_STATUSES),
            "avg_transaction_volume": random.uniform(1000, 10000)
        }

    def generate_normal_transaction(self, merchant_id: str) -> Dict:
        """Generate a normal transaction pattern"""
        # Normal business hours (9 AM to 9 PM)
        transaction_date = self.start_date + timedelta(
            days=random.randint(0, 30),
            hours=random.randint(9, 21),
            minutes=random.randint(0, 59)
        )
        
        return {
            "merchant_id": merchant_id,
            "transaction_date": transaction_date,
            "transaction_amount": random.uniform(100, 1000),
            "customer_id": str(uuid.uuid4())
        }

    def generate_fraudulent_transactions(self, merchant_id: str) -> List[Dict]:
        """Generate transactions with fraud patterns"""
        transactions = []
        fraud_type = random.choice(["late_night", "high_velocity", "customer_concentration"])
        
        if fraud_type == "late_night":
            # Generate late night transactions (11 PM to 4 AM)
            for _ in range(random.randint(3, 7)):
                transaction_date = self.start_date + timedelta(
                    days=random.randint(0, 30),
                    hours=random.randint(23, 24) if random.random() < 0.5 else random.randint(0, 4),
                    minutes=random.randint(0, 59)
                )
                transactions.append({
                    "merchant_id": merchant_id,
                    "transaction_date": transaction_date,
                    "transaction_amount": random.uniform(1000, 5000),
                    "customer_id": str(uuid.uuid4())
                })
                
        elif fraud_type == "high_velocity":
            # Generate multiple transactions within a short time window
            base_date = self.start_date + timedelta(days=random.randint(0, 30))
            for i in range(random.randint(5, 8)):
                transaction_date = base_date + timedelta(minutes=i*2)  # Transactions 2 minutes apart
                transactions.append({
                    "merchant_id": merchant_id,
                    "transaction_date": transaction_date,
                    "transaction_amount": random.uniform(500, 2000),
                    "customer_id": str(uuid.uuid4())
                })
                
        else:  # customer_concentration
            # Generate multiple transactions from same customer
            concentrated_customer = "ConcentratedCustomer"
            base_date = self.start_date + timedelta(days=random.randint(0, 30))
            for i in range(random.randint(8, 12)):
                transaction_date = base_date + timedelta(hours=random.randint(0, 23))
                transactions.append({
                    "merchant_id": merchant_id,
                    "transaction_date": transaction_date,
                    "transaction_amount": random.uniform(2000, 6000),
                    "customer_id": concentrated_customer
                })
                
        return transactions

    def generate_data(self, db: Session):
        """Generate complete dataset with both normal and fraudulent patterns"""
        try:
            # Generate merchants
            logger.info("Generating merchant profiles...")
            merchants = []
            for _ in range(self.NUM_MERCHANTS):
                merchant = self.generate_merchant_profile()
                merchants.append(merchant)
                
                # Create Merchant object and add to database
                db_merchant = Merchant(
                    merchant_id=merchant["merchant_id"],
                    name=merchant["name"],
                    business_type=merchant["business_type"],
                    registration_date=merchant["registration_date"],
                    gst_status=merchant["gst_status"],
                    avg_transaction_volume=merchant["avg_transaction_volume"]
                )
                db.add(db_merchant)
            
            db.commit()
            logger.info(f"Generated {len(merchants)} merchant profiles")

            # Generate transactions
            logger.info("Generating transactions...")
            transactions_count = 0
            
            for merchant in merchants:
                # Determine if this merchant will have fraud patterns
                is_fraud_merchant = random.random() < self.FRAUD_MERCHANT_PERCENTAGE
                
                if is_fraud_merchant:
                    # Generate some normal and some fraudulent transactions
                    normal_count = int(self.TRANSACTIONS_PER_MERCHANT * 0.7)  # 70% normal
                    for _ in range(normal_count):
                        tx = self.generate_normal_transaction(merchant["merchant_id"])
                        db_tx = Transaction(
                            merchant_id=tx["merchant_id"],
                            transaction_date=tx["transaction_date"],
                            transaction_amount=tx["transaction_amount"],
                            customer_id=tx["customer_id"]
                        )
                        db.add(db_tx)
                        transactions_count += 1
                    
                    # Add fraudulent transactions
                    fraud_transactions = self.generate_fraudulent_transactions(merchant["merchant_id"])
                    for tx in fraud_transactions:
                        db_tx = Transaction(
                            merchant_id=tx["merchant_id"],
                            transaction_date=tx["transaction_date"],
                            transaction_amount=tx["transaction_amount"],
                            customer_id=tx["customer_id"]
                        )
                        db.add(db_tx)
                        transactions_count += 1
                else:
                    # Generate only normal transactions
                    for _ in range(self.TRANSACTIONS_PER_MERCHANT):
                        tx = self.generate_normal_transaction(merchant["merchant_id"])
                        db_tx = Transaction(
                            merchant_id=tx["merchant_id"],
                            transaction_date=tx["transaction_date"],
                            transaction_amount=tx["transaction_amount"],
                            customer_id=tx["customer_id"]
                        )
                        db.add(db_tx)
                        transactions_count += 1
                
                # Commit every 1000 transactions
                if transactions_count % 1000 == 0:
                    db.commit()
                    logger.info(f"Generated {transactions_count} transactions...")
            
            # Final commit
            db.commit()
            logger.info(f"Successfully generated {transactions_count} transactions")
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error generating data: {str(e)}")
            raise

def generate_test_data(db: Session):
    """Wrapper function to generate test data"""
    generator = DataGenerator()
    generator.generate_data(db)

if __name__ == "__main__":
    from merchant_api.app.db import SessionLocal
    db = SessionLocal()
    generate_test_data(db)
    db.close()
