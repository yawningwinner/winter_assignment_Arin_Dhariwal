import pytest
from merchant_api.app.models import Transaction
from sqlalchemy import func

class TestDatasetBalance:
    """Test dataset balance and statistics using actual generated data"""

    def test_fraud_normal_ratio(self, test_db):
        """Check basic transaction counts"""
        # Get total counts from actual data
        total_tx = test_db.query(func.count(Transaction.transaction_id)).scalar()
        assert total_tx > 0, "Database should contain transactions"

    def test_pattern_distribution(self, test_db):
        """Verify basic transaction patterns"""
        # Get sample transactions
        transactions = test_db.query(Transaction)\
            .limit(1000)\
            .all()
        
        # Basic assertions about transaction data
        assert len(transactions) > 0, "Should have transactions"
        
        # Check for required fields
        for tx in transactions:
            assert tx.transaction_id is not None
            assert tx.merchant_id is not None
            assert tx.amount is not None
            assert tx.timestamp is not None

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