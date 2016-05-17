'''crest_endpoint.py: CREST centric REST API endpoints'''

import datetime
import os
import json
import configparser
import logging
from logging.handlers import TimedRotatingFileHandler, SMTPHandler
from flask import Flask, Response, jsonify, abort, Markup
from flask_restful import reqparse, Api, Resource, request
from flaskext.markdown import Markdown
import requests
import pandas

#### CONFIG PARSER ####
DEV_CONFIGFILE = os.getcwd() + "/init.ini" #TODO: figure out multi-file configparser in py35
#ALT_CONFIGFILE = os.getcwd() + '/init_local.ini'
config = configparser.ConfigParser()
config.read(DEV_CONFIGFILE)

BOOL_DEBUG_ENABLED = bool(config.get('GLOBAL', 'debug_enabled'))
CREST_FLASK_PORT   =  int(config.get('CREST', 'flask_port'))

#### GLOBALS ####


#### FLASK HANDLERS ####
app = Flask(__name__)
api = Api(app)
md  = Markdown(app)

#### LOGGING STUFF ####
LOG_ABSPATH = os.getcwd() + config.get('LOGGING', 'log_path')
if not os.path.exists(LOG_ABSPATH):
    os.mkdir(LOG_ABSPATH)
LOG_NAME    = __file__.replace('.py', '.log')
LOG_FORMAT  = '%(asctime)s;%(levelname)s;%(funcName)s;%(message)s'
LOG_LEVEL   = config.get('LOGGING', 'log_level')
LOG_FREQ    = config.get('LOGGING', 'log_freq')
LOG_TOTAL   = config.get('LOGGING', 'log_total')
EMAIL_TITLE = __file__.replace('.py', '') + " CRITICAL ERROR"
EMAIL_TOLIST= str(config.get('LOGGING', 'email_recipients')).split(',')
Logger = logging.getLogger(__name__)

#### LOGGING UTILITIES ####
def log_setup():
    '''Sets up logging object for app'''
    Logger.setLevel(LOG_LEVEL)
    generalHandler = TimedRotatingFileHandler(
        LOG_ABSPATH + '/' + __file__.replace('.py', '.log'),
        when        = LOG_FREQ,
        interval    = 1,
        backupCount = LOG_TOTAL
    )
    formatter = logging.Formatter(LOG_FORMAT)
    generalHandler.setFormatter(formatter)
    Logger.addHandler(generalHandler)

    #TODO: replace email handler with log scraper?
    emailHandler = SMTPHandler(
        mailhost    = config.get('LOGGING', 'email_server') + ':' + \
                      config.get('LOGGING', 'email_port'),
        fromaddr    = config.get('LOGGING', 'email_fromaddr'),
        toaddrs     = EMAIL_TOLIST,
        subject     = EMAIL_TITLE,
        credentials = (config.get('LOGGING', 'email_username'),
                       config.get('LOGGING', 'email_secret'))
    )
    emailHandler.setLevel(config.get('LOGGING', 'log_email_level'))
    emailHandler.setFormatter(formatter)
    Logger.addHandler(emailHandler)

def email_body_builder(errorMsg, helpMsg):
    '''Builds email message for easier reading with SMTPHandler'''
    None

#TODO: log access per endpoint to database?
#### API ENDPOINTS ####
def OHLC_endpoint(parser, returnType):
    return None, None
class OHLCendpoint(Resource):
    '''Recieve calls on OHLC endpoint'''
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('regionID',
                                   type=int,
                                   required=True,
                                   help='regionID required',
                                   location=['args', 'headers'])
        self.reqparse.add_argument('typeID',
                                   type=int,
                                   required=True,
                                   help='typeID required',
                                   location=['args', 'headers'])
        self.reqparse.add_argument('User-Agent',
                                   type=str,
                                   required=True,
                                   help='user-agent required',
                                   location=['headers'])
        self.reqparse.add_argument('api_key',
                                   type=str,
                                   required=False,
                                   help='API key for tracking requests',
                                   location=['args', 'headers'])

    def get(self, returnType):
        '''GET behavior'''
        Logger.info('OHLC request:' + returnType)
        Logger.debug(self.reqparse.parse_args())
        message, status = OHLC_endpoint(self.reqparse, returnType)

#### WORKER FUNCTIONS ####

#### MAIN ####
api.add_resource(OHLCendpoint, config.get('ENDPOINTS', 'OHLC') + \
    '.<returnType>')
if __name__ == '__main__':
    log_setup()
    if BOOL_DEBUG_ENABLED:
        app.run(
            debug=True,
            port = CREST_FLASK_PORT
        )
    else:
        app.run(
            host = '0.0.0.0',
            port = CREST_FLASK_PORT
        )
