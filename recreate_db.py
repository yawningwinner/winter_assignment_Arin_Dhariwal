from merchant_api.app.db import engine, Base
from merchant_api.app.models import Merchant, Transaction
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def recreate_database():
    try:
        # Drop all tables
        logger.info("Dropping all tables...")
        Base.metadata.drop_all(bind=engine)
        
        # Create all tables
        logger.info("Creating all tables with new schema...")
        Base.metadata.create_all(bind=engine)
        
        logger.info("Database recreation completed successfully!")
        
    except Exception as e:
        logger.error(f"Error recreating database: {str(e)}")
        raise

if __name__ == "__main__":
    recreate_database() 