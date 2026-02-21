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
This is basically the starting point of everything. It just sits there and checks 
the `data/` folder every 5 seconds. If it sees a CSV file it hasn't seen before, 
it passes it to the pipeline. I'm keeping track of already processed files in a 
simple set so the same file doesn't get processed twice.

### 2. Validator (`src/validator.py`)
Before doing anything with a file, I check if the data is actually usable. Four 
things get checked:
- are all the columns there that we expect?
- are there any empty/null values in important columns?
- are the numeric columns actually numbers?
- are the sensor readings within a realistic range? (e.g. temperature shouldn't 
be 9000°C)

If any of these fail, the file gets moved to quarantine and we log exactly why 
it failed. No guessing later.

### 3. Transformer (`src/transformer.py`)
Once the data passes validation, this cleans it up and gets it ready for the 
database. The timestamps in the raw data are Unix format (just a big number) so 
I convert those to actual readable datetimes. Column names get renamed to match 
the DB schema, data types get cast properly, and I run a min-max normalization 
on the numeric readings so everything is on the same scale. Each row also gets 
tagged with the filename it came from and when it was processed.

### 4. Aggregator (`src/aggregator.py`)
After transformation this calculates some basic stats for each sensor device — 
min, max, average, and standard deviation for each numeric column. So if there 
are 3 devices in the file, we get a separate stats row for each device for each 
metric. These go into their own table in the DB so you can query them without 
touching the raw data.

### 5. DB Handler (`src/db_handler.py`)
Everything that talks to the database goes through here. Raw rows go into 
`raw_sensor_data`, aggregated stats go into `aggregated_metrics`, and rejected 
files get logged in `quarantine_log`. I added a retry mechanism here too — if 
the DB is down or something goes wrong, it tries again up to 3 times with a 
5 second wait between attempts before finally giving up.

### 6. Pipeline Orchestrator (`src/pipeline.py`)
This is the main file that runs everything. It starts the watcher, and for each 
new file detected it runs through all the steps above in order. If anything breaks 
at any stage the error gets logged and the pipeline just moves on to the next file 
rather than crashing completely. Logs go to both the terminal and a file in `logs/` 
so you can check what happened after the fact.

---

## Database Schema

### `raw_sensor_data`
Every valid sensor reading ends up here, one row per reading.

| Column | Type | Description |
|---|---|---|
| id | SERIAL | Primary key |
| device_id | VARCHAR | Which sensor sent this |
| timestamp | TIMESTAMP | When the reading was taken |
| co | FLOAT | Carbon monoxide level |
| humidity | FLOAT | Humidity percentage |
| light | BOOLEAN | Was the light on or off |
| lpg | FLOAT | LPG gas level |
| motion | BOOLEAN | Was motion detected |
| smoke | FLOAT | Smoke level |
| temp | FLOAT | Temperature in Celsius |
| source_file | VARCHAR | Which CSV file this came from |
| ingested_at | TIMESTAMP | When our pipeline processed it |

### `aggregated_metrics`
Stats per device per file. One row per metric per device.

| Column | Type | Description |
|---|---|---|
| id | SERIAL | Primary key |
| source_file | VARCHAR | Which file these stats are from |
| device_id | VARCHAR | Which sensor device |
| metric_name | VARCHAR | e.g. temp, humidity, co |
| min_value | FLOAT | Lowest reading in the file |
| max_value | FLOAT | Highest reading in the file |
| avg_value | FLOAT | Average across all readings |
| std_value | FLOAT | How much the readings varied |
| record_count | INTEGER | How many rows were in the file |
| aggregated_at | TIMESTAMP | When this was calculated |

### `quarantine_log`
Any file that got rejected gets an entry here with the reason.

| Column | Type | Description |
|---|---|---|
| id | SERIAL | Primary key |
| source_file | VARCHAR | The file that was rejected |
| error_reason | TEXT | Why it was rejected |
| failed_at | TIMESTAMP | When it was rejected |

---

## Fault Tolerance

I tried to make sure one bad file doesn't bring everything down. Each stage has 
its own error handling so if something goes wrong we log it and move on. The DB 
retries a few times before giving up in case it's just a temporary connection 
issue. Bad files get physically moved to quarantine so nothing gets silently 
ignored — you can always go back and look at what failed and why.