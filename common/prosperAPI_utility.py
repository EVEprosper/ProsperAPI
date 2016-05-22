'''prosperAPI_utility.py: worker functions for CREST calls'''

import datetime
import os
import json
import configparser
import requests

CONFIG_FILE = 'init.ini' #TODO: change to .cfg?

def get_config(dir=''):
    config = configparser.ConfigParser()
    config_filepath = os.path.join(dir, CONFIG_FILE)
    
    if os.path.exists(config_filepath):
        with open(config_filepath, 'r') as filehandle:
            config.read_file(filehandle)
        return config
    return None