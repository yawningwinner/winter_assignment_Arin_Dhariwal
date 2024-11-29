import argparse
from merchant_api.app.schemas import MerchantProfile, TransactionHistory, RiskMetrics
from merchant_api.app.db import SessionLocal
from merchant_api.app.models import Transaction, Merchant
from datetime import datetime

def test_schemas(limit=5):
    db = SessionLocal()
    
    try:
        print(f"\nTesting Schemas with {limit} records:")
        print("=" * 60)
        
        # Test Merchant Profile Schema
        print("\nMerchant Profile Schema:")
        print("-" * 50)
        
        merchants = db.query(Merchant).limit(limit).all()
        for merchant in merchants:
            try:
                profile = MerchantProfile(
                    merchant_id=merchant.merchant_id,
                    business_name=merchant.business_name,
                    business_type=merchant.business_type,
                    business_model=merchant.business_model,
                    city=merchant.city,
                    state=merchant.state,
                    status=merchant.status,
                    registration_date=merchant.registration_date,
                    bank_name=merchant.bank_name,
                    account_number=merchant.account_number
                )
                print(f"✓ Valid Merchant Profile: {profile.business_name}")
                print(f"  ID: {profile.merchant_id}")
                print(f"  Type: {profile.business_type}")
                print()
                
            except Exception as e:
                print(f"✗ Invalid Merchant Profile: {str(e)}")
                print()
        
        # Test Transaction History Schema
        print("\nTransaction History Schema:")
        print("-" * 50)
        
        transactions = db.query(Transaction).limit(limit).all()
        for tx in transactions:
            try:
                history = TransactionHistory(
                    transaction_id=tx.transaction_id,
                    merchant_id=tx.merchant_id,
                    amount=tx.amount,
                    customer_id=tx.customer_id,
                    device_id=tx.device_id,
                    customer_location=tx.customer_location,
                    payment_method=tx.payment_method,
                    status=tx.status,
                    product_category=tx.product_category,
                    platform=tx.platform,
                    timestamp=tx.timestamp
                    # is_anomaly=tx.is_anomaly,
                    # anomaly_reasons=tx.anomaly_reasons
                )
                print(f"✓ Valid Transaction History: {history.transaction_id}")
                print(f"  Amount: ${history.amount:.2f}")
                print(f"  Status: {history.status}")
                print()
                
            except Exception as e:
                print(f"✗ Invalid Transaction History: {str(e)}")
                print()
                
    finally:
        db.close()

if __name__ == "__main__":
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Test data schemas")
    parser.add_argument('--limit', type=int, default=5, 
                       help='Number of records to test (default: 5)')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Run schema tests
    test_schemas(limit=args.limit) 