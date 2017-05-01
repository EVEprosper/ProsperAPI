"""test_split_utils.py: tests for split_utils.py"""
from os import path
from datetime import datetime, timedelta
import requests
from tinydb import TinyDB, Query

import pytest

import publicAPI.split_utils as split_utils
import publicAPI.exceptions as exceptions
import helpers

HERE = path.abspath(path.dirname(__file__))
ROOT = path.dirname(HERE)

SPLIT_FILE = path.join(ROOT, 'publicAPI', 'split_info.json')
SPLIT_CACHE = path.join(ROOT, 'publicAPI', 'cache', 'splitcache.json')

TEST_DATE = datetime.utcnow() - timedelta(days=10)
DEMO_SPLIT = {
    "type_id":34,
    "type_name":"Tritanium",
    "original_id":34,
    "new_id":35,
    "split_date":TEST_DATE.strftime('%Y-%m-%d'),
    "bool_mult_div":"False",
    "split_rate": 10
}

def test_splitinfo_happypath():
    """test SplitInfo behavior"""
    split_obj = split_utils.SplitInfo(DEMO_SPLIT)

    ## Validate data inside obj ##
    assert split_obj.type_id == DEMO_SPLIT['type_id']
    assert split_obj.type_name == DEMO_SPLIT['type_name']
    assert split_obj.original_id == DEMO_SPLIT['original_id']
    assert split_obj.new_id == DEMO_SPLIT['new_id']
    assert split_obj.split_date == datetime.strptime(DEMO_SPLIT['split_date'], '%Y-%m-%d')
    assert split_obj.bool_mult_div == False

    assert split_obj.split_rate == DEMO_SPLIT['split_rate']

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
    reverse_profile = dict(DEMO_SPLIT)
    reverse_profile['bool_mult_div'] = "True"
    split_obj = split_utils.SplitInfo(reverse_profile)

    ## Validate data inside obj ##
    assert split_obj.bool_mult_div == True

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
