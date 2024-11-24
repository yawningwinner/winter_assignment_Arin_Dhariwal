# Winter_Assignment

A merchant transaction analysis system featuring synthetic data generation, database management, and API endpoints for transaction monitoring and anomaly detection.

## Table of Contents
- [Features](#features)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Usage](#usage)
- [API Endpoints](#api-endpoints)

## Features

### 1. Data Generation System
- Generates realistic merchant profiles and transaction data
- Supports multiple business types and GST statuses
- Creates both normal and fraudulent transaction patterns including:
  - Late-night transactions
  - High-velocity transactions
  - Customer concentration patterns
- Configurable parameters for data generation

### 2. Database Management
- SQLAlchemy ORM for database operations
- Support for merchant and transaction data models
- Database initialization and cleanup utilities
- Batch processing for efficient data loading

### 3. REST API
- FastAPI-based endpoints for data access
- Transaction querying with date filtering
- Merchant profile management
- Anomaly detection capabilities

## Project Structure
```
modus_ai/
├── data_generator.py          # Synthetic data generation
├── add_data.py               # Data loading utilities
├── setup.py                  # Project configuration
├── merchant_api/
│   └── app/
│       ├── models.py         # Database models
│       ├── main.py          # API endpoints
│       ├── init_db.py       # Database initialization
│       └── crud.py          # Database operations
```

## Installation

1. **Clone the Repository**
   ```bash
   git clone https://github.com/yawningwinner/winter_assignment_Arin_Dhariwal.git
   ```

2. **Install Dependencies**
   ```bash
   pip install -e .
   ```

3. **Initialize Database**
   ```bash
   python -m merchant_api.app.init_db
   ```

## Usage

### 1. Generate Synthetic Data
```python
from merchant_api.app.db import SessionLocal
from data_generator import generate_test_data

db = SessionLocal()
generate_test_data(db)
db.close()
```

### 2. Load Existing Data
```python
from add_data import load_data

load_data()
```

### 3. Start the API Server
```bash
uvicorn merchant_api.app.main:app --reload
```

## API Endpoints

### Get All Merchants
```http
GET /merchants/
```

### Get Merchant Transactions
```http
GET /transactions/{merchant_id}
```
Query Parameters:
- `start_date`: Optional start date filter (YYYY-MM-DD)
- `end_date`: Optional end date filter (YYYY-MM-DD)

### Detect Anomalies
```http
POST /detect-anomalies/
```

### Get Merchant Anomalies
```http
GET /anomalies/{merchant_id}
```
Query Parameters:
- `start_date`: Optional start date filter (YYYY-MM-DD)
- `end_date`: Optional end date filter (YYYY-MM-DD)

## Data Models

### Merchant
- `merchant_id`: Unique identifier (M-XXXXX format)
- `name`: Business name
- `business_type`: Type of business
- `registration_date`: Date of registration
- `gst_status`: GST registration status
- `avg_transaction_volume`: Average transaction amount

### Transaction
- `merchant_id`: Reference to merchant
- `transaction_date`: Date and time of transaction
- `transaction_amount`: Transaction value
- `customer_id`: Customer identifier
- `is_anomaly`: Anomaly flag
- `anomaly_reasons`: Reasons for anomaly classification
