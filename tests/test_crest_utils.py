from os import path, makedirs, rmdir
from shutil import rmtree
from datetime import datetime, timedelta
import time
import pandas as pd
import numpy as np
import requests
from tinydb import Query

import pytest

import publicAPI.config as api_config
import publicAPI.crest_utils as crest_utils
import publicAPI.exceptions as exceptions
import helpers

HERE = path.abspath(path.dirname(__file__))
ROOT = path.dirname(HERE)

CONFIG_FILENAME = path.join(HERE, 'test_config.cfg')
CONFIG = helpers.get_config(CONFIG_FILENAME)
ROOT_CONFIG = helpers.get_config(
    path.join(ROOT, 'scripts', 'app.cfg'))

def test_validate_crest_fetcher(config=CONFIG):
    """exercise fetch_crest_endpoint"""
    pytest.skip('CREST Deprecated')
    region_data = crest_utils.fetch_crest_endpoint(
        'map_regions',
        region_id=config.get('TEST', 'region_id'),
        config=ROOT_CONFIG
    )
    region_keys = [ #not all keys, just important ones
        'name',
        'description',
        'marketHistory',
        'marketOrdersAll',
        'constellations'
    ]
    for key in region_keys:
        assert key in region_data.keys()
    assert region_data['name'] == 'The Forge'

    types_data = crest_utils.fetch_crest_endpoint(
        'inventory_types',
        type_id=config.get('TEST', 'type_id'),
        config=ROOT_CONFIG
    )
    type_keys = [ #not all keys, just important ones
        'capacity',
        'description',
        'iconID',
        'portionSize',
        'volume',
        'dogma',
        'radius',
        'published',
        'mass',
        'id',
        'name'
    ]
    for key in type_keys:
        assert key in types_data.keys()
    assert types_data['name'] == 'Tritanium'

    market_data = crest_utils.fetch_crest_endpoint(
        'market_history',
        type_id=config.get('TEST', 'type_id'),
        region_id=config.get('TEST', 'region_id'),
        config=ROOT_CONFIG
    )
    market_keys = [ #not all keys, just important ones
        'items',
        'pageCount',
        'totalCount'
    ]
    for key in market_keys:
        assert key in market_data.keys()
    assert len(market_data['items']) == market_data['totalCount']

def test_crest_fetcher_errors(config=CONFIG):
    """validate errors thrown by fetch_crest_endpoint"""
    pytest.skip('CREST Deprecated')
    with pytest.raises(exceptions.UnsupportedCrestEndpoint):
        data = crest_utils.fetch_crest_endpoint(
            'butts',
            region_id=config.get('TEST', 'region_id'),
            config=ROOT_CONFIG
        )

    with pytest.raises(exceptions.CrestAddressError):
        data = crest_utils.fetch_crest_endpoint(
            'inventory_types',
            region_id=config.get('TEST', 'region_id'),
            config=ROOT_CONFIG
        )

    with pytest.raises(exceptions.CrestAddressError):
        data = crest_utils.fetch_crest_endpoint(
            'market_history',
            region_id=config.get('TEST', 'region_id'),
            config=ROOT_CONFIG
        )

    with pytest.raises(requests.exceptions.HTTPError):
        data = crest_utils.fetch_crest_endpoint(
            'inventory_types',
            type_id=config.get('TEST', 'bad_typeid'),
            config=ROOT_CONFIG
        )

def test_validate_esi_fetcher(config=CONFIG):
    """exercise fetch_crest_endpoint"""
    region_data = crest_utils.fetch_esi_endpoint(
        'map_regions',
        region_id=config.get('TEST', 'region_id'),
        config=ROOT_CONFIG
    )
    region_keys = [ #not all keys, just important ones
        'name',
        'region_id',
        'description',
        'constellations'
    ]
    for key in region_keys:
        assert key in region_data.keys()
    assert region_data['name'] == 'The Forge'

    types_data = crest_utils.fetch_esi_endpoint(
        'inventory_types',
        type_id=config.get('TEST', 'type_id'),
        config=ROOT_CONFIG
    )
    type_keys = [ #not all keys, just important ones
        'capacity',
        'description',
        'icon_id',
        'portion_size',
        'volume',
        #'dogma',
        'radius',
        'published',
        'mass',
        'type_id',
        'name'
    ]
    for key in type_keys:
        assert key in types_data.keys()
    assert types_data['name'] == 'Tritanium'

    market_data = crest_utils.fetch_esi_endpoint(
        'market_history',
        type_id=config.get('TEST', 'type_id'),
        region_id=config.get('TEST', 'region_id'),
        config=ROOT_CONFIG
    )
    market_item = market_data[0]
    row_keys = [
        'date',
        'order_count',
        'volume',
        'highest',
        'lowest',
        'average'
    ]
    for key in row_keys:
        assert key in market_item.keys()
    assert len(market_data) >= 366

