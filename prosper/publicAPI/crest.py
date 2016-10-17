'''crest_utility.py: worker functions for CREST calls'''

import datetime
import os
import json
import logging

import requests

from prosper.common import prosper_utilities as utilities
from prosper.common.prosper_logging import create_logger
from prosper.common.prosper_config import get_config
HERE = os.path.abspath(os.path.dirname(__file__))
CONFIG_FILEPATH = os.path.join(HERE, 'crest.cfg')
config = get_config(CONFIG_FILEPATH)
#LOG_PATH = config.get('GLOBAL', 'log_path')
#if not LOG_PATH: #blank line
#    LOG_PATH = os.path.join(HERE, 'logs')
#    if not os.path.exists(LOG_PATH):
#        os.makedirs(LOG_PATH)
DEFAULT_LOGGER = logging.getLogger('NULL')
DEFAULT_LOGGER.addHandler(logging.NullHandler())
crestLogger = DEFAULT_LOGGER

#crestLogger = create_logger(
#    'crest_utility',
#    LOG_PATH,
#    None,
#    config.get('GLOBAL', 'log_level')
#)

#### GLOBALS ####
CACHE_ABSPATH = os.path.join(HERE, config.get('CACHING', 'cache_path'))
print(CACHE_ABSPATH)
if not os.path.exists(CACHE_ABSPATH):
    os.mkdir(CACHE_ABSPATH)
SDE_CACHE_LIMIT = int(config.get('CACHING', 'sde_cache_limit'))
CREST_URL   = config.get('ROOTPATH', 'public_crest')
USERAGENT   = config.get('GLOBAL', 'useragent')
RETRY_LIMIT = int(config.get('GLOBAL', 'default_retries'))

def override_logger(logObject):
    '''switch logger to a different script's logger'''
    global crestLogger
    crestLogger = logObject

class CRESTresults(object):
    '''Parser/storage for CREST/SDE lookups'''
    def __init__ (self):
        self.objectID      = -1
        self.objectName    = ''
        self.crestResponse = None
        self.endpointType  = ''
        self.bool_SuccessStatus = False

    def __bool__ (self):
        '''test if object is loaded with valid data'''
        return self.bool_SuccessStatus

    def parse_crest_response(self, crestJSON, endpointType):
        '''splits out crest response for name/ID/info conversion'''
        self.bool_SuccessStatus = False
        try:
            self.objectID   = crestJSON['id']
            self.objectName = crestJSON['name']
        except KeyError as err:
            error_str = 'Unable to laod name/ID from CREST object {endpointType} {err}'
            error_str = error_str.format(
                endpoint_type=endpointType,
                err=err
            )
            crestLogger.error(error_str)
            crestLogger.debug(crestJSON)
            return self.bool_SuccessStatus

        self.crestResponse = crestJSON
        self.endpointType  = endpointType
        self.bool_SuccessStatus = True
        info_str = 'Success: parsed {objectID}:{objectName} from: {endpointType}'
        info_str = info_str.format(
            objectID=self.objectID,
            objectName=self.objectName,
            endpointType=endpointType
        )
        crestLogger.info(info_str)
        return self.bool_SuccessStatus

    def write_cache_response(self, crestJSON, endpointType):
        '''update on-file cache'''
        cachePath = os.path.join(CACHE_ABSPATH, endpointType)
        if not os.path.exists(cachePath):
            #TODO: repeated function
            os.mkdir(cachePath)
            crestLogger.info('Created cache path: ' + cachePath)
            return False

        cacheFilePath  = os.path.join(cachePath, str(self.objectID) + '.json')
        bool_writeFile = False
        if os.path.isfile(cacheFilePath):
            #cache exists on file
            fileAccessStats  = os.stat(cacheFilePath)
            modifiedDatetime = datetime.datetime.fromtimestamp(
                fileAccessStats.st_mtime
            )
            nowDatetime = datetime.datetime.now()
            fileAge = (modifiedDatetime - nowDatetime).total_seconds()
            crestLogger.debug(cacheFilePath + '.fileAge=' + str(fileAge))
            if fileAge > SDE_CACHE_LIMIT:
                bool_writeFile = True
        else:
            bool_writeFile = True

        if bool_writeFile:
            crestLogger.info('updating cache file: ' + cacheFilePath)
            try:
                with open(cacheFilePath, 'w') as file_handle:
                    file_handle.write(json.dumps(crestJSON))
            except Exception as err:
                errorStr = 'Unable to write cache to file ' + str(err)
                crestLogger.error(errorStr)
                crestLogger.debug(crestJSON)

def test_typeid(typeID):
    '''Validates typeID is queryable'''
    crestObj = CRESTresults()

    try:    #test types
        typeID_INT = int(typeID)
    except ValueError as err:
        errorStr = 'bad typeID recieved: ' + str(err)
        crestLogger.error(errorStr)
        return None

    jsonObj = fetch_typeid(typeID)
    validCrest = crestObj.parse_crest_response(jsonObj, 'types')
    crestObj.write_cache_response(jsonObj, 'types')
    if validCrest:
        #success
        crestLogger.info('CREST/types pulled correctly')
        return crestObj
    else:
        errorStr = 'invalid crestObj'
        crestLogger.error(errorStr)
        return None

