from fastapi import FastAPI
from app.api.endpoints import anomaly
from app.db import engine, Base

app = FastAPI(
    title="Merchant API",
    description="API for merchant transaction anomaly detection",
    version="1.0.0"
)

# Create database tables
Base.metadata.create_all(bind=engine)

# Include routers with prefix and tags
app.include_router(
    anomaly.router,
    prefix="/api/v1",
    tags=["anomaly"]
)

# Root endpoint
@app.get("/")
async def root():
    return {"message": "Welcome to Merchant API"}