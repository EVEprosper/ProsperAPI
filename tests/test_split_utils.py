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

    if DEMO_SPLIT['bool_mult_div'].lower() == "false":
        assert split_obj.bool_mult_div == False
    else:
        assert split_obj.bool_mult_div == True

    assert split_obj.split_rate == DEMO_SPLIT['split_rate']

    ## Validate magicmethod behavior ##
    assert int(split_obj) == DEMO_SPLIT['new_id']
    assert bool(split_obj)  #should be True
    assert str(split_obj) == DEMO_SPLIT['type_name']

    test_price = 3.5
    test_volume = 1e6

    expected_price = test_price / DEMO_SPLIT['split_rate']
    expected_volume = test_volume * DEMO_SPLIT['split_rate']

    print(test_volume / split_obj)
    assert test_price * split_obj == expected_price
    assert split_obj * test_price == expected_price
    assert test_volume / split_obj == expected_volume
