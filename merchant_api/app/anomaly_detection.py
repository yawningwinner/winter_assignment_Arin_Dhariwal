from sqlalchemy.orm import Session
from sqlalchemy.sql import func, or_, extract
from sqlalchemy import and_, text
from datetime import datetime, timedelta
from merchant_api.app.models import Transaction
import logging
from typing import Dict, List
from merchant_api.app.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AnomalyDetector:
    def __init__(self):
        # Late Night Trading Pattern
        self.LATE_NIGHT_CONFIG = {
            "start_hour": settings.LATE_NIGHT_START,
            "end_hour": settings.LATE_NIGHT_END,
            "volume_threshold": settings.LATE_NIGHT_VOLUME_THRESHOLD,
            "min_daily_txns": settings.MIN_DAILY_TRANSACTIONS,
            "pattern_duration": settings.PATTERN_DURATION_DAYS
        }
        
        # Sudden Activity Spike Pattern
        self.SPIKE_CONFIG = {
            "normal_daily_min": settings.NORMAL_DAILY_MIN,
            "normal_daily_max": settings.NORMAL_DAILY_MAX,
            "spike_threshold": settings.SPIKE_THRESHOLD,
            "spike_duration": settings.SPIKE_DURATION_DAYS
        }
        
        # Split Transaction Pattern
        self.SPLIT_CONFIG = {
            "amount_min": settings.SPLIT_AMOUNT_MIN,
            "amount_max": settings.SPLIT_AMOUNT_MAX,
            "min_splits": settings.MIN_SPLITS,
            "time_window": settings.SPLIT_TIME_WINDOW
        }
        
        # Round Amount Pattern
        self.ROUND_CONFIG = {
            "amounts": settings.ROUND_AMOUNTS,
            "threshold": settings.ROUND_AMOUNT_THRESHOLD
        }
        
        # Customer Concentration Pattern
        self.CONCENTRATION_CONFIG = {
            "min_customers": settings.MIN_CUSTOMERS,
            "max_customers": settings.MAX_CUSTOMERS,
            "volume_threshold": settings.VOLUME_CONCENTRATION_THRESHOLD,
            "time_window": settings.CONCENTRATION_TIME_WINDOW
        }
        
        self.BATCH_SIZE = settings.BATCH_SIZE

    def detect_anomalies(self, db: Session) -> Dict[str, int]:
        stats = {
            "total_processed": 0,
            "anomalies_detected": 0,
            "late_night_trading": 0,
            "sudden_spike": 0,
            "split_transactions": 0,
            "round_amount": 0,
            "customer_concentration": 0
        }

        try:
            total_transactions = db.query(func.count(Transaction.id)).scalar()
            logger.info(f"Starting anomaly detection for {total_transactions} transactions")

            offset = 0
            while True:
                db.expire_all()
                
                transactions = db.query(Transaction).order_by(
                    Transaction.timestamp
                ).offset(offset).limit(self.BATCH_SIZE).all()
                
                if not transactions:
                    break

                for transaction in transactions:
                    anomaly_reasons = []
                    
                    # Check each pattern
                    if self._check_late_night_pattern(db, transaction):
                        anomaly_reasons.append("late_night_trading")
                        stats["late_night_trading"] += 1
                        logger.info(f"Late night pattern detected for transaction {transaction.transaction_id}")

                    if self._check_spike_pattern(db, transaction):
                        anomaly_reasons.append("sudden_spike")
                        stats["sudden_spike"] += 1
                        logger.info(f"Activity spike detected for transaction {transaction.transaction_id}")

                    if self._check_split_pattern(db, transaction):
                        anomaly_reasons.append("split_transactions")
                        stats["split_transactions"] += 1
                        logger.info(f"Split transaction pattern detected for transaction {transaction.transaction_id}")

                    if self._check_round_amount_pattern(db, transaction):
                        anomaly_reasons.append("round_amount")
                        stats["round_amount"] += 1
                        logger.info(f"Round amount pattern detected for transaction {transaction.transaction_id}")

                    if self._check_customer_concentration(db, transaction):
                        anomaly_reasons.append("customer_concentration")
                        stats["customer_concentration"] += 1
                        logger.info(f"Customer concentration detected for transaction {transaction.transaction_id}")

                    # Update transaction with findings
                    if anomaly_reasons:
                        db.execute(
                            text("""
                                UPDATE transactions 
                                SET is_anomaly = :is_anomaly, 
                                    anomaly_reasons = :reasons 
                                WHERE id = :id
                            """),
                            {
                                "is_anomaly": True,
                                "reasons": ",".join(anomaly_reasons),
                                "id": transaction.id
                            }
                        )
                        stats["anomalies_detected"] += 1
                    
                    stats["total_processed"] += 1

                try:
                    db.commit()
                    logger.info(f"Processed {stats['total_processed']} of {total_transactions} transactions")
                except Exception as e:
                    db.rollback()
                    logger.error(f"Error committing batch: {str(e)}")
                    raise

                offset += self.BATCH_SIZE

            logger.info("Anomaly detection completed")
            logger.info(f"Final statistics: {stats}")
            return stats

        except Exception as e:
            db.rollback()
            logger.error(f"Error during anomaly detection: {str(e)}")
            raise

    def _check_late_night_pattern(self, db: Session, transaction: Transaction) -> bool:
        """Check for late night trading pattern"""
        hour = transaction.timestamp.hour
        if hour >= self.LATE_NIGHT_CONFIG["start_hour"] or hour <= self.LATE_NIGHT_CONFIG["end_hour"]:
            # Check volume percentage in last 24 hours
            window_start = transaction.timestamp - timedelta(hours=24)
            
            total_txns = db.query(func.count(Transaction.id)).filter(
                Transaction.merchant_id == transaction.merchant_id,
                Transaction.timestamp.between(window_start, transaction.timestamp)
            ).scalar()
            
            night_txns = db.query(func.count(Transaction.id)).filter(
                Transaction.merchant_id == transaction.merchant_id,
                Transaction.timestamp.between(window_start, transaction.timestamp),
                or_(
                    extract('hour', Transaction.timestamp) >= self.LATE_NIGHT_CONFIG["start_hour"],
                    extract('hour', Transaction.timestamp) <= self.LATE_NIGHT_CONFIG["end_hour"]
                )
            ).scalar()
            
            if total_txns >= self.LATE_NIGHT_CONFIG["min_daily_txns"]:
                return (night_txns / total_txns) >= self.LATE_NIGHT_CONFIG["volume_threshold"]
        
        return False

    def _check_spike_pattern(self, db: Session, transaction: Transaction) -> bool:
        """Check for sudden activity spike"""
        # Check transactions in last 24 hours
        window_start = transaction.timestamp - timedelta(hours=24)
        
        txn_count = db.query(func.count(Transaction.id)).filter(
            Transaction.merchant_id == transaction.merchant_id,
            Transaction.timestamp.between(window_start, transaction.timestamp)
        ).scalar()
        
        # Compare with normal range
        return txn_count > self.SPIKE_CONFIG["spike_threshold"]

    def _check_split_pattern(self, db: Session, transaction: Transaction) -> bool:
        """Check for split transactions"""
        window_start = transaction.timestamp - timedelta(minutes=self.SPLIT_CONFIG["time_window"])
        
        # Check for similar transactions from same customer
        similar_txns = db.query(Transaction).filter(
            Transaction.merchant_id == transaction.merchant_id,
            Transaction.customer_id == transaction.customer_id,
            Transaction.timestamp.between(window_start, transaction.timestamp)
        ).all()
        
        if len(similar_txns) >= self.SPLIT_CONFIG["min_splits"]:
            total_amount = sum(tx.amount for tx in similar_txns)
            return self.SPLIT_CONFIG["amount_min"] <= total_amount <= self.SPLIT_CONFIG["amount_max"]
        
        return False

    def _check_round_amount_pattern(self, db: Session, transaction: Transaction) -> bool:
        """Check for round amount patterns"""
        # Check if current amount matches pattern
        if any(abs(transaction.amount - amount) < 1 for amount in self.ROUND_CONFIG["amounts"]):
            # Check frequency in recent transactions
            window_start = transaction.timestamp - timedelta(hours=24)
            
            total_txns = db.query(func.count(Transaction.id)).filter(
                Transaction.merchant_id == transaction.merchant_id,
                Transaction.timestamp.between(window_start, transaction.timestamp)
            ).scalar()
            
            round_txns = db.query(func.count(Transaction.id)).filter(
                Transaction.merchant_id == transaction.merchant_id,
                Transaction.timestamp.between(window_start, transaction.timestamp),
                or_(*[Transaction.amount == amount for amount in self.ROUND_CONFIG["amounts"]])
            ).scalar()
            
            if total_txns > 0:
                return (round_txns / total_txns) >= self.ROUND_CONFIG["threshold"]
        
        return False

    def _check_customer_concentration(self, db: Session, transaction: Transaction) -> bool:
        """Check for customer concentration"""
        window_start = transaction.timestamp - timedelta(hours=self.CONCENTRATION_CONFIG["time_window"])
        
        # Get total volume
        total_volume = db.query(func.sum(Transaction.amount)).filter(
            Transaction.merchant_id == transaction.merchant_id,
            Transaction.timestamp.between(window_start, transaction.timestamp)
        ).scalar() or 0
        
        if total_volume > 0:
            # Get volume per customer
            customer_volumes = db.query(
                Transaction.customer_id,
                func.sum(Transaction.amount).label('volume')
            ).filter(
                Transaction.merchant_id == transaction.merchant_id,
                Transaction.timestamp.between(window_start, transaction.timestamp)
            ).group_by(Transaction.customer_id).all()
            
            # Sort by volume and check concentration
            customer_volumes.sort(key=lambda x: x[1], reverse=True)
            top_customers = customer_volumes[:self.CONCENTRATION_CONFIG["max_customers"]]
            
            if len(top_customers) >= self.CONCENTRATION_CONFIG["min_customers"]:
                top_volume = sum(volume for _, volume in top_customers)
                return (top_volume / total_volume) >= self.CONCENTRATION_CONFIG["volume_threshold"]
        
        return False
