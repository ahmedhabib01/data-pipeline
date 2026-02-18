# Real-Time Sensor Data Pipeline

A real-time data pipeline that monitors a folder for incoming CSV files containing IoT sensor data, validates and transforms the data, and stores it in a PostgreSQL database for analysis.

## What it does

- Watches the `data/` folder every 5-10 seconds for new CSV files
- Validates incoming data (null checks, type checks, range checks)
- Moves bad files to `quarantine/` with detailed error logs
- Normalizes and transforms valid data
- Calculates aggregated metrics (min, max, avg, std) per sensor
- Stores everything in PostgreSQL

## Project Structure
```
data-pipeline/
├── data/           # Drop CSV files here for processing
├── quarantine/     # Files that failed validation end up here
├── logs/           # Processing and error logs
├── src/            # Pipeline source code
├── sql/            # Database schema
├── docs/           # Architecture and scaling docs
├── tests/          # Unit tests
├── sample_data/    # Sample CSVs for testing
└── requirements.txt
```

## Setup

Coming soon — full setup instructions will be added as the pipeline is built.

## Tech Stack

- Python 3.10+
- PostgreSQL
- watchdog (folder monitoring)
- pandas (data processing)
- SQLAlchemy (database ORM)