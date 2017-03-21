"""exceptions.py: collection of exceptions for publicAPI"""
class ValidatorException(Exception):
    """base class for various validators"""
    def __init__(self, status=0, message=''):
        self.status = status
        self.message = message
        Exception.__init__(self)
class UnsupportedFormat(ValidatorException):
    """exception for data_to_format failure"""
    pass
class IDValidationError(ValidatorException):
    """exception when you can't resolve CREST id query"""
    pass
class CRESTBadMarketData(ValidatorException):
    """exception when you can't pull `market_history` endpoint"""
    pass
class CRESTParseError(ValidatorException):
    """exception when you can't parse CREST data correctly"""
    pass

## crest_utils ##
class CrestException(Exception):
    """base class for CREST exceptions"""
    pass
class CacheSetupFailure(CrestException):
    """unable to set up cache file"""
    pass
class UnsupportedCrestEndpoint(CrestException):
    """don't know how to parse requested endpoint"""
    pass
class CrestAddressError(CrestException):
    """unable to format request url"""
    pass

## forecast_utils ##
class ForecastException(Exception):
    """base class for Forecast exceptions"""
    pass
class NoDataFoundInDB(ForecastException):
    """exception for empty db string found"""
    pass
class NotEnoughDataInDB(ForecastException):
    """exception for `raise_on_short` behavior"""
    pass
class EMDDataException(ForecastException):
    """collection of exceptions around EMD data"""
    pass
class UnableToFetchData(EMDDataException):
    """http error getting EMD data"""
    pass
class NoDataReturned(EMDDataException):
    """missing data in EMD data"""
    pass
