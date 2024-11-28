# Add consistent error handling
async def get_merchant_profile(merchant_id: str, db: Session):
    try:
        merchant = db.query(Merchant).filter(Merchant.merchant_id == merchant_id).first()
        if not merchant:
            raise HTTPException(status_code=404, detail=f"Merchant {merchant_id} not found")
        return merchant
    except SQLAlchemyError as e:
        logger.error(f"Database error: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error")
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Optional, Dict
from datetime import datetime
import logging

from merchant_api.app.schemas import MerchantResponse
from merchant_api.app.models import Merchant, Transaction
from merchant_api.app.db import get_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/merchants", tags=["merchants"])

@router.get("/", response_model=List[MerchantResponse])
async def get_merchants(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """
    Get list of merchants with their transaction statistics
    """
async def get_merchant_profile(merchant_id: str, db: Session):
    try:
        # First get basic merchant data
        merchants = (
            db.query(Merchant)
            .order_by(Merchant.merchant_id)
            .offset(skip)
            .limit(limit)
            .all()
        )
        
        if not merchants:
            return []
            
        # Get transaction stats for these merchants
        merchant_stats = {}
        for merchant in merchants:
            stats = db.query(
                func.count(Transaction.transaction_id).label('count'),
                func.coalesce(func.sum(Transaction.amount), 0.0).label('volume')
            ).filter(
                Transaction.merchant_id == merchant.merchant_id
            ).first()
            
            merchant_stats[merchant.merchant_id] = {
                'count': stats[0] if stats else 0,
                'volume': float(stats[1]) if stats else 0.0
            }
            
        # Convert to response format
        return [
            MerchantResponse(
                merchant_id=merchant.merchant_id,
                name=f"Merchant {merchant.merchant_id}",
                registration_date=datetime.utcnow(),
                status="active",
                risk_level=get_risk_level(
                    merchant_stats[merchant.merchant_id]['volume'],
                    merchant_stats[merchant.merchant_id]['count']
                ),
                total_transaction_count=merchant_stats[merchant.merchant_id]['count'],
                total_transaction_volume=merchant_stats[merchant.merchant_id]['volume']
            ) 
            for merchant in merchants
        ]
        
    except Exception as e:
        logger.error(f"Database error while fetching merchants: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while fetching merchants"
        )

def get_risk_level(volume: float, count: int) -> str:
    """
    Compute risk level based on transaction volume and count
    """
    if volume > 1000000 or count > 1000:
        return "high"
    elif volume > 100000 or count > 100:
        return "medium"
    else:
        return "low"

@router.get("/api/v1/merchants/{merchant_id}/stats", response_model=Dict)
async def get_merchant_stats(
    merchant_id: str,
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
        merchant = db.query(Merchant).filter(Merchant.merchant_id == merchant_id).first()
        if not merchant:
            raise HTTPException(status_code=404, detail=f"Merchant {merchant_id} not found")
        return merchant
    except SQLAlchemyError as e:
        logger.error(f"Database error: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error")

@router.get("/", response_model=List[MerchantResponse])
async def get_merchants(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Get detailed merchant transaction statistics"""
    """
    Get list of merchants with their transaction statistics
    """
    try:
        query = db.query(Transaction).filter(Transaction.merchant_id == merchant_id)
        
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
            "customer_count": len(set(query.with_entities(Transaction.customer_id).all())),
            "status_distribution": {}
        }

        # Payment method distribution
        payment_methods = query.with_entities(
            Transaction.payment_method,
            func.count(Transaction.transaction_id)
        ).group_by(Transaction.payment_method).all()
        # First get basic merchant data
        merchants = (
            db.query(Merchant)
            .order_by(Merchant.merchant_id)
            .offset(skip)
            .limit(limit)
            .all()
        )
        
        stats["payment_methods"] = {
            method: count for method, count in payment_methods
        }
        if not merchants:
            return []
            
        # Get transaction stats for these merchants
        merchant_stats = {}
        for merchant in merchants:
            stats = db.query(
                func.count(Transaction.transaction_id).label('count'),
                func.coalesce(func.sum(Transaction.amount), 0.0).label('volume')
            ).filter(
                Transaction.merchant_id == merchant.merchant_id
            ).first()
            
            merchant_stats[merchant.merchant_id] = {
                'count': stats[0] if stats else 0,
                'volume': float(stats[1]) if stats else 0.0
            }

        # Location distribution
        locations = query.with_entities(
            Transaction.customer_location,
            func.count(Transaction.transaction_id)
        ).group_by(Transaction.customer_location).all()
        
        stats["locations"] = {
            loc: count for loc, count in locations
        }

        # Status distribution
        statuses = query.with_entities(
            Transaction.status,
            func.count(Transaction.transaction_id)
        ).group_by(Transaction.status).all()
        # Convert to response format
        return [
            MerchantResponse(
                merchant_id=merchant.merchant_id,
                name=f"Merchant {merchant.merchant_id}",
                registration_date=datetime.utcnow(),
                status="active",
                risk_level=get_risk_level(
                    merchant_stats[merchant.merchant_id]['volume'],
                    merchant_stats[merchant.merchant_id]['count']
                ),
                total_transaction_count=merchant_stats[merchant.merchant_id]['count'],
                total_transaction_volume=merchant_stats[merchant.merchant_id]['volume']
            ) 
            for merchant in merchants
        ]
        
        stats["status_distribution"] = {
            status: count for status, count in statuses
        }

        return stats
    except SQLAlchemyError as e:
        logger.error(f"Database error while fetching merchants: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error")

def get_risk_level(volume: float, count: int) -> str:
    """
    Compute risk level based on transaction volume and count
    """
    if volume > 1000000 or count > 1000:
        return "high"
    elif volume > 100000 or count > 100:
        return "medium"
    else:
        return "low"

    except Exception as e:
        logger.error(f"Error fetching merchant stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
@router.get("/api/v1/merchants/{merchant_id}/stats", response_model=Dict)
async def get_merchant_stats(
    merchant_id: str,
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db)
):
    """Get detailed merchant transaction statistics"""
    try:
        # Verify merchant exists
        await get_merchant_profile(merchant_id, db)
        
        query = db.query(Transaction).filter(Transaction.merchant_id == merchant_id)
        
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
            "customer_count": len(set(query.with_entities(Transaction.customer_id).all())),
            "status_distribution": {}
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

        # Status distribution
        statuses = query.with_entities(
            Transaction.status,
            func.count(Transaction.transaction_id)
        ).group_by(Transaction.status).all()
        
        stats["status_distribution"] = {
            status: count for status, count in statuses
        }

        return stats
    except SQLAlchemyError as e:
        logger.error(f"Database error while fetching merchant stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error")

