'''crest_endpoint.py: CREST centric REST API endpoints'''
import sys
sys.path.insert(0, '../common')
import datetime
import os
import json
import logging
from logging.handlers import TimedRotatingFileHandler, SMTPHandler
from flask import Flask, Response, jsonify, Markup
from flask_restful import reqparse, Api, Resource, request
from flaskext.markdown import Markdown
import requests
import pandas
from pandas.io.json import json_normalize
import prosperAPI_utility
import crest_utility
from crest_utility import CRESTresults

#### CONFIG PARSER ####
config = prosperAPI_utility.get_config('common')
Logger = prosperAPI_utility.create_logger('crest_endpoint')

BOOL_DEBUG_ENABLED = bool(config.get('GLOBAL', 'debug_enabled'))
CREST_FLASK_PORT   =  int(config.get('CREST', 'flask_port'))

#### GLOBALS ####
VALID_RESPONSE_TYPES = ('json', 'csv', 'xml')


#### FLASK HANDLERS ####
app = Flask(__name__)
api = Api(app)
md  = Markdown(app)

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
        typeCRESTobj = crest_utility.test_typeid(typeID)
        if not typeCRESTobj:
            errorStr = 'Invalid TypeID given: ' + str(typeID)
            Logger.error(errorStr)
            return errorStr, 400
    Logger.info('Validated typeID: ' + str(typeID))
    #return typeCRESTobj.crestResponse, 200

    regionID       = -1
    regionCRESTobj = CRESTresults()
    if 'regionID' in args:
        regionID = args.get('regionID')
        regionCRESTobj = crest_utility.test_regionid(regionID)
        if not regionCRESTobj:
            errorStr = 'Invalid regionID given: ' + str(regionID)
            Logger.error(errorStr)
            return errorStr, 400
    Logger.info('Validated regionID: ' + str(regionID))
    #return regionCRESTobj.crestResponse, 200

    historyObj = fetch_crest_marketHistory(typeID, regionID)
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
        if not status:  #TODO: this is bad, so bad
            if returnType == 'csv':
                Logger.info('reporting csv')
                csvStr = message.to_csv(
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
                returnObj = output_csv(csvStr, 200)
                return returnObj
            elif returnType == 'json':
                Logger.info('reporting json')
                jsonObj = message.to_json(
                            path_or_buf=None,
                            orient='records'
                        )
                pretty_jsonObj = quandlfy_json(jsonObj)
                print(jsonObj)

#### WORKER FUNCTIONS ####
def fetch_crest_marketHistory(typeID, regionID):
    '''CREST history call is weird, reformat/overload fetch_crest'''
    Logger.info('Fetching market history from CREST ' +\
        str(typeID) + ':' + str(regionID))
    crestResponse = None
    marketHistory_uri = 'market/{regionID}/history/?{crestURL}inventory/types'
    marketHistory_uri = marketHistory_uri.format(
        regionID = regionID,
        crestURL = config.get('CREST', 'source_url')
    )
    crestResponse = crest_utility.fetch_crest(
        marketHistory_uri,
        typeID
    )#TODO, make this better
    return crestResponse
    #CREST HISTORY CALL: [crest_addr]/market/[regionID]/types/[typeID]/history/

def process_crest_for_OHLC(historyObj):
    '''refactor crest history into OHLC shape'''
    pandasObj_input = json_normalize(historyObj['items'])
    pandasObj_output = pandas.DataFrame(
        {
            'date'   : pandasObj_input['date'],
            'volume' : pandasObj_input['volume'],
            'close'  : pandasObj_input['avgPrice'],
            'open'   : pandasObj_input['avgPrice'].shift(1),
            'high'   : pandasObj_input['highPrice'],
            'low'    : pandasObj_input['lowPrice']
        }
    )
    Logger.info('Processed CREST->OHLC')
    Logger.debug(pandasObj_output[1:])
    return pandasObj_output[1:]

#### MAIN ####
api.add_resource(OHLCendpoint, config.get('ENDPOINTS', 'OHLC') + \
    '.<returnType>')
if __name__ == '__main__':
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
