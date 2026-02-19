import pandas as pd
import logging
from src.config import REQUIRED_COLUMNS, NUMERIC_COLUMNS, BOOLEAN_COLUMNS, VALUE_RANGES

logger = logging.getLogger(__name__)


def validate(df: pd.DataFrame, filename: str) -> tuple[bool, str]:
    """
    Runs all validation checks on a dataframe.
    Returns (True, '') if valid, or (False, reason) if invalid.
    """

    # ── Check 1: Required columns present ────────────────
    missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_cols:
        reason = f"Missing required columns: {missing_cols}"
        logger.warning(f"[{filename}] {reason}")
        return False, reason

    # ── Check 2: No nulls in key fields ──────────────────
    null_counts = df[REQUIRED_COLUMNS].isnull().sum()
    cols_with_nulls = null_counts[null_counts > 0].index.tolist()
    if cols_with_nulls:
        reason = f"Null values found in columns: {cols_with_nulls}"
        logger.warning(f"[{filename}] {reason}")
        return False, reason

    # ── Check 3: Numeric columns must be numeric ──────────
    for col in NUMERIC_COLUMNS:
        if not pd.api.types.is_numeric_dtype(df[col]):
            try:
                df[col] = pd.to_numeric(df[col], errors='raise')
            except Exception:
                reason = f"Column '{col}' contains non-numeric values"
                logger.warning(f"[{filename}] {reason}")
                return False, reason

    # ── Check 4: Value range checks ───────────────────────
    for col, (min_val, max_val) in VALUE_RANGES.items():
        if col in df.columns:
            out_of_range = df[(df[col] < min_val) | (df[col] > max_val)]
            if not out_of_range.empty:
                reason = (
                    f"Column '{col}' has {len(out_of_range)} rows "
                    f"outside acceptable range [{min_val}, {max_val}]"
                )
                logger.warning(f"[{filename}] {reason}")
                return False, reason

    logger.info(f"[{filename}] Validation passed successfully")
    return True, ''