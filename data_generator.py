import random
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from merchant_api.app.models import Merchant, Transaction
from merchant_api.app.db import SessionLocal
import numpy as np
from sqlalchemy import text

class DataGenerator:
    def __init__(self, db: Session):
        self.db = db
        self.business_types = ['retail', 'restaurant', 'ecommerce', 'services', 'travel']
        self.business_models = ['B2C', 'B2B', 'marketplace']
        self.payment_methods = ['credit_card', 'debit_card', 'upi', 'netbanking', 'wallet']
        self.product_categories = ['electronics', 'fashion', 'food', 'travel', 'entertainment']
        self.platforms = ['web', 'mobile', 'pos', 'kiosk']
        self.cities = ['Mumbai', 'Delhi', 'Bangalore', 'Chennai', 'Hyderabad']
        self.states = ['Maharashtra', 'Delhi', 'Karnataka', 'Tamil Nadu', 'Telangana']
        
    def generate_data(self):
        print("Clearing existing data...")
        self.db.execute(text("TRUNCATE TABLE transactions CASCADE"))
        self.db.execute(text("TRUNCATE TABLE merchants CASCADE"))
        self.db.commit()
        
        print("Generating merchant data...")
        merchants = self._generate_merchants(num_merchants=100)
        self.db.bulk_save_objects(merchants)
        self.db.commit()
        
        print("Generating transaction data...")
        self._generate_transactions(merchants)

    def _generate_merchants(self, num_merchants):
        merchants = []
        for i in range(1, num_merchants + 1):
            merchant = Merchant(
                merchant_id=f"M{i:04d}",
                business_name=f"Business_{i}",
                business_type=random.choice(self.business_types),
                business_model=random.choice(self.business_models),
                bank_name=f"Bank_{random.randint(1,5)}",
                account_number=f"ACCT{random.randint(10000,99999)}",
                city=random.choice(self.cities),
                state=random.choice(self.states),
                status=random.choices(['active', 'inactive'], weights=[0.95, 0.05])[0],
                registration_date=datetime.now() - timedelta(days=random.randint(0, 365))
            )
            merchants.append(merchant)
        return merchants

    def _generate_transactions(self, merchants):
        all_transactions = []
        used_transaction_ids = set()  # Track used IDs
        
        for merchant in merchants:
            # Generate 1000-2000 transactions per merchant
            num_transactions = random.randint(1000, 2000)
            
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=14)  # 2 weeks of data
            
            # Generate base amount parameters
            avg_amount = random.uniform(100, 1000)
            std_amount = avg_amount * 0.3
            
            for _ in range(num_transactions):
                # Generate unique transaction ID
                while True:
                    tx_id = f"TX{random.randint(100000, 999999)}"
                    if tx_id not in used_transaction_ids:
                        used_transaction_ids.add(tx_id)
                        break
                
                transaction = Transaction(
                    transaction_id=tx_id,
                    merchant_id=merchant.merchant_id,
                    amount=round(np.random.lognormal(np.log(avg_amount), 0.5), 2),
                    timestamp=start_date + timedelta(
                        seconds=random.randint(0, int((end_date - start_date).total_seconds()))
                    ),
                    customer_id=f"C{random.randint(1000, 9999)}",
                    device_id=f"D{random.randint(1000, 9999)}",
                    customer_location=random.choice(self.cities),
                    payment_method=random.choice(self.payment_methods),
                    status=random.choices(
                        ['success', 'failed', 'pending'],
                        weights=[0.95, 0.03, 0.02]
                    )[0],
                    product_category=random.choice(self.product_categories),
                    platform=random.choice(self.platforms)
                )
                all_transactions.append(transaction)
                
                # Commit in batches to avoid memory issues
                if len(all_transactions) >= 1000:
                    self.db.bulk_save_objects(all_transactions)
                    self.db.commit()
                    all_transactions = []
        
        # Save any remaining transactions
        if all_transactions:
            self.db.bulk_save_objects(all_transactions)
            self.db.commit()

    def _generate_pattern_transactions(self, merchant, original_tx, avg_amount):
        pattern_txs = []
        pattern_type = random.choice(['split', 'rapid', 'round'])
        
        if pattern_type == 'split':
            # Split into 2-4 smaller transactions
            splits = random.randint(2, 4)
            split_amount = original_tx.amount / splits
            for _ in range(splits):
                tx = self._create_transaction(
                    merchant,
                    original_tx.timestamp,
                    original_tx.timestamp + timedelta(minutes=30),
                    split_amount,
                    split_amount * 0.1
                )
                pattern_txs.append(tx)
                
        elif pattern_type == 'rapid':
            # Generate 2-3 rapid transactions
            for i in range(random.randint(2, 3)):
                tx = self._create_transaction(
                    merchant,
                    original_tx.timestamp,
                    original_tx.timestamp + timedelta(minutes=5),
                    avg_amount,
                    avg_amount * 0.3
                )
                pattern_txs.append(tx)
                
        elif pattern_type == 'round':
            # Generate 1-2 round amount transactions
            for _ in range(random.randint(1, 2)):
                amount = round(random.randint(1, 10) * 1000.0, 2)
                tx = self._create_transaction(
                    merchant,
                    original_tx.timestamp,
                    original_tx.timestamp + timedelta(hours=2),
                    amount,
                    amount * 0.1
                )
                pattern_txs.append(tx)
        
        return pattern_txs

def main():
    db = SessionLocal()
    generator = DataGenerator(db)
    try:
        generator.generate_data()
    finally:
        db.close()

if __name__ == "__main__":
    main()
