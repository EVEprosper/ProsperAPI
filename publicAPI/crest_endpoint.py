"""crest_endpoint.py: collection of public crest endpoints for Prosper"""

import sys
from os import path
from datetime import datetime
from enum import Enum

import ujson as json
from flask import Flask, Response, jsonify
from flask_restful import reqparse, Api, Resource, request

import publicAPI.forecast_utils as forecast_utils
import publicAPI.crest_utils as crest_utils
import publicAPI.api_utils as api_utils
import publicAPI.exceptions as exceptions
import publicAPI.config as api_config

import prosper.common.prosper_logging as p_logging
import prosper.common.prosper_config as p_config

HERE = path.abspath(path.dirname(__file__))
CONFIG_FILEPATH = path.join(HERE, 'publicAPI.cfg')

CONFIG = p_config.ProsperConfig(CONFIG_FILEPATH)
LOGGER = p_logging.DEFAULT_LOGGER
DEBUG = False

TEST = forecast_utils.LOGGER
## Flask Handles ##
#APP = Flask(__name__)
API = Api()

class AcceptedDataFormat(Enum):
    """enum for handling format support"""
    CSV = 0
    JSON = 1

def return_supported_types():
    """parse AccpetedDataFormat.__dict__ for accepted types"""
    supported_types = []
    for key in AcceptedDataFormat.__dict__.keys():
        if '_' not in key:
            supported_types.append(key.lower())

    return supported_types

def collect_stats(
        endpoint_name,
        args_payload,
        additional_data=None,
        db_name='CREST_stats.json',
        logger=LOGGER
):
    """save request information for later processing

    Args:
        endpoint_name (str): name of endpoint collecting data
        args_payload (:obj:`dict`): args provided
        additional_data (:obj:`dict`, optional): additional info to save
        db_name (str, optional): tinyDB filename
        logger (:obj:`logging.logger`, optional): logging handle for progress

    Returns:
        None

    """
    pass

## Flask Endpoints ##
@API.representation('text/csv')
def output_csv(data, status, headers=None):
    """helper for sending out CSV instead of JSON"""
    resp = API.make_response(data)
    resp.headers['Content-Type'] = 'text/csv'
    return resp

class OHLC_endpoint(Resource):
    """Handle calls on OHLC endpoint"""
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument(
            'regionID',
            type=int,
            required=True,
            help='regionid for market history API',
            location=['args', 'headers']
        )
        self.reqparse.add_argument(
            'typeID',
            type=int,
            required=True,
            help='typeid for market history API',
            location=['args', 'headers']
        )
        self.reqparse.add_argument(
            'User-Agent',
            type=str,
            required=True,
            help='User-Agent required',
            location=['headers']
        )
        self.reqparse.add_argument(
            'api',
            type=str,
            required=False,
            help='API key for tracking requests',
            location=['args', 'headers']
        )

    def get(self, return_type):
        """GET data from CREST and send out OHLC info"""
        args = self.reqparse.parse_args()
        #TODO: info archive
        LOGGER.info(
            'OHLC?regionID={0}&typeID={1}'.format(
                args.get('regionID'), args.get('typeID')
        ))
        LOGGER.debug(args)

        ## Validate inputs ##
        #TODO: error piping
        try:
            crest_utils.validate_id(
                'map_regions',
                args.get('regionID'),
                config=api_config.CONFIG,
                logger=LOGGER
            )
            crest_utils.validate_id(
                'inventory_types',
                args.get('typeID'),
                config=api_config.CONFIG,
                logger=LOGGER
            )
        except Exception as err:
            if isinstance(err, exceptions.ValidatorException):
                LOGGER.warning(
                    'ERROR: unable to validate type/region ids',
                    exc_info=True
                )
                return err.message, err.status
            else:
                LOGGER.error(
                    'ERROR: unable to validate type/region ids' +
                    'args={0}'.format(args),
                    exc_info=True
                )
                return 'UNHANDLED EXCEPTION', 500

        ## Fetch CREST ##
        #TODO: error piping
        try:
            data = crest_utils.fetch_market_history(
                args.get('regionID'),
                args.get('typeID'),
                config=api_config.CONFIG,
                logger=LOGGER
            )
            data = crest_utils.data_to_ohlc(data)
        except Exception as err:    #pragma: no cover
            if isinstance(err, exceptions.ValidatorException):
                LOGGER.warning(
                    'ERROR: unable to parse CREST data',
                    exc_info=True
                )
                return err.message, err.status
            else:
                LOGGER.error(
                    'ERROR: unhandled issue in parsing CREST data' +
                    'args={0}'.format(args),
                    exc_info=True
                )
                return 'UNHANDLED EXCEPTION', 500

        ## Format output ##
        message = crest_utils.OHLC_to_format(
            data,
            return_type
        )

        return message

