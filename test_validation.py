import argparse
from merchant_api.app.validation import TransactionValidator, MerchantValidator
from merchant_api.app.db import SessionLocal
from merchant_api.app.models import Transaction, Merchant

def test_validators(limit=5):
    db = SessionLocal()
    
    try:
        # Get sample data
        transactions = db.query(Transaction).limit(limit).all()
        merchants = db.query(Merchant).limit(limit).all()
        
        print(f"\nTesting Validation for {limit} records:")
        print("=" * 60)
        
        # Test Transaction Validation
        print("\nTransaction Validation:")
        print("-" * 50)
        
        for tx in transactions:
            try:
                validator = TransactionValidator(
                    transaction_id=tx.transaction_id,
                    merchant_id=tx.merchant_id,
                    amount=tx.amount,
                    customer_id=tx.customer_id,
                    timestamp=tx.timestamp,
                    device_id=tx.device_id,
                    customer_location=tx.customer_location,
                    payment_method=tx.payment_method,
                    status=tx.status,
                    product_category=tx.product_category,
                    platform=tx.platform
                )
                print(f"✓ Valid Transaction: {tx.transaction_id}")
                print(f"  Amount: ${tx.amount:.2f}")
                print(f"  Status: {tx.status}")
                print()
                
            except Exception as e:
                print(f"✗ Invalid Transaction {tx.transaction_id}: {str(e)}")
                print()
        
        # Test Merchant Validation
        print("\nMerchant Validation:")
        print("-" * 50)
        
        for merchant in merchants:
            try:
                validator = MerchantValidator(
                    merchant_id=merchant.merchant_id,
                    business_name=merchant.business_name,
                    business_type=merchant.business_type,
                    business_model=merchant.business_model,
                    city=merchant.city,
                    state=merchant.state,
                    status=merchant.status
                )
                print(f"✓ Valid Merchant: {merchant.merchant_id}")
                print(f"  Business: {merchant.business_name}")
                print(f"  Type: {merchant.business_type}")
                print()
                
            except Exception as e:
                print(f"✗ Invalid Merchant {merchant.merchant_id}: {str(e)}")
                print()
                
    finally:
        db.close()

if __name__ == "__main__":
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Test data validation")
    parser.add_argument('--limit', type=int, default=5, 
                       help='Number of records to validate (default: 5)')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Run validation
    test_validators(limit=args.limit) 