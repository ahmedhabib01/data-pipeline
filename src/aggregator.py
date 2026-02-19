import pandas as pd
import logging
from datetime import datetime
from src.config import NUMERIC_COLUMNS

logger = logging.getLogger(__name__)


def aggregate(df: pd.DataFrame, filename: str) -> pd.DataFrame:
    """
    Calculates min, max, avg, and std for each numeric metric
    per device. Returns a dataframe ready for DB insert.
    """

    logger.info(f"[{filename}] Starting aggregation")

    records = []

    for device_id, group in df.groupby('device_id'):
        for col in NUMERIC_COLUMNS:
            if col in group.columns:
                records.append({
                    'source_file'  : filename,
                    'device_id'    : device_id,
                    'metric_name'  : col,
                    'min_value'    : round(group[col].min(), 6),
                    'max_value'    : round(group[col].max(), 6),
                    'avg_value'    : round(group[col].mean(), 6),
                    'std_value'    : round(group[col].std(), 6),
                    'record_count' : len(group),
                    'aggregated_at': datetime.utcnow(),
                })

    agg_df = pd.DataFrame(records)
    logger.info(
        f"[{filename}] Aggregation complete — "
        f"{len(agg_df)} metric records generated"
    )
    return agg_df