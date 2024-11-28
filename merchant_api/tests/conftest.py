import pytest
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys

# Add the parent directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, parent_dir)

from app.models import Base, Merchant, Transaction
from app.config import settings

@pytest.fixture(scope="session")
def test_db():
    """Create test database connection to your generated data"""
    # Use the PostgreSQL database URL from settings
    DATABASE_URL = settings.DATABASE_URL
    
    # Create engine connected to your actual database
    engine = create_engine(DATABASE_URL)
    
    # Create session
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()
    
    yield db
    
    # Just close the session
    db.close()

@pytest.fixture(scope="session")
def sample_merchant(test_db):
    """Get a sample merchant from your generated data"""
    merchant = test_db.query(Merchant).first()
    assert merchant is not None, "No merchants found in database"
    return merchant

@pytest.fixture(scope="session")
def sample_transactions(test_db, sample_merchant):
    """Get a sample of transactions for testing"""
    # Get a mix of normal and fraudulent transactions
    transactions = test_db.query(Transaction)\
        .filter(Transaction.merchant_id == sample_merchant.merchant_id)\
        .limit(1000)\
        .all()
    
    assert len(transactions) > 0, "No transactions found in database"
    return transactions 