from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from merchant_api.app.schemas import (
    MerchantProfile, TransactionHistory, RiskMetrics, AnomalyResponse
)
from merchant_api.app.db import get_db
from merchant_api.app.models import Merchant, Transaction
from merchant_api.app.model_processor import ModelProcessor
from merchant_api.app.validation import TransactionValidator, MerchantValidator
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Router configuration
router = APIRouter(
    prefix="/api/Arinki",
    tags=["merchants"]
)

# Simple dependency function right in the same file
def get_model_processor():
    return ModelProcessor()
#Return all merchants
@router.get("/", response_model=List[MerchantProfile])
async def get_all_merchants(
    db: Session = Depends(get_db)
):
    return db.query(Merchant).all()

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
    except Exception as e:
        logger.error(f"Error fetching merchant profile: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/{merchant_id}/transactions", response_model=List[TransactionHistory])
async def get_transaction_history(
    merchant_id: str,
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    limit: int = Query(100, gt=0, le=1000),
    db: Session = Depends(get_db),
    model_processor: ModelProcessor = Depends(get_model_processor)
):
    """Get merchant's transaction history with risk analysis"""
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
        
        # Process transactions with ModelProcessor
        transaction_histories = []
        for txn in transactions:
            # Process transaction through model
            risk_analysis = model_processor.process_transaction({
                "amount": float(txn.amount),
                "timestamp": txn.timestamp,
                "status": txn.status
            })
            
            # Combine transaction data with risk analysis
            transaction_history = {
                "transaction_id": txn.transaction_id,
                "merchant_id": txn.merchant_id,
                "amount": txn.amount,
                "timestamp": txn.timestamp,
                "status": txn.status,
                "platform": txn.platform or "unknown",
                "customer_id": getattr(txn, 'customer_id', "unknown"),
                "device_id": getattr(txn, 'device_id', "unknown"),
                "risk_level": risk_analysis["risk_indicators"]["risk_level"],
                "anomaly_score": risk_analysis["anomaly_score"],
                "risk_patterns": risk_analysis["pattern_match"]
            }
            transaction_histories.append(transaction_history)
            
        return transaction_histories
        
    except Exception as e:
        logger.error(f"Error fetching transaction history: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/{merchant_id}/detect-anomalies")
async def detect_merchant_anomalies(
    merchant_id: str,
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db),
    model_processor: ModelProcessor = Depends(get_model_processor)
):
    """Detect anomalies for a specific merchant"""
    try:
        # Get transactions
        query = db.query(Transaction).filter(Transaction.merchant_id == merchant_id)
        if start_date:
            query = query.filter(Transaction.timestamp >= start_date)
        if end_date:
            query = query.filter(Transaction.timestamp <= end_date)
        
        transactions = query.order_by(Transaction.timestamp).all()
        
        if not transactions:
            return {
                "merchant_id": merchant_id,
                "total_processed": 0,
                "anomalies_detected": 0,
                "details": []
            }

        # Process transactions in batches
        batch_size = 100
        all_anomalies = []
        
        for i in range(0, len(transactions), batch_size):
            batch = transactions[i:i + batch_size]
            batch_data = [{
                "amount": float(t.amount),
                "timestamp": t.timestamp,
                "status": t.status
            } for t in batch]
            
            # Process batch through ModelProcessor
            results = model_processor.process_batch(batch_data)
            
            # Filter high-risk transactions
            for txn, result in zip(batch, results):
                if result["risk_indicators"]["risk_level"] == "high":
                    all_anomalies.append({
                        "transaction_id": txn.transaction_id,
                        "timestamp": txn.timestamp,
                        "amount": txn.amount,
                        "anomaly_score": result["anomaly_score"],
                        "risk_patterns": result["pattern_match"]
                    })
        
        return {
            "merchant_id": merchant_id,
            "total_processed": len(transactions),
            "anomalies_detected": len(all_anomalies),
            "details": all_anomalies
        }
        
    except Exception as e:
        logger.error(f"Error detecting anomalies: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/detect-all-anomalies")
