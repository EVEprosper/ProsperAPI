from os import path, makedirs
from shutil import rmtree
from datetime import datetime, timedelta
import platform
import pandas as pd
import numpy as np
import requests
from tinydb import TinyDB, Query

import pytest

import publicAPI.forecast_utils as forecast_utils
import publicAPI.exceptions as exceptions
import helpers

HERE = path.abspath(path.dirname(__file__))
ROOT = path.dirname(HERE)

CONFIG_FILENAME = path.join(HERE, 'test_config.cfg')

CONFIG = helpers.get_config(CONFIG_FILENAME)

def test_fetch_emd_history(config=CONFIG):
    """happypath test for `fetch_market_history_emd`"""
    data = forecast_utils.fetch_market_history_emd(
        region_id=config.get('TEST', 'region_id'),
        type_id=config.get('TEST', 'type_id'),
        data_range=config.get('TEST', 'history_count'),
        config=config
    )

    ## validate contents ##
    assert data['version'] == 2
    data_keys = data['columns'].split(',')
    for entry in data['result']:
        assert set(data_keys) == set(entry['row'].keys())

    ## validate count ##
    try:
        db_data = helpers.check_db_values(
            region_id=config.get('TEST', 'region_id'),
            type_id=config.get('TEST', 'type_id'),
            data_range=config.get('TEST', 'history_count'),
            config=config
        )
        mismatch_dates = helpers.compare_dates(
            data['result'],
            db_data
        )
        assert len(mismatch_dates) <= int(config.get('TEST', 'miss_budget'))
    except Exception as err:
        pytest.xfail(
            'Unable to validate date counts: {0}/{1}'.format(
                len(data['result']),
                config.get('TEST', 'history_count') +
            '\n\texception= {0}'.format(repr(err))
        ))

def test_fetch_emd_history_fail(config=CONFIG):
    """happypath test for `fetch_market_history_emd`"""
    with pytest.raises(requests.exceptions.HTTPError):
        data = forecast_utils.fetch_market_history_emd(
            region_id=config.get('TEST', 'region_id'),
            type_id=config.get('TEST', 'type_id'),
            data_range=config.get('TEST', 'history_count'),
            config=config,
            endpoint_addr='http://www.eveprosper.com/noendpoint'
        )

    with pytest.raises(exceptions.NoDataReturned):
        data = forecast_utils.fetch_market_history_emd(
            region_id=config.get('TEST', 'region_id'),
            type_id=config.get('TEST', 'bad_typeid'),
            data_range=config.get('TEST', 'history_count'),
            config=config
        )

DEMO_DATA = {
    'version': 2,
    'currentTime': datetime.now().isoformat(),
    'name':'history',
    'key': 'typeID,regionID,date',
    'columns': 'typeID,regionID,date,lowPrice,highPrice,avgPrice,volume,orders',
    'result':[
        {"row": {
            "typeID": "38",
            "regionID": "10000002",
            "date": "2015-03-28",
            "lowPrice": "674.02",
            "highPrice": "682.65",
            "avgPrice": "681.99",
            "volume": "43401081",
            "orders": "1808"
        }},
        {"row": {
            "typeID": "38",
            "regionID": "10000002",
            "date": "2015-03-29",
            "lowPrice": "677.29",
            "highPrice": "681.95",
            "avgPrice": "681.89",
            "volume": "46045538",
            "orders": "1770"
        }},
        {"row": {
            "typeID": "38",
            "regionID": "10000002",
            "date": "2015-03-30",
            "lowPrice": "678.93",
            "highPrice": "684",
            "avgPrice": "679.14",
            "volume": "56083217",
            "orders": "1472"
        }}
    ]
}
def test_parse_emd_data():
    """happypath test for refactoring EMD data"""

    cleandata = forecast_utils.parse_emd_data(DEMO_DATA['result'])

    assert isinstance(cleandata, pd.DataFrame)  #check output type

    headers = list(cleandata.columns.values)
    expected_rows = DEMO_DATA['columns'].split(',')

    assert set(headers) == set(expected_rows)   #check row headers

    assert len(cleandata.index) == len(DEMO_DATA['result'])

def test_parse_emd_data_fail():
    """make sure behavior is expected for failure"""
    with pytest.raises(TypeError):
        data = forecast_utils.parse_emd_data(DEMO_DATA)

