"""crest_utils.py collection of tools for handling crest endpoint APIs"""

from os import path
from datetime import datetime

import ujson as json
import requests
from tinydb import TinyDB, Query
import pandas as pd
from pandas.io.json import json_normalize

requests.models.json = json

import publicAPI.config as config
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

CREST_BASE = 'https://crest-tq.eveonline.com/'
def validate_id(
        endpoint_name,
        item_id,
        cache_buster=False,
        crest_base=CREST_BASE,
        logger=LOGGER
):
    """Check EVE Online CREST as source-of-truth for id lookup

    Args:
        endpoint_name (str): desired endpoint for data lookup
        item_id (int): id value to look up at endpoint (NOTE: only SDE replacement)
        cache_buster (bool, optional): skip caching, fetch from internet
        crest_base (str, optional): test-hook, override for crest base address
        logger (:obj:`logging.logger`, optional): logging handle

    Returns:
        (int): HTTP status code for error validation

    """
    pass

HISTORY_ENDPOINT = ''
def fetch_market_history(
        region_id,
        type_id,
        endpoint_name=HISTORY_ENDPOINT,
        crest_base=CREST_BASE,
        logger=LOGGER
):
    """Get market history data from EVE Online CREST endpoint

    Args:
        region_id (int): (validated) regionID value for CREST lookup
        type_id (int): (validated) typeID value for CREST lookup
        endpoint_name (str, optional): test-hook, override crest endpoint lookup
        crest_base (str, optional): test-hook, override for crest base address
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

class CrestException(Exception):
    """base class for CREST exceptions"""
    pass
class CacheSetupFailure(CrestException):
    """unable to set up cache file"""
    pass
class UnsupportedCrestEndpoint(CrestException):
    """don't know how to parse requested endpoint"""
    pass
class UnsupportedFormat(CrestException):
    """exception for data_to_format failure"""
    pass
