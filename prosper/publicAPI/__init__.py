"""__init__.py: Flask app configuration"""
from os import path

from flask import Flask

from prosper.publicAPI.crest_endpoint import API as crest_api
import prosper.common.prosper_logging as p_logging
import prosper.common.prosper_config as p_config

HERE = path.abspath(path.dirname(__file__))
def create_app(
        settings=None,
        local_configs=p_logging.COMMON_CONFIG,
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

    crest_api.init_app(app)
    #TODO mysql connector init_app()
    debug = app.debug

    #TODO: config.debug?
    log_builder = p_logging.ProsperLogger(
        'ProsperFlask',
        path.join(HERE, 'logs'),
        local_configs
    )
    if debug:
        log_builder.configure_debug_logger()
    else:
        log_builder.configure_discord_logger()

    for handle in log_builder.log_handlers:
        app.logger.addHandler(handle)

    return app
