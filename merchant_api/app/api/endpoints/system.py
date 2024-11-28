import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from datetime import datetime
from sqlalchemy import func

from merchant_api.app.schemas import MerchantResponse
from merchant_api.app.models import Merchant, Transaction
from merchant_api.app.db import get_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/system", tags=["system"])

@router.get("/merchants/", response_model=List[MerchantResponse])
async def get_merchants(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    try:
        merchants = (
            db.query(Merchant)
            .order_by(Merchant.merchant_id)
            .offset(skip)
            .limit(limit)
            .all()
        )
        
        if not merchants:
            return []
            
        return merchants
        
    except Exception as e:
        logger.error(f"Database error while fetching merchants: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while fetching merchants"
        ) 

@router.get("/stats", response_model=Dict)
async def get_system_stats(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db)
):
    """Get system-wide transaction statistics"""
    try:
        query = db.query(Transaction)
        
        if start_date:
            query = query.filter(Transaction.timestamp >= start_date)
        if end_date:
            query = query.filter(Transaction.timestamp <= end_date)

        stats = {
            "total_transactions": query.count(),
            "total_volume": float(query.with_entities(func.sum(Transaction.amount)).scalar() or 0),
            "payment_methods": {},
            "locations": {},
            "device_count": len(set(query.with_entities(Transaction.device_id).all())),
            "customer_count": len(set(query.with_entities(Transaction.customer_id).all()))
        }

        # Payment method distribution
        payment_methods = query.with_entities(
            Transaction.payment_method,
            func.count(Transaction.transaction_id)
        ).group_by(Transaction.payment_method).all()
        
        stats["payment_methods"] = {
            method: count for method, count in payment_methods
        }

        # Location distribution
        locations = query.with_entities(
            Transaction.customer_location,
            func.count(Transaction.transaction_id)
        ).group_by(Transaction.customer_location).all()
        
        stats["locations"] = {
            loc: count for loc, count in locations
        }

        return stats

    except Exception as e:
        logger.error(f"Error fetching system stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error") 