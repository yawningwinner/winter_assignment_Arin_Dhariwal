import pytest
from merchant_api.app.models import Transaction
from sqlalchemy import func

class TestDatasetBalance:
    """Test dataset balance and statistics using actual generated data"""

    def test_fraud_normal_ratio(self, test_db):
        """Check ratio of fraudulent to normal transactions"""
        # Get total counts from actual data
        total_tx = test_db.query(func.count(Transaction.transaction_id)).scalar()
        fraud_tx = test_db.query(func.count(Transaction.transaction_id))\
            .filter(Transaction.is_anomaly == True)\
            .scalar()
        
        # Calculate ratio
        fraud_ratio = fraud_tx / total_tx if total_tx > 0 else 0
        
        print(f"\nFraud ratio in actual data: {fraud_ratio:.2%}")
        # Verify reasonable fraud ratio (adjust based on your data)
        assert 0.01 <= fraud_ratio <= 0.10

    def test_pattern_distribution(self, test_db):
        """Verify distribution of different patterns in actual data"""
        # Get transactions with patterns
        transactions = test_db.query(Transaction)\
            .filter(Transaction.anomaly_reasons.isnot(None))\
            .limit(1000)\
            .all()
        
        # Count pattern occurrences
        pattern_counts = {}
        for tx in transactions:
            if tx.anomaly_reasons:
                patterns = [p.strip() for p in tx.anomaly_reasons.split(",") if p.strip()]
                for pattern in patterns:
                    pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1
        
        # Print pattern distribution
        print("\nPattern distribution in actual data:")
        for pattern, count in pattern_counts.items():
            print(f"{pattern}: {count}")
        
        assert len(pattern_counts) >= 2, "Not enough pattern diversity in actual data"

    def test_overall_statistics(self, test_db):
        """Validate overall dataset statistics"""
        # Get basic statistics
        stats = test_db.query(
            func.count(Transaction.transaction_id).label('total'),
            func.avg(Transaction.amount).label('avg_amount'),
            func.min(Transaction.amount).label('min_amount'),
            func.max(Transaction.amount).label('max_amount')
        ).first()
        
        # Verify dataset size
        assert stats.total >= 100  # Minimum dataset size
        
        # Verify amount ranges
        assert stats.min_amount > 0
        assert stats.max_amount < 50000  # Reasonable maximum
        assert 100 <= stats.avg_amount <= 5000  # Reasonable average range
        
        # Print statistics for debugging
        print("\nDataset statistics:")
        print(f"Total transactions: {stats.total}")
        print(f"Average amount: ${stats.avg_amount:.2f}")
        print(f"Amount range: ${stats.min_amount:.2f} - ${stats.max_amount:.2f}")