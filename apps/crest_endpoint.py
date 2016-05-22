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
#class CRESTresults(object):
#    '''Parser/storage for CREST/SDE lookups'''
#    def __init__ (self):
#        self.objectID      = -1
#        self.objectName    = ''
#        self.crestResponse = None
#        self.endpointType  = ''
#        self.bool_SuccessStatus = False
#
#    def __bool__ (self):
#        '''test if object is loaded with valid data'''
#        return self.bool_SuccessStatus
#
#    def parse_crest_response(self, crestJSON, endpointType):
#        '''splits out crest response for name/ID/info conversion'''
#        self.bool_SuccessStatus = False
#        try:
#            self.objectID   = crestJSON['id']
#            self.objectName = crestJSON['name']
#        except KeyError as err:
#            errorStr = 'Unable to load name/ID from CREST object ' + \
#                str(endpointType) + ' ' + str(err)
#            Logger.error(errorStr)
#            Logger.debug(crestJSON)
#            return self.bool_SuccessStatus
#
#        self.crestResponse = crestJSON
#        self.endpointType  = endpointType
#        self.bool_SuccessStatus = True
#        infoStr = 'Success: parsed ' + str(self.objectID) + ':' + \
#            str(self.objectName) + ' ' +\
#            'from ' + str(endpointType)
#        Logger.info(infoStr)
#        return self.bool_SuccessStatus
#
#    def write_cache_response(self, crestJSON, endpointType):
#        '''update on-file cache'''
#        cachePath = CACHE_ABSPATH + '/' + endpointType
#        if not os.path.exists(cachePath):
#            #TODO: repeated function
#            os.mkdir(cachePath)
#            Logger.info('Created cache path: ' + cachePath)
#            return False
#
#        cacheFilePath  = cachePath + '/' + str(self.objectID) + '.json'
#        bool_writeFile = False
#        if os.path.isfile(cacheFilePath):
#            #cache exists on file
#            fileAccessStats  = os.stat(cacheFilePath)
#            modifiedDatetime = datetime.datetime.fromtimestamp(
#                fileAccessStats.st_mtime
#            )
#            nowDatetime = datetime.datetime.now()
#            fileAge = (modifiedDatetime - nowDatetime).total_seconds()
#            Logger.debug(cacheFilePath + '.fileAge=' + str(fileAge))
#            if fileAge > SDE_CACHE_LIMIT:
#                bool_writeFile = True
#        else:
#            bool_writeFile = True
#
#        if bool_writeFile:
#            Logger.info('updating cache file: ' + cacheFilePath)
#            try:
#                with open(cacheFilePath, 'w') as file_handle:
#                    file_handle.write(json.dumps(crestJSON))
#            except Exception as err:
#                errorStr = 'Unable to write cache to file ' + str(err)
#                Logger.error(errorStr)
#                Logger.debug(crestJSON)

#def test_typeid(typeID):
#    '''Validates typeID is queryable'''
#    crestObj = CRESTresults()
#
#    try:    #test types
#        typeID_INT = int(typeID)
#    except ValueError as err:
#        errorStr = 'bad typeID recieved: ' + str(err)
#        Logger.error(errorStr)
#        return None
#
#    jsonObj = None
#    cacheResponse = check_cache(typeID, 'types')
#    if not cacheResponse:
#        Logger.info('fetching crest ' + str(typeID))
#        crestResponse = fetch_crest('types', typeID)    #test CREST endpoint
#        jsonObj = crestResponse
#    else:
#        Logger.info('using local cache ' + str(typeID))
#        jsonObj = cacheResponse
#
#    validCrest = crestObj.parse_crest_response(jsonObj, 'types')
#    crestObj.write_cache_response(jsonObj, 'types')
#    if validCrest:
#        #success
#        Logger.info('CREST/types pulled correctly')
#        return crestObj
#    else:
#        errorStr = 'invalid crestObj'
#        Logger.error(errorStr)
#        return None
#
#def test_regionid(regionID):
#    '''Validates regionID is queryable'''
#    crestObj = CRESTresults()
#
#    try:    #test types
#        regionID_INT = int(regionID)
#    except ValueError as err:
#        errorStr = 'bad regionID recieved: ' + str(err)
#        Logger.error(errorStr)
#        return None
#
#    jsonObj = None
#    cacheResponse = check_cache(regionID, 'regions')
#    if not cacheResponse:
#        crestResponse = fetch_crest('regions', regionID)  #test CREST endpoint
#        jsonObj = crestResponse
#    else:
#        jsonObj = cacheResponse
#
#    validCrest = crestObj.parse_crest_response(jsonObj, 'regions')
#    crestObj.write_cache_response(jsonObj, 'regions')
#    if validCrest:
#        #success
#        Logger.info('CREST/regions pulled correctly')
#        return crestObj
#    else:
#        errorStr = 'invalid crestObj'
#        Logger.error(errorStr)
#        return None

