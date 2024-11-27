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

        db = SessionLocal()
        try:
            # Add merchants
            for _, row in merchants_df.iterrows():
                merchant = Merchant(
                    # Basic Information
                    merchant_id=row['merchant_id'],
                    business_name=row['business_name'],
                    business_type=row['business_type'],
                    registration_date=pd.to_datetime(row['registration_date']).to_pydatetime(),
                    
                    # Business Details
                    business_model=row['business_model'],
                    product_category=row['product_category'],
                    average_ticket_size=float(row['average_ticket_size']),
                    
                    # Registration Details
                    gst_status=row['gst_status'],
                    pan_number=row['pan_number'],
                    epfo_registered=row['epfo_registered'],
                    
                    # Location Details
                    registered_address=row['registered_address'],
                    city=row['city'],
                    state=row['state'],
                    
                    # Financial Details
                    reported_revenue=float(row['reported_revenue']),
                    employee_count=int(row['employee_count']),
                    bank_account=row['bank_account']
                )
                db.add(merchant)
            
            db.commit()
            print(f"Loaded {len(merchants_df)} merchants successfully!")

            # Add transactions
            batch_size = 1000
            total_transactions = 0
            
            for i in range(0, len(transactions_df), batch_size):
                batch = transactions_df.iloc[i:i + batch_size]
                for _, row in batch.iterrows():
                    transaction = Transaction(
                        # Basic Transaction Info
                        transaction_id=row['transaction_id'],
                        merchant_id=row['merchant_id'],
                        timestamp=pd.to_datetime(row['timestamp']).to_pydatetime(),
                        amount=float(row['amount']),
                        
                        # Customer Info
                        customer_id=row['customer_id'],
                        device_id=row['device_id'],
                        customer_location=row['customer_location'],
                        
                        # Transaction Details
                        payment_method=row['payment_method'],
                        status=row['status'],
                        product_category=row['product_category'],
                        platform=row['platform'],
                        
                        # Risk Indicators
                        velocity_flag=bool(row['velocity_flag']),
                        amount_flag=bool(row['amount_flag']),
                        time_flag=bool(row['time_flag']),
                        device_flag=bool(row['device_flag'])
                    )
                    db.add(transaction)
                
                db.commit()
                total_transactions += len(batch)
                print(f"Processed {total_transactions} transactions...")
            
            print(f"Loaded {total_transactions} transactions successfully!")

        except Exception as e:
            print(f"Error loading data: {e}")
            db.rollback()
        finally:
            db.close()

    except Exception as e:
        print(f"Error reading CSV files: {e}")

if __name__ == "__main__":
    load_data()
