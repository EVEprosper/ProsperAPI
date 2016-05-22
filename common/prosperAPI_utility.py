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

def create_logger(logName, logLevel_override = ''):
    tmpConfig = get_config()

    logFolder = os.path.join('..', tmpConfig['LOGGING', 'logFolder'])
    if not os.path.exists(logFolder):
        os.makedirs(logFolder)

    logLevel = tmpConfig['LOGGING', 'logLevel']
    logFreq  = tmpConfig['LOGGING', 'logFreq']
    logTotal = tmpConfig['LOGGING', 'logTotal']
    logName  = logName + '.log'

    if logLevel_override:
        logLevel = logLevel_override

    logFullpath = os.path.join(logFolder, logName)
    generalHandler = TimedRotatingFileHandler(
        logFullpath,
        when        = logFreq,
        interval    = 1,
        backupCount = logTotal
    )

    emailSource     = tmpConfig['LOGGING', 'emailSource']
    emailRecipients = tmpConfig['LOGGING', 'emailRecipients']
    emailUsername   = tmpConfig['LOGGING', 'emailUsername']
    emailFromaddr   = tmpConfig['LOGGING', 'emailFromaddr']
    emailSecret     = tmpConfig['LOGGING', 'emailSecret']
    emailServer     = tmpConfig['LOGGING', 'emailServer']
    emailPort       = tmpConfig['LOGGING', 'emailPort']

    bool_doEmail = (
        emailSource     and
        emailRecipients and
        emailUsername   and
        emailFromaddr   and
        emailSecret     and
        emailServer     and
        emailPort
    )
