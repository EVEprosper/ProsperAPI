from os import path, listdir, remove
import platform
import io
from datetime import datetime, timedelta
import time
import json
import pandas as pd
from tinymongo import TinyMongoClient

import pytest
from flask import url_for

import publicAPI.exceptions as exceptions
import helpers

HERE = path.abspath(path.dirname(__file__))
ROOT = path.dirname(HERE)

CONFIG_FILENAME = path.join(HERE, 'test_config.cfg')
CONFIG = helpers.get_config(CONFIG_FILENAME)
ROOT_CONFIG = helpers.get_config(
    path.join(ROOT, 'scripts', 'app.cfg')
)
TEST_CACHE_PATH = path.join(HERE, 'cache')
CACHE_PATH = path.join(ROOT, 'publicAPI', 'cache')

BASE_URL = 'http://localhost:8000'

def test_clear_caches():
    """remove cache files for test"""
    helpers.clear_caches(True)

VIRGIN_RUNTIME = None

@pytest.mark.usefixtures('client_class')
class TestODBCcsv:
    """test framework for collecting endpoint stats"""
    def test_odbc_happypath(self):
        """exercise `collect_stats`"""
        global VIRGIN_RUNTIME
        fetch_start = time.time()
        req = self.client.get(
            url_for('ohlc_endpoint', return_type='csv') +
            '?typeID={type_id}&regionID={region_id}'.format(
                type_id=CONFIG.get('TEST', 'nosplit_id'),
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
                type_id=CONFIG.get('TEST', 'nosplit_id'),
                region_id=CONFIG.get('TEST', 'region_id')
            )
        )
        fetch_end = time.time()
        runtime = fetch_end - fetch_start
        if runtime > VIRGIN_RUNTIME/1.5:
            pytest.xfail('cached performance slower than expected')

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
                type_id=CONFIG.get('TEST', 'nosplit_id'),
                region_id=CONFIG.get('TEST', 'bad_regionid')
            )
        )
        assert req._status_code == 404

    def test_odbc_bad_format(self):
        """make sure expected errors happen on bad typeid"""
        req = self.client.get(
            url_for('ohlc_endpoint', return_type='butts') +
            '?typeID={type_id}&regionID={region_id}'.format(
                type_id=CONFIG.get('TEST', 'nosplit_id'),
                region_id=CONFIG.get('TEST', 'region_id')
            )
        )
        assert req._status_code == 405

@pytest.mark.usefixtures('client_class')
class TestODBCjson:
    """test framework for collecting endpoint stats"""
    def test_odbc_happypath(self):
        """exercise `collect_stats`"""
        test_clear_caches()
        global VIRGIN_RUNTIME
        fetch_start = time.time()
        req = self.client.get(
            url_for('ohlc_endpoint', return_type='json') +
            '?typeID={type_id}&regionID={region_id}'.format(
                type_id=CONFIG.get('TEST', 'nosplit_id'),
                region_id=CONFIG.get('TEST', 'region_id')
            )
        )
        fetch_end = time.time()
        VIRGIN_RUNTIME = fetch_end - fetch_start

        raw_data = json.loads(req.data.decode())
        data = pd.DataFrame(raw_data)

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

    def test_odbc_bad_typeid(self):
        """make sure expected errors happen on bad typeid"""
        req = self.client.get(
            url_for('ohlc_endpoint', return_type='json') +
            '?typeID={type_id}&regionID={region_id}'.format(
                type_id=CONFIG.get('TEST', 'bad_typeid'),
                region_id=CONFIG.get('TEST', 'region_id')
            )
        )
        assert req._status_code == 404

    def test_odbc_bad_regionid(self):
        """make sure expected errors happen on bad typeid"""
        req = self.client.get(
            url_for('ohlc_endpoint', return_type='json') +
            '?typeID={type_id}&regionID={region_id}'.format(
                type_id=CONFIG.get('TEST', 'nosplit_id'),
                region_id=CONFIG.get('TEST', 'bad_regionid')
            )
        )
        assert req._status_code == 404

