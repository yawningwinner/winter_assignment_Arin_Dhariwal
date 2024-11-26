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
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

# Merchant Profile Endpoints
@router.get("/merchants/{merchant_id}", response_model=MerchantProfile)
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
@router.get("/merchants/{merchant_id}/transactions", response_model=List[TransactionHistory])
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
@router.get("/merchants/{merchant_id}/risk-metrics", response_model=RiskMetrics)
async def get_risk_metrics(
    merchant_id: str,
    time_window: int = Query(30, gt=0, le=365, description="Time window in days"),
    db: Session = Depends(get_db)
):
    """Get merchant risk metrics and statistics"""
    try:
        # Verify merchant exists
        merchant = db.query(Merchant).filter(Merchant.merchant_id == merchant_id).first()
        if not merchant:
            raise HTTPException(status_code=404, detail=f"Merchant {merchant_id} not found")

        start_date = datetime.now() - timedelta(days=time_window)
        
        # Get transaction metrics
        total_txns = db.query(Transaction).filter(
            Transaction.merchant_id == merchant_id,
            Transaction.timestamp >= start_date
        ).count()
        
        anomaly_txns = db.query(Transaction).filter(
            Transaction.merchant_id == merchant_id,
            Transaction.timestamp >= start_date,
            Transaction.is_anomaly == True
        ).count()
        
        # Calculate risk score (basic implementation)
        risk_score = (anomaly_txns / total_txns * 100) if total_txns > 0 else 0
        
        # Get pattern distribution
        pattern_counts: Dict[str, int] = {}
        anomalies = db.query(Transaction).filter(
            Transaction.merchant_id == merchant_id,
            Transaction.timestamp >= start_date,
            Transaction.is_anomaly == True
        ).all()
        
        for tx in anomalies:
            if tx.anomaly_reasons:
                for pattern in tx.anomaly_reasons.split(","):
                    pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1
        
        return {
            "merchant_id": merchant_id,
            "risk_score": risk_score,
            "total_transactions": total_txns,
            "anomalous_transactions": anomaly_txns,
            "pattern_distribution": pattern_counts,
            "time_window_days": time_window,
            "last_updated": datetime.now()
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error calculating risk metrics: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Anomaly Detection Endpoint
@router.post("/merchants/{merchant_id}/detect-anomalies", response_model=AnomalyResponse)
async def detect_anomalies(
    merchant_id: str,
    start_date: Optional[datetime] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[datetime] = Query(None, description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """Run anomaly detection on merchant transactions"""
    try:
        # Verify merchant exists
        merchant = db.query(Merchant).filter(Merchant.merchant_id == merchant_id).first()
        if not merchant:
            raise HTTPException(status_code=404, detail=f"Merchant {merchant_id} not found")

        # Get transactions for analysis
        query = db.query(Transaction).filter(Transaction.merchant_id == merchant_id)
        if start_date:
            query = query.filter(Transaction.timestamp >= start_date)
        if end_date:
            query = query.filter(Transaction.timestamp <= end_date)
        
        transactions = query.order_by(Transaction.timestamp).all()
        
        if not transactions:
            return AnomalyResponse(
                merchant_id=merchant_id,
                total_processed=0,
                anomalies_detected=0,
                patterns={},
                details=[]
            )

        # Process transactions for anomalies
        anomaly_details = []
        pattern_counts = {}
        anomaly_count = 0

        for txn in transactions:
            # Simple anomaly checks (you can expand these)
            patterns = []
            
            # Check for large amounts
            if txn.amount > 10000:  # Example threshold
                patterns.append("large_amount")
            
            # Check for late night transactions
            if txn.timestamp.hour >= 23 or txn.timestamp.hour <= 4:
                patterns.append("late_night")
            
            # Update transaction if anomalies found
            if patterns:
                anomaly_count += 1
                txn.is_anomaly = True
                txn.anomaly_reasons = ",".join(patterns)
                
                # Update pattern counts
                for pattern in patterns:
                    pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1
                
                # Add to details
                anomaly_details.append(AnomalyDetail(
                    transaction_id=txn.transaction_id,
                    timestamp=txn.timestamp,
                    amount=txn.amount,
                    patterns=patterns
                ))
        
        # Commit changes to database
        db.commit()
        
        return AnomalyResponse(
            merchant_id=merchant_id,
            total_processed=len(transactions),
            anomalies_detected=anomaly_count,
            patterns=pattern_counts,
            details=anomaly_details
        )

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error detecting anomalies: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error while detecting anomalies: {str(e)}"
        )

# Add this new endpoint at the top of the file
@router.get("/merchants", response_model=List[MerchantProfile])
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

# Add this new endpoint
@router.post("/merchants/detect-all-anomalies", response_model=List[AnomalyResponse])
async def detect_all_anomalies(
    start_date: Optional[datetime] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[datetime] = Query(None, description="End date (YYYY-MM-DD)"),
    merchant_limit: int = Query(100, ge=1, le=1000, description="Maximum number of merchants to process"),
    db: Session = Depends(get_db)
):
    """Run anomaly detection on all merchants' transactions"""
    try:
        # Get all active merchants
        merchants = db.query(Merchant)\
            .filter(Merchant.status == 'active')\
            .limit(merchant_limit)\
            .all()

        if not merchants:
            return []

        all_results = []
        
        # Process each merchant
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

            # Process transactions for anomalies
            anomaly_details = []
            pattern_counts = {}
            anomaly_count = 0

            for txn in transactions:
                patterns = []
                
                # Large amount check
                if txn.amount > 10000:
                    patterns.append("large_amount")
                
                # Late night check
                if txn.timestamp.hour >= 23 or txn.timestamp.hour <= 4:
                    patterns.append("late_night")
                
                # Suspicious round amounts
                if txn.amount.is_integer() and txn.amount >= 1000:
                    patterns.append("round_amount")
                
                # Update transaction if anomalies found
                if patterns:
                    anomaly_count += 1
                    txn.is_anomaly = True
                    txn.anomaly_reasons = ",".join(patterns)
                    
                    # Update pattern counts
                    for pattern in patterns:
                        pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1
                    
                    # Add to details
                    anomaly_details.append(AnomalyDetail(
                        transaction_id=txn.transaction_id,
                        timestamp=txn.timestamp,
                        amount=txn.amount,
                        patterns=patterns
                    ))
            
            # Add results for this merchant
            if anomaly_count > 0:
                all_results.append(AnomalyResponse(
                    merchant_id=merchant.merchant_id,
                    total_processed=len(transactions),
                    anomalies_detected=anomaly_count,
                    patterns=pattern_counts,
                    details=anomaly_details
                ))
        
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
