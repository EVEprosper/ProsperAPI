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
VALID_RESPONSE_TYPES = ('json', 'csv', 'xml')
CREST_URL   = config.get('CREST', 'source_url')
USERAGENT   = config.get('GLOBAL', 'useragent')
RETRY_LIMIT = config.get('GLOBAL', 'default_retries')

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
    #todo: format emails better
    return errorMsg + '\n' + helpMsg

#TODO: log access per endpoint to database?
#### API ENDPOINTS ####
def OHLC_endpoint(parser, returnType):
    args = parser.parse_args()

    typeID       = -1
    typeID_CREST = None
    if 'typeID' in args:
        typeID = args.get('typeID')
        validTypeID, typeID_CREST = test_typeid(typeID)
        if not validTypeID:
            errorStr = 'Invalid TypeID given: ' + typeID
            Logger.error(errorStr)
            return errorStr, 400

    regionID       = -1
    regionID_CREST = None

    return None, None
class OHLCendpoint(Resource):
    '''Recieve calls on OHLC endpoint'''
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument(
            'regionID',
            type=int,
            required=True,
            help='regionID required',
            location=['args', 'headers']
        )
        self.reqparse.add_argument(
            'typeID',
            type=int,
            required=True,
            help='typeID required',
            location=['args', 'headers']
        )
        self.reqparse.add_argument(
            'User-Agent',
            type=str,
            required=True,
            help='user-agent required',
            location=['headers']
        )
        self.reqparse.add_argument(
            'api_key',
            type=str,
            required=False,
            help='API key for tracking requests',
            location=['args', 'headers']
        )

    def get(self, returnType):
        '''GET behavior'''
        Logger.info('OHLC request:' + returnType)
        Logger.debug(self.reqparse.parse_args())
        if returnType.lower() in VALID_RESPONSE_TYPES:
            message, status = OHLC_endpoint(self.reqparse, returnType.lower())
        else:
            errorStr = 'UNSUPPORTED RETURN TYPE: ' + returnType
            Logger.error(errorStr)
            message = errorStr
            status = 400

        return message, status

#### WORKER FUNCTIONS ####
def test_typeid(typeID):
    validTypeID  = False
    typeID_CREST = None
    try:
        typeID = int(typeID)
    except ValueError as err:
        errorStr = 'bad typeID recieved: ' + str(err)
        Logger.error(errorStr)
        return validTypeID, typeID_CREST

    crestResponse = fetch_crest('types', typeID)

def fetch_crest(endpointStr, value):
    crestResponse = None
    crest_endpoint_URL = CREST_URL + endpointStr + '/' + str(value) + '/'
    GET_headers = {
        'User-Agent': USERAGENT
    }
    last_error = ""
    Logger.info('Fetching CREST: ' + crest_endpoint_URL)
    for tries in range (0, RETRY_LIMIT):
        try:
            crest_request = requests.get(
                crest_endpoint_URL,
                headers=GET_headers
            )
        except requests.exceptions.ConnectTimeout as err:
            last_error = 'RETRY=' + str(tries) + ' ' + \
                'ConnectTimeout: ' + str(err)
            Logger.error(last_error)
            continue
        except requests.exceptions.ConnectionError as err:
            last_error = 'RETRY=' + str(tries) + ' ' + \
                'ConnectionError: ' + str(err)
            Logger.error(last_error)
            continue
        except requests.exceptions.ReadTimeout as err:
            last_error = 'RETRY=' + str(tries) + ' ' + \
                'ReadTimeout: ' + str(err)
            Logger.error(last_error)
            continue

        if crest_request.status_code == requests.codes.ok:
            try:
                crestResponse = crest_request.json()
            except ValueError as err:
                last_error = 'RETRY=' + str(tries) + ' ' + \
                    'request not JSON: ' + str(err)
                Logger.error(last_error)
                continue #try again
            break   #if all OK, break out of error checking
        else:
            last_error = 'RETRY=' + str(tries) + ' ' + \
                'bad status code: ' + str(crest_request.status_code)
            Logger.error(last_error)
            continue #try again
    else:
        criticalMessage = ''' ERROR: retries exceeded in crest_fetch()
    URL=''' + crest_endpoint_URL + '''
    LAST_ERROR=''' + last_error
        helpMsg = '''CREST Outage?'''
        criticalStr = email_body_builder(
            criticalMessage,
            helpMsg
        )
        Logger.critical(criticalStr)
    Logger.info('Fetched CREST:' + crest_endpoint_URL)
    Logger.debug(crestResponse)
    return(crestResponse)

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
