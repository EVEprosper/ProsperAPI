"""test_split_utils.py: tests for split_utils.py"""
from os import path
from math import floor
from datetime import datetime, timedelta
import requests
from tinydb import TinyDB, Query

import pandas as pd
import pytest

import publicAPI.split_utils as split_utils
import publicAPI.config as api_utils
import publicAPI.crest_utils as crest_utils
import publicAPI.forecast_utils as forecast_utils
import publicAPI.exceptions as exceptions
import helpers

HERE = path.abspath(path.dirname(__file__))
ROOT = path.dirname(HERE)

SPLIT_FILE = path.join(ROOT, 'publicAPI', 'split_info.json')
SPLIT_CACHE = path.join(ROOT, 'publicAPI', 'cache', 'splitcache.json')

DAYS_SINCE_SPLIT = 10
TEST_DATE = datetime.utcnow() - timedelta(days=DAYS_SINCE_SPLIT)
FUTURE_DATE = datetime.utcnow() + timedelta(days=DAYS_SINCE_SPLIT)
DEMO_SPLIT = {
    "type_id":35,
    "type_name":"Tritanium",
    "original_id":34,
    "new_id":35,
    "split_date":TEST_DATE.strftime('%Y-%m-%d'),
    "bool_mult_div":"False",
    "split_rate": 10
}
DEMO_UNSPLIT = {
    "type_id":34,
    "type_name":"Pyerite",
    "original_id":34,
    "new_id":35,
    "split_date":FUTURE_DATE.strftime('%Y-%m-%d'),
    "bool_mult_div":"True",
    "split_rate": 10
}
ROOT_CONFIG = helpers.get_config(
    path.join(ROOT, 'scripts', 'app.cfg')
)
TEST_CONFIG = helpers.get_config(
    path.join(HERE, 'test_config.cfg')
)
def test_splitinfo_happypath():
    """test SplitInfo behavior"""
    split_obj = split_utils.SplitInfo(DEMO_SPLIT)

    ## Validate data inside obj ##
    assert split_obj.type_id == DEMO_SPLIT['type_id']
    assert split_obj.type_name == DEMO_SPLIT['type_name']
    assert split_obj.original_id == DEMO_SPLIT['original_id']
    assert split_obj.new_id == DEMO_SPLIT['new_id']
    assert split_obj.split_date == datetime.strptime(DEMO_SPLIT['split_date'], '%Y-%m-%d')
    assert split_obj.date_str == DEMO_SPLIT['split_date']
    assert split_obj.bool_mult_div == False

    assert split_obj.split_rate == DEMO_SPLIT['split_rate']

    assert split_obj.current_typeid() == DEMO_SPLIT['new_id']

    ## Validate magicmethod behavior ##
    assert int(split_obj) == DEMO_SPLIT['new_id']
    assert bool(split_obj)  #should be True
    assert str(split_obj) == DEMO_SPLIT['type_name']

    test_price = 3.5
    test_volume = 1e6

    expected_price = test_price / DEMO_SPLIT['split_rate']
    expected_volume = test_volume * DEMO_SPLIT['split_rate']

    assert test_price * split_obj == expected_price
    assert split_obj * test_price == expected_price
    assert test_volume / split_obj == expected_volume

def test_splitinfo_reverse():
    """validate SplitInfo with "True" bool_mult_div"""
    split_obj = split_utils.SplitInfo(DEMO_UNSPLIT)

    ## Validate data inside obj ##
    assert split_obj.bool_mult_div == True
    assert split_obj.current_typeid() == DEMO_UNSPLIT['original_id']
    test_price = 3.5
    test_volume = 1e6

    expected_price = test_price * DEMO_SPLIT['split_rate']
    expected_volume = test_volume / DEMO_SPLIT['split_rate']

    assert test_price * split_obj == expected_price
    assert split_obj * test_price == expected_price
    assert test_volume / split_obj == expected_volume

