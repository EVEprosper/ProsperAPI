"""manager.py: Flask-Script launcher for services

using https://github.com/yabb85/ueki as prototype
"""
from os import path

from flask_script import Manager, Server

from publicAPI import create_app

import prosper.common.prosper_logging as p_logging
import prosper.common.prosper_config as p_config

HERE = path.abspath(path.dirname(__file__))
ROOT = path.dirname(HERE)

CONFIG_FILEPATH = path.join(HERE, 'app.cfg')

CONFIG = p_config.ProsperConfig(CONFIG_FILEPATH)

SETTINGS = {
    'PORT':8001
}
APP = create_app(SETTINGS, CONFIG)

MANAGER = Manager(APP)
MANAGER.add_command(
    'runserver',
    Server(
        host='0.0.0.0',
        port=SETTINGS['PORT']
    )
)
MANAGER.add_command(
    'debug',
    Server(
        use_debugger=True,
        port=SETTINGS['PORT']
    )
)

if __name__ == '__main__':
    MANAGER.run()
