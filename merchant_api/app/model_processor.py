from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import numpy as np
from merchant_api.app.cache import cached
from merchant_api.app.events import event_processor, EventType, EventPriority
import random

class ModelProcessor:
    def __init__(self):
        self.models = {}
        self.thresholds = {
            "amount": 10000,
            "velocity": 0.6,
            "risk_score": 60
        }

    @cached(ttl=timedelta(minutes=30))
    def process_transaction(self, transaction: Dict) -> Dict:
        """Process a single transaction through models"""
        # Calculate base scores
        amount_score = self._calculate_amount_score(transaction["amount"])
        time_score = self._calculate_time_score(transaction["timestamp"])
        
        # Calculate final anomaly score (weighted average)
        anomaly_score = 0.4 * amount_score + 0.6 * time_score
        
        # Determine patterns
        patterns = []
        if amount_score ==1.0:
            patterns.append("large_amount")
        if time_score > 0.7:
            patterns.append("suspicious_time")
        
        # Determine risk level
        risk_level = "high" if anomaly_score > 0.6 else "medium" if anomaly_score > 0.4 else "low"
        
        results = {
            "risk_indicators": {
                "high_amount": transaction["amount"] > self.thresholds["amount"],
                "suspicious_time": self._is_suspicious_time(transaction["timestamp"]),
                "risk_level": risk_level
            },
            "anomaly_score": anomaly_score,
            "pattern_match": patterns
        }
        
        return results

    def _calculate_amount_score(self, amount: float) -> float:
        """Calculate normalized score for transaction amount"""
        if(amount > 2500.0):
            return 1.0
        else:
            return amount / self.thresholds["amount"]

    def _calculate_time_score(self, timestamp: datetime) -> float:
        """Calculate score based on transaction time"""
        hour = timestamp.hour
        if hour >= 23 or hour <= 4:
            return 0.9
        elif hour >= 20 or hour <= 6:
            return 0.7
        return 0.2

    def _is_suspicious_time(self, timestamp: datetime) -> bool:
        """Check if transaction time is suspicious"""
        hour = timestamp.hour
        return hour >= 23 or hour <= 4

    def process_batch(self, transactions: List[Dict]) -> List[Dict]:
        """Process a batch of transactions"""
        results = []
        for tx in transactions:
            result = self.process_transaction(tx)
            results.append(result)
        
        # Add velocity check for batch
        if len(transactions) >= 3:
            # Calculate time difference between first and last transaction
            times = [datetime.fromisoformat(tx["timestamp"]) if isinstance(tx["timestamp"], str) 
                    else tx["timestamp"] for tx in transactions]
            time_diff = max(times) - min(times)
            
            # If transactions happen within 30 minutes
            if time_diff.total_seconds() < 1800:  # 30 minutes
                for result in results:
                    result["anomaly_score"] = min(1.0, result["anomaly_score"] + 0.3)
                    result["risk_indicators"]["high_velocity"] = True
                    result["risk_indicators"]["risk_level"] = "high"
                    if "high_velocity" not in result["pattern_match"]:
                        result["pattern_match"].append("high_velocity")
        
        return results 