def test_splitinfo_throws():
    """make sure bad behavior is caught"""
    short_profile = dict(DEMO_SPLIT)
    short_profile.pop('split_rate', None)
    with pytest.raises(exceptions.InvalidSplitConfig):
        split_obj = split_utils.SplitInfo(short_profile)

    bad_split = dict(DEMO_SPLIT)
    bad_split['split_rate'] = 'bacon'
    with pytest.raises(exceptions.InvalidSplitConfig):
        split_obj = split_utils.SplitInfo(bad_split)

    bad_date = dict(DEMO_SPLIT)
    bad_date['split_date'] = 'Tomorrow'
    with pytest.raises(exceptions.InvalidSplitConfig):
        split_obj = split_utils.SplitInfo(bad_date)

    bad_bool = dict(DEMO_SPLIT)
    bad_bool['bool_mult_div'] = 'bacon'
    with pytest.raises(exceptions.InvalidSplitConfig):
        split_obj = split_utils.SplitInfo(bad_bool)

def test_load_data():
    """push data into global scope for testing"""
    api_utils.SPLIT_INFO = split_utils.read_split_info()
    demosplit_obj = split_utils.SplitInfo(DEMO_SPLIT)
    revrsplit_obj = split_utils.SplitInfo(DEMO_UNSPLIT)

    api_utils.SPLIT_INFO[demosplit_obj.type_id] = demosplit_obj
    api_utils.SPLIT_INFO[revrsplit_obj.type_id] = revrsplit_obj

def test_datetime_helper():
    """validate datetime helper"""
    short_string = '2017-04-01'
    long_string  = '2017-04-01T12:14:10'
    bad_string   = '2017-04-01T12:14:10-07:00'

    short_datetime = split_utils.datetime_helper(short_string)
    long_datetime  = split_utils.datetime_helper(long_string)
    with pytest.raises(ValueError):
        bad_datetime = split_utils.datetime_helper(bad_string)

def test_split_history_throws():
    """make sure fetch_split_history throws expected errors"""
    with pytest.raises(exceptions.NoSplitConfigFound):
        split_obj = split_utils.fetch_split_history(
            TEST_CONFIG.get('TEST', 'region_id'),
            int(TEST_CONFIG.get('TEST', 'alt_id')) + 1,
            api_utils.SwitchCCPSource.EMD
        )

SPLIT_CACHE_FILE = path.join(
    ROOT, 'publicAPI', 'cache', TEST_CONFIG.get('TEST', 'splitcache_file')
)
def test_fetch_cache_data():
    """fetch data from cache and make sure shape is correct"""
    cache_data = split_utils.fetch_split_cache_data(
        TEST_CONFIG.get('TEST', 'region_id'),
        TEST_CONFIG.get('TEST', 'type_id'),
        split_cache_file=SPLIT_CACHE_FILE
    )
    missing_keys = set(cache_data.columns.values) - set(split_utils.KEEP_COLUMNS)
    assert missing_keys == set()

def test_fetch_cache_fail():
    """make sure bad-path is covered"""
    with pytest.raises(exceptions.NoSplitDataFound):
        cache_data = split_utils.fetch_split_cache_data(
            TEST_CONFIG.get('TEST', 'region_id'),
            int(TEST_CONFIG.get('TEST', 'type_id')) + 1,
            split_cache_file=SPLIT_CACHE_FILE
        )

def test_execute_split_forward():
    """check if execute_split works as expected"""
    split_obj = split_utils.SplitInfo(DEMO_SPLIT)
    cache_data = split_utils.fetch_split_cache_data(
        TEST_CONFIG.get('TEST', 'region_id'),
        TEST_CONFIG.get('TEST', 'type_id'),
        split_cache_file=SPLIT_CACHE_FILE
    )

    split_data = split_utils.execute_split(
        cache_data.copy(),  #copy b/c otherwise passed by reference
        split_obj
    )

    price_mod = split_obj.split_rate
    if not split_obj.bool_mult_div:
        price_mod = 1/price_mod
    for col_name in split_utils.PRICE_KEYS:
        price_diff = abs(split_data[col_name] - (cache_data[col_name] * price_mod))
        assert price_diff.max() < float(TEST_CONFIG.get('TEST', 'float_limit'))
        #float() is weird, look for difference to be trivially small

    vol_mod = 1/price_mod
    for col_name in split_utils.VOLUME_KEYS:
        vol_diff = abs(split_data[col_name] - (cache_data[col_name] * vol_mod))
        assert vol_diff.max() < float(TEST_CONFIG.get('TEST', 'float_limit'))

