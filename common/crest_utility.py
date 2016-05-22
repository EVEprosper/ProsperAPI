'''crest_utility.py: worker functions for CREST calls'''

import datetime
import os
import json
import requests
import prosperAPI_utility

config = prosperAPI_utility.get_config('common')
crestLogger = prosperAPI_utility.create_logger('crest_utility')

#### GLOBALS ####
CACHE_ABSPATH = os.path.join('..', config.get('CREST', 'cache_path'))
print(CACHE_ABSPATH)
if not os.path.exists(CACHE_ABSPATH):
    os.mkdir(CACHE_ABSPATH)
SDE_CACHE_LIMIT = int(config.get('CREST', 'sde_cache_limit'))
CREST_URL   = config.get('CREST', 'source_url')
USERAGENT   = config.get('GLOBAL', 'useragent')
RETRY_LIMIT = int(config.get('GLOBAL', 'default_retries'))

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
            errorStr = 'Unable to load name/ID from CREST object ' + \
                str(endpointType) + ' ' + str(err)
            crestLogger.error(errorStr)
            crestLogger.debug(crestJSON)
            return self.bool_SuccessStatus

        self.crestResponse = crestJSON
        self.endpointType  = endpointType
        self.bool_SuccessStatus = True
        infoStr = 'Success: parsed ' + str(self.objectID) + ':' + \
            str(self.objectName) + ' ' +\
            'from ' + str(endpointType)
        crestLogger.info(infoStr)
        return self.bool_SuccessStatus

    def write_cache_response(self, crestJSON, endpointType):
        '''update on-file cache'''
        cachePath = CACHE_ABSPATH + '/' + endpointType
        if not os.path.exists(cachePath):
            #TODO: repeated function
            os.mkdir(cachePath)
            crestLogger.info('Created cache path: ' + cachePath)
            return False

        cacheFilePath  = cachePath + '/' + str(self.objectID) + '.json'
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

    jsonObj = None
    cacheResponse = check_cache(typeID, 'types')
    if not cacheResponse:
        crestLogger.info('fetching crest ' + str(typeID))
        crestResponse = fetch_crest('types', typeID)    #test CREST endpoint
        jsonObj = crestResponse
    else:
        crestLogger.info('using local cache ' + str(typeID))
        jsonObj = cacheResponse

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

def test_regionid(regionID):
    '''Validates regionID is queryable'''
    crestObj = CRESTresults()

    try:    #test types
        regionID_INT = int(regionID)
    except ValueError as err:
        errorStr = 'bad regionID recieved: ' + str(err)
        crestLogger.error(errorStr)
        return None

    jsonObj = None
    cacheResponse = check_cache(regionID, 'regions')
    if not cacheResponse:
        crestResponse = fetch_crest('regions', regionID)  #test CREST endpoint
        jsonObj = crestResponse
    else:
        jsonObj = cacheResponse

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
def fetch_crest(endpointStr, value):
    '''Fetches CREST endpoints and returns JSON.  Has retry built in'''
    crestResponse = None
    crest_endpoint_URL = CREST_URL + endpointStr + '/' + str(value) + '/'
    GET_headers = {
        'User-Agent': USERAGENT
    }
    last_error = ""
    crestLogger.info('Fetching CREST: ' + crest_endpoint_URL)
    for tries in range (0, RETRY_LIMIT):
        try:
            crest_request = requests.get(
                crest_endpoint_URL,
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
        criticalMessage = ''' ERROR: retries exceeded in crest_fetch()
    URL=''' + crest_endpoint_URL + '''
    LAST_ERROR=''' + last_error
        helpMsg = '''CREST Outage?'''
        criticalStr = prosperAPI_utility.email_body_builder(
            criticalMessage,
            helpMsg
        )
        crestLogger.critical(criticalStr)
    crestLogger.info('Fetched CREST:' + crest_endpoint_URL)
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
    cacheFilePath = cachePath + '/' + str(objectID) + '.json'
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
