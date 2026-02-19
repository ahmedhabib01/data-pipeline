import pandas as pd
import logging
from datetime import datetime
from src.config import NUMERIC_COLUMNS, BOOLEAN_COLUMNS

logger = logging.getLogger(__name__)


def transform(df: pd.DataFrame, filename: str) -> pd.DataFrame:
    """
    Transforms and normalizes raw sensor data.
    Returns a cleaned, standardized dataframe ready for DB insert.
    """

    logger.info(f"[{filename}] Starting transformation, rows: {len(df)}")

    # ── Step 1: Convert Unix timestamp to datetime ────────
    df['ts'] = pd.to_datetime(df['ts'], unit='s')
    logger.info(f"[{filename}] Timestamps converted to datetime")

    # ── Step 2: Rename columns to match DB schema ─────────
    df = df.rename(columns={
        'ts'    : 'timestamp',
        'device': 'device_id',
    })

    # ── Step 3: Cast numeric columns to float ─────────────
    for col in NUMERIC_COLUMNS:
        df[col] = df[col].astype(float).round(6)

    # ── Step 4: Cast boolean columns ──────────────────────
    for col in BOOLEAN_COLUMNS:
        df[col] = df[col].astype(bool)

    # ── Step 5: Normalize numeric columns (min-max) ───────
    for col in NUMERIC_COLUMNS:
        col_min = df[col].min()
        col_max = df[col].max()
        if col_max - col_min > 0:
            df[f'{col}_normalized'] = (
                (df[col] - col_min) / (col_max - col_min)
            ).round(6)
        else:
            df[f'{col}_normalized'] = 0.0

    # ── Step 6: Tag with metadata ─────────────────────────
    df['source_file'] = filename
    df['ingested_at'] = datetime.utcnow()

    logger.info(f"[{filename}] Transformation complete")
    return df 