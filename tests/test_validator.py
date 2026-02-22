import pandas as pd
import pytest
from src.validator import validate


def make_valid_df():
    """Returns a basic valid dataframe for testing."""
    return pd.DataFrame({
        'ts'      : [1594512000.0, 1594512001.0],
        'device'  : ['b8:27:eb:bf:9d:51', 'b8:27:eb:bf:9d:51'],
        'co'      : [0.004, 0.005],
        'humidity': [51.0, 52.0],
        'light'   : [False, True],
        'lpg'     : [0.007, 0.008],
        'motion'  : [False, False],
        'smoke'   : [0.02, 0.03],
        'temp'    : [22.0, 23.0],
    })


def test_valid_data_passes():
    df = make_valid_df()
    is_valid, reason = validate(df, 'test_file.csv')
    assert is_valid is True
    assert reason == ''


def test_missing_column_fails():
    df = make_valid_df()
    df = df.drop(columns=['temp'])
    is_valid, reason = validate(df, 'test_file.csv')
    assert is_valid is False
    assert 'temp' in reason


def test_null_values_fail():
    df = make_valid_df()
    df.loc[0, 'humidity'] = None
    is_valid, reason = validate(df, 'test_file.csv')
    assert is_valid is False
    assert 'humidity' in reason


def test_out_of_range_temp_fails():
    df = make_valid_df()
    df.loc[0, 'temp'] = 999.0  # way out of range
    is_valid, reason = validate(df, 'test_file.csv')
    assert is_valid is False
    assert 'temp' in reason


def test_out_of_range_humidity_fails():
    df = make_valid_df()
    df.loc[0, 'humidity'] = 200.0  # over 100
    is_valid, reason = validate(df, 'test_file.csv')
    assert is_valid is False
    assert 'humidity' in reason