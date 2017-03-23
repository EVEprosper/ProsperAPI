"""manage_api.py: tool for adding/removing API keys"""
from os import path

from tinydb import TinyDB, Query
from plumbum import cli
import shortuuid

import prosper.common.prosper_logging as p_logging
HERE = path.abspath(path.dirname(__file__))
ROOT = path.dirname(HERE)

LOGGER = p_logging.DEFAULT_LOGGER

class ManageAPI(cli.Application):
    """Manager for Prosper API keys (manual)"""
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

    cache_path = path.join(ROOT, 'publicAPI', 'apikeys.json')
    @cli.switch(
        ['f', '--db'],
        str,
        help='path to alternate API database'
    )
    def override_cache_path(self, cache_path):
        """override cache path"""
        if path.isfile(cache_path):
            self.cache_path = cache_path
        else:
            raise FileNotFoundError

    def main(self):
        """application runtime"""
        global LOGGER
        LOGGER = self.__log_builder.logger

        LOGGER.info('hello world')

        username = cli.terminal.readline(
            message='Username for key: '
        ).rstrip()
        id_info = cli.terminal.readline(
            message='Info about user: '
        ).rstrip()

        LOGGER.info('making key for {0}:{1}'.format(username, id_info))

if __name__ == '__main__':
    ManageAPI.run()