async def detect_all_anomalies(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    merchant_limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    model_processor: ModelProcessor = Depends(get_model_processor)
):
    """Detect anomalies across all merchants"""
    try:
        merchants = db.query(Merchant)\
            .filter(Merchant.status == 'active')\
            .limit(merchant_limit)\
            .all()

        all_results = []
        
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

            # Process transactions
            transaction_data = [{
                "amount": float(t.amount),
                "timestamp": t.timestamp,
                "status": t.status
            } for t in transactions]
            
            results = model_processor.process_batch(transaction_data)
            
            # Filter high-risk transactions
            anomalies = []
            for txn, result in zip(transactions, results):
                if result["risk_indicators"]["risk_level"] == "high":
                    anomalies.append({
                        "transaction_id": txn.transaction_id,
                        "timestamp": txn.timestamp,
                        "amount": txn.amount,
                        "anomaly_score": result["anomaly_score"],
                        "risk_patterns": result["pattern_match"]
                    })
            
            if anomalies:
                all_results.append({
                    "merchant_id": merchant.merchant_id,
                    "total_processed": len(transactions),
                    "anomalies_detected": len(anomalies),
                    "details": anomalies
                })
        
        return all_results

    except Exception as e:
        logger.error(f"Error detecting anomalies across merchants: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error detecting anomalies: {str(e)}"
        )
