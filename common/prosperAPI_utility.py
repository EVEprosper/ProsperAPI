'''prosperAPI_utility.py: worker functions for CREST calls'''

import os
import logging
from logging.handlers import TimedRotatingFileHandler, SMTPHandler
import configparser
from configparser import ExtendedInterpolation

CONFIG_FILE = 'prosperAPI.cfg' #TODO: change to .cfg?

def get_config(subpath=''):
    '''returns config object for parsing global values'''
    config = configparser.ConfigParser(
        interpolation  = ExtendedInterpolation(),
        allow_no_value = True,
        delimiters     = ('=')
    )
    if subpath:
        config_filepath = os.path.join('..', subpath, CONFIG_FILE)
    else:
        config_filepath = os.path.join('..', 'common', CONFIG_FILE)

    if os.path.exists(config_filepath):
        with open(config_filepath, 'r') as filehandle:
            config.read_file(filehandle)
        return config
    return None

def create_logger(logName, logLevel_override = ''):
    '''creates logging handle for programs'''
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

def email_body_builder(errorMsg, helpMsg):
    '''Builds email message for easier reading with SMTPHandler'''
    #todo: format emails better
    return errorMsg + '\n' + helpMsg

def quandlfy_json(jsonObj):
    '''turn object from JSON into QUANDL-style JSON'''
    None

def quandlfy_xml(xmlObj):
    '''turn object from XML into QUANDL-style XML'''
    None
