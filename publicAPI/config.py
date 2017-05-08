"""config.py: a place to hold config/globals"""
from os import path
from enum import Enum

import prosper.common.prosper_logging as p_logging
import prosper.common.prosper_config as p_config

HERE = path.abspath(path.dirname(__file__))

LOGGER = p_logging.DEFAULT_LOGGER
CONFIG = None #TODO

USER_AGENT = 'lockefox https://github.com/EVEprosper/ProsperAPI'
USER_AGENT_SHORT = 'lockefox @EVEProsper test'

DEFAULT_RANGE = 60
MAX_RANGE = 180
DEFAULT_HISTORY_RANGE = 700
EXPECTED_CREST_RANGE = 400

SPLIT_CACHE_FILE = path.join(HERE, 'cache', 'splitcache.json')

class SwitchCCPSource(Enum):
    """enum for switching between crest/esi"""
    ESI = 'ESI'
    CREST = 'CREST'
    EMD = 'EMD'

def load_globals(config=CONFIG):
    """loads global vars from config object"""
    global USER_AGENT, USER_AGENT_SHORT, DEFAULT_RANGE, MAX_RANGE

    USER_AGENT = config.get('GLOBAL', 'useragent')
    USER_AGENT_SHORT = config.get('GLOBAL', 'useragent_short')

    DEFAULT_RANGE = int(config.get('CREST', 'prophet_range'))
    MAX_RANGE = int(config.get('CREST', 'prophet_max'))

SPLIT_INFO = {}
