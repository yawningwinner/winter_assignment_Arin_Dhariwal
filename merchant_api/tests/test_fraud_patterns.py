import pytest
from datetime import datetime, timedelta
from merchant_api.app.model_processor import ModelProcessor

class TestFraudPatterns:
    """Test fraud pattern detection using actual data samples"""

    def test_pattern_characteristics(self, test_db, sample_transactions):
        """Verify pattern detection on actual fraudulent transactions"""
        model_processor = ModelProcessor()
        
        # Find a known fraudulent transaction
        fraud_tx = next(
            (tx for tx in sample_transactions if tx.is_anomaly),
            None
        )
        
        assert fraud_tx is not None, "No fraudulent transactions found in sample"
        
        # Convert to dictionary format
        test_transaction = {
            "transaction_id": fraud_tx.transaction_id,
            "merchant_id": fraud_tx.merchant_id,
            "amount": fraud_tx.amount,
            "timestamp": fraud_tx.timestamp,
            "customer_id": fraud_tx.customer_id,
            "customer_location": fraud_tx.customer_location
        }
        
        # Process transaction
        result = model_processor.process_transaction(test_transaction)
        
        # Verify our model detects what was marked as fraud in the data
        assert result["anomaly_score"] > 0.5
        assert result["risk_indicators"]["risk_level"] in ["medium", "high"]