@pytest.mark.usefixtures('client_class')
class TestODBCsplit:
    """make sure behavior for splits is maintained"""
    def test_validate_forward_split(self):
        req = self.client.get(
            url_for('ohlc_endpoint', return_type='csv') +
            '?typeID={type_id}&regionID={region_id}'.format(
                type_id=CONFIG.get('TEST', 'type_id'),
                region_id=CONFIG.get('TEST', 'region_id')
            )
        )

        data = None
        with io.StringIO(req.data.decode()) as buff:
            data = pd.read_csv(buff)

        assert req._status_code == 200



TEST_API_KEY = ''
def test_get_api_key():
    """fetch api key from cache for testing"""
    global TEST_API_KEY
    connection = TinyMongoClient(CACHE_PATH)
    api_db = connection.prosperAPI.users
    vals = api_db.find()

    if not vals:
        pytest.xfail('Unable to test without test keys')

    test_key = vals['api_key']
    connection.close()
    TEST_API_KEY = test_key

@pytest.mark.usefixtures('client_class')
class TestProphetcsv:
    """test framework for collecting endpoint stats"""
    def test_prophet_happypath(self):
        """exercise `collect_stats`"""
        if platform.system() == 'Darwin':
            pytest.xfail('Unable to run fbprophet on mac')

        test_clear_caches()
        assert TEST_API_KEY != ''
        global VIRGIN_RUNTIME
        fetch_start = time.time()
        req = self.client.get(
            url_for('prophetendpoint', return_type='csv') +
            '?typeID={type_id}&regionID={region_id}&api={api_key}&range={range}'.format(
                type_id=CONFIG.get('TEST', 'nosplit_id'),
                region_id=CONFIG.get('TEST', 'region_id'),
                api_key=TEST_API_KEY,
                range=CONFIG.get('TEST', 'forecast_range')
            )
        )
        fetch_end = time.time()
        VIRGIN_RUNTIME = fetch_end - fetch_start

        data = None
        with io.StringIO(req.data.decode()) as buff:
            data = pd.read_csv(buff)

        assert req._status_code == 200
        expected_headers = [
            'date',
            'avgPrice',
            'yhat',
            'yhat_low',
            'yhat_high',
            'prediction'
        ]

        assert set(expected_headers) == set(data.columns.values)
        ##TODO: validate ranges?

    def test_prophet_happypath_cached(self):
        """exercise `collect_stats`"""
        if platform.system() == 'Darwin':
            pytest.xfail('Unable to run fbprophet on mac')

        fetch_start = time.time()
        req = self.client.get(
            url_for('prophetendpoint', return_type='csv') +
            '?typeID={type_id}&regionID={region_id}&api={api_key}&range={range}'.format(
                type_id=CONFIG.get('TEST', 'nosplit_id'),
                region_id=CONFIG.get('TEST', 'region_id'),
                api_key=TEST_API_KEY,
                range=CONFIG.get('TEST', 'forecast_range')
            )
        )
        fetch_end = time.time()
        runtime = fetch_end - fetch_start
        if runtime > VIRGIN_RUNTIME/1.5:
            pytest.xfail('cached performance slower than expected')

    def test_prophet_bad_regionid(self):
        """exercise `collect_stats`"""
        if platform.system() == 'Darwin':
            pytest.xfail('Unable to run fbprophet on mac')

        req = self.client.get(
            url_for('prophetendpoint', return_type='csv') +
            '?typeID={type_id}&regionID={region_id}&api={api_key}&range={range}'.format(
                type_id=CONFIG.get('TEST', 'nosplit_id'),
                region_id=CONFIG.get('TEST', 'bad_regionid'),
                api_key=TEST_API_KEY,
                range=CONFIG.get('TEST', 'forecast_range')
            )
        )
        assert req._status_code == 404

    def test_prophet_bad_typeid(self):
        """exercise `collect_stats`"""
        if platform.system() == 'Darwin':
            pytest.xfail('Unable to run fbprophet on mac')
        req = self.client.get(
            url_for('prophetendpoint', return_type='csv') +
            '?typeID={type_id}&regionID={region_id}&api={api_key}&range={range}'.format(
                type_id=CONFIG.get('TEST', 'bad_typeid'),
                region_id=CONFIG.get('TEST', 'region_id'),
                api_key=TEST_API_KEY,
                range=CONFIG.get('TEST', 'forecast_range')
            )
        )
        assert req._status_code == 404

    def test_prophet_bad_api(self):
        """exercise `collect_stats`"""
        if platform.system() == 'Darwin':
            pytest.xfail('Unable to run fbprophet on mac')
        req = self.client.get(
            url_for('prophetendpoint', return_type='csv') +
            '?typeID={type_id}&regionID={region_id}&api={api_key}&range={range}'.format(
                type_id=CONFIG.get('TEST', 'nosplit_id'),
                region_id=CONFIG.get('TEST', 'region_id'),
                api_key='IMAHUGEBUTT',
                range=CONFIG.get('TEST', 'forecast_range')
            )
        )
        assert req._status_code == 401

    def test_prophet_bad_range(self):
        """exercise `collect_stats`"""
        if platform.system() == 'Darwin':
            pytest.xfail('Unable to run fbprophet on mac')
        req = self.client.get(
            url_for('prophetendpoint', return_type='csv') +
            '?typeID={type_id}&regionID={region_id}&api={api_key}&range={range}'.format(
                type_id=CONFIG.get('TEST', 'nosplit_id'),
                region_id=CONFIG.get('TEST', 'region_id'),
                api_key=TEST_API_KEY,
                range=9001
            )
        )
        assert req._status_code == 413

    def test_prophet_bad_format(self):
        """exercise `collect_stats`"""
        if platform.system() == 'Darwin':
            pytest.xfail('Unable to run fbprophet on mac')
        req = self.client.get(
            url_for('prophetendpoint', return_type='butts') +
            '?typeID={type_id}&regionID={region_id}&api={api_key}&range={range}'.format(
                type_id=CONFIG.get('TEST', 'nosplit_id'),
                region_id=CONFIG.get('TEST', 'region_id'),
                api_key=TEST_API_KEY,
                range=CONFIG.get('TEST', 'forecast_range')
            )
        )
        assert req._status_code == 405

