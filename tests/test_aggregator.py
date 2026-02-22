import pandas as pd
import pytest
from src.aggregator import aggregate


def make_transformed_df():
    """Simulates a dataframe that has already been through transformer."""
    return pd.DataFrame({
        'device_id': ['device_A', 'device_A', 'device_B'],
        'timestamp': pd.to_datetime(['2024-01-01', '2024-01-02', '2024-01-01']),
        'co'       : [0.004, 0.006, 0.003],
        'humidity' : [51.0, 53.0, 60.0],
        'light'    : [False, True, False],
        'lpg'      : [0.007, 0.009, 0.005],
        'motion'   : [False, False, True],
        'smoke'    : [0.02, 0.04, 0.01],
        'temp'     : [22.0, 24.0, 20.0],
        'source_file': ['test.csv', 'test.csv', 'test.csv'],
        'ingested_at': pd.Timestamp.utcnow(),
    })


def test_aggregation_returns_dataframe():
    df = make_transformed_df()
    result = aggregate(df, 'test.csv')
    assert isinstance(result, pd.DataFrame)


def test_aggregation_has_correct_columns():
    df = make_transformed_df()
    result = aggregate(df, 'test.csv')
    expected_cols = [
        'source_file', 'device_id', 'metric_name',
        'min_value', 'max_value', 'avg_value',
        'std_value', 'record_count', 'aggregated_at'
    ]
    for col in expected_cols:
        assert col in result.columns


def test_aggregation_correct_min_max():
    df = make_transformed_df()
    result = aggregate(df, 'test.csv')
    device_a_temp = result[
        (result['device_id'] == 'device_A') &
        (result['metric_name'] == 'temp')
    ]
    assert device_a_temp['min_value'].values[0] == 22.0
    assert device_a_temp['max_value'].values[0] == 24.0


def test_aggregation_groups_by_device():
    df = make_transformed_df()
    result = aggregate(df, 'test.csv')
    devices = result['device_id'].unique()
    assert 'device_A' in devices
    assert 'device_B' in devices