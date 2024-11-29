from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional, List, Dict
from merchant_api.app.db import SessionLocal, engine
from merchant_api.app.models import Base, Merchant, Transaction
from merchant_api.app.validation import TransactionValidator, MerchantValidator
from merchant_api.app.processing import DataProcessor
from merchant_api.app.api.endpoints import anomaly
from merchant_api.app.cache import cache_manager
from merchant_api.app.events import event_processor, EventType, EventPriority
from merchant_api.app.model_processor import ModelProcessor

# Create FastAPI app instance
app = FastAPI(title="Merchant Investigation API")

# Initialize components
model_processor = ModelProcessor()

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

# Add the router with correct prefix
app.include_router(anomaly.router, tags=["merchants"])

# Add shutdown event to clean up resources
@app.on_event("shutdown")
async def shutdown_event():
    cache_manager.clear()  # Clear cache on shutdown

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)