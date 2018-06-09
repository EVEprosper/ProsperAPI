"""crest_utils.py collection of tools for handling crest endpoint APIs"""

from os import path, makedirs
from datetime import datetime
import configparser
import logging
import warnings

import ujson as json
from retrying import retry
import requests
from tinydb import TinyDB, Query
import pandas as pd
from pandas.io.json import json_normalize

requests.models.json = json

import publicAPI.exceptions as exceptions
import publicAPI.config as api_config
import prosper.common.prosper_logging as p_logging

LOGGER = logging.getLogger('publicAPI')
HERE = path.abspath(path.dirname(__file__))

CACHE_PATH = path.join(HERE, 'cache')
makedirs(CACHE_PATH, exist_ok=True)

def setup_cache_file(
        cache_filename#,
        #cache_path=CACHE_PATH,
):
    """build tinyDB handle to cache file

    Args:
        cache_filename (str): path to desired cache file
        cache_path (str, optional): path to cache folder
        logger (:obj:`logging.logger`, optional): logging handle

    Returns:
        (:obj:`TinyDB.TinyDB`): cache db

    """
    if not path.isdir(CACHE_PATH):
        makedirs(CACHE_PATH)

    db_filename = path.join(CACHE_PATH, cache_filename + '.json')
    return TinyDB(db_filename)

def write_cache_entry(
        tinydb_handle,
        index_key,
        data_payload
):
    """write data to tinydb

    Args:
        tinydb_handle (:obj:`tinydb.TinyDB`): database to write to
        index_key (any, int): index key value
        data_payload (:obj:`dict`): object to save to cache

    Returns:
        None

    """
    if tinydb_handle.search(Query().index_key == index_key):
        tinydb_handle.update(
            {
                'cache_datetime': datetime.utcnow().timestamp(),
                'payload': data_payload
            },
            Query().index_key == index_key
        )
    else:
        tinydb_handle.insert(
            {
                'cache_datetime': datetime.utcnow().timestamp(),
                'payload': data_payload,
                'index_key': index_key

            }
        )

def endpoint_to_kwarg(
        endpoint_name,
        type_id
):
    """recast endpoint_name to **kwarg pair

    TODO: this is kinda hacky, move to class/enum?
    Args:
        endpoint_name (str): name of endpoint
        type_id (int): EVE Online ID

    Returns:
        (:obj:`dict`) kwarg pair

    """
    kwarg_pair = {}
    if endpoint_name == 'inventory_types':
        kwarg_pair = {'type_id': type_id}
    elif endpoint_name =='map_regions':
        kwarg_pair = {'region_id': type_id}
    else:
        raise exceptions.UnsupportedCrestEndpoint(
            'No configuration for ' + str(endpoint_name)
        )

    return kwarg_pair

def validate_id(
        endpoint_name,
        type_id,
        # mode=api_config.SwitchCCPSource.ESI,
        cache_buster=False,
        config=api_config.CONFIG,
        logger=logging.getLogger('publicAPI'),
):
    """Check EVE Online CREST as source-of-truth for id lookup

    Args:
        endpoint_name (str): desired endpoint for data lookup
        type_id (int): id value to look up at endpoint (NOTE: only SDE replacement)
        cache_buster (bool, optional): skip caching, fetch from internet
        config (:obj:`prosper.common.ProsperConfig`): configuration object
        logger (:obj:`logging.logger`): logging handle

    Returns:
        int: HTTP status code for error validation

    """
    ## Check local cache for value ##
    try:
        db_handle = setup_cache_file(endpoint_name)
    except Exception as err_msg:    #pragma: no cover
        logger.error(
            'ERROR: unable to connect to local tinyDB cache' +
            '\n\tendpoint_name: {0}'.format(endpoint_name) +
            '\n\tcache_path: {0}'.format(CACHE_PATH),
            exc_info=True
        )

    if not cache_buster:
        logger.info('--searching cache for id: %s', type_id)
        logger.debug('endpoint_name=%s', endpoint_name)
        logger.debug('type_id=%s', type_id)

        cache_time = datetime.utcnow().timestamp() - int(config.get('CACHING', 'sde_cache_limit'))
        cache_val = db_handle.search(
            (Query().cache_datetime >= cache_time) &
            (Query().index_key == type_id)
        )


        if cache_val:
            logger.info('--found type_id cache for id: {0}'.format(type_id))
            logger.debug(cache_val)
            return cache_val[0]['payload']    #skip CREST

    ## Request info from CREST ##
    logger.info('--fetching CREST ID information')
    logger.debug('endpoint_name=%s', endpoint_name)
    logger.debug('type_id=%s', type_id)
    try:
        kwarg_pair = endpoint_to_kwarg(
            endpoint_name,
            type_id
        )
        type_info = None
        type_info = fetch_esi_endpoint(
            endpoint_name,
            **kwarg_pair,
            config=config
        )
    except Exception as err_msg:
        logger.warning(
            'ERROR: unable to connect to CREST' +
            '\n\tendpoint_name: {0}'.format(endpoint_name) +
            '\n\ttype_id: {0}'.format(type_id),
            exc_info=True
        )
        raise exceptions.IDValidationError(
            status=404,
            message='Unable to validate {0}:{1}'.format(
                endpoint_name,
                type_id
            )
        )

    ## Update cache ##
    logger.info('--updating cache')
    try:
        write_cache_entry(
            db_handle,
            type_id,
            type_info
        )
    except Exception as err_msg:    #pragma: no cover
        logger.error(
            'ERROR: unable to write to cache' +
            '\n\ttype_id: {0}'.format(type_id) +
            '\n\ttype_info: {0}'.format(type_info),
            exc_info=True
        )

    db_handle.close()

    return type_info

