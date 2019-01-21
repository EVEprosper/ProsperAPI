"""forecast_utils.py: collection of tools for forecasting future performance"""
from os import path, makedirs
from datetime import datetime, timedelta
import logging

import ujson as json
import pandas as pd
from pandas.io.json import json_normalize
from fbprophet import Prophet
import requests
from tinydb import TinyDB, Query

requests.models.json = json

import publicAPI.crest_utils as crest_utils
import publicAPI.config as api_config
import publicAPI.exceptions as exceptions
import prosper.common.prosper_logging as p_logging

HERE = path.abspath(path.dirname(__file__))

CACHE_PATH = path.join(HERE, 'cache')
makedirs(CACHE_PATH, exist_ok=True)
def check_prediction_cache(
        region_id,
        type_id,
        cache_path=CACHE_PATH,
        db_filename='prophet.json'
):
    """check tinyDB for cached predictions

    Args:
        region_id (int): EVE Online region ID
        type_id (int): EVE Online type ID
        cache_path (str): path to caches
        db_filename (str): name of tinydb

    Returns:
        pandas.DataFrame: cached prediction

    """
    utc_today = datetime.utcnow().strftime('%Y-%m-%d')

    prediction_db = TinyDB(path.join(cache_path, db_filename))

    raw_data = prediction_db.search(
        (Query().cache_date == utc_today) &
        (Query().region_id == region_id) &
        (Query().type_id == type_id)
    )

    prediction_db.close()

    if raw_data:
        panda_data = pd.read_json(raw_data[0]['prediction'])
        return panda_data
    else:
        return None

def write_prediction_cache(
        region_id,
        type_id,
        prediction_data,
        cache_path=CACHE_PATH,
        db_filename='prophet.json',
        logger=logging.getLogger('publicAPI')
):
    """update tinydb latest prediction

    Args:
        region_id (int): EVE Online region ID
        type_id (int): EVE Online type ID
        prediction_data (:obj:`pandas.DataFrame`): data to write to cache
        cache_path (str, optional): path to caches
        db_filename (str, optional): name of tinydb

    Returns:
        None

    """
    logger.info('--caching result')
    utc_today = datetime.utcnow().strftime('%Y-%m-%d')

    prediction_db = TinyDB(path.join(cache_path, db_filename))

    ## clear previous cache ##
    prediction_db.remove(
        (Query().cache_date <= utc_today) &
        (Query().region_id == region_id) &
        (Query().type_id == type_id)
    )

    ## Prepare new entry for cache ##
    cleaned_data = prediction_data.to_json(
        date_format='iso',
        orient='records'
        )
    data = {
        'cache_date': utc_today,
        'region_id': region_id,
        'type_id': type_id,
        'lastWrite': datetime.utcnow().timestamp(),
        'prediction':cleaned_data
    }
    logger.debug(data)
    prediction_db.insert(data)

    prediction_db.close()

DEFAULT_RANGE = api_config.DEFAULT_HISTORY_RANGE
CREST_RANGE = api_config.EXPECTED_CREST_RANGE
MAX_PREDICT_RANGE = api_config.MAX_RANGE
MIN_DATA = api_config.DEFAULT_RANGE
def check_requested_range(
        requested_range,
        max_range=MAX_PREDICT_RANGE,
        raise_for_status=False
):
    """cap requested range to avoid crazy forecasts

    Args:
        requested_range (int): number of days to forecast
        max_range (int): capped days (no more than this)
        raise_for_status (bool): raise exception if request too much

    Returns:
        int: requested_range

    """

    if int(requested_range) <= int(max_range):
        return requested_range

    else:
        if raise_for_status:
            raise exceptions.InvalidRangeRequested(
                status=413,
                message='Invalid range requested.  Max range={0}'.format(max_range)
            )
        return max_range

