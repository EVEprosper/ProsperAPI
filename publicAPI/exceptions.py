"""exceptions.py: collection of exceptions for publicAPI"""
class ValidatorException(Exception):
    """base class for various validators"""
    def __init__(self):
        self.status = 0
        self.message = ''
        Exception.__init__(self)

class ForecastException(Exception):
    """base class for Forecast exceptions"""
    pass
class NoDataFoundInDB(ForecastException):
    """exception for empty db string found"""
    pass
class NotEnoughDataInDB(ForecastException):
    """exception for `raise_on_short` behavior"""
    pass
class UnsupportedFormat(ForecastException):
    """exception for data_to_format failure"""
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
