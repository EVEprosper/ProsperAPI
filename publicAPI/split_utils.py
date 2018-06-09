"""split_utils.py: tool for handling type_id split/remapping"""
from os import path, makedirs
from datetime import datetime
import ast
import logging

import ujson as json
import pandas as pd
import numpy as np
from tinydb import TinyDB, Query

import publicAPI.config as api_config
import publicAPI.crest_utils as crest_utils
import publicAPI.forecast_utils as forecast_utils
import publicAPI.exceptions as exceptions

HERE = path.abspath(path.dirname(__file__))
class SplitInfo(object):
    """utility for managing split information"""
    def __init__(self, json_entry=None):
        self.type_id = -1
        self.original_id = -1
        self.new_id = -1
        self.split_rate = -1
        self.bool_mult_div = None
        self.type_name = ''
        self.split_date = None
        self.date_str = ''
        if json_entry:
            self.load_object(json_entry)


    #int(SplitInfo) = "what does the type_id switch to?"
    def __int__(self):
        return self.new_id

    #bool(SplitInfo) = "has the split happened yet?"
    def __bool__(self):
        return bool(self.split_date < datetime.utcnow())

    #new_price = old_price * SplitInfo()
    def multiply(self, other):
        """wrap multiply for mul/rmul"""
        if self.bool_mult_div:
            return other * self.split_rate
        else:
            return other / self.split_rate
    def __rmul__(self, other):
        return self.multiply(other)
    def __mul__(self, other):
        return self.multiply(other)

    #new_count = old_count / SplitInfo()
    def divide(self, other):
        """wrap divide for div/rdiv"""
        if self.bool_mult_div:
            return other / self.split_rate
        else:
            return other * self.split_rate
    def __rtruediv__(self, other):
        return self.divide(other)

    #type_name for reasons
    def __str__(self):
        return self.type_name

    def current_typeid(self):
        """get the current live typeid"""
        if bool(self):
            return self.new_id
        else:
            return self.original_id

    def load_object(self, json_entry):
        """loads info from json object into helper

        Args:
            json_entry (:obj:`dict`): one item to be parsed
                {'type_id', 'type_name', 'original_id', 'new_id',
                'split_date', 'bool_mult_div', 'split_rate'}

        Returns:
            None

        """
        #TODO: bonus points for inserting with __dict__
        try:
            self.type_id = int(json_entry['type_id'])
            self.type_name = json_entry['type_name']
            self.original_id = int(json_entry['original_id'])
            self.new_id = int(json_entry['new_id'])
            self.split_date = datetime.strptime(
                json_entry['split_date'],
                '%Y-%m-%d'
            )
            self.date_str = self.split_date.strftime('%Y-%m-%d')
            split_rate = json_entry['split_rate']
        except Exception as err_msg:
            raise exceptions.InvalidSplitConfig(
                'Unable to parse config {0}'.format(repr(err_msg))
            )

        #TODO: this is shitty
        if isinstance(split_rate, str):
            try:
                self.split_rate = ast.literal_eval(split_rate)
            except Exception as err_msg:
                raise exceptions.InvalidSplitConfig(
                    'Unable to parse split_rate {0}'.format(repr(err_msg))
                )
        else:
            self.split_rate = split_rate


        if json_entry['bool_mult_div'].lower() == 'true':
            self.bool_mult_div = True
        elif json_entry['bool_mult_div'].lower() == 'false':
            self.bool_mult_div = False
        else:
            raise exceptions.InvalidSplitConfig(
                'Unable to parse `bool_mult_div`={0}'.format(json_entry['bool_mult_div'])
            )

        if self.type_id == self.original_id:
            self.original_item = True
        else:
            self.original_item = False

