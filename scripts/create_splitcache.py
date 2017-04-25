"""manage_api.py: tool for adding/removing API keys"""
from os import path, makedirs
from enum import Enum
import warnings

from tinydb import TinyDB
from plumbum import cli
import pandas as pd

import prosper.common.prosper_logging as p_logging
import publicAPI.crest_utils as crest_utils
import publicAPI.forecast_utils as forecast_utils
HERE = path.abspath(path.dirname(__file__))
ROOT = path.dirname(HERE)

LOGGER = p_logging.DEFAULT_LOGGER
CACHE_PATH = path.join(ROOT, 'publicAPI', 'cache')
makedirs(CACHE_PATH, exist_ok=True)

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
    11000031,   #'Thera'
]

class DataSources(Enum):
    SQL = 'sql',
    EMD = 'eve-marketdata',
    CREST = 'crest',
    ESI = 'esi'

def fetch_data(
        type_id,
        region_id,
        data_range,
        data_source,
        logger=LOGGER
):
    """fetch/crunch data for cache

    Args:
        type_id (int): EVE Online type_id for data
        data_range (int): days of back-propogation to fetch
        data_source (:enum:`DataSources`): which data source to fetch
        logger (:obj:`logging.logger`, optional): logging handle for printing

    Returns:
        (:obj:`pandas.DataFrame`): data for caching

    """
    if data_source == DataSources.CREST:
        data = fetch_crest(
            type_id,
            region_id,
            data_range
        )
    elif data_source == DataSources.ESI:
        data = fetch_esi(
            type_id,
            region_id,
            data_range
        )
    elif data_source == DataSources.EMD:
        data = fetch_emd(
            type_id,
            region_id,
            data_range
        )
    elif data_source == DataSources.SQL:
        raise NotImplementedError('SQL connection not supported at this time')
    else:
        raise NotImplementedError('Invalid DataSource: {0}'.format(repr(data_source)))

    return data

CREST_MAX = 400
def fetch_crest(
        type_id,
        region_id,
        data_range=400,
        logger=LOGGER
):
    """fetch data from CREST endpoint

    Args:
        type_id (int): EVE Online type_id
        region_id (int): EVE Online region_id
        data_range (int, optional): days of back-propogation
        logger (:obj:`logging.logger`, optional) logging handle

    Returns:
        (:obj:`pandas.DataFrame`): data from endpoint

    """
    if data_range > CREST_MAX:
        warnings.warn('CREST only returns %d days' % CREST_MAX, UserWarning)

    raise NotImplementedError('CREST fetching not supported')

def fetch_esi(
        type_id,
        region_id,
        data_range=400,
        logger=LOGGER
):
    """fetch data from ESI endpoint

    Args:
        type_id (int): EVE Online type_id
        region_id (int): EVE Online region_id
        data_range (int, optional): days of back-propogation
        logger (:obj:`logging.logger`, optional) logging handle

    Returns:
        (:obj:`pandas.DataFrame`): data from endpoint

    """
    if data_range > CREST_MAX:
        warnings.warn('ESI only returns %d days' % CREST_MAX, UserWarning)

    raise NotImplementedError('ESI fetching not supported')

def fetch_emd(
        type_id,
        region_id,
        data_range=400,
        logger=LOGGER
):
    """fetch data from eve-marketdata endpoint

    Args:
        type_id (int): EVE Online type_id
        region_id (int): EVE Online region_id
        data_range (int, optional): days of back-propogation
        logger (:obj:`logging.logger`, optional) logging handle

    Returns:
        (:obj:`pandas.DataFrame`): data from endpoint

    """
    pass

class SplitCache(cli.Application):
    """Seeds a splitcache file for research purposes"""
    __log_builder = p_logging.ProsperLogger(
        'api_manager',
        HERE
    )
    debug = cli.Flag(
        ['d', '--debug'],
        help='debug mode: do not write to live database'
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
        str,
        help='How many days to back-fetch'
    )
    def override_back_range(self, back_range):
        """override back_range from user"""
        self.back_range = back_range

    data_source = DataSources.EMD
    @cli.switch(
        ['s', '--source'],
        str,
        help='where to source data for backfill'
    )
    def override_data_source(self, data_source):
        """override data_source from user"""
        self.data_source = DataSources(data_source.lower())

    cache_path = path.join(CACHE_PATH, 'splitcache.json')
    @cli.switch(
        ['c', '--db'],
        str,
        help='path to alternate API database'
    )
    def override_cache_path(self, cache_path):
        """override cache path"""
        if path.isfile(cache_path):
            self.cache_path = cache_path
        else:
            raise FileNotFoundError

    type_id = 29668
    @cli.switch(
        ['t', '--type'],
        int,
        help='typeID required for back-db'
    )
    def override_type_id(self, type_id):
        """override type_id from user"""
        self.type_id = type_id

    def main(self):
        """application runtime"""
        global LOGGER
        LOGGER = self.__log_builder.logger

        LOGGER.info('hello world')

        for region_id in cli.terminal.Progress(REGION_LIST):
            LOGGER.debug('Fetching region_id: %d' % region_id)
            data = fetch_data(
                self.type_id,
                region_id,
                self.back_range,
                self.data_source,
                LOGGER
            )

if __name__ == '__main__':
    ManageAPI.run()
