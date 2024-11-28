from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from datetime import datetime
import logging

from merchant_api.app.db import get_db
from merchant_api.app.models import Transaction, Merchant
from merchant_api.app.schemas import TransactionResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/transactions", tags=["transactions"])

@router.get("/", response_model=List[TransactionResponse])
def get_transactions(
    merchant_id: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None,
    status: Optional[str] = None,
    limit: int = Query(default=100, le=1000),
    db: Session = Depends(get_db)
):
    """
    Get transactions with optional filtering
    """
    try:
        query = db.query(Transaction)

        if merchant_id:
            query = query.filter(Transaction.merchant_id == merchant_id)
        if start_date:
            query = query.filter(Transaction.timestamp >= start_date)
        if end_date:
            query = query.filter(Transaction.timestamp <= end_date)
        if min_amount:
            query = query.filter(Transaction.amount >= min_amount)
        if max_amount:
            query = query.filter(Transaction.amount <= max_amount)
        if status:
            query = query.filter(Transaction.status == status)

        return query.order_by(desc(Transaction.timestamp)).limit(limit).all()

    except Exception as e:
        logger.error(f"Error fetching transactions: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching transactions: {str(e)}"
        )

@router.get("/transactions/stats")
def get_transaction_stats(
    merchant_id: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db)
):
    """
    Get transaction statistics including total volume, average amount, and transaction count.
    """
    query = db.query(
        func.count(Transaction.transaction_id).label('total_transactions'),
        func.sum(Transaction.amount).label('total_volume'),
        func.avg(Transaction.amount).label('average_amount')
    )
    
    if merchant_id:
        query = query.filter(Transaction.merchant_id == merchant_id)
    if start_date:
        query = query.filter(Transaction.timestamp >= start_date)
    if end_date:
        query = query.filter(Transaction.timestamp <= end_date)
    
    result = query.first()
    
    return {
        "total_transactions": result.total_transactions,
        "total_volume": float(result.total_volume) if result.total_volume else 0.0,
        "average_amount": float(result.average_amount) if result.average_amount else 0.0
    }

@router.get("/transactions/patterns")
def detect_patterns(
    merchant_id: str,
    lookback_days: int = Query(default=30, le=90),
    threshold_multiplier: float = Query(default=2.0, ge=1.5, le=5.0),
    db: Session = Depends(get_db)
):
    """
    Detect unusual patterns in transaction data.
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=lookback_days)
    
    # Get merchant's transactions within the time period
    transactions = db.query(Transaction).filter(
        Transaction.merchant_id == merchant_id,
        Transaction.timestamp.between(start_date, end_date)
    ).order_by(Transaction.timestamp).all()
    
    if not transactions:
        raise HTTPException(status_code=404, detail="No transactions found for this merchant")
    
    # Calculate baseline metrics
    amounts = [tx.amount for tx in transactions]
    avg_amount = sum(amounts) / len(amounts)
    threshold = avg_amount * threshold_multiplier
    
    # Detect patterns
    patterns = {
        "high_value_transactions": [
            {
                "transaction_id": tx.transaction_id,
                "amount": tx.amount,
                "timestamp": tx.timestamp
            }
            for tx in transactions if tx.amount > threshold
        ],
        "split_payments": _detect_split_payments(transactions),
        "rapid_succession": _detect_rapid_succession(transactions)
    }
    
    return patterns

def _detect_split_payments(transactions: List[Transaction], time_window_minutes: int = 5):
    """Helper function to detect potential split payments."""
    split_payments = []
    for i, tx1 in enumerate(transactions[:-1]):
        related_txs = []
        for tx2 in transactions[i+1:]:
            time_diff = abs((tx2.timestamp - tx1.timestamp).total_seconds() / 60)
            if time_diff > time_window_minutes:
                break
            if tx1.customer_id == tx2.customer_id:
                related_txs.append({
                    "transaction_id": tx2.transaction_id,
                    "amount": tx2.amount,
                    "timestamp": tx2.timestamp
                })
        if related_txs:
            split_payments.append({
                "main_transaction": {
                    "transaction_id": tx1.transaction_id,
                    "amount": tx1.amount,
                    "timestamp": tx1.timestamp
                },
                "related_transactions": related_txs
            })
    return split_payments

def _detect_rapid_succession(transactions: List[Transaction], time_window_minutes: int = 1):
    """Helper function to detect transactions in rapid succession."""
    rapid_groups = []
    current_group = []
    
    for i, tx in enumerate(transactions):
        if not current_group:
            current_group.append(tx)
            continue
            
        time_diff = abs((tx.timestamp - current_group[-1].timestamp).total_seconds() / 60)
        if time_diff > time_window_minutes:
            rapid_groups.append(current_group)
            current_group = [tx]
        else:
            current_group.append(tx) 