def test_esi_fetcher_errors(config=CONFIG):
    """validate errors thrown by fetch_crest_endpoint"""
    with pytest.raises(exceptions.UnsupportedCrestEndpoint):
        data = crest_utils.fetch_esi_endpoint(
            'butts',
            region_id=config.get('TEST', 'region_id'),
            config=ROOT_CONFIG
        )

    with pytest.raises(exceptions.CrestAddressError):
        data = crest_utils.fetch_esi_endpoint(
            'inventory_types',
            region_id=config.get('TEST', 'region_id'),
            config=ROOT_CONFIG
        )

    with pytest.raises(exceptions.CrestAddressError):
        data = crest_utils.fetch_esi_endpoint(
            'market_history',
            region_id=config.get('TEST', 'region_id'),
            config=ROOT_CONFIG
        )

    with pytest.raises(requests.exceptions.HTTPError):
        data = crest_utils.fetch_esi_endpoint(
            'inventory_types',
            type_id=config.get('TEST', 'bad_typeid'),
            config=ROOT_CONFIG
        )

def test_endpoint_to_kwarg():
    """validate `endpoint_to_kwarg` behavior"""
    type_pair = crest_utils.endpoint_to_kwarg(
        'inventory_types',
        9999
    )
    assert type_pair == {'type_id': 9999}

    region_pair = crest_utils.endpoint_to_kwarg(
        'map_regions',
        -9999
    )
    assert region_pair == {'region_id': -9999}

    with pytest.raises(exceptions.UnsupportedCrestEndpoint):
        bad_pair = crest_utils.endpoint_to_kwarg(
            'butts',
            420
        )

TEST_CACHE_PATH = path.join(HERE, 'cache')
crest_utils.CACHE_PATH = TEST_CACHE_PATH #Override default for test

@pytest.mark.incremental
class TestTinyDBHelp:
    """validate TinyDB functions"""
    def test_make_db(self):
        makedirs(TEST_CACHE_PATH, exist_ok=True)
        tdb_handle = crest_utils.setup_cache_file('dummy_handle')
        #assert tdb_handle
        assert path.isfile(path.join(TEST_CACHE_PATH, 'dummy_handle.json'))

        tdb_handle.close()

        helpers.clear_caches()
        #rmtree(TEST_CACHE_PATH)
        tdb_handle = crest_utils.setup_cache_file('dummy_handle')
        #assert tdb_handle
        assert path.isfile(path.join(TEST_CACHE_PATH, 'dummy_handle.json'))

        tdb_handle.close()

    def test_write_cache(self):
        """validate write_cache behavior"""
        tdb_handle = crest_utils.setup_cache_file('dummy_handle')

        dummy_data = {'butts': 1, 'stuff': True}

        crest_utils.write_cache_entry(
            tdb_handle,
            999,
            dummy_data
        )

        cache_data = tdb_handle.search(Query().index_key == 999)[0]
        assert 'cache_datetime' in cache_data.keys()
        cache_datetime = cache_data['cache_datetime']
        assert cache_data['index_key'] == 999
        assert cache_data['payload'] == dummy_data


        crest_utils.write_cache_entry(
            tdb_handle,
            999,
            dummy_data
        )

        time.sleep(1)
        new_data = tdb_handle.search(Query().index_key == 999)
        assert len(new_data) == 1
        assert new_data[0]['cache_datetime'] >= cache_datetime
        assert new_data[0]['index_key'] == 999
        assert new_data[0]['payload'] == dummy_data

        tdb_handle.close()

