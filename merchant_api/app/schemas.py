from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime

# Merchant Schemas
class MerchantBase(BaseModel):
    business_name: str
    business_type: str
    business_model: str
    city: str
    state: str
    status: str = "active"

class MerchantCreate(MerchantBase):
    merchant_id: str
    bank_name: str
    account_number: str

class MerchantUpdate(MerchantBase):
    business_name: Optional[str] = None
    business_type: Optional[str] = None
    business_model: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    status: Optional[str] = None

class MerchantProfile(MerchantBase):
    merchant_id: str
    registration_date: datetime
    bank_name: str
    account_number: str

    class Config:
        from_attributes = True

# Transaction Schemas
class TransactionBase(BaseModel):
    amount: float
    customer_id: str
    device_id: str
    customer_location: str
    payment_method: str
    status: str
    product_category: str
    platform: str

class TransactionCreate(TransactionBase):
    pass

class TransactionHistory(BaseModel):
    transaction_id: str
    merchant_id: str
    amount: float
    timestamp: datetime
    status: str
    platform: str
    customer_id: str = "unknown"
    device_id: str = "unknown"
    customer_location: str = "unknown"
    payment_method: str = "unknown"
    product_category: str = "unknown"
    is_anomaly: bool = False
    anomaly_reasons: Optional[str] = None

    class Config:
        from_attributes = True

# Risk Metrics Schema
class RiskMetrics(BaseModel):
    merchant_id: str
    risk_score: float
    total_transactions: int
    anomalous_transactions: int
    pattern_distribution: Dict[str, int]
    time_window_days: int
    last_updated: datetime

# Anomaly Detection Schemas
class AnomalyDetail(BaseModel):
    transaction_id: str
    timestamp: datetime
    amount: float
    patterns: List[str]

class AnomalyResponse(BaseModel):
    merchant_id: str
    total_processed: int
    anomalies_detected: int
    patterns: Dict[str, int]
    details: List[AnomalyDetail] 