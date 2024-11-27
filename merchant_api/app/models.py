from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from merchant_api.app.db import Base

class Merchant(Base):
    __tablename__ = "merchants"

    id = Column(Integer, primary_key=True, index=True)
    
    # Basic Information
    merchant_id = Column(String, unique=True, index=True)
    business_name = Column(String)
    business_type = Column(String)
    registration_date = Column(DateTime)
    
    # Business Details
    business_model = Column(String)  # Online/Offline/Hybrid
    product_category = Column(String)
    average_ticket_size = Column(Float)
    
    # Registration Details
    gst_status = Column(Boolean)
    pan_number = Column(String)
    epfo_registered = Column(Boolean)
    
    # Location Details
    registered_address = Column(String)
    city = Column(String)
    state = Column(String)
    
    # Financial Details
    reported_revenue = Column(Float)
    employee_count = Column(Integer)
    bank_account = Column(String)
    bank_name = Column(String)
    account_number = Column(String)
    status = Column(String)

    # Relationship
    transactions = relationship("Transaction", back_populates="merchant")

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(String, unique=True, index=True)
    merchant_id = Column(String, ForeignKey("merchants.merchant_id"))
    timestamp = Column(DateTime)
    amount = Column(Float)
    
    # Customer Info
    customer_id = Column(String)
    device_id = Column(String)
    customer_location = Column(String)
    
    # Transaction Details
    payment_method = Column(String)
    status = Column(String)
    product_category = Column(String)
    platform = Column(String)
    
    # Risk Indicators
    velocity_flag = Column(Boolean, default=False)
    amount_flag = Column(Boolean, default=False)
    time_flag = Column(Boolean, default=False)
    device_flag = Column(Boolean, default=False)
    
    # Anomaly Detection Fields
    is_anomaly = Column(Boolean, default=False)
    anomaly_reasons = Column(String, nullable=True)

    merchant = relationship("Merchant", back_populates="transactions")
