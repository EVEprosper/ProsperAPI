"""test_split_utils.py: tests for split_utils.py"""
from os import path
from datetime import datetime, timedelta
import requests
from tinydb import TinyDB, Query

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

TEST_DATE = datetime.utcnow() - timedelta(days=10)
FUTURE_DATE = datetime.utcnow() + timedelta(days=10)
DEMO_SPLIT = {
    "type_id":34,
    "type_name":"Tritanium",
    "original_id":34,
    "new_id":35,
    "split_date":TEST_DATE.strftime('%Y-%m-%d'),
    "bool_mult_div":"False",
    "split_rate": 10
}
DEMO_UNSPLIT = {
    "type_id":35,
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

def test_split_history_throws():
    """make sure fetch_split_history throws expected errors"""
    with pytest.raises(exceptions.NoSplitConfigFound):
        split_obj = split_utils.fetch_split_history(
            TEST_CONFIG.get('TEST', 'region_id'),
            int(TEST_CONFIG.get('TEST', 'alt_id')) + 1,
            api_utils.SwitchCCPSource.EMD
        )

@pytest.mark.incremental
class TestNoSplit:
    """validate behavior if there's no split to perform"""
    test_type_id = DEMO_UNSPLIT['type_id']
    def test_future_split(self):
        """try on a split that hasn't happened yet"""
        test_data_esi = split_utils.fetch_split_history(
            TEST_CONFIG.get('TEST', 'region_id'),
            self.test_type_id,
            api_utils.SwitchCCPSource.ESI,
            config=ROOT_CONFIG
        )
        expected_esi = crest_utils.fetch_market_history(
            TEST_CONFIG.get('TEST', 'region_id'),
            self.test_type_id,
            mode=api_utils.SwitchCCPSource.ESI,
            config=ROOT_CONFIG
        )
        for column in test_data_esi.columns.values:
            assert test_data_esi[column].equals(expected_esi[column])
        #assert test_data_esi.equals(crest_utils.fetch_market_history(
        #    TEST_CONFIG.get('TEST', 'region_id'),
        #    self.test_type_id,
        #    mode=api_utils.SwitchCCPSource.ESI,
        #    config=ROOT_CONFIG
        #))

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

        test_data_emd = split_utils.fetch_split_history(
            TEST_CONFIG.get('TEST', 'region_id'),
            self.test_type_id,
            api_utils.SwitchCCPSource.ESI,
            data_range=TEST_CONFIG.get('TEST', 'history_count'),
            config=ROOT_CONFIG
        )
        assert test_data_emd.equals(forecast_utils.fetch_extended_history(
            TEST_CONFIG.get('TEST', 'region_id'),
            self.test_type_id,
            data_range=TEST_CONFIG.get('TEST', 'history_count'),
            config=ROOT_CONFIG
        ))


