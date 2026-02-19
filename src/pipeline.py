import os
import shutil
import logging
import pandas as pd
from datetime import datetime
from src.config import QUARANTINE_DIR, LOG_DIR
from src.validator import validate
from src.transformer import transform
from src.aggregator import aggregate
from src.db_handler import insert_raw_data, insert_aggregated_metrics, log_quarantine
from src.file_watcher import FileWatcher

# ── Logging Setup ─────────────────────────────────────────
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(QUARANTINE_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s — %(message)s',
    handlers=[
        logging.FileHandler(
            os.path.join(LOG_DIR, f"pipeline_{datetime.utcnow().strftime('%Y%m%d')}.log")
        ),
        logging.StreamHandler()  # also print to console
    ]
)

logger = logging.getLogger(__name__)


def process_file(filepath: str):
    """
    Full pipeline for a single CSV file:
    1. Read the file
    2. Validate
    3. Transform
    4. Aggregate
    5. Store in DB
    6. Quarantine if invalid
    """

    filename = os.path.basename(filepath)
    logger.info(f"{'='*50}")
    logger.info(f"Processing file: {filename}")

    # ── Step 1: Read CSV ──────────────────────────────────
    try:
        df = pd.read_csv(filepath)
        logger.info(f"[{filename}] Loaded {len(df)} rows")
    except Exception as e:
        logger.error(f"[{filename}] Failed to read file: {e}")
        _quarantine_file(filepath, filename, f"Failed to read CSV: {e}")
        return

    # ── Step 2: Validate ──────────────────────────────────
    is_valid, reason = validate(df, filename)
    if not is_valid:
        logger.warning(f"[{filename}] Validation failed: {reason}")
        _quarantine_file(filepath, filename, reason)
        return

    # ── Step 3: Transform ─────────────────────────────────
    try:
        df = transform(df, filename)
    except Exception as e:
        logger.error(f"[{filename}] Transformation failed: {e}")
        _quarantine_file(filepath, filename, f"Transformation error: {e}")
        return

    # ── Step 4: Aggregate ─────────────────────────────────
    try:
        agg_df = aggregate(df, filename)
    except Exception as e:
        logger.error(f"[{filename}] Aggregation failed: {e}")
        _quarantine_file(filepath, filename, f"Aggregation error: {e}")
        return

    # ── Step 5: Store in DB ───────────────────────────────
    try:
        insert_raw_data(df, filename)
        insert_aggregated_metrics(agg_df, filename)
        logger.info(f"[{filename}] Successfully stored in database")
    except Exception as e:
        logger.error(f"[{filename}] Database insert failed: {e}")
        _quarantine_file(filepath, filename, f"Database insert failed: {e}")
        return

    logger.info(f"[{filename}] Pipeline completed successfully")


def _quarantine_file(filepath: str, filename: str, reason: str):
    """
    Moves a failed file to the quarantine folder and logs the reason.
    """
    try:
        dest = os.path.join(QUARANTINE_DIR, filename)
        shutil.move(filepath, dest)
        logger.info(f"[{filename}] Moved to quarantine: {reason}")
    except Exception as e:
        logger.error(f"[{filename}] Failed to quarantine file: {e}")

    # Log to DB quarantine table
    try:
        log_quarantine(filename, reason)
    except Exception as e:
        logger.error(f"[{filename}] Failed to log quarantine to DB: {e}")


def run():
    """
    Entry point — starts the file watcher which
    triggers process_file() for every new CSV detected.
    """
    logger.info("Pipeline starting up...")
    watcher = FileWatcher(callback=process_file)
    watcher.start()


if __name__ == '__main__':
    run()