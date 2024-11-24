# Winter_Assignment

A merchant transaction analysis system that generates synthetic merchant data, manages transactions, and provides API endpoints for monitoring and analysis.

## Table of Contents
- [Features](#features)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Database Setup](#database-setup)
- [Usage](#usage)
- [API Endpoints](#api-endpoints)

## Features

### 1. Data Generation System (`data_generator.py`)
- Generates synthetic merchant profiles and transaction data
- Creates realistic patterns including:
  - Normal business transactions
  - Fraudulent patterns (late-night transactions, high-velocity transactions, customer concentration)
- Configurable parameters for merchant count and transaction volume
- Supports various business types and GST statuses

### 2. Database Management
- PostgreSQL database with SQLAlchemy ORM
- Merchant and Transaction models
- Database initialization and recreation utilities
- Support for both synthetic and CSV data loading

### 3. REST API (`main.py`)
- FastAPI-based endpoints for data access
- Transaction querying with date filtering
- Merchant profile management
- Anomaly detection capabilities

## Project Structure
```
modus_ai/
├── data_generator.py          # Synthetic data generation
├── add_data.py               # CSV data loading utility
├── setup_database.py         # Database setup script
├── recreate_db.py           # Database recreation utility
├── merchant_api/
│   └── app/
│       ├── models.py         # Database models
│       ├── main.py          # API endpoints
│       ├── init_db.py       # Database initialization
│       └── db.py            # Database configuration
```

## Installation

1. **Clone the Repository**
   ```bash
   git clone https://github.com/yawningwinner/winter_assignment_Arin_Dhariwal.git
   ```

2. **Install Dependencies**
   ```bash
   pip install fastapi sqlalchemy psycopg2-binary uvicorn pandas python-dotenv
   ```

3. **Configure Database**
   - Ensure PostgreSQL is installed and running
   - Update database credentials in `merchant_api/app/db.py`

## Database Setup

### Option 1: Generate Synthetic Data
```bash
python setup_database.py
```
This will:
- Initialize the database schema
- Generate synthetic merchants and transactions
- Include both normal and fraudulent patterns

### Option 2: Load from CSV
```bash
python add_data.py
```
This will:
- Clear existing tables
- Load merchant profiles from `data/merchant_profiles.csv`
- Load transactions from `data/transaction_data.csv`

### Reset Database
```bash
python recreate_db.py
```

## Usage

### Start the API Server
```bash
uvicorn merchant_api.app.main:app --reload
```

## API Endpoints

### Get All Merchants
```http
GET /merchants/
```
Returns a list of all merchant profiles.

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
Triggers anomaly detection across all transactions.

### Get Merchant Anomalies
```http
GET /anomalies/{merchant_id}
```
Query Parameters:
- `start_date`: Optional start date filter (YYYY-MM-DD)
- `end_date`: Optional end date filter (YYYY-MM-DD)

## Data Models

### Merchant
```python
class Merchant:
    merchant_id: str          # Format: M-XXXXX
    name: str                 # Business name
    business_type: str        # Type of business
    registration_date: date   # Registration date
    gst_status: str          # GST registration status
    avg_transaction_volume: float
```

### Transaction
```python
class Transaction:
    merchant_id: str          # Reference to merchant
    transaction_date: datetime
    transaction_amount: float
    customer_id: str
    is_anomaly: bool
    anomaly_reasons: str      # Comma-separated reasons
```

## Database Configuration
The default database configuration in `db.py`:
```python
DATABASE_URL = "postgresql://merchant_user:password123@localhost:5432/merchant_db"
```
Update these credentials according to your PostgreSQL setup.