@pytest.mark.incremental
class TestValidateID:
    """collection of tests for `validate_id` testing"""
    type_id = int(CONFIG.get('TEST', 'type_id'))
    region_id = int(CONFIG.get('TEST', 'region_id'))
    bad_typeid = int(CONFIG.get('TEST', 'bad_typeid'))

    def test_clear_cachefiles(self):
        """init test, clean up paths before test"""
        helpers.clear_caches()
        #rmtree(TEST_CACHE_PATH)
        #makedirs(TEST_CACHE_PATH)

    def test_happypath_types(self):
        """make sure behavior is expected for direct use"""
        pytest.skip('CREST endpoint deprecated')
        type_info = crest_utils.validate_id(
            'inventory_types',
            self.type_id,
            config=ROOT_CONFIG
        )
        assert type_info['name'] == 'Tritanium'

        type_info_retry = crest_utils.validate_id(
            'inventory_types',
            self.type_id,
            config=ROOT_CONFIG
        )
        assert type_info_retry == type_info

        type_info_esi = crest_utils.validate_id(
            'inventory_types',
            self.type_id,
            cache_buster=True,
            config=ROOT_CONFIG,
            mode=api_config.SwitchCCPSource.ESI
        )
        print(type_info)
        print(type_info_esi)
        assert type_info == type_info_esi
        #assert type_info_esi['name'] == type_info['name']
        #assert type_info_esi['description'] == type_info['description']
        #assert type_info_esi['published'] == type_info['published']
        #assert type_info_esi['radius'] == type_info['radius']
        #assert type_info_esi['icon_id'] == type_info['iconID']
        #assert type_info_esi['capacity'] == type_info['capacity']
        #assert type_info_esi['type_id'] == type_info['id']

    def test_happypath_regions(self):
        """make sure behavior is good for regions too"""
        region_info = crest_utils.validate_id(
            'map_regions',
            self.region_id,
            config=ROOT_CONFIG
        )
        assert region_info['name'] == 'The Forge'

        region_info_retry = crest_utils.validate_id(
            'map_regions',
            self.region_id,
            config=ROOT_CONFIG
        )
        assert region_info_retry == region_info

        region_info_esi = crest_utils.validate_id(
            'map_regions',
            self.region_id,
            cache_buster=True,
            config=ROOT_CONFIG,
        )

        assert region_info_esi['name'] == region_info['name']
        assert region_info_esi['region_id'] == region_info['region_id']
        assert region_info_esi['description'] == region_info['description']

    def test_cache_files(self):
        """make sure cache files were generated"""
        assert path.isfile(path.join(TEST_CACHE_PATH, 'inventory_types.json'))
        assert path.isfile(path.join(TEST_CACHE_PATH, 'map_regions.json'))

    def test_validate_bad_ids(self):
        """check behavior with bad id's"""
        with pytest.raises(exceptions.IDValidationError):
            data = crest_utils.validate_id(
                'inventory_types',
                self.bad_typeid,
                config=ROOT_CONFIG
            )

        try:
            data = crest_utils.validate_id(
                'inventory_types',
                self.bad_typeid,
                config=ROOT_CONFIG
            )
        except exceptions.IDValidationError as err_msg:
            assert err_msg.status == 404
            assert isinstance(err_msg.message, str)

    def test_validate_types_cache(self):
        """make sure cachebuster and stash agree"""
        type_info = crest_utils.validate_id(
            'inventory_types',
            self.type_id,
            config=ROOT_CONFIG,
            cache_buster=True,
        )
        tdb_handle = crest_utils.setup_cache_file('inventory_types')
        type_cache = tdb_handle.search(Query().index_key == self.type_id)[0]

        assert type_info == type_cache['payload']

    def test_validate_region_cache(self):
        """make sure cachebuster and stash agree"""
        type_info = crest_utils.validate_id(
            'map_regions',
            self.region_id,
            config=ROOT_CONFIG,
            cache_buster=True,
        )
        tdb_handle = crest_utils.setup_cache_file('map_regions')
        type_cache = tdb_handle.search(Query().index_key == self.region_id)[0]

        assert type_info == type_cache['payload']

#def test_fetch_market_history(config=CONFIG):
#    """test `fetch_market_history` utility"""
#    #pytest.skip('CREST Deprecated')
#    data = crest_utils.fetch_market_history(
#        config.get('TEST', 'region_id'),
#        config.get('TEST', 'type_id'),
#        config=ROOT_CONFIG
#    )
#
#    assert isinstance(data, pd.DataFrame)
#    expected_cols = [
#        'date',
#        'avgPrice',
#        'highPrice',
#        'lowPrice',
#        'volume',
#        'orders'
#        #extra keys:
#        #'volume_str',
#        #'orderCountStr'
#    ]
#    for key in expected_cols:
#        assert key in data.columns.values
#
#    ohlc = crest_utils.data_to_ohlc(data)
#
#    assert ohlc['date'].equals(data['date'])
#    assert ohlc['open'].equals(data['avgPrice'])
#    assert ohlc['high'].equals(data['highPrice'])
#    assert ohlc['low'].equals(data['lowPrice'])
#    assert ohlc['volume'].equals(data['volume'])
#
#    assert data['avgPrice'].shift(1).equals(ohlc['close'])
#
def test_fetch_market_history_esi(config=CONFIG):
    """test `fetch_market_history` utility"""

    data = crest_utils.fetch_market_history(
        config.get('TEST', 'region_id'),
        config.get('TEST', 'type_id'),
        config=ROOT_CONFIG,
    )

    assert isinstance(data, pd.DataFrame)
    expected_cols = [
        'date',
        'avgPrice',
        'highPrice',
        'lowPrice',
        'volume',
        'orders'
        #extra keys:
        #'volume_str',
        #'orderCountStr'
    ]
    for key in expected_cols:
        assert key in data.columns.values

    ohlc = crest_utils.data_to_ohlc(data)

    assert ohlc['date'].equals(data['date'])
    assert ohlc['open'].equals(data['avgPrice'])
    assert ohlc['high'].equals(data['highPrice'])
    assert ohlc['low'].equals(data['lowPrice'])
    assert ohlc['volume'].equals(data['volume'])

    assert data['avgPrice'].shift(1).equals(ohlc['close'])
