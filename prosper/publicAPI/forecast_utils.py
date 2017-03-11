"""forecast_utils.py: collection of tools for forecasting future performance"""

from os import path
from datetime import datetime

import ujson as json
import pandas as pd
from pandas.io.json import json_normalize
from fbprophet import Prophet

import crest_utils
import prosper.common.prosper_logging as p_logging

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
        (pandas.data_frame): collection of data from database
            ['date', 'avgPrice', 'highPrice', 'lowPrice', 'volume', 'orders']
    """
    pass

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
            ['date', 'avgPrice', 'yhat', 'yhat_low', 'yhat_high']

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

