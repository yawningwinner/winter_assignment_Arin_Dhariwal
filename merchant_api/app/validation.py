from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pydantic import BaseModel, validator, Field
import re

class TransactionValidator(BaseModel):
    transaction_id: str = Field(..., min_length=8, max_length=32)
    merchant_id: str = Field(..., min_length=4, max_length=16)
    amount: float = Field(..., gt=0)
    customer_id: str
    timestamp: datetime
    device_id: str
    customer_location: str
    payment_method: str
    status: str
    product_category: str
    platform: str

    @validator('transaction_id')
    def validate_transaction_id(cls, v):
        if not re.match(r'^[A-Z0-9]+$', v):
            raise ValueError('Transaction ID must contain only uppercase letters and numbers')
        return v

    @validator('amount')
    def validate_amount(cls, v):
        if v > 1000000:  # Example threshold
            raise ValueError('Transaction amount exceeds maximum limit')
        return v

    @validator('timestamp')
    def validate_timestamp(cls, v):
        if v > datetime.now():
            raise ValueError('Timestamp cannot be in the future')
        if v < datetime.now() - timedelta(days=365):
            raise ValueError('Transaction too old')
        return v

class MerchantValidator(BaseModel):
    merchant_id: str = Field(..., min_length=4, max_length=16)
    business_name: str = Field(..., min_length=2, max_length=100)
    business_type: str
    business_model: str
    city: str
    state: str
    status: str = Field(..., pattern='^(active|inactive|suspended)$')

    # @validator('merchant_id')
    # def validate_merchant_id(cls, v):
    #     if not re.match(r'^M\d+$', v):
    #         raise ValueError('Merchant ID must start with M followed by numbers')
    #     return v 