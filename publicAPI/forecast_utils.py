"""forecast_utils.py: collection of tools for forecasting future performance"""
from os import path
from datetime import datetime, timedelta

import ujson as json
import pandas as pd
from pandas.io.json import json_normalize
from fbprophet import Prophet
import requests

requests.models.json = json

import publicAPI.crest_utils as crest_utils
import publicAPI.config as api_config
import prosper.common.prosper_logging as p_logging

HERE = path.abspath(path.dirname(__file__))
LOGGER = p_logging.DEFAULT_LOGGER

DEFAULT_RANGE = 700
CREST_RANGE = 365
def fetch_extended_history(
        region_id,
        type_id,
        raise_on_short=False,
        data_range=DEFAULT_RANGE,
        logger=LOGGER
):
    """fetch data from database

    Args:
        region_id (int): EVE Online regionID: https://crest-tq.eveonline.com/regions/
        type_id (int): EVE Online typeID: https://crest-tq.eveonline.com/types/
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
        config=api_config.CONFIG
    ):
    """use EMD endpoint to fetch data instead of MySQL

    Args:
        region_id (int): EVE Online regionID: https://crest-tq.eveonline.com/regions/
        type_id (int): EVE Online typeID: https://crest-tq.eveonline.com/types/
        data_range (int): number of days to fetch
        endpoint_addr (str, optional): EMD endpoint to query against
        config (:obj:`configparser.ConfigParser`, optional): overrides for config

    Returns:
        (:obj:`dict` json): collection of data from endpoint
            ['typeID', 'regionID', 'date', 'lowPrice', 'highPrice', 'avgPrice', 'volume', 'orders']

    """
    payload = {
        'region_ids': region_id,
        'type_ids': type_id,
        'days': data_range,
        'char_name': config.get('GLOBAL', 'useragent_short')
    }
    headers = {
        'User-Agent': config.get('GLOBAL', 'useragent')
    }

    req = requests.get(
        endpoint_addr,
        headers=headers,
        params=payload
    )
    req.raise_for_status()
    data = req.json()['emd']

    if not data['result']:
        raise NoDataReturned()

    return data

def parse_emd_data(data_result):
    """condition data to collapse 'row' keys

    Args:
        data_result (:obj:`list`): data['result'] collection of row data

    Returns:
        (:obj:`pandas.DataFrame`): processed row data in table form

    """
    clean_data = []
    for row in data_result:
        clean_data.append(row['row'])

    table_data = pd.DataFrame(clean_data)

    return table_data

def build_forecast(
        data,
        forecast_range,
        truncate_range=0,
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
    data['date'] = pd.to_datetime(data['date'])
    filter_date = data['date'].max()

    ## Build DataFrame ##
    predict_df = pd.DataFrame()
    predict_df['ds'] = data['date']
    predict_df['y'] = data['avgPrice']

    ## Run prediction ##
    # https://facebookincubator.github.io/prophet/docs/quick_start.html#python-api
    model = Prophet()
    model.fit(predict_df)
    future = model.make_future_dataframe(periods=forecast_range)
    tst = model.predict(future)
    model.plot(tst)
    predict_df = pd.merge(
        predict_df, model.predict(future),
        on='ds',
        how='right')

    #print(predict_df.tail())

    ## Build report for endpoint ##
    report = pd.DataFrame()
    report['date'] = pd.to_datetime(predict_df['ds'], format='%Y-%m-%d')
    report['avgPrice'] = predict_df['y']
    report['yhat'] = predict_df['yhat']
    report['yhat_low'] = predict_df['yhat_lower']
    report['yhat_high'] = predict_df['yhat_upper']
    report['prediction'] = False
    report.loc[report.date > filter_date, 'prediction'] = True

    if truncate_range > 0:
        cut_date = datetime.utcnow() - timedelta(days=truncate_range)
        report = report.loc[report.date > cut_date]

    return report



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
class EMDDataException(ForecastException):
    """collection of exceptions around EMD data"""
    pass
class UnableToFetchData(EMDDataException):
    """http error getting EMD data"""
    pass
class NoDataReturned(EMDDataException):
    """missing data in EMD data"""
    pass

if __name__ == '__main__':
    import prosper.common.prosper_config as p_config
    CONFIG_FILE = path.join(HERE, 'publicAPI.cfg')
    CONFIG = p_config.ProsperConfig(CONFIG_FILE)

    data = fetch_market_history_emd(
        region_id=10000002,
        type_id=40,
        data_range=720,
        config=CONFIG
    )
    df = parse_emd_data(data['result'])
    forecast = build_forecast(
        df,
        60,
        200
    )
