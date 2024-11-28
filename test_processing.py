import argparse
from merchant_api.app.processing import DataProcessor
from merchant_api.app.db import SessionLocal
from merchant_api.app.models import Merchant

def test_merchant_analysis(limit=5):
    # Initialize processor and DB session
    db = SessionLocal()
    processor = DataProcessor(db)
    
    try:
        # Get a limited number of merchants
        merchants = db.query(Merchant).limit(limit).all()
        
        if not merchants:
            print("No merchants found in database!")
            return
            
        print(f"\nAnalyzing {len(merchants)} Merchants (Limit: {limit}):")
        print("=" * 60)
        
        # Iterate through each merchant
        for merchant in merchants:
            print(f"\nMerchant ID: {merchant.merchant_id}")
            print(f"Business Name: {merchant.business_name}")
            print(f"Business Type: {merchant.business_type}")
            print("-" * 50)
            
            # Get transaction summary
            summary = processor.summarize_transactions(merchant.merchant_id)
            print("\nTransaction Summary:")
            print(f"Total Transactions: {summary['metrics'].get('total_transactions', 0)}")
            print(f"Total Amount: ${summary['metrics'].get('total_amount', 0):.2f}")
            print(f"Average Amount: ${summary['metrics'].get('average_amount', 0):.2f}")
            if 'success_rate' in summary['metrics']:
                print(f"Success Rate: {summary['metrics']['success_rate']:.1f}%")
            if 'unique_customers' in summary['metrics']:
                print(f"Unique Customers: {summary['metrics']['unique_customers']}")
            
            # Get risk metrics
            risk = processor.calculate_risk_metrics(merchant.merchant_id)
            print("\nRisk Analysis:")
            print(f"Risk Score: {risk['risk_score']:.2f}")
            print("Risk Factors:")
            for factor, value in risk['factors'].items():
                print(f"- {factor}: {value:.2f}")
            
            # Get timeline
            timeline = processor.generate_timeline(merchant.merchant_id)
            if timeline:
                print("\nRecent Events:")
                for event in timeline[:3]:  # Show last 3 events
                    print(f"- {event['timestamp']}: {event['event_type']} ({event['severity']})")
            
            print("\n" + "=" * 60)  # Separator between merchants
            
    finally:
        db.close()

if __name__ == "__main__":
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Analyze merchant transactions")
    parser.add_argument('--limit', type=int, default=5, help='Number of merchants to analyze (default: 5)')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Run analysis with specified limit
    test_merchant_analysis(limit=args.limit) 