def fetch_crest_marketHistory(typeID, regionID):
    '''CREST history call is weird, reformat/overload fetch_crest'''
    Logger.info('Fetching market history from CREST ' +\
        str(typeID) + ':' + str(regionID))
    crestResponse = None
    crestResponse = crest_utility.fetch_crest(
        'market/' + str(regionID) + '/types/' + str(typeID),
        'history'
    )
    return crestResponse
    #CREST HISTORY CALL: [crest_addr]/market/[regionID]/types/[typeID]/history/

#def fetch_crest(endpointStr, value):
#    '''Fetches CREST endpoints and returns JSON.  Has retry built in'''
#    crestResponse = None
#    crest_endpoint_URL = CREST_URL + endpointStr + '/' + str(value) + '/'
#    GET_headers = {
#        'User-Agent': USERAGENT
#    }
#    last_error = ""
#    Logger.info('Fetching CREST: ' + crest_endpoint_URL)
#    for tries in range (0, RETRY_LIMIT):
#        try:
#            crest_request = requests.get(
#                crest_endpoint_URL,
#                headers=GET_headers
#            )
#        except requests.exceptions.ConnectTimeout as err:
#            last_error = 'RETRY=' + str(tries) + ' ' + \
#                'ConnectTimeout: ' + str(err)
#            Logger.error(last_error)
#            continue
#        except requests.exceptions.ConnectionError as err:
#            last_error = 'RETRY=' + str(tries) + ' ' + \
#                'ConnectionError: ' + str(err)
#            Logger.error(last_error)
#            continue
#        except requests.exceptions.ReadTimeout as err:
#            last_error = 'RETRY=' + str(tries) + ' ' + \
#                'ReadTimeout: ' + str(err)
#            Logger.error(last_error)
#            continue
#
#        if crest_request.status_code == requests.codes.ok:
#            try:
#                crestResponse = crest_request.json()
#            except ValueError as err:
#                last_error = 'RETRY=' + str(tries) + ' ' + \
#                    'request not JSON: ' + str(err)
#                Logger.error(last_error)
#                continue #try again
#            break   #if all OK, break out of error checking
#        else:
#            last_error = 'RETRY=' + str(tries) + ' ' + \
#                'bad status code: ' + str(crest_request.status_code)
#            Logger.error(last_error)
#            continue #try again
#    else:
#        criticalMessage = ''' ERROR: retries exceeded in crest_fetch()
#    URL=''' + crest_endpoint_URL + '''
#    LAST_ERROR=''' + last_error
#        helpMsg = '''CREST Outage?'''
#        criticalStr = prosperAPI_utility.email_body_builder(
#            criticalMessage,
#            helpMsg
#        )
#        Logger.critical(criticalStr)
#    Logger.info('Fetched CREST:' + crest_endpoint_URL)
#    Logger.debug(crestResponse)
#    return crestResponse
#
#def check_cache(objectID, endpointName):
#    '''Try to read CREST/SDE items off disk'''
#    cachePath = CACHE_ABSPATH + '/' + endpointName
#    if not os.path.exists(cachePath):
#        #TODO: repeated function
#        os.mkdir(cachePath)
#        Logger.info('Created cache path: ' + cachePath)
#        return None
#
#    jsonObj = None
#    cacheFilePath = cachePath + '/' + str(objectID) + '.json'
#    if os.path.isfile(cacheFilePath):
#        try:
#            with open(cacheFilePath, 'r') as file_handle:
#                jsonObj = json.load(file_handle)
#        except Exception as err:
#            errorStr = 'unable to read json: ' + cacheFilePath + \
#                ' ' + str(err)
#            Logger.error(errorStr)
#            #TODO: delete cached file?
#            return None #need to read again from CREST
#        return jsonObj
#    else:
#        return None
#def quandlfy_json(jsonObj):
#    '''formats dataframe into quandl format'''
#    None

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