def fetch_typeid(typeID, override_cache=False):
    '''fetches typeid conversion from CREST or cache'''
    endpoint_url = CREST_URL + config.get('RESOURCES', 'inventory_types')
    endpoint_url = endpoint_url.format(
        typeID=typeID
    )
    jsonObj = None
    cacheResponse = check_cache(typeID, 'types')
    if (not cacheResponse) or override_cache:
        crestLogger.info('fetching crest ' + str(typeID))
        crestResponse = fetch_crest(endpoint_url)    #test CREST endpoint
        jsonObj = crestResponse
    else:
        crestLogger.info('using local cache ' + str(typeID))
        jsonObj = cacheResponse

    return jsonObj

def test_regionid(regionID):
    '''Validates regionID is queryable'''
    crestObj = CRESTresults()

    try:    #test types
        regionID_INT = int(regionID)
    except ValueError as err:
        errorStr = 'bad regionID recieved: ' + str(err)
        crestLogger.error(errorStr)
        return None

    jsonObj = fetch_regionid(regionID)
    validCrest = crestObj.parse_crest_response(jsonObj, 'regions')
    crestObj.write_cache_response(jsonObj, 'regions')
    if validCrest:
        #success
        crestLogger.info('CREST/regions pulled correctly')
        return crestObj
    else:
        errorStr = 'invalid crestObj'
        crestLogger.error(errorStr)
        return None

def fetch_regionid(regionID, override_cache=False):
    '''fetches regionid conversion from CREST or cache'''
    endpoint_url = CREST_URL + config.get('RESOURCES', 'map_regions')
    endpoint_url = endpoint_url.format(
        regionID=regionID
    )
    jsonObj = None
    cacheResponse = check_cache(regionID, 'regions')
    if (not cacheResponse) or override_cache:
        crestResponse = fetch_crest(endpoint_url)  #test CREST endpoint
        jsonObj = crestResponse
    else:
        jsonObj = cacheResponse

    return jsonObj

def fetch_market_history(typeID, regionID, override_cache=False):
    '''fetches market history from CREST or cache'''
    endpoint_url = CREST_URL + config.get('RESOURCES', 'market_history')
    endpoint_url = endpoint_url.format(
        typeID=typeID,
        regionID=regionID
    )
    jsonObj = None
    #TODO: cached market_history utility?
    jsonObj = fetch_crest(endpoint_url)
    return jsonObj

#def fetch_crest(endpointStr, value):
def fetch_crest(crestURL):
    '''Fetches CREST endpoints and returns JSON.  Has retry built in'''
    crestResponse = None
    #crest_endpoint_URL = CREST_URL + endpointStr + '/' + str(value) + '/'
    print(crestURL)
    GET_headers = {
        'User-Agent': USERAGENT
    }
    last_error = ""
    crestLogger.info('Fetching CREST: ' + crestURL)
    for tries in range (0, RETRY_LIMIT):
        try:
            crest_request = requests.get(
                crestURL,
                headers=GET_headers
            )
        except requests.exceptions.ConnectTimeout as err:
            last_error = 'RETRY=' + str(tries) + ' ' + \
                'ConnectTimeout: ' + str(err)
            crestLogger.error(last_error)
            continue
        except requests.exceptions.ConnectionError as err:
            last_error = 'RETRY=' + str(tries) + ' ' + \
                'ConnectionError: ' + str(err)
            crestLogger.error(last_error)
            continue
        except requests.exceptions.ReadTimeout as err:
            last_error = 'RETRY=' + str(tries) + ' ' + \
                'ReadTimeout: ' + str(err)
            crestLogger.error(last_error)
            continue

        if crest_request.status_code == requests.codes.ok:
            try:
                crestResponse = crest_request.json()
            except ValueError as err:
                last_error = 'RETRY=' + str(tries) + ' ' + \
                    'request not JSON: ' + str(err)
                crestLogger.error(last_error)
                continue #try again
            break   #if all OK, break out of error checking
        else:
            last_error = 'RETRY=' + str(tries) + ' ' + \
                'bad status code: ' + str(crest_request.status_code)
            crestLogger.error(last_error)
            continue #try again
    else:
        critical_message = ''' ERROR: retries exceeded in crest_fetch()
    URL=''' + crestURL + '''
    LAST_ERROR=''' + last_error
        helpMsg = '''CREST Outage?'''
        critical_string = utilities.email_body_builder(
            critical_message,
            helpMsg
        )
        crestLogger.critical(critical_string)
    crestLogger.info('Fetched CREST:' + crestURL)
    crestLogger.debug(crestResponse)
    return crestResponse

def check_cache(objectID, endpointName):
    '''Try to read CREST/SDE items off disk'''
    cachePath = os.path.join(CACHE_ABSPATH, endpointName)
    if not os.path.exists(cachePath):
        #TODO: repeated function
        os.mkdir(cachePath)
        crestLogger.info('Created cache path: ' + cachePath)
        return None

    jsonObj = None
    cacheFilePath = os.path.join(cachePath, str(objectID) + '.json')
    if os.path.isfile(cacheFilePath):
        try:
            with open(cacheFilePath, 'r') as file_handle:
                jsonObj = json.load(file_handle)
        except Exception as err:
            errorStr = 'unable to read json: ' + cacheFilePath + \
                ' ' + str(err)
            crestLogger.error(errorStr)
            #TODO: delete cached file?
            return None #need to read again from CREST
        return jsonObj
    else:
        return None
