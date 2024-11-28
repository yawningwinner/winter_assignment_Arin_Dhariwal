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

### Merchant API Endpoints

#### 1. Get Merchant Profile
```http
GET /api/v1/system/merchants/{merchant_id}
```
Retrieves detailed merchant profile including business information, status, and key metrics. Use this endpoint to get a comprehensive view of a merchant's profile and current standing.

#### 2. Get Transaction History
```http
GET /api/v1/system/merchants/{merchant_id}/transactions
```
Fetches paginated transaction history for a specific merchant. Includes detailed transaction data, payment methods, amounts, and statuses. Supports filtering by date range and transaction status.

#### 3. Get Risk Metrics
```http
GET /api/v1/system/merchants/{merchant_id}/risk-metrics
```
Calculates and returns comprehensive risk metrics for a merchant. This includes:
- Overall risk score (0-100)
- Transaction volume analysis
- Failure rate patterns
- Velocity checks
- Historical risk trends

#### 4. Detect Merchant Anomalies
```http
POST /api/v1/system/merchants/{merchant_id}/detect-anomalies
```
Analyzes a specific merchant's transactions for anomalies using advanced detection algorithms. Identifies unusual patterns in:
- Transaction amounts
- Transaction frequency
- Geographic distribution
- Time-based patterns

#### 5. List All Merchants
```http
GET /api/v1/system/merchants
```
Returns a paginated list of all merchants in the system. Includes basic information for each merchant and supports filtering by status, business type, and risk level.

#### 6. Detect All Anomalies
```http
POST /api/v1/system/merchants/detect-all-anomalies
```
Performs bulk anomaly detection across all merchants. Useful for system-wide monitoring and identifying patterns that might not be visible at individual merchant level.

#### 7. Get Transaction Summary
```http
GET /api/v1/system/merchants/{merchant_id}/summary
```
Provides aggregated transaction statistics including:
- Total transaction volume
- Success/failure rates
- Average transaction size
- Peak transaction periods
- Payment method distribution

#### 8. Get Merchant Timeline
```http
GET /api/v1/system/merchants/{merchant_id}/timeline
```
Generates a chronological view of merchant activity, showing:
- Transaction patterns over time
- Key events and milestones
- Volume trends
- Risk score changes
- Notable incidents


## Testing

Run the test suite:
```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run all tests
pytest tests/
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
```bash
# Run model processor tests
python test_model.py
```

### Data Processing (`app/processing.py`)
Manages transaction data analysis and reporting:
```bash
# Run data processing tests
# Default: analyzes 5 merchants
python test_processing.py

# Analyze specific number of merchants
python test_processing.py --limit 10
```

### Data Models (`app/models.py`) and Schemas (`app/schemas.py`)
Database models and data validation schemas:
```bash
# Run schema validation tests
python test_schemas.py --limit 10
```

### Validation (`app/validation.py`)
Input validation and data integrity:
```bash
# Run validation tests
python test_validation.py --limit 10
```

### Test All Modules
```bash
# Run all test files
python test_model.py
python test_processing.py
python test_schemas.py
python test_validation.py
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


