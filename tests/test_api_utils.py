"""test_api_utils.py: exercise api utilities"""
from os import path
from datetime import datetime
from tinymongo import TinyMongoClient
import shortuuid

import pytest

import publicAPI.api_utils as api_utils
import publicAPI.exceptions as exceptions
import helpers

HERE = path.abspath(path.dirname(__file__))
ROOT = path.dirname(HERE)

CACHE_PATH = path.join(ROOT, 'publicAPI', 'cache')

DO_API_TESTS = True

def test_good_key():
    """validating check_key logic"""
    connection = TinyMongoClient(CACHE_PATH)
    api_db = connection.prosperAPI.users
    vals = api_db.find()

    if not vals:
        global DO_API_TESTS
        DO_API_TESTS = False
        pytest.xfail('Unable to test without test keys')

    test_key = vals['api_key']
    assert api_utils.check_key(test_key)

    new_vals = api_db.find_one({'api_key': test_key})

    # TODO: fails on virgin key
    old_time = datetime.strptime(
        vals['last_accessed'],
        '%Y-%m-%dT%H:%M:%S.%f').timestamp()

    new_time = datetime.strptime(
        new_vals['last_accessed'],
        '%Y-%m-%dT%H:%M:%S.%f').timestamp()

    assert new_time > old_time

def test_bad_key():
    """validate failed key logic"""
    if not DO_API_TESTS:
        pytest.xfail('Unable to test without test keys')

    bad_key = shortuuid.uuid()

    assert api_utils.check_key(bad_key) is False

def test_bad_key_raises():
    """validate failed key logic"""
    if not DO_API_TESTS:
        pytest.xfail('Unable to test without test keys')

    bad_key = shortuuid.uuid()

    with pytest.raises(exceptions.APIKeyInvalid):
        authorized = api_utils.check_key(
            bad_key,
            throw_on_fail=True
        )

    try:
        authorized = api_utils.check_key(
            bad_key,
            throw_on_fail=True
        )
    except Exception as err_msg:
        assert err_msg.status == 401
        assert isinstance(err_msg.message, str)
