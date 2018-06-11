"""manage_api.py: tool for adding/removing API keys"""
from os import path, makedirs
from datetime import datetime
from enum import Enum
import warnings

from tinydb import TinyDB, Query
from plumbum import cli
import pandas as pd
import ujson as json

import prosper.common.prosper_logging as p_logging
import prosper.common.prosper_config as p_config
import publicAPI.crest_utils as crest_utils
import publicAPI.forecast_utils as forecast_utils
import publicAPI.config as api_utils
HERE = path.abspath(path.dirname(__file__))
ROOT = path.dirname(HERE)

CACHE_PATH = path.join(ROOT, 'publicAPI', 'cache')
CONFIG = p_config.ProsperConfig(path.join(HERE, 'app.cfg'))
makedirs(CACHE_PATH, exist_ok=True)
PROGNAME = 'splitcache_helper'

REGION_LIST = [
    10000001,   #'Derelik',
    10000002,   #'The Forge',
    10000003,   #'Vale of the Silent',
    10000005,   #'Detorid',
    10000006,   #'Wicked Creek',
    10000007,   #'Cache',
    10000008,   #'Scalding Pass',
    10000009,   #'Insmother',
    10000010,   #'Tribute',
    10000011,   #'Great Wildlands',
    10000012,   #'Curse',
    10000013,   #'Malpais',
    10000014,   #'Catch',
    10000015,   #'Venal',
    10000016,   #'Lonetrek',
    10000018,   #'The Spire',
    10000020,   #'Tash-Murkon',
    10000021,   #'Outer Passage',
    10000022,   #'Stain',
    10000023,   #'Pure Blind',
    10000025,   #'Immensea',
    10000027,   #'Etherium Reach',
    10000028,   #'Molden Heath',
    10000029,   #'Geminate',
    10000030,   #'Heimatar',
    10000031,   #'Impass',
    10000032,   #'Sinq Liaison',
    10000033,   #'The Citadel',
    10000034,   #'The Kalevala Expanse',
    10000035,   #'Deklein',
    10000036,   #'Devoid',
    10000037,   #'Everyshore',
    10000038,   #'The Bleak Lands',
    10000039,   #'Esoteria',
    10000040,   #'Oasa',
    10000041,   #'Syndicate',
    10000042,   #'Metropolis',
    10000043,   #'Domain',
    10000044,   #'Solitude',
    10000045,   #'Tenal',
    10000046,   #'Fade',
    10000047,   #'Providence',
    10000048,   #'Placid',
    10000049,   #'Khanid',
    10000050,   #'Querious',
    10000051,   #'Cloud Ring',
    10000052,   #'Kador',
    10000053,   #'Cobalt Edge',
    10000054,   #'Aridia',
    10000055,   #'Branch',
    10000056,   #'Feythabolis',
    10000057,   #'Outer Ring',
    10000058,   #'Fountain',
    10000059,   #'Paragon Soul',
    10000060,   #'Delve',
    10000061,   #'Tenerifis',
    10000062,   #'Omist',
    10000063,   #'Period Basis',
    10000064,   #'Essence',
    10000065,   #'Kor-Azor',
    10000066,   #'Perrigen Falls',
    10000067,   #'Genesis',
    10000068,   #'Verge Vendor',
    10000069,   #'Black Rise',
    #11000031,   #'Thera'
]

class DataSources(Enum):
    SQL = 'sql'
    EMD = 'eve-marketdata'
    CREST = 'crest'
    ESI = 'esi'

def fetch_data(
        type_id,
        region_id,
        data_range,
        data_source,
        logger=logging.getLogger(PROGNAME)
):
    """fetch/crunch data for cache

    Args:
        type_id (int): EVE Online type_id for data
        data_range (int): days of back-propogation to fetch
        data_source (:enum:`DataSources`): which data source to fetch
        logger (:obj:`logging.logger`): logging handle for printing

    Returns:
        pandas.DataFrame: data for caching

    """
    if data_source == DataSources.ESI:
        data = fetch_esi(
            type_id,
            region_id,
            data_range,
            logger
        )
    elif data_source == DataSources.EMD:
        data = fetch_emd(
            type_id,
            region_id,
            data_range,
            logger
        )
    elif data_source == DataSources.SQL:
        raise NotImplementedError('SQL connection not supported at this time')
    else:
        raise NotImplementedError('Invalid DataSource: {0}'.format(repr(data_source)))

    data['type_id'] = type_id
    data['region_id'] = region_id
    data['data_source'] = data_source.name
    data['cache_date'] = datetime.utcnow().strftime('%Y-%m-%d')
    return data

