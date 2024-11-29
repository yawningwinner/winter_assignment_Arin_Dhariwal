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

5. **Data Generation**
   Generates test data:
     ```bash
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

#### 1. Get All Merchants
```http
GET /api/Arinki/merchants/
```

Returns a list of all merchants in the system with their basic information and current status.

#### 2. Get Merchant Profile
```http
GET /api/Arinki/merchants/{merchant_id}
```

Retrieves detailed merchant profile including business information, registration details, and current status.

#### 3. Create Merchant
```http
POST /api/Arinki/merchants/
```

Creates a new merchant in the system. Requires merchant details including business name, type, and location.

**Request Body:**
```json
{
    "merchant_id": "M0001",
    "business_name": "Example Business",
    "business_type": "retail",
    "business_model": "b2c",
    "city": "New York",
    "state": "NY",
    "status": "active"
}
```

#### 4. Update Merchant
```http
PUT /api/Arinki/merchants/{merchant_id}
```

Updates an existing merchant's information. All fields are optional except merchant_id.

#### 5. Get Merchant Risk Metrics
```http
GET /api/Arinki/merchants/{merchant_id}/risk-metrics
```

Calculates and returns comprehensive risk metrics including:
- Overall risk score
- Risk factor breakdown
- Pattern analysis
- Historical trends
- Velocity metrics

#### 6. Get Merchant Events
```http
GET /api/Arinki/merchants/{merchant_id}/events
```

Retrieves filtered events for specific patterns:
- Large amount transactions
- High velocity patterns
- Suspicious time patterns

**Query Parameters:**
- `event_types`: Array of event types to filter
- `start_date`: Optional start date
- `end_date`: Optional end date
- `limit`: Maximum number of events to return (default: 100)

#### 7. Create Transaction
```http
POST /api/Arinki/merchants/{merchant_id}/transactions
```

Creates a new transaction for a merchant with real-time risk analysis.

**Request Body:**
```json
{
    "transaction_id": "TXN123456",
    "merchant_id": "M0001",
    "amount": 1000.00,
    "customer_id": "CUST123",
    "timestamp": "2024-01-01T12:00:00",
    "device_id": "DEV123",
    "customer_location": "New York",
    "payment_method": "credit_card",
    "status": "pending",
    "product_category": "electronics",
    "platform": "web"
}
```

**Response includes:**
- Transaction details
- Risk analysis
- Pattern detection
- Anomaly scores

#### 8. Get Transaction History
```http
GET /api/Arinki/merchants/{merchant_id}/transactions
```

Retrieves transaction history with risk analysis for each transaction.

**Query Parameters:**
- `start_date`: Optional start date
- `end_date`: Optional end date
- `status`: Filter by transaction status
- `limit`: Maximum number of transactions to return

#### 9. Detect Anomalies
```http
POST /api/Arinki/merchants/{merchant_id}/detect-anomalies
```

Performs comprehensive anomaly detection on merchant transactions.

**Response includes:**
- Identified patterns
- Risk levels
- Anomaly details
- Recommended actions

#### 10. System-wide Anomaly Detection
```http
POST /api/Arinki/merchants/detect-all-anomalies
```

Performs batch anomaly detection across all merchants.

**Response includes:**
- Merchant-wise anomalies
- System-wide patterns
- Risk distribution
- Batch analysis results

All endpoints include:
- Proper error handling
- Input validation
- Rate limiting
- Authentication (to be implemented)
- Comprehensive logging


## Testing

Run the test suite:
```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run all tests
pytest tests/
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
│   ├── validation.py       # Input validation
│   └── config.py           # Settings
├── data_generator.py        # Test data generation
└── requirements.txt        # Dependencies
```

## Future Improvements
### Feature Enhancements
- Real-time notification system for high-risk transactions
- Machine learning model integration for improved fraud detection
- Advanced visualization dashboard for pattern analysis

### Code Quality
- Increase test coverage
- Add integration tests
- Implement automated code quality checks

### Data Management
- Add data archival strategy
- Implement data retention policies
- Add data export functionality
- Improve synthetic data generation
- Add data validation rules


