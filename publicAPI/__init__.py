"""__init__.py: Flask app configuration"""
from os import path

from flask import Flask

import publicAPI.crest_endpoint as crest_endpoint
import publicAPI.config as config
import publicAPI.split_utils as split_utils

import prosper.common.prosper_logging as p_logging

HERE = path.abspath(path.dirname(__file__))

def create_app(
        settings=None,
        local_configs=None,
        testmode=False
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
    crest_endpoint.APP_HACK = app

    log_builder = p_logging.ProsperLogger(
        'publicAPI',
        '/var/log/prosper/',
        local_configs
    )
    if not app.debug or not testmode:
        log_builder.configure_discord_logger()
    else:
        log_builder.configure_debug_logger()

    if log_builder:
        for handle in log_builder:
            app.logger.addHandler(handle)

        config.LOGGER = log_builder.get_logger()

    config.CONFIG = local_configs
    config.load_globals(local_configs)
    crest_endpoint.LOGGER = app.logger

    config.SPLIT_INFO = split_utils.read_split_info(logger=crest_endpoint.LOGGER)
    return app
