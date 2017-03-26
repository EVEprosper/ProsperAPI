from os import path, listdir, remove
import io
from datetime import datetime, timedelta
import time
import pandas as pd
#from tinydb import TinyDB, Query

import pytest
from flask import url_for

#import publicAPI.crest_endpoint as crest_endpoint
import publicAPI.exceptions as exceptions
import helpers

HERE = path.abspath(path.dirname(__file__))
ROOT = path.dirname(HERE)

CONFIG_FILENAME = path.join(HERE, 'test_config.cfg')
CONFIG = helpers.get_config(CONFIG_FILENAME)
ROOT_CONFIG = helpers.get_config(
    #path.join(ROOT, 'publicAPI', 'publicAPI.cfg'))
    path.join(ROOT, 'scripts', 'app.cfg'))
TEST_CACHE_PATH = path.join(HERE, 'cache')

BASE_URL = 'http://localhost:8000'
def test_clear_caches():
    """remove cache files for test"""
    cache_path = path.join(ROOT, 'publicAPI', 'cache')
    for file in listdir(cache_path):
        if file == 'apikeys.json':
            continue
        else:
            remove(path.join(cache_path, file))

VIRGIN_RUNTIME = None
#@pytest.mark.incremental
@pytest.mark.usefixtures('client_class')
class TestODBCcsv:
    """test framework for collecting endpoint stats"""
    def test_odbc_happypath(self):
        """exercise `collect_stats`"""
        #print(url_for('ohlc_endpoint', return_type='csv'))
        global VIRGIN_RUNTIME
        fetch_start = time.time()
        req = self.client.get(
            url_for('ohlc_endpoint', return_type='csv') +
            '?typeID={type_id}&regionID={region_id}'.format(
                type_id=CONFIG.get('TEST', 'type_id'),
                region_id=CONFIG.get('TEST', 'region_id')
            )
        )
        fetch_end = time.time()
        VIRGIN_RUNTIME = fetch_end - fetch_start
        print(req.__dict__)
        data = None
        with io.StringIO(req.data.decode()) as buff:
            data = pd.read_csv(buff)

        assert req._status_code == 200
        expected_headers = [
            'date',
            'open',
            'high',
            'low',
            'close',
            'volume'
        ]

        assert set(expected_headers) == set(data.columns.values)

    def test_odbc_happypath_cached(self):
        """rerun test with cached values"""
        fetch_start = time.time()
        req = self.client.get(
            url_for('ohlc_endpoint', return_type='csv') +
            '?typeID={type_id}&regionID={region_id}'.format(
                type_id=CONFIG.get('TEST', 'type_id'),
                region_id=CONFIG.get('TEST', 'region_id')
            )
        )
        fetch_end = time.time()
        runtime = fetch_end - fetch_start
        assert runtime < VIRGIN_RUNTIME/1.5

    def test_odbc_bad_typeid(self):
        """make sure expected errors happen on bad typeid"""
        req = self.client.get(
            url_for('ohlc_endpoint', return_type='csv') +
            '?typeID={type_id}&regionID={region_id}'.format(
                type_id=CONFIG.get('TEST', 'bad_typeid'),
                region_id=CONFIG.get('TEST', 'region_id')
            )
        )
        assert req._status_code == 404

    def test_odbc_bad_regionid(self):
        """make sure expected errors happen on bad typeid"""
        req = self.client.get(
            url_for('ohlc_endpoint', return_type='csv') +
            '?typeID={type_id}&regionID={region_id}'.format(
                type_id=CONFIG.get('TEST', 'type_id'),
                region_id=CONFIG.get('TEST', 'bad_regionid')
            )
        )
        assert req._status_code == 404
