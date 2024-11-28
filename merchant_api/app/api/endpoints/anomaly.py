from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from merchant_api.app.schemas import (
    MerchantProfile, MerchantCreate, MerchantUpdate,
    TransactionHistory, TransactionCreate,
    RiskMetrics, AnomalyResponse, AnomalyDetail
)
from merchant_api.app.db import get_db
from merchant_api.app.models import Merchant, Transaction
from merchant_api.app.anomaly_detection import AnomalyDetector
from merchant_api.app.processing import DataProcessor
from merchant_api.app.cache import cached
from merchant_api.app.events import event_processor, EventType, EventPriority
from merchant_api.app.model_processor import ModelProcessor
import logging
import numpy as np
from sqlalchemy import func

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Use a single prefix for all merchant-related endpoints
router = APIRouter(
    prefix="/api/v1/system/merchants",
    tags=["merchants"]
)

# Initialize processors
model_processor = ModelProcessor()

# Merchant Profile Endpoints
@router.get("/{merchant_id}", response_model=MerchantProfile)
async def get_merchant_profile(
    merchant_id: str,
    db: Session = Depends(get_db)
):
    """Get detailed merchant profile"""
    try:
        merchant = db.query(Merchant).filter(Merchant.merchant_id == merchant_id).first()
        if not merchant:
            raise HTTPException(status_code=404, detail=f"Merchant {merchant_id} not found")
        return merchant
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error fetching merchant profile: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Transaction History Endpoints
@router.get("/{merchant_id}/transactions", response_model=List[TransactionHistory])
async def get_transaction_history(
    merchant_id: str,
    start_date: Optional[datetime] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[datetime] = Query(None, description="End date (YYYY-MM-DD)"),
    limit: int = Query(100, gt=0, le=1000),
    db: Session = Depends(get_db)
):
    """Get merchant's transaction history with optional date filtering"""
    try:
        # Verify merchant exists
        merchant = db.query(Merchant).filter(Merchant.merchant_id == merchant_id).first()
        if not merchant:
            raise HTTPException(status_code=404, detail=f"Merchant {merchant_id} not found")

        # Build query
        query = db.query(Transaction).filter(Transaction.merchant_id == merchant_id)
        
        if start_date:
            query = query.filter(Transaction.timestamp >= start_date)
        if end_date:
            query = query.filter(Transaction.timestamp <= end_date)
        
        transactions = query.order_by(Transaction.timestamp.desc()).limit(limit).all()
        
        if not transactions:
            return []
            
        return transactions
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error fetching transaction history: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Risk Metrics Endpoints
@router.get("/{merchant_id}/risk-metrics")
async def get_merchant_risk_metrics(
    merchant_id: str,
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db)
):
    try:
        logger.info(f"Calculating risk metrics for merchant {merchant_id}")
        
        # Validate merchant exists
        merchant = db.query(Merchant).filter(Merchant.merchant_id == merchant_id).first()
        if not merchant:
            logger.warning(f"Merchant not found: {merchant_id}")
            raise HTTPException(status_code=404, detail="Merchant not found")

        # Build query for transactions
        query = db.query(Transaction).filter(Transaction.merchant_id == merchant_id)
        
        if start_date:
            query = query.filter(Transaction.timestamp >= start_date)
        if end_date:
            query = query.filter(Transaction.timestamp <= end_date)
        
        # Execute query and log count
        transactions = query.all()
        logger.info(f"Found {len(transactions)} transactions for analysis")
        
        if not transactions:
            logger.info(f"No transactions found for merchant {merchant_id}")
            return {
                "merchant_id": merchant_id,
                "risk_score": 0,
                "total_transactions": 0,
                "metrics": {
                    "anomaly_rate": 0,
                    "failure_rate": 0,
                    "average_transaction_amount": 0,
                    "transaction_volume": 0
                },
                "time_period": {
                    "start_date": start_date,
                    "end_date": end_date
                }
            }

        # Calculate basic metrics
        total_transactions = len(transactions)
        anomalous_transactions = sum(1 for t in transactions if getattr(t, 'is_anomaly', False))
        failed_transactions = sum(1 for t in transactions if t.status == 'failed')
        
        # Calculate amounts safely
        amounts = [float(t.amount) for t in transactions if t.amount is not None]
        avg_amount = sum(amounts) / len(amounts) if amounts else 0
        
        # Calculate rates
        anomaly_rate = (anomalous_transactions / total_transactions * 100) if total_transactions > 0 else 0
        failure_rate = (failed_transactions / total_transactions * 100) if total_transactions > 0 else 0
        
        # Calculate time period
        actual_start_date = start_date or min(t.timestamp for t in transactions)
        actual_end_date = end_date or max(t.timestamp for t in transactions)
        days_diff = max(1, (actual_end_date - actual_start_date).days)
        
        daily_volume = total_transactions / days_diff
        
        # Calculate risk score with bounds checking
        volume_factor = min(1, daily_volume / 1000)
        amount_factor = min(1, avg_amount / 10000)
        
        risk_score = (
            (anomaly_rate * 0.4) +
            (failure_rate * 0.3) +
            (volume_factor * 20) +
            (amount_factor * 10)
        )
        
        risk_score = max(0, min(100, risk_score))
        
        logger.info(f"Successfully calculated risk metrics for merchant {merchant_id}")
        
        return {
            "merchant_id": merchant_id,
            "risk_score": round(risk_score, 2),
            "total_transactions": total_transactions,
            "metrics": {
                "anomaly_rate": round(anomaly_rate, 2),
                "failure_rate": round(failure_rate, 2),
                "average_transaction_amount": round(avg_amount, 2),
                "transaction_volume": round(daily_volume, 2)
            },
            "time_period": {
                "start_date": actual_start_date,
                "end_date": actual_end_date
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating risk metrics for merchant {merchant_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error calculating risk metrics: {str(e)}"
        )

# Create shared anomaly detection function
def detect_anomalies(transactions: List[Transaction], 
                    time_window_minutes: int = 60,
                    amount_threshold: float = 2.0,
                    volume_threshold: float = 2.0) -> List[Dict]:
    """
    Core anomaly detection logic used by both single-merchant and all-merchant endpoints.
    
    Args:
        transactions: List of transactions to analyze
        time_window_minutes: Size of the sliding window in minutes
        amount_threshold: Number of standard deviations for amount anomalies
        volume_threshold: Number of standard deviations for volume anomalies
    """
    if not transactions:
        return []

    # Sort transactions by timestamp
    sorted_txns = sorted(transactions, key=lambda x: x.timestamp)
    
    # Initialize results
    anomalies = []
    window_size = timedelta(minutes=time_window_minutes)
    
    # Calculate baseline metrics
    all_amounts = [t.amount for t in transactions]
    baseline_mean_amount = np.mean(all_amounts)
    baseline_std_amount = np.std(all_amounts)
    
    # Analyze each transaction
    for i, txn in enumerate(sorted_txns):
        window_start = txn.timestamp - window_size
        window_end = txn.timestamp
        
        # Get transactions in current window
        window_txns = [
            t for t in sorted_txns[max(0, i-100):i+1]  # Use last 100 txns for efficiency
            if window_start <= t.timestamp <= window_end
        ]
        
        # Skip if not enough data
        if len(window_txns) < 5:
            continue
            
        # Calculate window metrics
        window_amounts = [t.amount for t in window_txns]
        window_mean = np.mean(window_amounts)
        window_std = np.std(window_amounts)
        
        # Volume anomaly detection
        expected_volume = len(window_txns) / (time_window_minutes / 60)  # transactions per hour
        actual_volume = len([t for t in window_txns if t.timestamp >= window_end - timedelta(hours=1)])
        
        volume_zscore = (actual_volume - expected_volume) / (np.sqrt(expected_volume) + 1e-6)
        amount_zscore = (txn.amount - window_mean) / (window_std + 1e-6)
        
        # Check for anomalies
        anomaly_types = []
        if abs(amount_zscore) > amount_threshold:
            anomaly_types.append("amount")
        if abs(volume_zscore) > volume_threshold:
            anomaly_types.append("volume")
            
        if anomaly_types:
            anomalies.append({
                "transaction_id": txn.transaction_id,
                "merchant_id": txn.merchant_id,
                "timestamp": txn.timestamp,
                "amount": txn.amount,
                "anomaly_types": anomaly_types,
                "amount_zscore": round(float(amount_zscore), 2),
                "volume_zscore": round(float(volume_zscore), 2)
            })
    
    return anomalies

# Update individual endpoint
@router.post("/{merchant_id}/detect-anomalies")
async def detect_merchant_anomalies_endpoint(
    merchant_id: str,
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db)
):
    try:
        # Get transactions
        query = db.query(Transaction).filter(Transaction.merchant_id == merchant_id)
        if start_date:
            query = query.filter(Transaction.timestamp >= start_date)
        if end_date:
            query = query.filter(Transaction.timestamp <= end_date)
        
        transactions = query.order_by(Transaction.timestamp).all()
        
        # Use shared detection logic
        anomalies = detect_anomalies(transactions)
        
        # Update transaction records
        for anomaly in anomalies:
            txn = db.query(Transaction).filter(
                Transaction.transaction_id == anomaly['transaction_id']
            ).first()
            if txn:
                txn.is_anomaly = True
                txn.anomaly_reasons = ",".join(anomaly['anomaly_types'])
        
        db.commit()
        
        return {
            "merchant_id": merchant_id,
            "total_processed": len(transactions),
            "anomalies_detected": len(anomalies),
            "details": anomalies
        }
        
    except Exception as e:
        logger.error(f"Error detecting anomalies: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error detecting anomalies: {str(e)}"
        )

# Add this new endpoint at the top of the file
@router.get("/", response_model=List[MerchantProfile])
async def get_all_merchants(
    skip: int = Query(0, ge=0, description="Skip first N records"),
    limit: int = Query(100, ge=1, le=1000, description="Limit number of records returned"),
    status: Optional[str] = Query(None, description="Filter by merchant status"),
    db: Session = Depends(get_db)
):
    """Get list of all merchants with optional filtering and pagination"""
    try:
        query = db.query(Merchant)
        
        # Apply status filter if provided
        if status:
            query = query.filter(Merchant.status == status)
        
        # Apply pagination
        merchants = query.offset(skip).limit(limit).all()
        
        if not merchants:
            return []
            
        return merchants
    except Exception as e:
        logger.error(f"Error fetching merchants: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while fetching merchants"
        )

# Update bulk endpoint
@router.post("/detect-all-anomalies")
async def detect_all_anomalies_endpoint(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    merchant_limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    try:
        # Get all active merchants
        merchants = db.query(Merchant)\
            .filter(Merchant.status == 'active')\
            .limit(merchant_limit)\
            .all()

        if not merchants:
            return []

        all_results = []
        
        # Process each merchant using the same detection logic
        for merchant in merchants:
            # Get transactions for analysis
            query = db.query(Transaction)\
                .filter(Transaction.merchant_id == merchant.merchant_id)
            
            if start_date:
                query = query.filter(Transaction.timestamp >= start_date)
            if end_date:
                query = query.filter(Transaction.timestamp <= end_date)
            
            transactions = query.order_by(Transaction.timestamp).all()
            
            if not transactions:
                continue

            # Use shared detection logic
            anomalies = detect_anomalies(transactions)
            
            # Update transaction records
            for anomaly in anomalies:
                txn = db.query(Transaction).filter(
                    Transaction.transaction_id == anomaly['transaction_id']
                ).first()
                if txn:
                    txn.is_anomaly = True
                    txn.anomaly_reasons = ",".join(anomaly['anomaly_types'])
            
            if anomalies:  # Only include merchants with anomalies
                all_results.append({
                    "merchant_id": merchant.merchant_id,
                    "total_processed": len(transactions),
                    "anomalies_detected": len(anomalies),
                    "details": anomalies
                })
        
        # Commit all changes
        db.commit()
        
        return all_results

    except Exception as e:
        logger.error(f"Error detecting anomalies across merchants: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error while detecting anomalies: {str(e)}"
        )

@router.get("/{merchant_id}/summary", response_model=Dict)
async def get_transaction_summary(
    merchant_id: str,
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db)
):
    """Get summarized transaction data for a merchant"""
    try:
        processor = DataProcessor(db)
        summary = processor.summarize_transactions(merchant_id, start_date, end_date)
        return summary
    except Exception as e:
        logger.error(f"Error generating transaction summary: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error generating transaction summary"
        )

@router.get("/{merchant_id}/timeline")
async def get_merchant_timeline(
    merchant_id: str,
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    interval: str = Query("hour", description="Aggregation interval: hour, day, or week"),
    db: Session = Depends(get_db)
):
    try:
        logger.info(f"Generating timeline for merchant {merchant_id}")
        
        # Validate merchant exists
        merchant = db.query(Merchant).filter(Merchant.merchant_id == merchant_id).first()
        if not merchant:
            logger.warning(f"Merchant not found: {merchant_id}")
            raise HTTPException(status_code=404, detail="Merchant not found")

        # Build base query
        query = db.query(Transaction).filter(Transaction.merchant_id == merchant_id)
        
        # Apply date filters if provided
        if start_date:
            query = query.filter(Transaction.timestamp >= start_date)
        if end_date:
            query = query.filter(Transaction.timestamp <= end_date)
            
        # Get all transactions
        transactions = query.order_by(Transaction.timestamp).all()
        
        if not transactions:
            logger.info(f"No transactions found for merchant {merchant_id}")
            return {
                "merchant_id": merchant_id,
                "timeline": [],
                "summary": {
                    "total_transactions": 0,
                    "total_amount": 0,
                    "anomalies_detected": 0
                }
            }

        # Determine time buckets based on interval
        def get_bucket_key(timestamp):
            if interval == "hour":
                return timestamp.replace(minute=0, second=0, microsecond=0)
            elif interval == "day":
                return timestamp.replace(hour=0, minute=0, second=0, microsecond=0)
            else:  # week
                return timestamp - timedelta(days=timestamp.weekday())

        # Group transactions by time bucket
        timeline_data = {}
        for txn in transactions:
            bucket = get_bucket_key(txn.timestamp)
            
            if bucket not in timeline_data:
                timeline_data[bucket] = {
                    "timestamp": bucket,
                    "transaction_count": 0,
                    "total_amount": 0,
                    "successful_transactions": 0,
                    "failed_transactions": 0,
                    "anomalous_transactions": 0,
                    "average_amount": 0
                }
            
            data = timeline_data[bucket]
            data["transaction_count"] += 1
            data["total_amount"] += float(txn.amount)
            
            if txn.status == "success":
                data["successful_transactions"] += 1
            elif txn.status == "failed":
                data["failed_transactions"] += 1
                
            if getattr(txn, 'is_anomaly', False):
                data["anomalous_transactions"] += 1
                
            data["average_amount"] = data["total_amount"] / data["transaction_count"]

        # Convert to list and sort by timestamp
        timeline = [
            {
                "timestamp": str(k),
                "transaction_count": v["transaction_count"],
                "total_amount": round(v["total_amount"], 2),
                "successful_transactions": v["successful_transactions"],
                "failed_transactions": v["failed_transactions"],
                "anomalous_transactions": v["anomalous_transactions"],
                "average_amount": round(v["average_amount"], 2)
            }
            for k, v in timeline_data.items()
        ]
        timeline.sort(key=lambda x: x["timestamp"])

        # Calculate summary statistics
        total_transactions = len(transactions)
        total_amount = sum(float(t.amount) for t in transactions)
        total_anomalies = sum(1 for t in transactions if getattr(t, 'is_anomaly', False))

        logger.info(f"Successfully generated timeline for merchant {merchant_id}")
        
        return {
            "merchant_id": merchant_id,
            "timeline": timeline,
            "summary": {
                "total_transactions": total_transactions,
                "total_amount": round(total_amount, 2),
                "anomalies_detected": total_anomalies
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating timeline for merchant {merchant_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error generating timeline: {str(e)}"
        )

def detect_merchant_anomalies(db: Session, merchant_id: str) -> List[Dict]:
    """Detect anomalies for a specific merchant"""
    # Get merchant transactions for last 24 hours
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=24)
    
    transactions = (db.query(Transaction)
                   .filter(Transaction.merchant_id == merchant_id)
                   .filter(Transaction.timestamp.between(start_time, end_time))
                   .order_by(Transaction.timestamp)
                   .all())
    
    return detect_anomalies(transactions)

def detect_all_merchant_anomalies(db: Session) -> Dict[str, List[Dict]]:
    """Detect anomalies for all merchants"""
    # Get all transactions for last 24 hours
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=24)
    
    transactions = (db.query(Transaction)
                   .filter(Transaction.timestamp.between(start_time, end_time))
                   .order_by(Transaction.timestamp)
                   .all())
    
    # Group transactions by merchant
    merchant_transactions = {}
    for txn in transactions:
        if txn.merchant_id not in merchant_transactions:
            merchant_transactions[txn.merchant_id] = []
        merchant_transactions[txn.merchant_id].append(txn)
    
    # Detect anomalies for each merchant
    all_anomalies = {}
    for merchant_id, merchant_txns in merchant_transactions.items():
        anomalies = detect_anomalies(merchant_txns)
        if anomalies:  # Only include merchants with anomalies
            all_anomalies[merchant_id] = anomalies
            
    return all_anomalies

@router.get("/{merchant_id}/events")
async def get_merchant_events(
    merchant_id: str,
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    event_types: List[str] = Query(["anomaly", "high_volume", "failure_spike"], description="Types of events to include"),
    db: Session = Depends(get_db)
):
    try:
        logger.info(f"Fetching events for merchant {merchant_id}")
        
        # Validate merchant exists
        merchant = db.query(Merchant).filter(Merchant.merchant_id == merchant_id).first()
        if not merchant:
            raise HTTPException(status_code=404, detail="Merchant not found")

        # Build query
        query = db.query(Transaction).filter(Transaction.merchant_id == merchant_id)
        if start_date:
            query = query.filter(Transaction.timestamp >= start_date)
        if end_date:
            query = query.filter(Transaction.timestamp <= end_date)
            
        transactions = query.order_by(Transaction.timestamp).all()
        
        if not transactions:
            return {
                "merchant_id": merchant_id,
                "total_events": 0,
                "events": []
            }

        events = []
        window_size = timedelta(hours=1)
        
        # Group transactions into hourly windows
        windows = {}
        for txn in transactions:
            window_start = txn.timestamp.replace(minute=0, second=0, microsecond=0)
            if window_start not in windows:
                windows[window_start] = []
            windows[window_start].append(txn)

        # Analyze each window for events
        for window_start, window_txns in windows.items():
            window_end = window_start + window_size
            
            # Calculate window metrics
            total_txns = len(window_txns)
            if total_txns == 0:
                continue
                
            failed_txns = sum(1 for t in window_txns if t.status == 'failed')
            anomalous_txns = sum(1 for t in window_txns if getattr(t, 'is_anomaly', False))
            total_amount = sum(float(t.amount) for t in window_txns)
            
            # Check for different types of events
            if "anomaly" in event_types and anomalous_txns > 0:
                events.append({
                    "type": "anomaly",
                    "timestamp": window_start,
                    "details": {
                        "anomalous_transactions": anomalous_txns,
                        "total_transactions": total_txns,
                        "anomaly_rate": round(anomalous_txns / total_txns * 100, 2)
                    },
                    "severity": "high" if anomalous_txns / total_txns > 0.1 else "medium"
                })

            if "high_volume" in event_types and total_txns > 100:  # Threshold can be adjusted
                events.append({
                    "type": "high_volume",
                    "timestamp": window_start,
                    "details": {
                        "transaction_count": total_txns,
                        "total_amount": round(total_amount, 2),
                        "average_amount": round(total_amount / total_txns, 2)
                    },
                    "severity": "high" if total_txns > 200 else "medium"
                })

            if "failure_spike" in event_types and failed_txns > 0:
                failure_rate = failed_txns / total_txns
                if failure_rate > 0.05:  # 5% threshold
                    events.append({
                        "type": "failure_spike",
                        "timestamp": window_start,
                        "details": {
                            "failed_transactions": failed_txns,
                            "total_transactions": total_txns,
                            "failure_rate": round(failure_rate * 100, 2)
                        },
                        "severity": "high" if failure_rate > 0.1 else "medium"
                    })

        # Sort events by timestamp
        events.sort(key=lambda x: x["timestamp"])
        
        logger.info(f"Found {len(events)} events for merchant {merchant_id}")
        
        return {
            "merchant_id": merchant_id,
            "total_events": len(events),
            "events": events,
            "time_period": {
                "start": start_date or min(t.timestamp for t in transactions),
                "end": end_date or max(t.timestamp for t in transactions)
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching events for merchant {merchant_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching merchant events: {str(e)}"
        )