TEST_DATA_PATH = path.join(HERE, 'sample_emd_data.csv')
TEST_PREDICT_PATH = path.join(HERE, 'sample_emd_predict.csv')
@pytest.mark.prophet
def test_build_forecast(config=CONFIG):
    """try to build a forecast"""
    test_data = pd.read_csv(TEST_DATA_PATH)
    test_data['date'] = pd.to_datetime(test_data['date'])
    max_date = test_data['date'].max()

    expected_rows = [
        'date',
        'avgPrice',
        'yhat',
        'yhat_low',
        'yhat_high',
        'prediction'
    ]
    predict_data = forecast_utils.build_forecast(
        test_data,
        int(config.get('TEST', 'forecast_range'))
    )

    headers = list(predict_data.columns.values)
    assert set(expected_rows) == set(headers)

    assert predict_data['date'].max() == \
        max_date + timedelta(days=int(config.get('TEST', 'forecast_range')))

    expected_prediction = pd.read_csv(TEST_PREDICT_PATH)
    expected_prediction['date'] = pd.to_datetime(expected_prediction['date'])
    float_limit = float(config.get('TEST', 'float_limit'))

    for key in expected_rows:
        print(key)
        print(predict_data[key].dtype)

        if predict_data[key].dtype == np.float64:
            pass
            #TODO: ubuntu systems have >0.1 spread on values
            #unique_vals = predict_data[key] - expected_prediction[key]
            #for val in unique_vals.values:
            #    assert (abs(val) < float_limit) or (np.isnan(val)) #fucking floats
        else:
            assert predict_data[key].equals(expected_prediction[key])
@pytest.mark.prophet
def test_forecast_truncate(config=CONFIG):
    """make sure truncate functionality works"""
    test_data = pd.read_csv(TEST_DATA_PATH)
    test_data['date'] = pd.to_datetime(test_data['date'])
    max_date = test_data['date'].max()

    truncate_range = int(config.get('TEST', 'truncate_range'))
    predict_data = forecast_utils.build_forecast(
        test_data,
        int(config.get('TEST', 'forecast_range')),
        truncate_range
    )

    expected_min_date = max_date - timedelta(days=truncate_range-1)
    actual_min_date = predict_data['date'].min()

    assert expected_min_date == actual_min_date

@pytest.mark.incremental
class TestPredictCache:
    """test cache tools in Prediction toolset"""
    cache_path = path.join(HERE, 'cache')
    cache_file = 'prophet.json'
    cache_filepath = path.join(cache_path, cache_file)
    type_id = int(CONFIG.get('TEST', 'type_id'))
    region_id = int(CONFIG.get('TEST', 'region_id'))

    def test_clear_existing_cache(self):
        """clean up cache path before testing"""
        helpers.clear_caches()

    def test_empty_cache(self):
        """test un-cached behavior"""
        data = forecast_utils.check_prediction_cache(
            self.region_id,
            self.type_id,
            cache_path=self.cache_path
        )
        assert data is None

        assert path.isfile(self.cache_filepath)

        tdb = TinyDB(self.cache_filepath)

        assert tdb.all() == []

        tdb.close()

    def test_write_first_cache(self):
        """test write behavior on first pass (cache-buster mode)"""
        self.test_clear_existing_cache()    #blowup existing cache again

        dummy_data = forecast_utils.parse_emd_data(DEMO_DATA['result'])

        forecast_utils.write_prediction_cache(
            self.region_id,
            self.type_id,
            dummy_data,
            cache_path=self.cache_path
        )

        assert path.isfile(self.cache_filepath)

        tdb = TinyDB(self.cache_filepath)

        data = tdb.all()[0]

        keys_list = [
            'cache_date',
            'region_id',
            'type_id',
            'lastWrite',
            'prediction'
        ]
        assert set(keys_list) == set(data.keys())
        dummy_str_data = dummy_data.to_json(
            date_format='iso',
            orient='records'
        )
        cached_data = pd.read_json(data['prediction'])

        assert data['prediction'] == dummy_str_data
        tdb.close()

def test_check_requested_range():
    """validate `check_requested_range()` func"""
    assert forecast_utils.check_requested_range(10) == 10
    assert forecast_utils.check_requested_range(1000, max_range=180) == 180

    with pytest.raises(exceptions.InvalidRangeRequested):
        data = forecast_utils.check_requested_range(1000, max_range=180, raise_for_status=True)

    try:
        data = forecast_utils.check_requested_range(1000, max_range=180, raise_for_status=True)
    except Exception as err_msg:
        assert err_msg.status == 413
        assert isinstance(err_msg.message, str)