def read_split_info(
        split_info_file=path.join(HERE, 'split_info.json'),
        logger=logging.getLogger('publicAPI'),
):
    """initialize SPLIT_INFO for project

    Notes:
        Does not update global SPLIT_INFO (use `main` scope)

    Args:
        split_info_file (str, optional): path to split_info.json
        logger (:obj:`logging.logger`, optional): logging handle

    Returns:
        (:obj:`dict`) dict of type_id:SplitInfo

    """
    logger.info('Reading split file: {0}'.format(split_info_file))
    with open(split_info_file, 'r') as split_fh:
        split_list = json.load(split_fh)

    logger.info('loading split info into objects')
    split_collection = {}
    for split_info in split_list:
        split_obj = SplitInfo(split_info)
        logger.debug(split_obj)
        split_collection[split_obj.type_id] = split_obj

    return split_collection

def datetime_helper(
        datetime_str
):
    """try to conver datetime for comparison

    Args:
        datetime_str (str): datetime str (%Y-%m-%d) or (%Y-%m-%dT%H:%M:S)

    Returns:
        (:obj:`datetime.datetime`)

    """
    try:
        return_datetime = datetime.strptime(datetime_str, '%Y-%m-%d')
    except Exception:
        try:
            return_datetime = datetime.strptime(datetime_str, '%Y-%m-%dT%H:%M:%S')
        except Exception:
            raise

    return return_datetime

KEEP_COLUMNS = [
    'date', 'avgPrice', 'highPrice', 'lowPrice', 'volume', 'orders'
]
def fetch_split_cache_data(
        region_id,
        type_id,
        split_date=None,
        #split_cache_file=SPLIT_CACHE_FILE,
        keep_columns=KEEP_COLUMNS
):
    """get data from cache

    Args:
        region_id (int): EVE Online region id
        type_id (int): EVE Online type id
        split_cache_file (str, optional): path to split file

    Returns:
        (:obj:`pandas.data_frame`) pandas collection of data
            ['date', 'avgPrice', 'highPrice', 'lowPrice', 'volume', 'orders']

    """
    db_handle = TinyDB(api_config.SPLIT_CACHE_FILE)

    if split_date:
        split_data = db_handle.search(
            (Query().region_id == int(region_id)) &
            (Query().type_id == int(type_id)) &
            (Query().date <= split_date)
        )
    else:
        split_data = db_handle.search(
            (Query().region_id == int(region_id)) &
            (Query().type_id == int(type_id))
        )
    if not split_data:
        raise exceptions.NoSplitDataFound()

    split_data = pd.DataFrame(split_data)
    split_data = split_data[keep_columns]
    split_data.sort_values(
        by='date',
        ascending=False,
        inplace=True
    )

    return split_data

def combine_split_history(
        current_data,
        split_data,
        keep_columns=KEEP_COLUMNS
):
    """combine two dataframes into one at split_date

    Args:
        current_data (:obj:`pandas.DataFrame`): data from remote source
        split_data (:obj:`pandas.DataFrame`): data from cache
        keep_columns (:obj:`list`, optional): expected headers/columns for dataframe

    Returns:
        (:obj:`pandas.DataFrame`): combined data

    """
    current_data['date'] = pd.to_datetime(current_data['date']).dt.strftime('%Y-%m-%d')
    max_cache_date = split_data['date'].max()

    current_data = current_data[current_data.date > max_cache_date]
    current_data = current_data[keep_columns]
    current_data = current_data.append(
        split_data,
        ignore_index=True
    )
    current_data.sort_values(
        by='date',
        ascending=False,
        inplace=True
    )

    return current_data

PRICE_KEYS = ['avgPrice', 'highPrice', 'lowPrice']
VOLUME_KEYS = ['volume', 'orders']
def execute_split(
        split_dataframe,
        split_obj,
        price_keys=PRICE_KEYS,
        volume_keys=VOLUME_KEYS
):
    """apply split to dataframe

    Args:
        price_dataframe (:obj:`pandas.DataFrame`): data to be updated
        split_obj (:obj:`split_utils.SplitInfo`): recipe for splitting
        price_keys (:obj:`list`, optional): price columns
        volume_keys (:obj:`list`, optional): volume columns

    Returns:
        (:obj:`pandas.DataFrame`): updated dataframe

    """
    # vv FIXME vv: serial access to recast dataframe #
    split_cols = list(price_keys)
    split_cols.extend(volume_keys)
    for key in split_cols:
        split_dataframe[key] = pd.to_numeric(split_dataframe[key])
    # ^^ FIXME ^^ #

    split_dataframe[price_keys] = split_dataframe[price_keys] * split_obj
    split_dataframe[volume_keys] = split_dataframe[volume_keys] / split_obj

    return split_dataframe

