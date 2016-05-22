'''prosperAPI_utility.py: worker functions for CREST calls'''

import datetime
import os
import json
import configparser
from configparser import ExtendedInterpolation
import requests

CONFIG_FILE = 'prosperAPI.cfg' #TODO: change to .cfg?

def get_config(dir=''):
    config = configparser.ConfigParser(
        interpolation  = ExtendedInterpolation(),
        allow_no_value = True,
        delimiters     = ('=')
    )
    config_filepath = os.path.join(dir, CONFIG_FILE)
    
    if os.path.exists(config_filepath):
        with open(config_filepath, 'r') as filehandle:
            config.read_file(filehandle)
        return config
    return None
    
def create_logger(log_name, log_level='INFO'):
    