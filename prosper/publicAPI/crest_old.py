'''crest_utility.py: worker functions for CREST calls'''

import datetime
#import os
from os import path, makedirs
import json

import requests

from prosper.common import prosper_utilities as utilities
import prosper.common.prosper_logging as p_logging
from prosper.common.prosper_logging import create_logger
from prosper.common.prosper_config import get_config

HERE = os.path.abspath(os.path.dirname(__file__))
CONFIG_FILEPATH = os.path.join(HERE, 'prosperAPI.cfg')
config = get_config(CONFIG_FILEPATH)

crestLogger = p_logging.DEFAULT_LOGGER

#### GLOBALS ####
CACHE_ABSPATH = os.path.join(HERE, config.get('CACHING', 'cache_path'))
print(CACHE_ABSPATH)
if not os.path.exists(CACHE_ABSPATH):
    os.makedirs(CACHE_ABSPATH)
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

def test_typeid(type_id):
    '''Validates typeID is queryable'''
    crestObj = CRESTresults()

    try:    #test types
        type_id = int(type_id)
    except ValueError as err:
        errorStr = 'bad type_id recieved: ' + str(err)
        crestLogger.error(errorStr)
        return None

    jsonObj = fetch_typeid(type_id)
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

def fetch_typeid(type_id, override_cache=False):
    '''fetches typeid conversion from CREST or cache'''
    endpoint_url = CREST_URL + config.get('RESOURCES', 'inventory_types')
    endpoint_url = endpoint_url.format(
        type_id=type_id
    )
    jsonObj = None
    cacheResponse = check_cache(type_id, 'types')
    if (not cacheResponse) or override_cache:
        crestLogger.info('fetching crest ' + str(type_id))
        crestResponse = fetch_crest(endpoint_url)    #test CREST endpoint
        jsonObj = crestResponse
    else:
        crestLogger.info('using local cache ' + str(type_id))
        jsonObj = cacheResponse

    return jsonObj

def test_regionid(region_id):
    '''Validates regionID is queryable'''
    crestObj = CRESTresults()

    try:    #test types
        region_id = int(region_id)
    except ValueError as err:
        errorStr = 'bad regionID recieved: ' + str(err)
        crestLogger.error(errorStr)
        return None

    jsonObj = fetch_regionid(region_id)
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

def fetch_regionid(region_id, override_cache=False):
    '''fetches regionid conversion from CREST or cache'''
    endpoint_url = CREST_URL + config.get('RESOURCES', 'map_regions')
    endpoint_url = endpoint_url.format(
        region_id=region_id
    )
    json_obj = {}
    cache_response = check_cache(region_id, 'regions')
    if (not cache_response) or override_cache:
        cache_response = fetch_crest(endpoint_url)  #test CREST endpoint
        json_obj = cache_response
    else:
        json_obj = cache_response

    return jsonObj

def fetch_market_history(type_id, region_id, override_cache=False):
    '''fetches market history from CREST or cache'''
    endpoint_url = CREST_URL + config.get('RESOURCES', 'market_history')
    endpoint_url = endpoint_url.format(
        type_id=type_id,
        region_id=region_id
    )
    json_obj = {}
    #TODO: cached market_history utility?
    json_obj = fetch_crest(endpoint_url)
    return json_obj

#def fetch_crest(endpointStr, value):
def fetch_crest(crest_url):
    '''Fetches CREST endpoints and returns JSON.  Has retry built in'''
    crest_response = {}
    #crest_endpoint_URL = CREST_URL + endpointStr + '/' + str(value) + '/'
    crestLogger.debug(crest_url)
    GET_headers = {
        'User-Agent': USERAGENT
    }
    last_exception = None
    crestLogger.info('Fetching CREST: ' + crest_url)
    for tries in range (0, RETRY_LIMIT):
        try:
            crest_request = requests.get(
                crest_url,
                headers=GET_headers
            )
            crest_request.raise_for_status()
            crest_response = crest_request.json()
        except Exception as err_msg:
            last_exception = err_msg
            continue
    else:
        crestLogger.critical(
            'CRITICAL: retries exceeded' +
            '\n\turl={0}'.format(crest_url) +
            '\n\tlast_error={0}'.format(repr(last_exception))
        )

    crestLogger.info('Fetched CREST:' + crest_url)
    crestLogger.debug(crest_response)
    return crest_response

def check_cache(object_id, endpoint_name):
    '''Try to read CREST/SDE items off disk'''
    cache_path = path.join(CACHE_ABSPATH, endpoint_name)
    if not path.exists(cache_path):
        crestLogger.info('Creating cache path: ' + cache_path)
    makedirs(cache_path, exist_ok=True)

    json_obj = {}
    cache_filepath = path.join(cache_path, str(object_id) + '.json')
    if path.isfile(cache_filepath):
        try:
            with open(cache_filepath, 'r') as file_handle:
                json_obj = json.load(file_handle)
        except Exception:
            crestLogger.error(
                'unable to read json: ' + cache_filepath,
                exc_info=True
            )
            return None #need to read again from CREST
        return json_obj
    else:
        return None
