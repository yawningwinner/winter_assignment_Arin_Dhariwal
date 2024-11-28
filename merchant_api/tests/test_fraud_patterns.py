import pytest
from datetime import datetime, timedelta
from merchant_api.app.model_processor import ModelProcessor
from app.models import Transaction

class TestFraudPatterns:
    """Test fraud pattern detection using actual data samples"""

    def test_pattern_characteristics(self, test_db, sample_transactions):
        """Verify basic transaction characteristics"""
        assert len(sample_transactions) > 0, "Should have sample transactions"
        
        # Basic validation of transaction fields
        for tx in sample_transactions:
            assert tx.transaction_id is not None
            assert tx.merchant_id is not None
            assert tx.amount > 0
            assert tx.timestamp is not None