def fetch_split_history(
        region_id,
        type_id,
        fetch_source,
        data_range=400,
        #split_cache_file=SPLIT_CACHE_FILE,
        config=api_config.CONFIG,
        logger=api_config.LOGGER
):
    """for split items, fetch and stitch the data together

    Args:
        region_id (int): EVE Online region_id
        type_id (int): EVE Online type_id
        fetch_source (:enum:`api_config.SwitchCCPSource`): which endpoint to fetch
        data_range (int, optional): how much total data to fetch
        config (:obj:`configparser.ConfigParser`, optional): config overrides
        logger (:obj:`logging.logger`, optional): logging handle

    Returns:
        (:obj:`pandas.DataFrame`) data from endpoint

    """
    ## Figure out if there's work to do ##
    if type_id not in api_config.SPLIT_INFO:
        raise exceptions.NoSplitConfigFound(
            'No config set for {0}'.format(type_id)
        )

    split_obj = api_config.SPLIT_INFO[type_id]
    fetch_id = split_obj.current_typeid()

    logger.debug(split_obj.__dict__)
    logger.info(
        'fetching data from remote {0} (was {1})'.\
        format(type_id, fetch_id)
    )
    ## Get current market data ##
    if fetch_source == api_config.SwitchCCPSource.EMD:
        logger.info('--EMD fetch')
        current_data = forecast_utils.fetch_market_history_emd(
            region_id,
            fetch_id,
            data_range=data_range,
            config=config,
            #logger=logger
        )
        current_data = forecast_utils.parse_emd_data(current_data['result'])
    else:
        logger.info('--CCP fetch')
        current_data = crest_utils.fetch_market_history(
            region_id,
            fetch_id,
            mode=fetch_source,
            config=config,
            logger=logger
        )

    ## Early exit: split too old or hasn't happened yet ##
    min_date = datetime_helper(current_data['date'].min())
    if min_date > split_obj.split_date or not bool(split_obj):
        #split is too old OR split hasn't happened yet
        logger.info('No split work -- Returning current pull')
        return current_data

    ## Fetch split data ##
    logger.info(
        '--fetching data from cache {0}@{1}'.format(
            split_obj.original_id, region_id
    ))
    split_data = fetch_split_cache_data(
        region_id,
        split_obj.original_id,
        split_date=split_obj.date_str
    )

    if type_id == split_obj.new_id: #adjust the back history
        logger.info('--splitting old-data')
        split_data = execute_split(
            split_data,
            split_obj
        )
    # vv FIX ME vv: Testable? #
    elif type_id == split_obj.original_id: #adjust the current data

        logger.info('--splitting new-data')
        current_data = execute_split(
            current_data,
            split_obj
        )
    # ^^ FIX ME ^^ #
    else:   #pragma: no cover
        logger.error(
            'Unable to map new/old type_ids correctly' +
            '\n\ttype_id={0}'.format(type_id) +
            '\n\toriginal_id={0} new_id={1}'.format(split_obj.original_id, split_obj.new_id),
            exc_info=True
        )
        raise exceptions.MissmatchedTypeIDs(
            status=500,
            message='unable to map types to splitcache function'
        )

    logger.info('--combining data')
    current_data.to_csv('current_data.csv', index=False)
    split_data.to_csv('split_data.csv', index=False)
    combined_data = combine_split_history(
        current_data.copy(),    #pass by value, not by reference
        split_data.copy()
    )

    if fetch_source == api_config.SwitchCCPSource.CREST:
        logger.info('--Setting CREST datetime')
        combined_data['date'] = pd.to_datetime(combined_data['date']).\
            dt.strftime('%Y-%m-%dT%H:%M:%S')
    return combined_data

