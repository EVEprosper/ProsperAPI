"""__init__.py: Flask app configuration"""
from os import path

from flask import Flask

import publicAPI.crest_endpoint as crest_endpoint
import publicAPI.config as config

import prosper.common.prosper_logging as p_logging
import prosper.common.prosper_config as p_config

HERE = path.abspath(path.dirname(__file__))
CONFIG_FILE = path.join(HERE, 'publicAPI.cfg')
CONFIG = p_config.ProsperConfig(CONFIG_FILE)

def create_app(
        settings=None,
        local_configs=CONFIG,
        log_builder=None
):
    """create Flask application (ROOT)

    Modeled from: https://github.com/yabb85/ueki/blob/master/ueki/__init__.py

    Args:
        settings (:obj:`dict`, optional): collection of Flask options
        local_configs (:obj:`configparser.ConfigParser` optional): app private configs
        log_builder (:obj:`prosper_config.ProsperLogger`, optional): logging container

    """
    app = Flask(__name__)

    if settings:
        app.config.update(settings)

    crest_endpoint.API.init_app(app)

    if not log_builder:
        ## build default logging objects ##
        log_builder = p_logging.ProsperLogger(
            'publicAPI',
            HERE,
            local_configs
        )
        if not app.debug:
            log_builder.configure_discord_logger()

    if log_builder:
        for handle in log_builder:
            app.logger.addHandler(handle)

        config.LOGGER = log_builder.get_logger()
    config.CONFIG = CONFIG

    crest_endpoint.LOGGER = app.logger
    return app
