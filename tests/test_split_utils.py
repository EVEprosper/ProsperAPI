"""test_split_utils.py: tests for split_utils.py"""
from os import path
from datetime import datetime, timedelta
import requests
from tinydb import TinyDB, Query

import pytest

import publicAPI.test_utils as test_utils
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
