# Merchant Transaction Analysis System

A real-time transaction monitoring system that detects fraudulent patterns and anomalies in merchant transactions. The system generates synthetic merchant data, processes transactions, and provides API endpoints for analysis.

## Features

- Real-time transaction monitoring
- Fraud pattern detection
- Synthetic data generation
- REST API endpoints
- PostgreSQL database with SQLAlchemy ORM

## Quick Start

### Prerequisites
- Python 3.8+
- PostgreSQL
- Virtual environment (recommended)

### First-Time Setup

1. **Clone Repository**
   ```bash
   git clone https://github.com/yawningwinner/winter_assignment_Arin_Dhariwal.git
   cd winter_assignment_Arin_Dhariwal
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv myenv
   source myenv/bin/activate  # On Mac/Linux
   # or
   myenv\Scripts\activate     # On Windows
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Database Setup**
   ```bash
   # Create PostgreSQL database and user
   createdb merchant_db
   createuser merchant_user

   # Grant privileges (in psql)
   psql merchant_db
   GRANT ALL PRIVILEGES ON DATABASE merchant_db TO merchant_user;
   \q
   ```

5. **System Initialization**
   - **1. Database Setup (`setup_database.py`)**
     Handles initial database schema creation and setup:
     ```bash
     python setup_database.py
     ```

     This script:
     - Creates required database tables:
       - `merchants`: Merchant profiles and details
       - `transactions`: Transaction records and metadata
       - `audit_logs`: System audit trails
     - Sets up indexes for performance optimization
     - Establishes foreign key relationships
     - Creates necessary constraints
     - Initializes lookup tables (if any)

   - **2. Data Generation (`data_generator.py`)**
     After schema setup, generates test data:
     ```bash
     python data_generator.py
     ```

   - **3. Database Recreation (`recreate_db.py`)**
     For resetting the system to a clean state:
     ```bash
     python recreate_db.py
     ```

   The initialization sequence should be:
   ```bash
   # 1. First-time setup
   python setup_database.py
   python data_generator.py

   # Or for a clean restart
   python recreate_db.py
   python data_generator.py
   ```

6. **Start API Server**
   ```bash
   uvicorn app.main:app --reload
   ```

   API will be available at:
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

## API Documentation

### Merchant Endpoints
- `GET /api/v1/merchants` - List all merchants (with pagination)
- `GET /api/v1/merchants/{merchant_id}` - Get merchant details
- `GET /api/v1/merchants/{merchant_id}/transactions` - Get merchant's transactions

### Transaction Analysis
- `GET /api/v1/merchants/{merchant_id}/risk-metrics` - Get merchant risk analysis
- `POST /api/v1/merchants/{merchant_id}/detect-anomalies` - Run anomaly detection
- `POST /api/v1/merchants/detect-all-anomalies` - Bulk anomaly detection

### Query Parameters
- `start_date`: Filter by start date (YYYY-MM-DD)
- `end_date`: Filter by end date (YYYY-MM-DD)
- `limit`: Number of records per page
- `skip`: Number of records to skip
- `status`: Filter by merchant status

## Testing

Run the test suite:
```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run all tests
pytest tests/

# Run with coverage
pytest --cov=app tests/
```

## Data Management

### Generate Fresh Data
```bash
# Clear existing data and recreate schema
python recreate_db.py

# Generate new test data
python data_generator.py
```

### Fraud Patterns Generated
- Late night trading patterns
- Sudden activity spikes
- Split transactions
- Round amount patterns
- Customer concentration patterns

## Configuration

Key settings in `app/config.py`:
```python
# Database
DATABASE_URL = "postgresql://merchant_user@localhost:5432/merchant_db"

# Data Generation
NUM_MERCHANTS = 100
FRAUD_RATIO = 0.03  # 3% fraud transactions

# Pattern Detection
LATE_NIGHT_START = 23  # 11 PM
LATE_NIGHT_END = 4    # 4 AM
SPIKE_THRESHOLD = 3.0
```

## Core Modules

### Model Processor (`app/model_processor.py`)
Handles real-time transaction analysis and fraud detection:
- Transaction scoring and risk assessment
- Pattern detection (large amounts, suspicious timing)
- Batch processing with velocity checks
- Cached results for performance optimization

```python
# Example usage
processor = ModelProcessor()
result = processor.process_transaction(transaction_data)
print(result['anomaly_score'])  # 0.75
```

### Data Processing (`app/processing.py`)
Manages transaction data analysis and reporting:
- Transaction summarization and metrics
- Risk scoring and trend analysis
- Timeline generation for significant events
- Location-based risk assessment

```python
# Example usage
processor = DataProcessor(db_session)
metrics = processor.calculate_risk_metrics(merchant_id)
print(metrics['risk_score'])  # 65.4
```

### Data Models (`app/models.py`)
SQLAlchemy models defining the database schema:
- Merchant information
- Transaction records
- Relationship mappings
- Audit trails

### Data Schemas (`app/schemas.py`)
Pydantic models for data validation and serialization:
- `MerchantProfile`: Merchant details and registration
- `TransactionHistory`: Transaction records with anomaly flags
- `RiskMetrics`: Risk scoring and pattern analysis
- `AnomalyResponse`: Anomaly detection results

### Validation (`app/validation.py`)
Input validation and data integrity:
- Transaction data validation
- Merchant information validation
- Business rule enforcement
- Format and constraint checking

```python
# Example validation
validator = TransactionValidator(
    transaction_id="TX123",
    amount=500.00,
    # ... other fields
)
```

## Project Structure
```
merchant_api/
├── app/
│   ├── main.py              # FastAPI application
│   ├── db.py               # Database configuration
│   ├── models.py           # SQLAlchemy models
│   ├── schemas.py          # Pydantic schemas
│   ├── model_processor.py  # Transaction analysis
│   ├── processing.py       # Data processing
│   ├── validation.py       # Input validation
│   └── config.py           # Settings
├── data_generator.py        # Test data generation
├── recreate_db.py          # Database management
└── requirements.txt        # Dependencies
```

## Future Improvements

### Performance Optimizations
- Implement Redis caching for frequently accessed data
- Add database query optimization and indexing
- Implement batch processing for large datasets
- Add connection pooling for better database performance

### Feature Enhancements
- Real-time notification system for high-risk transactions
- Machine learning model integration for improved fraud detection
- Advanced visualization dashboard for pattern analysis

### Code Quality
- Increase test coverage
- Add integration tests
- Implement CI/CD pipeline
- Add API documentation generation
- Implement automated code quality checks

### Data Management
- Add data archival strategy
- Implement data retention policies
- Add data export functionality
- Improve synthetic data generation
- Add data validation rules


