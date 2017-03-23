"""test_api_utils.py: exercise api utilities"""
from os import path
from datetime import datetime
from tinydb import TinyDB, Query
import shortuuid

import pytest

import publicAPI.api_utils as api_utils
import publicAPI.exceptions as exceptions
import helpers

HERE = path.abspath(path.dirname(__file__))
ROOT = path.dirname(HERE)

CACHE_PATH = path.join(ROOT, 'publicAPI', 'cache', 'apikeys.json')

DO_API_TESTS = True

def test_good_key():
    """validating check_key logic"""
    tdb = TinyDB(CACHE_PATH)
    vals = tdb.all()

    if not vals:
        global DO_API_TESTS
        DO_API_TESTS = False
        pytest.xfail('Unable to test without test keys')

    test_key = vals[0]['api_key']
    tdb.close()
    assert api_utils.check_key(test_key)

    tdb = TinyDB(CACHE_PATH)
    new_vals = tdb.search(Query().api_key == test_key)

    old_time = datetime.strptime(
        vals[0]['last_accessed'],
        '%Y-%m-%dT%H:%M:%S.%f').timestamp()

    new_time = datetime.strptime(
        new_vals[0]['last_accessed'],
        '%Y-%m-%dT%H:%M:%S.%f').timestamp()

    assert new_time > old_time

def test_bad_key():
    """validate failed key logic"""
    if not DO_API_TESTS:
        pytest.xfail('Unable to test without test keys')

    bad_key = shortuuid.uuid()

    assert api_utils.check_key(bad_key) is False
