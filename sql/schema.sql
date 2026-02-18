-- ============================================
-- Real-Time Sensor Data Pipeline - DB Schema
-- ============================================

-- Table 1: Raw sensor readings (every valid incoming row)
CREATE TABLE IF NOT EXISTS raw_sensor_data (
    id              SERIAL PRIMARY KEY,
    device_id       VARCHAR(50)     NOT NULL,
    timestamp       TIMESTAMP       NOT NULL,
    co              FLOAT,
    humidity        FLOAT,
    light           BOOLEAN,
    lpg             FLOAT,
    motion          BOOLEAN,
    smoke           FLOAT,
    temp            FLOAT,
    source_file     VARCHAR(255)    NOT NULL,
    ingested_at     TIMESTAMP       DEFAULT CURRENT_TIMESTAMP
);

-- Index for fast querying by device and time
CREATE INDEX IF NOT EXISTS idx_raw_device_id   ON raw_sensor_data(device_id);
CREATE INDEX IF NOT EXISTS idx_raw_timestamp   ON raw_sensor_data(timestamp);
CREATE INDEX IF NOT EXISTS idx_raw_source_file ON raw_sensor_data(source_file);


-- Table 2: Aggregated metrics per device per file
CREATE TABLE IF NOT EXISTS aggregated_metrics (
    id              SERIAL PRIMARY KEY,
    source_file     VARCHAR(255)    NOT NULL,
    device_id       VARCHAR(50)     NOT NULL,
    metric_name     VARCHAR(50)     NOT NULL,  -- e.g. 'temp', 'humidity', 'co'
    min_value       FLOAT,
    max_value       FLOAT,
    avg_value       FLOAT,
    std_value       FLOAT,
    record_count    INTEGER,
    aggregated_at   TIMESTAMP       DEFAULT CURRENT_TIMESTAMP
);

-- Index for fast querying by device and file
CREATE INDEX IF NOT EXISTS idx_agg_device_id   ON aggregated_metrics(device_id);
CREATE INDEX IF NOT EXISTS idx_agg_source_file ON aggregated_metrics(source_file);
CREATE INDEX IF NOT EXISTS idx_agg_metric_name ON aggregated_metrics(metric_name);


-- Table 3: Quarantine log (track every rejected file and why)
CREATE TABLE IF NOT EXISTS quarantine_log (
    id              SERIAL PRIMARY KEY,
    source_file     VARCHAR(255)    NOT NULL,
    error_reason    TEXT            NOT NULL,
    failed_at       TIMESTAMP       DEFAULT CURRENT_TIMESTAMP
);