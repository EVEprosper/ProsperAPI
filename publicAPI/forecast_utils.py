"""forecast_utils.py: collection of tools for forecasting future performance"""
import sys
from os import path
from datetime import datetime

import ujson as json
import pandas as pd
from pandas.io.json import json_normalize
from fbprophet import Prophet
import requests

requests.models.json = json

import publicAPI.crest_utils as crest_utils
import publicAPI.config as config
import prosper.common.prosper_logging as p_logging

HERE = path.abspath(path.dirname(__file__))
LOGGER = p_logging.DEFAULT_LOGGER

DEFAULT_RANGE = 700
CREST_RANGE = 365
def fetch_extended_history(
        region_id,
        type_id,
        db_cursor,
        raise_on_short=False,
        data_range=DEFAULT_RANGE,
        logger=LOGGER
):
    """fetch data from database

    Args:
        region_id (int): EVE Online regionID: https://crest-tq.eveonline.com/regions/
        type_id (int): EVE Online typeID: https://crest-tq.eveonline.com/types/
        db_cursor (:obj:`MySQL.cursor`): database cursor for querying,
        raise_on_short (bool, optional): raise exception if <365 entries found
        data_range (int, optional): how far back to fetch data
        logger (:obj:`logging.logger`): logging handle

    Returns:
        (:obj:`pandas.data_frame`): collection of data from database
            ['date', 'avgPrice', 'highPrice', 'lowPrice', 'volume', 'orders']
    """
    pass

EMD_MARKET_HISTORY = 'http://eve-marketdata.com/api/item_history2.json'
def fetch_market_history_emd(
        region_id,
        type_id,
        data_range,
        endpoint_addr=EMD_MARKET_HISTORY,
        logger=LOGGER
):
    """use EMD endpoint to fetch data instead of MySQL

    Args:
        region_id (int): EVE Online regionID: https://crest-tq.eveonline.com/regions/
        type_id (int): EVE Online typeID: https://crest-tq.eveonline.com/types/
        data_range (int): number of days to fetch
        endpoint_addr (str, optional): EMD endpoint to query against
        logger (:obj:`logging.logger`): logging handle

    Returns:
        (:obj:`dict` json): collection of data from endpoint
            ['typeID', 'regionID', 'date', 'lowPrice', 'highPrice', 'avgPrice', 'volume', 'orders']

    """
    payload = {
        'region_ids': region_id,
        'type_ids': type_id,
        'days': data_range,
        'char_name': CONFIG.get('GLOBAL', 'useragent_short')
    }
    headers = {
        'User-Agent': CONFIG.get('GLOBAL', 'useragent')
    }


def build_forecast(
        data,
        forecast_range,
        truncate_range=False,
        logger=LOGGER
):
    """build a forecast for publishing

    Args:
        data (:obj:`pandas.data_frame`): data to build prediction
        forecast_range (int): how much time into the future to forecast
        truncate_range (int, optional): truncate output to CREST_RANGE
        logger (:obj:`logging.logger`, optional): logging handle

    Returns:
        (:obj:`pandas.data_frame`): collection of data + forecast info
            ['date', 'avgPrice', 'yhat', 'yhat_low', 'yhat_high', 'prediction']

    """
    pass

def data_to_format(
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

class ForecastException(Exception):
    """base class for Forecast exceptions"""
    pass
class NoDataFoundInDB(ForecastException):
    """exception for empty db string found"""
    pass
class NotEnoughDataInDB(ForecastException):
    """exception for `raise_on_short` behavior"""
    pass
class UnsupportedFormat(ForecastException):
    """exception for data_to_format failure"""
    pass

