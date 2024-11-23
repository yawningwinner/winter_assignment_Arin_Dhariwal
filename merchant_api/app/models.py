from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from merchant_api.app.db import Base

class Merchant(Base):
    __tablename__ = "merchants"

    id = Column(Integer, primary_key=True, index=True)
    merchant_id = Column(String, unique=True, index=True)
    name = Column(String)
    business_type = Column(String)
    registration_date = Column(DateTime)
    gst_status = Column(String)
    avg_transaction_volume = Column(Float)

    transactions = relationship("Transaction", back_populates="merchant")

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    merchant_id = Column(String, ForeignKey("merchants.merchant_id"))
    transaction_date = Column(DateTime)
    transaction_amount = Column(Float)
    customer_id = Column(String)
    is_anomaly = Column(Boolean, default=False)
    anomaly_reasons = Column(String, nullable=True)

    merchant = relationship("Merchant", back_populates="transactions")