DEFAULT_RANGE = CONFIG.get('CREST', 'prophet_range')
MAX_RANGE = CONFIG.get('CREST', 'prophet_max')
class ProphetEndpoint(Resource):
    """Handle calls on Prophet endpoint"""
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument(
            'regionID',
            type=int,
            required=True,
            help='regionid for market history API',
            location=['args', 'headers']
        )
        self.reqparse.add_argument(
            'typeID',
            type=int,
            required=True,
            help='typeid for market history API',
            location=['args', 'headers']
        )
        self.reqparse.add_argument(
            'User-Agent',
            type=str,
            required=True,
            help='User-Agent required',
            location=['headers']
        )
        self.reqparse.add_argument(
            'api',
            type=str,
            required=True,
            help='API key for tracking requests',
            location=['args', 'headers']
        )
        self.reqparse.add_argument(
            'range',
            type=int,
            required=False,
            help='Range for forecasting: default=' + DEFAULT_RANGE + ' max=' + MAX_RANGE,
            location=['args', 'headers']
        )

    def get(self, return_type):
        args = self.reqparse.parse_args()
        LOGGER.info(
            'prophet?regionID={0}&typeID={1}&range={2}'.format(
                args.get('regionID'), args.get('typeID'), args.get('range')
        ))
        LOGGER.debug(args)

        ## Validate inputs ##
        try:
            api_utils.check_key(
                args.get('api'),
                throw_on_fail=True,
                logger=LOGGER
            )
            crest_utils.validate_id(
                'map_regions',
                args.get('regionID'),
                config=api_config.CONFIG,
                logger=LOGGER
            )
            crest_utils.validate_id(
                'inventory_types',
                args.get('typeID'),
                config=api_config.CONFIG,
                logger=LOGGER
            )
            forecast_range = forecast_utils.check_requested_range(
                args.get('range'),
                max_range=MAX_RANGE,
                raise_for_status=True
            )
        except Exception as err:
            if isinstance(err, exceptions.ValidatorException):
                LOGGER.warning(
                    'ERROR: unable to validate type/region ids',
                    exc_info=True
                )
                return err.message, err.status
            else:
                LOGGER.error(
                    'ERROR: unable to validate type/region ids' +
                    'args={0}'.format(args),
                    exc_info=True
                )
                return 'UNHANDLED EXCEPTION', 500

        ## check cache ##
        cache_data = forecast_utils.check_prediction_cache(
            args.get('regionID'),
            args.get('typeID')
        )
        if cache_data:
            LOGGER.info('returning cached forecast')
            message = forecast_utils.data_to_format(
                cache_data,
                forecast_range,
                return_type
            )
            return message

        ## No cache, get data ##
        try:
            data = forecast_utils.fetch_extended_history(
                args.get('regionID'),
                args.get('typeID'),
                data_range=MAX_RANGE,
                config=api_config.CONFIG,
                logger=LOGGER
            )
            data = forecast_utils.build_forecast(
                data,
                MAX_RANGE
            )
        except Exception as err_msg:
            if isinstance(err, exceptions.ValidatorException):
                LOGGER.warning(
                    'ERROR: unable to generate forecast',
                    exc_info=True
                )
                return err.message, err.status
            else:
                LOGGER.error(
                    'ERROR: unable to generate forecast' +
                    'args={0}'.format(args),
                    exc_info=True
                )
                return 'UNHANDLED EXCEPTION', 500

        ## Update cache ##
        forecast_utils.write_prediction_cache(
            args.get('regionID'),
            args.get('typeID'),
            data,
            logger=LOGGER
        )
        ## Format output ##
        message = forecast_utils.data_to_format(
            data,
            return_type,
            forecast_range
        )

        return message


## Flask Endpoints ##
API.add_resource(
    OHLC_endpoint,
    CONFIG.get('ENDPOINTS', 'OHLC') + '.<return_type>'
)

API.add_resource(
    ProphetEndpoint,
    CONFIG.get('ENDPOINTS', 'prophet') + '.<return_type>'
)
