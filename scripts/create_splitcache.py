"""manage_api.py: tool for adding/removing API keys"""
from os import path, makedirs
from enum import Enum

from tinydb import TinyDB
from plumbum import cli

import prosper.common.prosper_logging as p_logging
HERE = path.abspath(path.dirname(__file__))
ROOT = path.dirname(HERE)

LOGGER = p_logging.DEFAULT_LOGGER
CACHE_PATH = path.join(ROOT, 'publicAPI', 'cache')
makedirs(CACHE_PATH, exist_ok=True)

class DataSources(Enum):
    SQL = 'sql',
    EMD = 'eve-marketdata',
    CREST = 'crest',
    ESI = 'esi'

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
        self.data_source = DataSource(data_source)

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

if __name__ == '__main__':
    ManageAPI.run()