@router.get("/{merchant_id}/risk-metrics", response_model=Dict)
async def get_merchant_risk_metrics(
    merchant_id: str,
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db),
    model_processor: ModelProcessor = Depends(get_model_processor)
):
    """Get risk metrics for a specific merchant"""
    try:
        # Verify merchant exists
        merchant = db.query(Merchant).filter(Merchant.merchant_id == merchant_id).first()
        if not merchant:
            raise HTTPException(status_code=404, detail=f"Merchant {merchant_id} not found")

        # Get transactions
        query = db.query(Transaction).filter(Transaction.merchant_id == merchant_id)
        if start_date:
            query = query.filter(Transaction.timestamp >= start_date)
        if end_date:
            query = query.filter(Transaction.timestamp <= end_date)
        
        transactions = query.order_by(Transaction.timestamp).all()
        
        if not transactions:
            return {
                "merchant_id": merchant_id,
                "total_transactions": 0,
                "risk_summary": {
                    "high_risk_count": 0,
                    "medium_risk_count": 0,
                    "low_risk_count": 0,
                    "average_risk_score": 0
                },
                "pattern_summary": {
                    "large_amount": 0,
                    "suspicious_time": 0,
                    "high_velocity": 0
                },
                "time_period": {
                    "start_date": start_date,
                    "end_date": end_date
                }
            }

        # Process transactions through ModelProcessor
        transaction_data = [{
            "amount": float(t.amount),
            "timestamp": t.timestamp,
            "status": t.status
        } for t in transactions]
        
        # Process in batches of 100 for efficiency
        batch_size = 100
        all_results = []
        
        for i in range(0, len(transaction_data), batch_size):
            batch = transaction_data[i:i + batch_size]
            results = model_processor.process_batch(batch)
            all_results.extend(results)

        # Calculate metrics
        total_transactions = len(all_results)
        high_risk = sum(1 for r in all_results if r["risk_indicators"]["risk_level"] == "high")
        medium_risk = sum(1 for r in all_results if r["risk_indicators"]["risk_level"] == "medium")
        low_risk = sum(1 for r in all_results if r["risk_indicators"]["risk_level"] == "low")
        avg_risk_score = sum(r["anomaly_score"] for r in all_results) / total_transactions

        # Count patterns
        large_amount_count = sum(1 for r in all_results if "large_amount" in r["pattern_match"])
        suspicious_time_count = sum(1 for r in all_results if "suspicious_time" in r["pattern_match"])
        high_velocity_count = sum(1 for r in all_results if "high_velocity" in r["pattern_match"])

        return {
            "merchant_id": merchant_id,
            "total_transactions": total_transactions,
            "risk_summary": {
                "high_risk_count": high_risk,
                "medium_risk_count": medium_risk,
                "low_risk_count": low_risk,
                "average_risk_score": round(avg_risk_score, 2)
            },
            "pattern_summary": {
                "large_amount": large_amount_count,
                "suspicious_time": suspicious_time_count,
                "high_velocity": high_velocity_count
            },
            "risk_indicators": {
                "high_risk_percentage": round((high_risk / total_transactions) * 100, 2),
                "pattern_frequency": {
                    "large_amount": round((large_amount_count / total_transactions) * 100, 2),
                    "suspicious_time": round((suspicious_time_count / total_transactions) * 100, 2),
                    "high_velocity": round((high_velocity_count / total_transactions) * 100, 2)
                }
            },
            "time_period": {
                "start_date": start_date or min(t.timestamp for t in transactions),
                "end_date": end_date or max(t.timestamp for t in transactions)
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating risk metrics for merchant {merchant_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/{merchant_id}/events", response_model=Dict)
async def get_merchant_events(
    merchant_id: str,
    event_types: List[str] = Query(
        ["large_amount", "high_velocity", "suspicious_time"],
        description="Event types to filter"
    ),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    limit: int = Query(100, gt=0, le=1000),
    db: Session = Depends(get_db),
    model_processor: ModelProcessor = Depends(get_model_processor)
):
    """Get filtered events for a specific merchant"""
    try:
        # Validate event types
        valid_events = {"large_amount", "high_velocity", "suspicious_time"}
        invalid_events = set(event_types) - valid_events
        if invalid_events:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid event types: {', '.join(invalid_events)}"
            )

        # Verify merchant exists
        merchant = db.query(Merchant).filter(Merchant.merchant_id == merchant_id).first()
        if not merchant:
            raise HTTPException(status_code=404, detail=f"Merchant {merchant_id} not found")

        # Get transactions
        query = db.query(Transaction).filter(Transaction.merchant_id == merchant_id)
        if start_date:
            query = query.filter(Transaction.timestamp >= start_date)
        if end_date:
            query = query.filter(Transaction.timestamp <= end_date)
        
        transactions = query.order_by(Transaction.timestamp.desc()).limit(limit).all()
        
        if not transactions:
            return {
                "merchant_id": merchant_id,
                "total_transactions": 0,
                "events": [],
                "time_period": {
                    "start_date": start_date,
                    "end_date": end_date
                }
            }

        # Process transactions through ModelProcessor
        transaction_data = [{
            "amount": float(t.amount),
            "timestamp": t.timestamp,
            "status": t.status
        } for t in transactions]
        
        # Process in batches for high velocity detection
        batch_size = 100
        all_results = []
        events = []
        
        for i in range(0, len(transaction_data), batch_size):
            batch = transaction_data[i:i + batch_size]
            batch_results = model_processor.process_batch(batch)
            
            # Match transactions with their analysis results
            for txn, result in zip(transactions[i:i + batch_size], batch_results):
                matched_events = []
                
                # Check each requested event type
                if "large_amount" in event_types and "large_amount" in result["pattern_match"]:
                    matched_events.append("large_amount")
                
                if "suspicious_time" in event_types and "suspicious_time" in result["pattern_match"]:
                    matched_events.append("suspicious_time")
                    
                if "high_velocity" in event_types and "high_velocity" in result["pattern_match"]:
                    matched_events.append("high_velocity")
                
                if matched_events:  # Only include transactions with matching events
                    events.append({
                        "transaction_id": txn.transaction_id,
                        "timestamp": txn.timestamp,
                        "amount": float(txn.amount),
                        "events": matched_events,
                        "risk_level": result["risk_indicators"]["risk_level"],
                        "anomaly_score": round(result["anomaly_score"], 2)
                    })

        return {
            "merchant_id": merchant_id,
            "total_transactions": len(transactions),
            "events_found": len(events),
            "events": sorted(
                events,
                key=lambda x: x["timestamp"],
                reverse=True
            ),
            "summary": {
                "large_amount": sum(1 for e in events if "large_amount" in e["events"]),
                "suspicious_time": sum(1 for e in events if "suspicious_time" in e["events"]),
                "high_velocity": sum(1 for e in events if "high_velocity" in e["events"])
            },
            "time_period": {
                "start_date": start_date or min(t.timestamp for t in transactions),
                "end_date": end_date or max(t.timestamp for t in transactions)
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching events for merchant {merchant_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

# New Merchant Endpoints
@router.post("/", response_model=MerchantProfile, status_code=status.HTTP_201_CREATED)
async def create_merchant(
    merchant: MerchantValidator,
    db: Session = Depends(get_db)
):
    """Create a new merchant"""
    try:
        # Check if merchant already exists
        existing_merchant = db.query(Merchant).filter(
            Merchant.merchant_id == merchant.merchant_id
        ).first()
        
        if existing_merchant:
            raise HTTPException(
                status_code=400,
                detail=f"Merchant with ID {merchant.merchant_id} already exists"
            )

        # Create new merchant
        new_merchant = Merchant(
            merchant_id=merchant.merchant_id,
            business_name=merchant.business_name,
            business_type=merchant.business_type,
            business_model=merchant.business_model,
            city=merchant.city,
            state=merchant.state,
            status=merchant.status
        )
        
        db.add(new_merchant)
        db.commit()
        db.refresh(new_merchant)
        
        return new_merchant

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating merchant: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")

@router.put("/{merchant_id}", response_model=MerchantProfile)
async def update_merchant(
    merchant_id: str,
    merchant: MerchantValidator,
    db: Session = Depends(get_db)
):
    """Update an existing merchant"""
    try:
        # Verify merchant exists
        existing_merchant = db.query(Merchant).filter(
            Merchant.merchant_id == merchant_id
        ).first()
        
        if not existing_merchant:
            raise HTTPException(
                status_code=404,
                detail=f"Merchant {merchant_id} not found"
            )

        # Update merchant fields
        update_data = merchant.dict(exclude={'merchant_id'}, exclude_unset=True)
        
        # Update fields
        for field, value in update_data.items():
            setattr(existing_merchant, field, value)
        
        db.commit()
        db.refresh(existing_merchant)
        
        return existing_merchant

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating merchant: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")

# New Transaction Endpoints
@router.post("/{merchant_id}/transactions", response_model=TransactionHistory)
async def create_transaction(
    merchant_id: str,
    transaction: TransactionValidator,
    db: Session = Depends(get_db),
    model_processor: ModelProcessor = Depends(get_model_processor)
):
    """Create a new transaction for a merchant"""
    try:
        # Verify merchant exists and is active
        merchant = db.query(Merchant).filter(
            Merchant.merchant_id == merchant_id,
            Merchant.status == 'active'
        ).first()
        
        if not merchant:
            raise HTTPException(
                status_code=404,
                detail=f"Active merchant {merchant_id} not found"
            )

        # Verify merchant_id matches
        if transaction.merchant_id != merchant_id:
            raise HTTPException(
                status_code=400,
                detail="Transaction merchant_id does not match path parameter"
            )

        # Create new transaction
        new_transaction = Transaction(
            transaction_id=transaction.transaction_id,
            merchant_id=transaction.merchant_id,
            amount=transaction.amount,
            customer_id=transaction.customer_id,
            timestamp=transaction.timestamp,
            device_id=transaction.device_id,
            customer_location=transaction.customer_location,
            payment_method=transaction.payment_method,
            status=transaction.status,
            product_category=transaction.product_category,
            platform=transaction.platform
        )
        
        # Process transaction through model
        risk_analysis = model_processor.process_transaction({
            "amount": float(new_transaction.amount),
            "timestamp": new_transaction.timestamp,
            "status": new_transaction.status
        })
        
        db.add(new_transaction)
        db.commit()
        db.refresh(new_transaction)
        
        # Return transaction with risk analysis
        return {
            "transaction_id": new_transaction.transaction_id,
            "merchant_id": new_transaction.merchant_id,
            "amount": new_transaction.amount,
            "timestamp": new_transaction.timestamp,
            "status": new_transaction.status,
            "platform": new_transaction.platform,
            "customer_id": new_transaction.customer_id,
            "device_id": new_transaction.device_id,
            "risk_level": risk_analysis["risk_indicators"]["risk_level"],
            "anomaly_score": risk_analysis["anomaly_score"],
            "risk_patterns": risk_analysis["pattern_match"]
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating transaction: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")
    