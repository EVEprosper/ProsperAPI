"""config.py: a place to hold config/globals"""
from os import path

import prosper.common.prosper_logging as p_logging
import prosper.common.prosper_config as p_config

HERE = path.abspath(path.dirname(__file__))

LOGGER = p_logging.DEFAULT_LOGGER
CONFIG = None #TODO
