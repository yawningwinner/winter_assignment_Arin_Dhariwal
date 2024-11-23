import logging
from merchant_api.app.init_db import init_database
from data_generator import generate_test_data
from merchant_api.app.db import SessionLocal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_database():
    try:
        # Initialize database schema
        logger.info("Initializing database schema...")
        init_database()
        
        # Generate test data
        logger.info("Generating test data...")
        db = SessionLocal()
        try:
            generate_test_data(db)
        finally:
            db.close()
            
        logger.info("Database setup completed successfully!")
        
    except Exception as e:
        logger.error(f"Error during database setup: {str(e)}")
        raise

if __name__ == "__main__":
    setup_database() 