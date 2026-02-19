import time
import logging
import psycopg2
import pandas as pd
from psycopg2.extras import execute_values
from src.config import DB_CONFIG, MAX_RETRIES, RETRY_DELAY

logger = logging.getLogger(__name__)


def get_connection():
    """Creates and returns a new database connection."""
    return psycopg2.connect(**DB_CONFIG)


def insert_raw_data(df: pd.DataFrame, filename: str):
    """
    Inserts transformed sensor rows into raw_sensor_data table.
    Retries up to MAX_RETRIES times on failure.
    """

    columns = [
        'device_id', 'timestamp', 'co', 'humidity', 'light',
        'lpg', 'motion', 'smoke', 'temp', 'source_file', 'ingested_at'
    ]

    rows = [
        (
            row['device_id'],
            row['timestamp'],
            row['co'],
            row['humidity'],
            bool(row['light']),
            row['lpg'],
            bool(row['motion']),
            row['smoke'],
            row['temp'],
            row['source_file'],
            row['ingested_at'],
        )
        for _, row in df.iterrows()
    ]

    _insert_with_retry(
        query=f"""
            INSERT INTO raw_sensor_data
            ({', '.join(columns)})
            VALUES %s
        """,
        rows=rows,
        label=f"raw data [{filename}]"
    )


def insert_aggregated_metrics(agg_df: pd.DataFrame, filename: str):
    """
    Inserts aggregated metric rows into aggregated_metrics table.
    Retries up to MAX_RETRIES times on failure.
    """

    rows = [
        (
            row['source_file'],
            row['device_id'],
            row['metric_name'],
            row['min_value'],
            row['max_value'],
            row['avg_value'],
            row['std_value'],
            row['record_count'],
            row['aggregated_at'],
        )
        for _, row in agg_df.iterrows()
    ]

    _insert_with_retry(
        query="""
            INSERT INTO aggregated_metrics
            (source_file, device_id, metric_name, min_value,
             max_value, avg_value, std_value, record_count, aggregated_at)
            VALUES %s
        """,
        rows=rows,
        label=f"aggregated metrics [{filename}]"
    )


def log_quarantine(filename: str, reason: str):
    """
    Logs a rejected file into the quarantine_log table.
    """
    _insert_with_retry(
        query="""
            INSERT INTO quarantine_log (source_file, error_reason)
            VALUES %s
        """,
        rows=[(filename, reason)],
        label=f"quarantine log [{filename}]"
    )


def _insert_with_retry(query: str, rows: list, label: str):
    """
    Generic insert with retry logic.
    Attempts the insert up to MAX_RETRIES times before giving up.
    """
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            conn = get_connection()
            cur  = conn.cursor()
            execute_values(cur, query, rows)
            conn.commit()
            cur.close()
            conn.close()
            logger.info(f"Successfully inserted {label} on attempt {attempt}")
            return

        except Exception as e:
            logger.error(
                f"Insert failed for {label} "
                f"(attempt {attempt}/{MAX_RETRIES}): {e}"
            )
            if attempt < MAX_RETRIES:
                logger.info(f"Retrying in {RETRY_DELAY} seconds...")
                time.sleep(RETRY_DELAY)
            else:
                logger.critical(
                    f"All {MAX_RETRIES} attempts failed for {label}. "
                    f"Data may be lost!"
                )
                raise