def test_execute_split_backwards():
    """check if execute_split works as expected"""
    split_obj = split_utils.SplitInfo(DEMO_UNSPLIT)
    cache_data = split_utils.fetch_split_cache_data(
        TEST_CONFIG.get('TEST', 'region_id'),
        TEST_CONFIG.get('TEST', 'type_id'),
        split_cache_file=SPLIT_CACHE_FILE
    )

    split_data = split_utils.execute_split(
        cache_data.copy(),  #copy b/c otherwise passed by reference
        split_obj
    )

    price_mod = split_obj.split_rate
    if not split_obj.bool_mult_div:
        price_mod = 1/price_mod
    for col_name in split_utils.PRICE_KEYS:
        price_diff = abs(split_data[col_name] - (cache_data[col_name] * price_mod))
        assert price_diff.max() < float(TEST_CONFIG.get('TEST', 'float_limit'))

    vol_mod = 1/price_mod
    for col_name in split_utils.VOLUME_KEYS:
        vol_diff = abs(split_data[col_name] - (cache_data[col_name] * vol_mod))
        assert vol_diff.max() < float(TEST_CONFIG.get('TEST', 'float_limit'))

@pytest.mark.incremental
class TestNoSplit:
    """validate behavior if there's no split to perform"""
    test_type_id = DEMO_UNSPLIT['type_id']
    def test_future_split_esi(self):
        """validate on ESI"""
        test_data_esi = split_utils.fetch_split_history(
            TEST_CONFIG.get('TEST', 'region_id'),
            self.test_type_id,
            api_utils.SwitchCCPSource.ESI,
            config=ROOT_CONFIG
        )
        assert test_data_esi.equals(crest_utils.fetch_market_history(
            TEST_CONFIG.get('TEST', 'region_id'),
            self.test_type_id,
            mode=api_utils.SwitchCCPSource.ESI,
            config=ROOT_CONFIG
        ))

    def test_future_split_crest(self):
        """validate with CREST source"""
        test_data_crest = split_utils.fetch_split_history(
            TEST_CONFIG.get('TEST', 'region_id'),
            self.test_type_id,
            api_utils.SwitchCCPSource.CREST,
            config=ROOT_CONFIG
        )
        assert test_data_crest.equals(crest_utils.fetch_market_history(
            TEST_CONFIG.get('TEST', 'region_id'),
            self.test_type_id,
            mode=api_utils.SwitchCCPSource.CREST,
            config=ROOT_CONFIG
        ))

    def test_future_split_emd(self):
        """valdiate with EMD source"""
        test_data_emd = split_utils.fetch_split_history(
            TEST_CONFIG.get('TEST', 'region_id'),
            self.test_type_id,
            api_utils.SwitchCCPSource.EMD,
            data_range=TEST_CONFIG.get('TEST', 'history_count'),
            config=ROOT_CONFIG
        )
        emd_data_raw = forecast_utils.fetch_market_history_emd(
            TEST_CONFIG.get('TEST', 'region_id'),
            self.test_type_id,
            data_range=TEST_CONFIG.get('TEST', 'history_count'),
            config=ROOT_CONFIG
        )
        assert test_data_emd.equals(forecast_utils.parse_emd_data(emd_data_raw['result']))

    def test_short_split(self):
        """make sure escaped if split was too far back"""
        short_days = floor(DAYS_SINCE_SPLIT/2)
        test_data_emd = split_utils.fetch_split_history(
            TEST_CONFIG.get('TEST', 'region_id'),
            DEMO_SPLIT['type_id'],
            api_utils.SwitchCCPSource.EMD,
            data_range=short_days,
            config=ROOT_CONFIG
        )
        emd_data_raw = forecast_utils.fetch_market_history_emd(
            TEST_CONFIG.get('TEST', 'region_id'),
            DEMO_SPLIT['type_id'],
            data_range=short_days,
            config=ROOT_CONFIG
        )
        assert test_data_emd.equals(forecast_utils.parse_emd_data(emd_data_raw['result']))