def fetch_extended_history(
        region_id,
        type_id,
        mode=api_config.SwitchCCPSource.ESI,
        min_data=MIN_DATA,
        crest_range=CREST_RANGE,
        config=api_config.CONFIG,
        data_range=DEFAULT_RANGE,
        logger=logging.getLogger('publicAPI')
):
    """fetch data from database

    Args:
        region_id (int): EVE Online regionID: https://crest-tq.eveonline.com/regions/
        type_id (int): EVE Online typeID: https://crest-tq.eveonline.com/types/
        cache_buster (bool): skip cache, fetch new data
        data_range (int): how far back to fetch data
        logger (:obj:`logging.logger`): logging handle

    Returns:
        pandas.DataFrame: collection of data from database
            ['date', 'avgPrice', 'highPrice', 'lowPrice', 'volume', 'orders']
    """
    logger.info('--fetching history data')
    try:
        raw_data = fetch_market_history_emd(
            region_id,
            type_id,
            data_range,
            config=config
        )
        logger.debug(raw_data['result'][:5])
        data = parse_emd_data(raw_data['result'])
    except Exception as err_msg:    #pragma: no cover
        logger.warning(
            'ERROR: trouble getting data from EMD' +
            '\n\tregion_id={0}'.format(region_id) +
            '\n\ttype_id={0}'.format(type_id) +
            '\n\tdata_range={0}'.format(data_range),
            exc_info=True
        )
        data = []

    if len(data) < crest_range: #pragma: no cover
        logger.info('--Not enough data found, fetching CREST data')

        try:
            data = crest_utils.fetch_market_history(
                region_id,
                type_id,
                config=config,
                logger=logger
            )
        except Exception as err_msg:    #pragma: no cover
            logger.error(
                'ERROR: trouble getting data from CREST' +
                '\n\tregion_id={0}'.format(region_id) +
                '\n\ttype_id={0}'.format(type_id),
                exc_info=True
            )
            raise exceptions.EMDBadMarketData(
                status=500,
                message='Unable to fetch historical data'
            )

    if len(data) < min_data:    #pragma: no cover
        logger.warning(
            'Not enough data to seed prediction' +
            '\n\tregion_id={0}'.format(region_id) +
            '\n\ttype_id={0}'.format(type_id) +
            '\n\tlen(data)={0}'.format(len(data))
        )
        raise exceptions.ProphetNotEnoughData(
            status=500,
            message='Not enough data to build a prediction'
        )

    return data

def trim_prediction(
        data,
        prediction_days,
        history_days=CREST_RANGE
):
    """trim predicted dataframe into shape for results

    Args:
        data (:obj:`pandas.DataFrame`): data reported
        history_days (int): number of days BACK to report
        prediction_days (int): number of days FORWARD to report

    Returns:
        pandas.DataFrame: same shape as original dataframe, but with days removed

    """
    back_date = datetime.utcnow() - timedelta(days=history_days)
    forward_date = datetime.utcnow() + timedelta(days=prediction_days)

    back_date_str = back_date.strftime('%Y-%m-%d')
    forward_date_str = forward_date.strftime('%Y-%m-%d')

    trim_data = data.loc[data.date >= back_date_str]
    trim_data = trim_data.loc[trim_data.date <= forward_date_str]

    return trim_data

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
        dict: JSONable collection of data from endpoint
            ['typeID', 'regionID', 'date', 'lowPrice', 'highPrice', 'avgPrice', 'volume', 'orders']

    """
    payload = {
        'region_ids': region_id,
        'type_ids': type_id,
        'days': data_range,
        'char_name': 'lockefox',
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
        raise exceptions.NoDataReturned()

    return data

def parse_emd_data(data_result):
    """condition data to collapse 'row' keys

    Args:
        data_result (:obj:`list`): data['result'] collection of row data

    Returns:
        pandas.DataFrame: processed row data in table form

    """
    clean_data = []
    for row in data_result:
        clean_data.append(row['row'])

    table_data = pd.DataFrame(clean_data)

    return table_data

def build_forecast(
        data,
        forecast_range,
        truncate_range=0
):
    """build a forecast for publishing

    Args:
        data (:obj:`pandas.data_frame`): data to build prediction
        forecast_range (int): how much time into the future to forecast
        truncate_range (int, optional): truncate output to CREST_RANGE

    Returns:
        pandas.DataFrame: collection of data + forecast info
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

    predict_df = pd.merge(
        predict_df, model.predict(future),
        on='ds',
        how='right'
    )

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
        cut_date = filter_date - timedelta(days=truncate_range)
        report = report.loc[report.date > cut_date]

    return report

