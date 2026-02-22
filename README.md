# Real-Time Sensor Data Pipeline

A real-time data pipeline built for processing IoT sensor data. It watches a folder 
for incoming CSV files, validates and transforms the data, computes aggregated metrics 
per sensor device, and stores everything in a PostgreSQL database. Bad files get moved 
to a quarantine folder with a reason logged so nothing is silently ignored.

Built as part of a data engineering assessment.

---

## How it works

You drop a CSV file into the `data/` folder. The pipeline picks it up within 5 seconds, 
runs it through validation, cleans it up, calculates some stats, and loads it into the 
database. If something is wrong with the file it gets moved to `quarantine/` and the 
reason gets logged. The whole thing runs continuously in the background without needing 
any manual input.

---

## Project Structure
```
data-pipeline/
├── data/                   # Drop CSV files here; pipeline watches this folder
├── quarantine/             # Files that failed validation end up here
├── logs/                   # Daily log files get created here automatically
├── sample_data/
│   └── batches/            # Sample CSV files for testing
├── src/
│   ├── config.py           # All settings: DB connection, paths, validation rules
│   ├── validator.py        # Checks incoming data for nulls, types, ranges
│   ├── transformer.py      # Cleans and normalizes the data
│   ├── aggregator.py       # Computes min, max, avg, std per device
│   ├── db_handler.py       # Handles all database inserts with retry logic
│   ├── file_watcher.py     # Monitors the data/ folder for new files
│   └── pipeline.py         # Main orchestrator that ties everything together
├── sql/
│   └── schema.sql          # Database schema — run this first
├── docs/
│   ├── architecture.md     # How the pipeline is designed and why
│   └── scaling.md          # How this would scale in production
├── tests/
│   ├── test_validator.py   # Unit tests for the validation module
│   └── test_aggregator.py  # Unit tests for the aggregation module
├── split_data.py           # Utility script to split large CSV into batches
├── requirements.txt        # Python dependencies
└── .env                    # Your local DB credentials (not committed to git)
```

---

## Requirements

- Python 3.10+
- PostgreSQL 14+
- pip

---

## Setup

### 1. Clone the repo
```bash
git clone https://github.com/ahmedhabib01/data-pipeline.git
cd data-pipeline
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Set up the database

Make sure PostgreSQL is running, then:
```bash
psql -U postgres -c "CREATE DATABASE sensor_pipeline;"
psql -U postgres -d sensor_pipeline -f sql/schema.sql
```

### 4. Create your `.env` file
```
DB_HOST=localhost
DB_PORT=5432
DB_NAME=sensor_pipeline
DB_USER=postgres
DB_PASSWORD=your_password
```

### 5. Run it
```bash
python -m src.pipeline
```

### 6. Test it by dropping a sample file in
```bash
cp sample_data/batches/sensor_batch_001.csv data/
```

You should see it get picked up and processed within 5 seconds.

---

## Running tests
```bash
pytest tests/
```

---

## Dataset

Using the [IoT Sensor Data](https://www.kaggle.com/datasets/garystafford/environmental-sensor-data-132k) 
dataset from Kaggle — temperature, humidity, CO, LPG, smoke, light and motion 
readings from multiple devices. The `split_data.py` script breaks it into smaller 
batch files to simulate incoming data.

---

## Validation rules

| Column | Rule |
|---|---|
| all columns | no nulls allowed |
| co, humidity, lpg, smoke, temp | must be numeric |
| temp | -50 to 50 |
| humidity | 0 to 100 |
| co, lpg, smoke | 0 to 1 |

---

## Dependencies

| Package | Purpose |
|---|---|
| watchdog | watches the folder |
| pandas | data processing |
| psycopg2-binary | PostgreSQL connection |
| python-dotenv | loads .env config |
| pytest | running tests |