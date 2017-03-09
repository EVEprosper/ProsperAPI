'''crest_endpoint.py: CREST centric REST API endpoints'''
import sys
import datetime
import os
import json

from logging.handlers import TimedRotatingFileHandler, SMTPHandler
from flask import Flask, Response, jsonify, Markup
from flask_restful import reqparse, Api, Resource, request
import requests
import pandas
from pandas.io.json import json_normalize

import crest
from crest import CRESTresults
import prosper.common.prosper_logging as p_logging
from prosper.common.prosper_config import get_config


#### CONFIG PARSER ####
HERE = os.path.abspath(os.path.dirname(__file__))
CONFIG_FILEPATH = os.path.join(HERE, 'prosperAPI.cfg')
config = get_config(CONFIG_FILEPATH)
LOG_PATH = config.get('LOGGING', 'log_folder')


LOGGER = p_logging.DEFAULT_LOGGER

BOOL_DEBUG_ENABLED = bool(config.get('GLOBAL', 'debug_enabled'))
CREST_FLASK_PORT   =  int(config.get('CREST', 'flask_port'))
#### GLOBALS ####
VALID_RESPONSE_TYPES = ('json', 'csv', 'xml', 'quandl')


#### FLASK HANDLERS ####
app = Flask(__name__)
api = Api(app)

#### LOGGING STUFF ####

#### LOGGING UTILITIES ####


#TODO: log access per endpoint to database?
#### FLASK STUFF ####
@api.representation('text/csv')
def output_csv(data, status, headers=None):
    resp = app.make_response(data)
    resp.headers['Content-Type'] = 'text/csv'
    return resp

#### API ENDPOINTS ####
def OHLC_endpoint(parser, returnType):
    '''Function for building OHLC response'''
    args = parser.parse_args()

    #TODO: shortcut for CSV? return?
    typeID       = -1
    typeCRESTobj = CRESTresults()
    if 'typeID' in args:
        typeID = args.get('typeID')
        typeCRESTobj = crest.test_typeid(typeID)
        if not typeCRESTobj:
            errorStr = 'Invalid TypeID given: ' + str(typeID)
            LOGGER.error(errorStr)
            return errorStr, 400
    LOGGER.info('Validated typeID: ' + str(typeID))
    #return typeCRESTobj.crestResponse, 200

    regionID       = -1
    regionCRESTobj = CRESTresults()
    if 'regionID' in args:
        regionID = args.get('regionID')
        regionCRESTobj = crest.test_regionid(regionID)
        if not regionCRESTobj:
            errorStr = 'Invalid regionID given: ' + str(regionID)
            LOGGER.error(errorStr)
            return errorStr, 400
    LOGGER.info('Validated regionID: ' + str(regionID))
    #return regionCRESTobj.crestResponse, 200

    #historyObj = fetch_crest_marketHistory(typeID, regionID)
    historyObj = crest.fetch_market_history(typeID, regionID)

    pandasObj  = process_crest_for_OHLC(historyObj)
    return pandasObj, None #TODO: this is bad

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

    def get(self, return_type):
        '''GET behavior'''
        LOGGER.info('OHLC request:' + return_type)
        LOGGER.debug(self.reqparse.parse_args())
        if return_type.lower() in VALID_RESPONSE_TYPES:
            message, status = OHLC_endpoint(self.reqparse, return_type.lower())
        else:
            error_str = 'UNSUPPORTED RETURN TYPE: ' + return_type
            LOGGER.warning(error_str)
            message = error_str
            status = 400
            return message, status
        if not status:  #TODO: this is bad, so bad
            if return_type == 'csv':
                LOGGER.info('reporting csv')
                csv_str = message.to_csv(
                    path_or_buf=None,
                    columns=[
                        'date',
                        'open',
                        'high',
                        'low',
                        'close',
                        'volume'
                    ],
                    header=True,
                    index=False
                )
                return_obj = output_csv(csv_str, 200)
                return return_obj
            elif return_type == 'json':
                LOGGER.info('reporting json')
                json_obj = message.to_json(
                    path_or_buf=None,
                    orient='records'
                )
                return json.loads(json_obj)

#### WORKER FUNCTIONS ####
def process_crest_for_OHLC(history_obj):
    '''refactor crest history into OHLC shape'''
    pandas_input = json_normalize(history_obj['items'])
    pandas_output = pandas.DataFrame(
        {
            'date'   : pandas_input['date'],
            'volume' : pandas_input['volume'],
            'close'  : pandas_input['avgPrice'],
            'open'   : pandas_input['avgPrice'].shift(1),
            'high'   : pandas_input['highPrice'],
            'low'    : pandas_input['lowPrice']
        }
    )
    LOGGER.info('Processed CREST->OHLC')
    LOGGER.debug(pandas_output[1:])
    return pandas_output[1:]

#### MAIN ####
api.add_resource(OHLCendpoint, config.get('ENDPOINTS', 'OHLC') + \
    '.<returnType>')
if __name__ == '__main__':
    LOG_BUILDER = p_logging.ProsperLoger(
        'ProsperAPI',
        LOG_PATH,
        config
    )

    if BOOL_DEBUG_ENABLED:
        LOG_BUILDER.configure_debug_logger()
        LOGGER = LOG_BUILDER.get_logger()
        crest.override_logger(LOGGER)
        app.run(
            debug=True,
            port=CREST_FLASK_PORT
        )
    else:
        LOG_BUILDER.configure_discord_logger()
        LOGGER = LOG_BUILDER.get_logger()
        crest.override_logger(LOGGER)
        app.run(
            host='0.0.0.0',
            port=CREST_FLASK_PORT
        )
