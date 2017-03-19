from os import path
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import requests

import pytest

import publicAPI.crest_utils as crest_utils
import publicAPI.exceptions as exceptions
import helpers

HERE = path.abspath(path.dirname(__file__))
ROOT = path.dirname(HERE)

CONFIG_FILENAME = path.join(HERE, 'test_config.cfg')
CONFIG = helpers.get_config(CONFIG_FILENAME)
ROOT_CONFIG = helpers.get_config(
    path.join(ROOT, 'publicAPI', 'publicAPI.cfg'))

def test_validate_crest_fetcher(config=CONFIG):
    """exercise fetch_crest_endpoint"""
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
