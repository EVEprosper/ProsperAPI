"""manager.py: Flask-Script launcher for services

using https://github.com/yabb85/ueki as prototype
"""
from os import path

from flask_script import Manager, Server
from plumbum import cli

from prosper.publicAPI import create_app

import prosper.common.prosper_logging as p_logging
import prosper.common.prosper_config as p_config

HERE = path.abspath(path.dirname(__file__))
ROOT = path.dirname(HERE)

CONFIG_FILEPATH = path.join(HERE, 'app.cfg')

CONFIG = p_config.ProsperConfig(CONFIG_FILEPATH)

SETTINGS = {
    'PORT':8001
}
APP = create_app(SETTINGS)

#manager = Manager(app)
#manager.add_command(
#    'runserver',
#    Server(
#        host='0.0.0.0',
#        port=SETTINGS['PORT']
#    )
#)
#manager.add_command(
#    'debug',
#    Server(
#        host='localhost',
#        port=SETTINGS['PORT']
#    )
#)
class PublicAPIRunner(cli.Application):
    """CLI wrapper for starting up/debugging Flask application"""
    _log_builder = p_logging.ProsperLogger(
        'ProsperAPI',
        CONFIG.get('LOGGING', 'log_path'),   #TODO, remove log_path?
        CONFIG
    )

    @cli.switch(
        ['v', '--verbose'],
        help='enable verbose logging'
    )
    def enable_verbose(self):
        """verbose logging: log to stdout"""
        self._log_builder.configure_debug_logger()

    debug = cli.Flag(
        ['d', '--debug'],
        help='run in headless/debug mode, do not connect to internet'
    )

    port = int(CONFIG.get('CREST', 'flask_port'))

    def main(self):
        """__main__ section for launching Flask app"""
        global LOGGER, DEBUG, MYSQL
        DEBUG = self.debug
        if not DEBUG:
            self._log_builder.configure_discord_logger()

        LOGGER = self._log_builder.get_logger()
        #TODO: push logger out to helper lib

        APP.config['MYSQL_USER']     = CONFIG.get('DB', 'user')
        APP.config['MYSQL_PASSWORD'] = CONFIG.get('DB', 'passwd')
        APP.config['MYSQL_DB']       = CONFIG.get('DB', 'schema')
        APP.config['MYSQL_PORT']     = CONFIG.get('DB', 'port')
        APP.config['MYSQL_HOST']     = CONFIG.get('DB', 'host')

        #MYSQL = MySQL(APP)  #TODO

        try:
            if DEBUG:
                Server(
                    host='localhost',
                    port=SETTINGS['PORT']
                )
            else:
                Server(
                    host='0.0.0.0',
                    port=SETTINGS['PORT']
                )
        except Exception as err:
            LOGGER.critical(
                __name__ + ' exiting unexpectedly',
                exc_info=True
            )

if __name__ == '__main__':
    PublicAPIRunner.run()