@pytest.mark.usefixtures('client_class')
class TestProphetjson:
    """test framework for collecting endpoint stats"""
    def test_prophet_happypath(self):
        """exercise `collect_stats`"""
        if platform.system() == 'Darwin':
            pytest.xfail('Unable to run fbprophet on mac')

        test_clear_caches()
        global VIRGIN_RUNTIME
        fetch_start = time.time()
        req = self.client.get(
            url_for('prophetendpoint', return_type='json') +
            '?typeID={type_id}&regionID={region_id}&api={api_key}&range={range}'.format(
                type_id=CONFIG.get('TEST', 'nosplit_id'),
                region_id=CONFIG.get('TEST', 'region_id'),
                api_key=TEST_API_KEY,
                range=CONFIG.get('TEST', 'forecast_range')
            )
        )
        fetch_end = time.time()
        VIRGIN_RUNTIME = fetch_end - fetch_start

        raw_data = json.loads(req.data.decode())
        data = pd.DataFrame(raw_data)

        assert req._status_code == 200
        expected_headers = [
            'date',
            'avgPrice',
            'yhat',
            'yhat_low',
            'yhat_high',
            'prediction'
        ]

        assert set(expected_headers) == set(data.columns.values)
        ##TODO: validate ranges?

    def test_prophet_happypath_cached(self):
        """exercise `collect_stats`"""
        if platform.system() == 'Darwin':
            pytest.xfail('Unable to run fbprophet on mac')

        fetch_start = time.time()
        req = self.client.get(
            url_for('prophetendpoint', return_type='json') +
            '?typeID={type_id}&regionID={region_id}&api={api_key}&range={range}'.format(
                type_id=CONFIG.get('TEST', 'nosplit_id'),
                region_id=CONFIG.get('TEST', 'region_id'),
                api_key=TEST_API_KEY,
                range=CONFIG.get('TEST', 'forecast_range')
            )
        )
        fetch_end = time.time()
        runtime = fetch_end - fetch_start
        if runtime > VIRGIN_RUNTIME/1.5:
            pytest.xfail('cached performance slower than expected')

    def test_prophet_bad_regionid(self):
        """exercise `collect_stats`"""
        if platform.system() == 'Darwin':
            pytest.xfail('Unable to run fbprophet on mac')

        req = self.client.get(
            url_for('prophetendpoint', return_type='json') +
            '?typeID={type_id}&regionID={region_id}&api={api_key}&range={range}'.format(
                type_id=CONFIG.get('TEST', 'nosplit_id'),
                region_id=CONFIG.get('TEST', 'bad_regionid'),
                api_key=TEST_API_KEY,
                range=CONFIG.get('TEST', 'forecast_range')
            )
        )
        assert req._status_code == 404

    def test_prophet_bad_typeid(self):
        """exercise `collect_stats`"""
        if platform.system() == 'Darwin':
            pytest.xfail('Unable to run fbprophet on mac')

        req = self.client.get(
            url_for('prophetendpoint', return_type='json') +
            '?typeID={type_id}&regionID={region_id}&api={api_key}&range={range}'.format(
                type_id=CONFIG.get('TEST', 'bad_typeid'),
                region_id=CONFIG.get('TEST', 'region_id'),
                api_key=TEST_API_KEY,
                range=CONFIG.get('TEST', 'forecast_range')
            )
        )
        assert req._status_code == 404

    def test_prophet_bad_api(self):
        """exercise `collect_stats`"""
        if platform.system() == 'Darwin':
            pytest.xfail('Unable to run fbprophet on mac')

        req = self.client.get(
            url_for('prophetendpoint', return_type='json') +
            '?typeID={type_id}&regionID={region_id}&api={api_key}&range={range}'.format(
                type_id=CONFIG.get('TEST', 'nosplit_id'),
                region_id=CONFIG.get('TEST', 'region_id'),
                api_key='IMAHUGEBUTT',
                range=CONFIG.get('TEST', 'forecast_range')
            )
        )
        assert req._status_code == 401

    def test_prophet_bad_range(self):
        """exercise `collect_stats`"""
        if platform.system() == 'Darwin':
            pytest.xfail('Unable to run fbprophet on mac')

        req = self.client.get(
            url_for('prophetendpoint', return_type='json') +
            '?typeID={type_id}&regionID={region_id}&api={api_key}&range={range}'.format(
                type_id=CONFIG.get('TEST', 'nosplit_id'),
                region_id=CONFIG.get('TEST', 'region_id'),
                api_key=TEST_API_KEY,
                range=9000
            )
        )
        assert req._status_code == 413


@pytest.mark.usefixtures('client_class')
class TestProphetSplit:
    """make sure behavior for splits is maintained"""
    def test_validate_forward_split(self):
        if platform.system() == 'Darwin':
            pytest.xfail('Unable to run fbprophet on mac')

        test_clear_caches()
        assert TEST_API_KEY != ''
        req = self.client.get(
            url_for('prophetendpoint', return_type='csv') +
            '?typeID={type_id}&regionID={region_id}&api={api_key}&range={range}'.format(
                type_id=CONFIG.get('TEST', 'type_id'),
                region_id=CONFIG.get('TEST', 'region_id'),
                api_key=TEST_API_KEY,
                range=CONFIG.get('TEST', 'forecast_range')
            )
        )

        data = None
        with io.StringIO(req.data.decode()) as buff:
            data = pd.read_csv(buff)

        assert req._status_code == 200
