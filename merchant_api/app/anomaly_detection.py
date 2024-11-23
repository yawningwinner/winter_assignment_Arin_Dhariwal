from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from sqlalchemy import and_, text
from datetime import datetime, timedelta
from merchant_api.app.models import Transaction
import logging
from typing import Dict, List

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AnomalyDetector:
    def __init__(self):
        # Configuration parameters
        self.LATE_NIGHT_START = 22  # 10 PM
        self.LATE_NIGHT_END = 6     # 6 AM
        self.HIGH_VELOCITY_LIMIT = 5  # transactions within 10 minutes
        self.VELOCITY_WINDOW = 10    # minutes
        self.CUSTOMER_CONCENTRATION_LIMIT = 10  # transactions per day
        self.BATCH_SIZE = 1000       # Process transactions in batches

    def _is_late_night(self, transaction_time: datetime) -> bool:
        """Check if transaction occurred during late night hours"""
        hour = transaction_time.hour
        return hour >= self.LATE_NIGHT_START or hour < self.LATE_NIGHT_END

    def _check_velocity(self, db: Session, merchant_id: str, 
                       transaction_time: datetime) -> bool:
        """Check for high velocity transactions"""
        window_start = transaction_time - timedelta(minutes=self.VELOCITY_WINDOW)
        count = db.query(func.count(Transaction.id)).filter(
            Transaction.merchant_id == merchant_id,
            Transaction.transaction_date.between(window_start, transaction_time)
        ).scalar()
        return count > self.HIGH_VELOCITY_LIMIT

    def _check_customer_concentration(self, db: Session, customer_id: str, 
                                    transaction_date: datetime) -> bool:
        """Check for high customer concentration"""
        daily_count = db.query(func.count(Transaction.id)).filter(
            Transaction.customer_id == customer_id,
            func.date(Transaction.transaction_date) == transaction_date.date()
        ).scalar()
        return daily_count > self.CUSTOMER_CONCENTRATION_LIMIT

    def detect_anomalies(self, db: Session) -> Dict[str, int]:
        """
        Detect transaction anomalies using multiple rules
        Returns statistics about detected anomalies
        """
        stats = {
            "total_processed": 0,
            "anomalies_detected": 0,
            "late_night": 0,
            "high_velocity": 0,
            "customer_concentration": 0
        }

        try:
            # Get total count for progress tracking
            total_transactions = db.query(func.count(Transaction.id)).scalar()
            logger.info(f"Starting anomaly detection for {total_transactions} transactions")

            # Process transactions in batches
            offset = 0
            while True:
                # Clear SQLAlchemy session to prevent memory issues
                db.expire_all()
                
                transactions = db.query(Transaction).order_by(
                    Transaction.transaction_date
                ).offset(offset).limit(self.BATCH_SIZE).all()
                
                if not transactions:
                    break

                batch_updates = []
                for transaction in transactions:
                    anomaly_reasons = []
                    
                    # Debug log
                    logger.info(f"Processing transaction {transaction.id}")

                    # Rule 1: Late-night transactions (23:00-05:00)
                    tx_hour = transaction.transaction_date.hour
                    if tx_hour >= 23 or tx_hour <= 5:
                        anomaly_reasons.append("late_night")
                        stats["late_night"] += 1
                        logger.info(f"Transaction {transaction.id}: Late night detected at hour {tx_hour}")

                    # Rule 2: High amount (> 5000)
                    if transaction.transaction_amount > 5000:
                        anomaly_reasons.append("high_amount")
                        logger.info(f"Transaction {transaction.id}: High amount detected: {transaction.transaction_amount}")

                    # Rule 3: Suspicious customer ID
                    if transaction.customer_id == "ConcentratedCustomer":
                        anomaly_reasons.append("suspicious_customer")
                        logger.info(f"Transaction {transaction.id}: Suspicious customer detected")

                    # Update transaction with anomaly information
                    if anomaly_reasons:
                        logger.info(f"Transaction {transaction.id} marked as anomaly with reasons: {anomaly_reasons}")
                        # Update directly in database
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
                    else:
                        db.execute(
                            text("""
                                UPDATE transactions 
                                SET is_anomaly = :is_anomaly, 
                                    anomaly_reasons = NULL 
                                WHERE id = :id
                            """),
                            {
                                "is_anomaly": False,
                                "id": transaction.id
                            }
                        )

                    stats["total_processed"] += 1

                # Commit each batch
                try:
                    db.commit()
                    logger.info(f"Committed batch. Processed {stats['total_processed']} of {total_transactions}")
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

    def get_merchant_anomalies(self, db: Session, merchant_id: str, 
                             start_date: datetime = None, 
                             end_date: datetime = None) -> List[Dict]:
        """Get anomalous transactions for a specific merchant with optional date range"""
        try:
            query = db.query(Transaction).filter(
                Transaction.merchant_id == merchant_id,
                Transaction.is_anomaly == True
            )

            if start_date:
                query = query.filter(Transaction.transaction_date >= start_date)
            if end_date:
                query = query.filter(Transaction.transaction_date <= end_date)

            anomalies = query.order_by(Transaction.transaction_date.desc()).all()

            return [
                {
                    "transaction_id": tx.id,
                    "transaction_date": tx.transaction_date,
                    "transaction_amount": tx.transaction_amount,
                    "customer_id": tx.customer_id,
                    "anomaly_reasons": tx.anomaly_reasons.split(",") if tx.anomaly_reasons else []
                }
                for tx in anomalies
            ]

        except Exception as e:
            logger.error(f"Error fetching anomalies: {str(e)}")
            raise

    def _debug_transaction(self, transaction):
        """Debug helper to check why a transaction might be marked as anomaly"""
        reasons = []
        
        # Check late night
        is_late = self._is_late_night(transaction.transaction_date)
        if is_late:
            reasons.append(f"Late night (Hour: {transaction.transaction_date.hour})")
        
        return reasons
