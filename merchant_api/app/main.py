from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional, List, Dict
from merchant_api.app.db import SessionLocal, engine
from merchant_api.app.models import Base, Merchant, Transaction
from merchant_api.app.anomaly_detection import AnomalyDetector
from merchant_api.app.api.endpoints import anomaly

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

# Add the router with prefix
app.include_router(
    anomaly.router,
    prefix="/api/v1",
    tags=["merchants"]
)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)