CREST_BASE = 'https://crest-tq.eveonline.com/'
def fetch_crest_endpoint(
        endpoint_name,
        crest_base=CREST_BASE,
        config=api_config.CONFIG,
        **kwargs
):
    """Fetch payload from EVE Online's CREST service

    Args:
        endpoint_name (str): name of endpoint (in config)
        config (`configparser.ConfigParser`, optional): override for config obj
        **kwargs (:obj:`dict`): key/values to overwrite in query

    Returns:
        (:obj:`dict`): JSON object returned by endpoint

    """
    warnings.warn('CREST service deprecated by CCP, use ESI', DeprecationWarning)
    try:
        crest_url = crest_base + config.get('RESOURCES', endpoint_name)
    except (configparser.NoOptionError, KeyError):
        raise exceptions.UnsupportedCrestEndpoint(
            'No {0} found in [RESOURCES]'.format(endpoint_name))

    try:
        crest_url = crest_url.format(**kwargs)
    except KeyError as err_msg:
        raise exceptions.CrestAddressError(repr(err_msg))

    headers = {
        'User-Agent': config.get('GLOBAL', 'useragent')
    }

    @retry(wait_fixed=2000, stop_max_delay=10000)
    def fetch_crest_endpoint_get():
        # no try-except, catch in caller
        # done to make logging path easier
        req = requests.get(
            crest_url,
            headers=headers
        )
        req.raise_for_status()
        return req

    req = fetch_crest_endpoint_get()
    req.raise_for_status()
    data = req.json()

    return data

ESI_BASE = 'https://esi.tech.ccp.is/latest/'
def fetch_esi_endpoint(
        endpoint_name,
        esi_base=ESI_BASE,
        config=api_config.CONFIG,
        **kwargs
):
    """Fetch payload from EVE Online's ESI service

    Notes:
        Only works on unauth'd endpoints

    Args:
        endpoint_name (str): name of endpoint (in config)
        esi_base (str): URI for ESI
        config (`configparser.ConfigParser`): override for config obj
        **kwargs (dict): key/values to overwrite in query

    Returns:
        dict: JSON object returned by endpoint

    """
    try:
        esi_url = esi_base + config.get('ESI_RESOURCES', endpoint_name)
    except (configparser.NoOptionError, KeyError):
        raise exceptions.UnsupportedCrestEndpoint(
            'No {0} found in [ESI_RESOURCES]'.format(endpoint_name))

    try:
        esi_url = esi_url.format(**kwargs)
    except KeyError as err_msg:
        raise exceptions.CrestAddressError(repr(err_msg))

    headers = {
        'User-Agent': config.get('GLOBAL', 'useragent')
    }

    @retry(wait_fixed=2000, stop_max_delay=10000)
    def fetch_esi_endpoint_get():
        # no try-except, catch in caller
        # done to make logging path easier
        req = requests.get(
            esi_url,
            headers=headers
        )
        req.raise_for_status()
        return req

    req = fetch_esi_endpoint_get()
    req.raise_for_status()
    data = req.json()

    return data

def fetch_market_history(
        region_id,
        type_id,
        config=api_config.CONFIG,
        logger=LOGGER
):
    """Get market history data from EVE Online ESI endpoint

    Args:
        region_id (int): (validated) regionID value for ESI lookup
        type_id (int): (validated) typeID value for CREST lookup
        config (:obj:`prosper.common.ProsperConfig`): configuration object
        logger (:obj:`logging.logger`): logging handle

    Returns:
        pandas.data_frame: pandas collection of data
            ['date', 'avgPrice', 'highPrice', 'lowPrice', 'volume', 'orders']
    """
    logger.info('--fetching market data from ESI')
    logger.debug('region_id: %s', region_id)
    logger.debug('type_id: %s', type_id)
    try:
        raw_data = fetch_esi_endpoint(
            'market_history',
            region_id=region_id,
            type_id=type_id,
            config=config
        )
        logger.debug(raw_data[:5])
    except Exception as err_msg:    #pragma: no cover
        logger.error(
            'ERROR: unable to fetch market history from ESI' +
            '\n\ttype_id: {0}'.format(type_id) +
            '\n\tregion_id: {0}'.format(region_id),
            exc_info=True
        )
        raise exceptions.CRESTBadMarketData(
            status=404,
            message='Unable to fetch data for {0}@{1}'.format(
                type_id,
                region_id
            )
        )

    logger.info('--pushing data into pandas')

    try:
        return_data = pd.DataFrame(raw_data)
    except Exception as err_msg:    #pragma: no cover
        logger.error(
            'ERROR: unable to parse CREST history data' +
            '\n\ttype_id: {0}'.format(type_id) +
            '\n\tregion_id: {0}'.format(region_id),
            exc_info=True
        )
        raise exceptions.CRESTParseError(
            status=500,
            message='Unable to parse CREST data from CCP'
        )

    logger.info('--fixing column names')
    return_data.rename(
        columns={
            'lowest': 'lowPrice',
            'highest': 'highPrice',
            'average': 'avgPrice',
            'order_count': 'orders'
        },
        inplace=True
    )

    return return_data

def data_to_ohlc(
        data
):
    """recast CREST data to OHLC shape

    Args:
        data (:obj:`pandas.DataFrame`): data to recast

    Returns:
        (:obj:`pandas.DataFrame`): OHLC format
            ['date', 'open', 'high', 'low', 'close', 'volume']

    """
    ohlc = pd.DataFrame({
        'date'  : data['date'],
        'open'  : data['avgPrice'],
        'high'  : data['highPrice'],
        'low'   : data['lowPrice'],
        'close' : data['avgPrice'].shift(1),
        'volume': data['volume']
    })

    return ohlc
