from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional, List, Dict
from merchant_api.app.db import SessionLocal, engine
from merchant_api.app.models import Base, Merchant, Transaction
from merchant_api.app.anomaly_detection import AnomalyDetector

# Create FastAPI app instance
app = FastAPI(title="Merchant Investigation API")

# Initialize anomaly detector
detector = AnomalyDetector()

# Dependency for database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def read_root():
    return {"message": "Welcome to Merchant Investigation API"}

@app.get("/merchants/", response_model=List[Dict])
def get_merchants(db: Session = Depends(get_db)):
    try:
        merchants = db.query(Merchant).all()
        return [
            {
                "merchant_id": merchant.merchant_id,
                "name": merchant.name,
                "business_type": merchant.business_type,
                "registration_date": merchant.registration_date,
                "gst_status": merchant.gst_status,
                "avg_transaction_volume": merchant.avg_transaction_volume
            }
            for merchant in merchants
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/transactions/{merchant_id}")
def get_transactions(
    merchant_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    try:
        query = db.query(Transaction).filter(Transaction.merchant_id == merchant_id)
        
        if start_date:
            query = query.filter(Transaction.transaction_date >= datetime.fromisoformat(start_date))
        if end_date:
            query = query.filter(Transaction.transaction_date <= datetime.fromisoformat(end_date))
        
        transactions = query.all()
        
        if not transactions:
            raise HTTPException(
                status_code=404,
                detail=f"No transactions found for merchant {merchant_id}"
            )
        
        return [
            {
                "transaction_id": tx.id,
                "merchant_id": tx.merchant_id,
                "transaction_date": tx.transaction_date,
                "transaction_amount": tx.transaction_amount,
                "customer_id": tx.customer_id,
                "is_anomaly": tx.is_anomaly if hasattr(tx, 'is_anomaly') else False,
                "anomaly_reasons": tx.anomaly_reasons.split(",") if hasattr(tx, 'anomaly_reasons') and tx.anomaly_reasons else []
            }
            for tx in transactions
        ]
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid date format. Please use YYYY-MM-DD format. Error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/detect-anomalies/")
def trigger_anomaly_detection(db: Session = Depends(get_db)):
    try:
        stats = detector.detect_anomalies(db)
        return {
            "message": "Anomaly detection completed successfully",
            "statistics": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/anomalies/{merchant_id}")
def get_anomalies(
    merchant_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    try:
        start_dt = datetime.fromisoformat(start_date) if start_date else None
        end_dt = datetime.fromisoformat(end_date) if end_date else None
        
        anomalies = detector.get_merchant_anomalies(db, merchant_id, start_dt, end_dt)
        if not anomalies:
            raise HTTPException(
                status_code=404,
                detail=f"No anomalies found for merchant {merchant_id}"
            )
        return anomalies
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid date format. Please use YYYY-MM-DD format. Error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Add this at the end of the file
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)