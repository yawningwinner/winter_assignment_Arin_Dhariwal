import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from merchant_api.app.models import Base
from merchant_api.app.db import engine
from data_generator import DataGenerator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_database():
    """Initialize database schema and populate with test data"""
    try:
        logger.info("Initializing database schema...")
        # Drop and recreate all tables
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        
        # Create a database session
        Session = sessionmaker(bind=engine)
        db = Session()
        
        logger.info("Generating test data...")
        DataGenerator(db)
        
        logger.info("Database setup completed successfully!")
        
    except Exception as e:
        logger.error(f"Error during database setup: {str(e)}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    setup_database() 