"""crest_utils.py collection of tools for handling crest endpoint APIs"""

from os import path
from datetime import datetime

import ujson as json
import requests
from tinydb import TinyDB, Query
import pandas as pd
from pandas.io.json import json_normalize

requests.models.json = json

import publicAPI.exceptions as exceptions
import publicAPI.config as api_config
import prosper.common.prosper_logging as p_logging

LOGGER = p_logging.DEFAULT_LOGGER
HERE = path.abspath(path.dirname(__file__))

CACHE_PATH = path.join(HERE, 'cache')
def setup_cache_file(
        cache_filename,
        cache_path=CACHE_PATH,
        logger=LOGGER
):
    """build tinyDB handle to cache file

    Args:
        cache_filename (str): path to desired cache file
        cache_path (str, optional): path to cache folder
        logger (:obj:`logging.logger`, optional): logging handle

    Returns:
        (:obj:`TinyDB.TinyDB`): cache db

    """
    pass


def validate_id(
        endpoint_name,
        item_id,
        cache_buster=False,
        logger=LOGGER
):
    """Check EVE Online CREST as source-of-truth for id lookup

    Args:
        endpoint_name (str): desired endpoint for data lookup
        item_id (int): id value to look up at endpoint (NOTE: only SDE replacement)
        cache_buster (bool, optional): skip caching, fetch from internet
        logger (:obj:`logging.logger`, optional): logging handle

    Returns:
        (int): HTTP status code for error validation

    """
    pass

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
    try:
        crest_url = crest_base + config.get('RESOURCES', endpoint_name)
    except KeyError:
        raise exceptions.UnsupportedCrestEndpoint(
            'No {0} found in [RESOURCES]'.format(endpoint_name))

    try:
        crest_url = crest_url.format(**kwargs)
    except KeyError as err_msg:
        raise exceptions.CrestAddressError(repr(err_msg))

    headers = {
        'User-Agent': config.get('GLOBAL', 'useragent')
    }

    # no try-except, catch in caller
    # done to make logging path easier
    req = requests.get(
        crest_url,
        headers=headers
    )
    req.raise_for_status()
    data = req.json()

    return data

def fetch_market_history(
        region_id,
        type_id,
        logger=LOGGER
):
    """Get market history data from EVE Online CREST endpoint

    Args:
        region_id (int): (validated) regionID value for CREST lookup
        type_id (int): (validated) typeID value for CREST lookup
        logger (:obj:`logging.logger`, optional): logging handle

    Returns:
        (:obj:`pandas.data_frame`) pandas collection of data
            ['date', 'avgPrice', 'highPrice', 'lowPrice', 'volume', 'orders']
    """
    pass

def OHLC_to_format(
        data,
        format_type,
        logger=LOGGER
):
    """reformat pandas dataframe to desired format (and recast keys if required)

    Args:
        data (:obj:`pandas.data_frame`): data to format for release
        format_type(:enum:`AcceptedDataFormat`): desired data type
        logger (:obj:`logging.logger`, optional): logging handle

    Returns:
        (`list` or `dict`) processed output

    """
    pass
