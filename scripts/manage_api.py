"""manage_api.py: tool for adding/removing API keys"""
from os import path, makedirs
from datetime import datetime

from tinydb import TinyDB, Query
from plumbum import cli
import shortuuid

import prosper.common.prosper_logging as p_logging
HERE = path.abspath(path.dirname(__file__))
ROOT = path.dirname(HERE)

LOGGER = p_logging.DEFAULT_LOGGER
CACHE_PATH = path.join(ROOT, 'publicAPI', 'cache')
makedirs(CACHE_PATH, exist_ok=True)

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

    force = cli.Flag(
        ['f', '--force'],
        help='force new api key'
    )

    @cli.switch(
        ['v', '--verbose'],
        help='Enable verbose messaging'
    )
    def enable_verbose(self):
        """toggle verbose logger"""
        self.__log_builder.configure_debug_logger()

    cache_path = path.join(CACHE_PATH, 'apikeys.json')
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


        api_db = TinyDB(self.cache_path)

        current_key = api_db.search(
            Query().user_name == username
        )
        if current_key:
            key_msg = \
            'user already has a key' + \
            '\n\tapi_key={0}'.format(current_key[0]['api_key']) + \
            '\n\tuser_name={0}'.format(current_key[0]['user_name']) + \
            '\n\tuser_info={0}'.format(current_key[0]['user_info']) + \
            '\n\tkey_generated={0}'.format(current_key[0]['key_generated']) + \
            '\n\tlast_accessed={0}'.format(current_key[0]['last_accessed'])

            print(key_msg)
            if not self.debug:
                LOGGER.info(key_msg)

            if not self.force:
                exit()

        if current_key and not self.debug:
            api_db.remove(
                Query().user_name == username
            )

        api_key_entry = {
            'api_key': shortuuid.uuid(),
            'user_name': username,
            'user_info': id_info,
            'key_generated': datetime.now().isoformat(),
            'last_accessed': None
        }

        if not self.debug:
            api_db.insert(api_key_entry)

        check_key = api_db.search(
            Query().user_name == username
        )

        if self.debug:
            api_msg = 'Key generated for {0}: {1}'.format(username, api_key_entry['api_key'])
        else:
            api_msg = 'Key generated for {0}: {1}'.\
                format(check_key[0]['user_name'], check_key[0]['api_key'])

        print(api_msg)
        if not self.debug:
            LOGGER.info(api_msg)
if __name__ == '__main__':
    ManageAPI.run()
