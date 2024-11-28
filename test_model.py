from datetime import datetime
from merchant_api.app.model_processor import ModelProcessor
from merchant_api.app.db import SessionLocal
from merchant_api.app.models import Transaction

def test_real_transactions():
    # Initialize processor
    processor = ModelProcessor()
    
    # Get database session
    db = SessionLocal()
    
    try:
        # Get some real transactions from database
        transactions = db.query(Transaction).all()
        
        print(f"\nAnalyzing {len(transactions)} transactions:")
        print("-" * 50)
        
        for tx in transactions:
            # Convert transaction to dictionary format
            transaction_data = {
                "transaction_id": tx.transaction_id,
                "amount": tx.amount,
                "timestamp": tx.timestamp,
                "customer_id": tx.customer_id,
                "customer_location": tx.customer_location
            }
            
            # Process transaction
            result = processor.process_transaction(transaction_data)
            
            # Print analysis
            print(f"\nTransaction ID: {tx.transaction_id}")
            print(f"Amount: ${tx.amount:.2f}")
            print(f"Time: {tx.timestamp}")
            print(f"Anomaly Score: {result['anomaly_score']:.2f}")
            print(f"Risk Level: {result['risk_indicators']['risk_level']}")
            print(f"Patterns: {result['pattern_match']}")
            print("-" * 50)
    
    finally:
        db.close()

if __name__ == "__main__":
    test_real_transactions() 