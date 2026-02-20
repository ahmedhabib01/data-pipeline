# Pipeline Architecture

## Overview

This pipeline monitors a local folder for incoming CSV files containing IoT sensor 
data, validates and transforms the data, computes aggregated metrics, and stores 
everything in a PostgreSQL database. It runs continuously without manual intervention 
and handles failures gracefully.

---

## Architecture Diagram
```
+------------------+       +------------------+       +------------------+
|                  |       |                  |       |                  |
|   data/ folder   | ----> |   File Watcher   | ----> |    Validator     |
|   (CSV files)    |       |  (every 5 sec)   |       |                  |
|                  |       |                  |       +--------+---------+
+------------------+       +------------------+                |
                                                        Valid  |  Invalid
                                                               |
                                          +--------------------+----------+
                                          |                               |
                                 +--------v---------+          +----------v--------+
                                 |                  |          |                   |
                                 |   Transformer    |          |   Quarantine/     |
                                 |                  |          |   Error Log       |
                                 +--------+---------+          |                   |
                                          |                    +-------------------+
                                          |
                                 +--------v---------+
                                 |                  |
                                 |   Aggregator     |
                                 |                  |
                                 +--------+---------+
                                          |
                                 +--------v---------+
                                 |                  |
                                 |   DB Handler     |
                                 |  (PostgreSQL)    |
                                 |                  |
                                 +------------------+
```

---

## Components

### 1. File Watcher (`src/file_watcher.py`)
Continuously scans the `data/` folder every 5 seconds for new CSV files. When a 
new file is detected it triggers the pipeline immediately. Already processed files 
are tracked in memory to avoid duplicate processing.

### 2. Validator (`src/validator.py`)
Runs four checks on every incoming file:
- **Column check** — ensures all required columns are present
- **Null check** — rejects files with missing values in key fields
- **Type check** — ensures numeric columns contain numeric data
- **Range check** — ensures sensor readings fall within acceptable ranges

Files that fail any check are moved to `quarantine/` with a detailed reason logged.

### 3. Transformer (`src/transformer.py`)
Prepares validated data for storage:
- Converts Unix timestamps to human-readable datetime
- Renames columns to match the database schema
- Casts columns to correct data types
- Applies min-max normalization to numeric sensor readings
- Tags each row with the source filename and ingestion timestamp

### 4. Aggregator (`src/aggregator.py`)
After transformation, computes per-device metrics for each numeric column:
- Minimum, maximum, average, and standard deviation
- Groups by `device_id` so each device gets its own metric record
- Tags results with source file and aggregation timestamp

### 5. DB Handler (`src/db_handler.py`)
Manages all database interactions:
- Inserts raw transformed rows into `raw_sensor_data` table
- Inserts computed metrics into `aggregated_metrics` table
- Logs rejected files into `quarantine_log` table
- Implements retry logic — retries up to 3 times on failure with a 5 second delay

### 6. Pipeline Orchestrator (`src/pipeline.py`)
The main entry point that wires all components together. It:
- Sets up logging to both console and daily log files
- Starts the file watcher
- Passes each detected file through the full pipeline
- Handles errors at every stage without crashing the entire process

---

## Database Schema

### `raw_sensor_data`
Stores every valid incoming sensor reading with metadata tags.

| Column | Type | Description |
|---|---|---|
| id | SERIAL | Primary key |
| device_id | VARCHAR | Sensor device identifier |
| timestamp | TIMESTAMP | Reading timestamp |
| co | FLOAT | Carbon monoxide level |
| humidity | FLOAT | Humidity percentage |
| light | BOOLEAN | Light sensor state |
| lpg | FLOAT | LPG gas level |
| motion | BOOLEAN | Motion detected |
| smoke | FLOAT | Smoke level |
| temp | FLOAT | Temperature in Celsius |
| source_file | VARCHAR | Origin CSV filename |
| ingested_at | TIMESTAMP | When it was processed |

### `aggregated_metrics`
Stores computed statistics per device per file.

| Column | Type | Description |
|---|---|---|
| id | SERIAL | Primary key |
| source_file | VARCHAR | Origin CSV filename |
| device_id | VARCHAR | Sensor device identifier |
| metric_name | VARCHAR | e.g. temp, humidity, co |
| min_value | FLOAT | Minimum reading |
| max_value | FLOAT | Maximum reading |
| avg_value | FLOAT | Average reading |
| std_value | FLOAT | Standard deviation |
| record_count | INTEGER | Number of rows aggregated |
| aggregated_at | TIMESTAMP | When aggregation ran |

### `quarantine_log`
Tracks every rejected file and the reason for rejection.

| Column | Type | Description |
|---|---|---|
| id | SERIAL | Primary key |
| source_file | VARCHAR | Rejected filename |
| error_reason | TEXT | Why it was rejected |
| failed_at | TIMESTAMP | When it was rejected |

---

## Fault Tolerance

- Every stage is wrapped in try/except — a failure in one file does not stop the pipeline
- Failed DB inserts are retried up to 3 times before giving up
- All errors are written to dated log files in `logs/`
- Rejected files are physically moved to `quarantine/` for manual inspection
- The file watcher recovers from unexpected errors and continues scanning