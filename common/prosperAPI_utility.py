'''prosperAPI_utility.py: worker functions for CREST calls'''

import datetime
import os
import json
import configparser
from configparser import ExtendedInterpolation
import logging
from logging.handlers import TimedRotatingFileHandler, SMTPHandler
import requests

CONFIG_FILE = 'prosperAPI.cfg' #TODO: change to .cfg?

def get_config(dir=''):
    config = configparser.ConfigParser(
        interpolation  = ExtendedInterpolation(),
        allow_no_value = True,
        delimiters     = ('=')
    )
    config_filepath = os.path.join('..', dir, CONFIG_FILE)
    print(config_filepath)
    if os.path.exists(config_filepath):
        with open(config_filepath, 'r') as filehandle:
            config.read_file(filehandle)
        return config
    return None

def create_logger(logName, logLevel_override = ''):
    tmpConfig = get_config('common')

    logFolder = os.path.join('..', tmpConfig.get('LOGGING', 'logFolder'))
    if not os.path.exists(logFolder):
        os.makedirs(logFolder)

    Logger = logging.getLogger(logName)

    logLevel  = tmpConfig.get('LOGGING', 'logLevel')
    logFreq   = tmpConfig.get('LOGGING', 'logFreq')
    logTotal  = tmpConfig.get('LOGGING', 'logTotal')
    logName   = logName + '.log'
    logFormat = '%(asctime)s;%(levelname)s;%(funcName)s;%(message)s'

    if logLevel_override:
        logLevel = logLevel_override

    logFullpath = os.path.join(logFolder, logName)

    Logger.setLevel(logLevel)
    generalHandler = TimedRotatingFileHandler(
        logFullpath,
        when        = logFreq,
        interval    = 1,
        backupCount = logTotal
    )
    formatter = logging.Formatter(logFormat)
    generalHandler.setFormatter(formatter)
    Logger.addHandler(generalHandler)

    emailSource     = tmpConfig.get('LOGGING', 'emailSource')
    emailRecipients = tmpConfig.get('LOGGING', 'emailRecipients')
    emailUsername   = tmpConfig.get('LOGGING', 'emailUsername')
    emailFromaddr   = tmpConfig.get('LOGGING', 'emailFromaddr')
    emailSecret     = tmpConfig.get('LOGGING', 'emailSecret')
    emailServer     = tmpConfig.get('LOGGING', 'emailServer')
    emailPort       = tmpConfig.get('LOGGING', 'emailPort')
    emailTitle      = logName + ' CRITICAL ERROR'

    bool_doEmail = (
        emailSource     and
        emailRecipients and
        emailUsername   and
        emailFromaddr   and
        emailSecret     and
        emailServer     and
        emailPort
    )
    if bool_doEmail:
        emailHandler = SMTPHandler(
            mailhost    = emailServer + ':' + emailPort,
            fromaddr    = emailFromaddr,
            toaddrs     = str(emailRecipients).split(','),
            subject     = emailTitle,
            credentials = (emailUsername, emailSecret)
        )
        emailHandler.setFormatter(formatter)
        Logger.addHandler(emailHandler)

    return Logger
