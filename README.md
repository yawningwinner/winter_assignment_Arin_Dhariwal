# Merchant Transaction Analysis System

A merchant transaction analysis system that generates synthetic merchant data, manages transactions, and provides API endpoints for monitoring and anomaly detection.

## Table of Contents
- [Features](#features)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Database Setup](#database-setup)
- [API Documentation](#api-documentation)
- [Usage Examples](#usage-examples)

## Features

### 1. Data Generation System (`data_generator.py`)
- Generates synthetic merchant profiles and transaction data
- Creates realistic patterns including:
  - Normal business transactions
  - Fraudulent patterns (late-night transactions, high-velocity transactions)
- Configurable parameters for merchant count and transaction volume

### 2. Database Management
- PostgreSQL database with SQLAlchemy ORM
- Merchant and Transaction models
- Database initialization and recreation utilities
- Support for both synthetic and CSV data loading

### 3. REST API Endpoints
#### Merchant Profile Management
- Get all merchants (with pagination)
- Get merchant profile by ID
- Filter merchants by status

#### Transaction Management
- Get transaction history with date filtering
- Transaction status monitoring
- Detailed transaction analysis

#### Risk & Anomaly Detection
- Real-time anomaly detection
- Risk metrics calculation
- Pattern recognition:
  - Large amount transactions
  - Late night activity
  - Round amount patterns
- Bulk anomaly detection across merchants

## Project Structure
```
merchant_api/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── db.py               # Database configuration
│   ├── models.py           # SQLAlchemy models
│   ├── schemas.py          # Pydantic schemas
│   └── api/
│       ├── __init__.py
│       └── endpoints/
│           ├── __init__.py
│           └── anomaly.py   # API endpoints
├── data_generator.py        # Synthetic data generation
├── setup_database.py       # Database setup script
└── requirements.txt        # Project dependencies
```

## Installation

1. **Clone the Repository**
```bash
git clone https://github.com/yawningwinner/winter_assignment_Arin_Dhariwal.git
cd winter_assignment_Arin_Dhariwal
```

2. **Create Virtual Environment**
```bash
python -m venv myenv
source myenv/bin/activate  # On Windows: myenv\Scripts\activate
```

3. **Install Dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure Database**
Update database credentials in `merchant_api/app/db.py`:
```python
DATABASE_URL = "postgresql://user:password@localhost:5432/merchant_db"
```

## Database Setup

1. **Initialize Database**
```bash
python setup_database.py
```

2. **Generate Sample Data**
```bash
python data_generator.py
```
3. **Clear the previously created tables**
```bash
python recreate_db.py
```

## API Documentation

### Available Endpoints

#### Merchant Endpoints
```http
GET /api/v1/merchants
GET /api/v1/merchants/{merchant_id}
```

#### Transaction Endpoints
```http
GET /api/v1/merchants/{merchant_id}/transactions
```

#### Risk & Anomaly Detection
```http
GET /api/v1/merchants/{merchant_id}/risk-metrics
POST /api/v1/merchants/{merchant_id}/detect-anomalies
POST /api/v1/merchants/detect-all-anomalies
```

### Query Parameters
- `start_date`: Filter by start date (YYYY-MM-DD)
- `end_date`: Filter by end date (YYYY-MM-DD)
- `limit`: Number of records to return
- `skip`: Number of records to skip
- `status`: Filter by merchant status

## Usage Examples

### Start the API Server
```bash
uvicorn merchant_api.app.main:app --reload
```

### API Calls

1. **Get All Merchants**
```bash
curl -X GET "http://localhost:8000/api/v1/merchants?limit=10&skip=0"
```

2. **Get Merchant Profile**
```bash
curl -X GET "http://localhost:8000/api/v1/merchants/M5528135"
```

3. **Detect Anomalies**
```bash
curl -X POST "http://localhost:8000/api/v1/merchants/M5528135/detect-anomalies" \
     -H "accept: application/json" \
     -d '{"start_date": "2024-01-01", "end_date": "2024-02-01"}'
```

