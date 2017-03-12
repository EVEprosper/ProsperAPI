"""__init__.py: Flask app configuration"""
from os import path

from flask import Flask

from prosper.publicAPI.crest_endpoint import API as crest_api
import prosper.common.prosper_logging as p_logging

HERE = path.abspath(path.dirname(__file__))
def create_app(settings=None):
    """create Flask application (ROOT)

    Modeled from: https://github.com/yabb85/ueki/blob/master/ueki/__init__.py
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
        path.join(HERE, 'logs')
        #TODO config
    )
    if debug:
        log_builder.configure_debug_logger()
    else:
        log_builder.configure_discord_logger()

    for handle in log_builder.log_handlers:
        app.logger.addHandler(handle)

    return app
