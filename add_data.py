import pandas as pd
from sqlalchemy.orm import Session
from merchant_api.app.db import SessionLocal, engine
from merchant_api.app.models import Merchant, Transaction, Base
from datetime import datetime

def clear_tables():
    # Drop and recreate all tables
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("Tables cleared successfully!")

def load_data():
    try:
        # Clear existing data
        clear_tables()

        # Read CSV files
        merchants_df = pd.read_csv("data/merchant_profiles.csv")
        transactions_df = pd.read_csv("data/transaction_data.csv")

        # Create database session
        db = SessionLocal()

        try:
            # Add merchants
            for _, row in merchants_df.iterrows():
                merchant = Merchant(
                    merchant_id=row['MerchantID'],
                    name=row['Name'],
                    business_type=row['BusinessType'],
                    registration_date=pd.to_datetime(row['RegistrationDate']).to_pydatetime(),
                    gst_status=row['GSTStatus'],
                    avg_transaction_volume=float(row['AvgTransactionVolume'])
                )
                db.add(merchant)
            
            # Commit merchants first
            db.commit()
            print(f"Loaded {len(merchants_df)} merchants successfully!")

            # Add transactions
            batch_size = 1000
            total_transactions = 0
            
            for i in range(0, len(transactions_df), batch_size):
                batch = transactions_df.iloc[i:i + batch_size]
                for _, row in batch.iterrows():
                    transaction = Transaction(
                        merchant_id=row['MerchantID'],
                        transaction_date=pd.to_datetime(row['TransactionDate']).to_pydatetime(),
                        transaction_amount=float(row['TransactionAmount']),
                        customer_id=str(row['CustomerID']),
                        is_anomaly=bool(row['IsAnomaly'])
                    )
                    db.add(transaction)
                
                db.commit()
                total_transactions += len(batch)
                print(f"Processed {total_transactions} transactions...")
            
            print(f"Loaded {total_transactions} transactions successfully!")
            print("All data loaded successfully!")

        except Exception as e:
            print(f"Error loading data: {e}")
            db.rollback()
        finally:
            db.close()

    except Exception as e:
        print(f"Error reading CSV files: {e}")

if __name__ == "__main__":
    load_data()
