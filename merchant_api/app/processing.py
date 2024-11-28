from datetime import datetime, timedelta
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from merchant_api.app.models import Transaction, Merchant
import pandas as pd
import numpy as np

class DataProcessor:
    def __init__(self, db: Session):
        self.db = db

    def summarize_transactions(
        self,
        merchant_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict:
        """Generate transaction summary metrics"""
        query = self.db.query(Transaction).filter(Transaction.merchant_id == merchant_id)
        
        if start_date:
            query = query.filter(Transaction.timestamp >= start_date)
        if end_date:
            query = query.filter(Transaction.timestamp <= end_date)

        transactions = query.all()
        df = pd.DataFrame([vars(t) for t in transactions])
        
        if df.empty:
            return {
                "merchant_id": merchant_id,
                "period": {"start": start_date, "end": end_date},
                "metrics": {},
                "trends": {}
            }

        # Calculate metrics
        metrics = {
            "total_transactions": len(df),
            "total_amount": float(df['amount'].sum()),
            "average_amount": float(df['amount'].mean()),
            "max_amount": float(df['amount'].max()),
            "success_rate": float((df['status'] == 'success').mean() * 100),
            "unique_customers": len(df['customer_id'].unique())
        }

        # Calculate trends
        df['date'] = pd.to_datetime(df['timestamp']).dt.date
        daily_trends = df.groupby('date').agg({
            'amount': ['count', 'sum', 'mean'],
            'transaction_id': 'count'
        }).reset_index()

        trends = {
            "daily_volume": daily_trends['transaction_id']['count'].tolist(),
            "daily_amount": daily_trends['amount']['sum'].tolist(),
            "dates": daily_trends['date'].astype(str).tolist()
        }

        return {
            "merchant_id": merchant_id,
            "period": {"start": start_date, "end": end_date},
            "metrics": metrics,
            "trends": trends
        }

    def calculate_risk_metrics(self, merchant_id: str) -> Dict:
        """Calculate comprehensive risk metrics"""
        # Get recent transactions
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        transactions = self.db.query(Transaction).filter(
            Transaction.merchant_id == merchant_id,
            Transaction.timestamp.between(start_date, end_date)
        ).all()

        if not transactions:
            return {"risk_score": 0, "factors": {}}

        df = pd.DataFrame([vars(t) for t in transactions])
        
        # Calculate risk factors
        risk_factors = {
            "high_value_ratio": float((df['amount'] > df['amount'].quantile(0.95)).mean()),
            "failed_tx_ratio": float((df['status'] != 'success').mean()),
            "late_night_ratio": float((pd.to_datetime(df['timestamp']).dt.hour.isin([23,0,1,2,3,4])).mean()),
            "velocity_score": self._calculate_velocity_score(df),
            "location_risk": self._calculate_location_risk(df)
        }

        # Calculate composite risk score (0-100)
        weights = {
            "high_value_ratio": 0.3,
            "failed_tx_ratio": 0.2,
            "late_night_ratio": 0.15,
            "velocity_score": 0.2,
            "location_risk": 0.15
        }

        risk_score = sum(factor * weights[name] for name, factor in risk_factors.items()) * 100

        return {
            "risk_score": round(risk_score, 2),
            "factors": risk_factors,
            "trend": self._calculate_risk_trend(merchant_id)
        }

    def generate_timeline(self, merchant_id: str, days: int = 30) -> List[Dict]:
        """Generate timeline of significant events"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Get transactions and anomalies
        transactions = self.db.query(Transaction).filter(
            Transaction.merchant_id == merchant_id,
            Transaction.timestamp.between(start_date, end_date)
        ).order_by(Transaction.timestamp).all()

        timeline = []
        
        for tx in transactions:
            if self._is_significant_event(tx):
                timeline.append({
                    "timestamp": tx.timestamp,
                    "event_type": self._determine_event_type(tx),
                    "details": self._get_event_details(tx),
                    "severity": self._calculate_event_severity(tx)
                })

        return sorted(timeline, key=lambda x: x['timestamp'], reverse=True)

    def _calculate_velocity_score(self, df: pd.DataFrame) -> float:
        """Calculate transaction velocity risk score"""
        if df.empty:
            return 0.0
            
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp')
        
        # Calculate time differences between consecutive transactions
        df['time_diff'] = df['timestamp'].diff().dt.total_seconds()
        
        # Calculate velocity score based on short time differences
        velocity_score = float((df['time_diff'] < 60).mean())  # Transactions less than 1 minute apart
        
        return velocity_score

    def _calculate_location_risk(self, df: pd.DataFrame) -> float:
        """Calculate location-based risk score"""
        if df.empty:
            return 0.0
            
        # Count unique locations
        location_counts = df['customer_location'].value_counts()
        
        # Calculate risk based on location diversity
        unique_locations = len(location_counts)
        total_transactions = len(df)
        
        location_risk = 1 - (unique_locations / total_transactions)
        
        return float(location_risk)

    def _calculate_risk_trend(self, merchant_id: str) -> List[float]:
        """Calculate daily risk scores for trend analysis"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        daily_scores = []
        current_date = start_date
        
        while current_date <= end_date:
            next_date = current_date + timedelta(days=1)
            
            # Get transactions for the day
            transactions = self.db.query(Transaction).filter(
                Transaction.merchant_id == merchant_id,
                Transaction.timestamp.between(current_date, next_date)
            ).all()
            
            if transactions:
                df = pd.DataFrame([vars(t) for t in transactions])
                # Calculate simple daily risk score
                risk_score = (
                    (df['amount'] > df['amount'].mean() + 2 * df['amount'].std()).mean() +
                    (df['status'] != 'success').mean()
                ) / 2 * 100
            else:
                risk_score = 0
                
            daily_scores.append(round(risk_score, 2))
            current_date = next_date
            
        return daily_scores

    def _is_significant_event(self, transaction: Transaction) -> bool:
        """Determine if a transaction is a significant event"""
        return (
            transaction.is_anomaly or
            transaction.amount > 10000 or
            transaction.status != 'success' or
            (datetime.now() - transaction.timestamp).total_seconds() < 3600  # Last hour
        )

    def _determine_event_type(self, transaction: Transaction) -> str:
        """Determine the type of event"""
        if transaction.is_anomaly:
            return "anomaly"
        if transaction.amount > 10000:
            return "high_value"
        if transaction.status != 'success':
            return "failed"
        return "recent"

    def _get_event_details(self, transaction: Transaction) -> Dict:
        """Get detailed information about the event"""
        return {
            "transaction_id": transaction.transaction_id,
            "amount": transaction.amount,
            "status": transaction.status,
            "customer_id": transaction.customer_id,
            "location": transaction.customer_location,
            "anomaly_reasons": transaction.anomaly_reasons.split(",") if transaction.anomaly_reasons else []
        }

    def _calculate_event_severity(self, transaction: Transaction) -> str:
        """Calculate event severity level"""
        if transaction.is_anomaly and transaction.amount > 10000:
            return "high"
        if transaction.is_anomaly or transaction.amount > 5000:
            return "medium"
        return "low" 