CREST_MAX = 400
def fetch_esi(
        type_id,
        region_id,
        data_range=400,
        logger=logging.getLogger(PROGNAME)
):
    """fetch data from ESI endpoint

    Args:
        type_id (int): EVE Online type_id
        region_id (int): EVE Online region_id
        data_range (int, optional): days of back-propogation
        logger (:obj:`logging.logger`) logging handle

    Returns:
        pandas.DataFrame: data from endpoint

    """
    logger.info('--Fetching price history: ESI')
    if data_range > CREST_MAX:
        warning_msg = 'ESI only returns %d days' % CREST_MAX
        warnings.warn(warning_msg, UserWarning)
        logger.warning(warning_msg)

    data = crest_utils.fetch_market_history(
        region_id,
        type_id,
        config=CONFIG,
        logger=logger
    )

    return data.tail(n=data_range)

def fetch_emd(
        type_id,
        region_id,
        data_range=400,
        logger=logging.getLogger(PROGNAME)
):
    """fetch data from eve-marketdata endpoint

    Args:
        type_id (int): EVE Online type_id
        region_id (int): EVE Online region_id
        data_range (int, optional): days of back-propogation
        logger (:obj:`logging.logger`) logging handle

    Returns:
        pandas.DataFrame: data from endpoint

    """
    logger.info('--Fetching price history: EMD')

    data = forecast_utils.fetch_extended_history(
        region_id,
        type_id,
        data_range=data_range,
        config=CONFIG,
        min_data=0,
        logger=logger
    )

    return data

def write_to_cache_file(
        data,
        cache_path,
        type_id=0,
        region_id=0,
        logger=logging.getLogger(PROGNAME)
):
    """save data to tinyDB

    Args:
        data (:obj:`pandas.DataFrame`): data to write out
        cache_path (str): path to cache file
        type_id (int, optional): EVE Online type_id
        region_id (int, optional): EVE Online region_id
        logger (:obj:`logging.logger`): logging handle

    Returns:
        None

    """
    ## get DB ##
    logger.info('Writing data to cache')
    tdb = TinyDB(cache_path)

    date_min = data['date'].min()
    logger.debug(date_min)
    ## clean out existing entries ##
    if (type_id and region_id):
        logger.info('--Removing old cache entries')
        tdb.remove(
            (Query().region_id == region_id) &
            (Query().type_id == type_id) &
            (Query().date >= date_min)
        )

    caching_data_str = data.to_json(
        date_format='iso',
        orient='records'
    )
    cache_data = json.loads(caching_data_str)
    logger.info('--Writing to cache file')
    tdb.insert_multiple(cache_data)

class SplitCache(cli.Application):
    """Seeds a splitcache file for research purposes"""
    __log_builder = p_logging.ProsperLogger(
        'splitcache_helper',
        HERE
    )
    debug = cli.Flag(
        ['d', '--debug'],
        help='debug mode: do not write to live database'
    )
    force = cli.Flag(
        ['f', '--force'],
        help='Clean out old cache entries'
    )
    @cli.switch(
        ['v', '--verbose'],
        help='Enable verbose messaging'
    )
    def enable_verbose(self):
        """toggle verbose logger"""
        self.__log_builder.configure_debug_logger()

    back_range = 750
    @cli.switch(
        ['r', '--range'],
        int,
        help='How many days to back-fetch'
    )
    def override_back_range(self, back_range):
        """override back_range from user"""
        self.back_range = back_range

    data_source = DataSources.EMD
    @cli.switch(
        ['s', '--source'],
        str,
        help='where to source data for backfill')
    def override_data_source(self, data_source):
        """override data_source from user"""
        self.data_source = DataSources(data_source.lower())

    cache_path = path.join(CACHE_PATH, 'splitcache.json')
    @cli.switch(
        ['c', '--db'],
        str,
        help='path to alternate API database')
    def override_cache_path(self, cache_path):
        """override cache path"""
        self.cache_path = cache_path

    type_id = 29668
    @cli.switch(
        ['t', '--type'],
        str,
        help='typeID required for back-db')
    def override_type_id(self, type_id):
        """override type_id from user"""
        self.type_id = list(map(int, type_id.split(',')))

    region_list = REGION_LIST
    @cli.switch(
        ['--regions'],
        str,
        help='list of regions to scrape')
    def override_region_list(self, region_str):
        """override region list from user"""
        self.region_list = list(map(int, region_str.split(',')))

    def main(self):
        """application runtime"""
        logger = self.__log_builder.logger

        logger.info('hello world')

        for region_id in cli.terminal.Progress(self.region_list):
            for type_id in self.type_id:
                logger.info('Fetching: {0}@{1}'.format(type_id, region_id))
                data = fetch_data(
                    type_id,
                    region_id,
                    self.back_range,
                    self.data_source,
                    logger
                )
                if self.force:
                    ## WARNING: deletes old cache values ##
                    write_to_cache_file(
                        data,
                        self.cache_path,
                        type_id=type_id,
                        region_id=region_id,
                        logger=logger
                    )
                else:
                    write_to_cache_file(
                        data,
                        self.cache_path,
                        logger=logger
                    )

if __name__ == '__main__':
    SplitCache.run()
