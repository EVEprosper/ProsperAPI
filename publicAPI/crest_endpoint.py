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

CONFIG = api_config.CONFIG
LOGGER = p_logging.DEFAULT_LOGGER
DEBUG = False

TEST = forecast_utils.LOGGER
## Flask Handles ##
API = Api()
APP_HACK = Flask(__name__)  #flask-restful CSV writer sucks

class AcceptedDataFormat(Enum):
    """enum for handling format support"""
    CSV = 'csv'
    JSON = 'json'

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
    resp = APP_HACK.make_response(data)

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
        LOGGER.info('OHLC {0} Request: {1}'.format(return_type, args))

        if return_type not in return_supported_types():
            return 'INVALID RETURN FORMAT', 405

        mode = crest_utils.SwitchCCPSource(
            api_config.CONFIG.get('GLOBAL', 'crest_or_esi')
        )
        ## Validate inputs ##
        try:
            crest_utils.validate_id(
                'map_regions',
                args.get('regionID'),
                mode=mode,
                config=api_config.CONFIG,
                logger=LOGGER
            )
            crest_utils.validate_id(
                'inventory_types',
                args.get('typeID'),
                mode=mode,
                config=api_config.CONFIG,
                logger=LOGGER
            )
        except exceptions.ValidatorException as err:
            LOGGER.warning(
                'ERROR: unable to validate type/region ids' +
                '\n\targs={0}'.format(args),
                exc_info=True
            )
            return err.message, err.status
        except Exception: #pragma: no cover
            LOGGER.error(
                'ERROR: unable to validate type/region ids' +
                'args={0}'.format(args),
                exc_info=True
            )
            return 'UNHANDLED EXCEPTION', 500

        ## Fetch CREST ##
        try:
            data = crest_utils.fetch_market_history(
                args.get('regionID'),
                args.get('typeID'),
                config=api_config.CONFIG,
                mode=mode,
                logger=LOGGER
            )
            data = crest_utils.data_to_ohlc(data)
        except exceptions.ValidatorException as err:
            LOGGER.warning(
                'ERROR: unable to parse CREST data' +
                '\n\targs={0}'.format(args),
                exc_info=True
            )
            return err.message, err.status
        except Exception: #pragma: no cover
        #except Exception as err:    #pragma: no cover
            LOGGER.error(
                'ERROR: unhandled issue in parsing CREST data' +
                'args={0}'.format(args),
                exc_info=True
            )
            return 'UNHANDLED EXCEPTION', 500

        ## Format output ##
        if return_type == AcceptedDataFormat.JSON.value:
            LOGGER.info('rolling json response')
            data_str = data.to_json(
                path_or_buf=None,
                orient='records'
            )
            message = json.loads(data_str)
        elif return_type == AcceptedDataFormat.CSV.value:
            LOGGER.info('rolling csv response')
            data_str = data.to_csv(
                path_or_buf=None,
                header=True,
                index=False,
                columns=[
                    'date',
                    'open',
                    'high',
                    'low',
                    'close',
                    'volume'
                ]
            )
            message = output_csv(data_str, 200)
        else:   #pragma: no cover
            #TODO: CUT?
            LOGGER.error(
                'invalid format requested' +
                '\n\targs={0}'.format(args) +
                '\n\treturn_type={0}'.format(return_type),
                exc_info=True
            )
            return 'UNSUPPORTED FORMAT', 500

        return message

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
            help='Range for forecasting: default={0} max={1}'.\
                format(api_config.DEFAULT_RANGE, api_config.MAX_RANGE),
            location=['args', 'headers']
        )

    def get(self, return_type):
        args = self.reqparse.parse_args()
        LOGGER.info('Prophet {0} Request: {1}'.format(return_type, args))


        if return_type not in return_supported_types():
            return 'INVALID RETURN FORMAT', 405

        mode = crest_utils.SwitchCCPSource(
            api_config.CONFIG.get('GLOBAL', 'crest_or_esi')
        )
        forecast_range = api_config.DEFAULT_RANGE
        if 'range' in args:
            forecast_range = args.get('range')
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
                mode=mode,
                logger=LOGGER
            )
            crest_utils.validate_id(
                'inventory_types',
                args.get('typeID'),
                config=api_config.CONFIG,
                mode=mode,
                logger=LOGGER
            )
            forecast_range = forecast_utils.check_requested_range(
                forecast_range,
                max_range=api_config.MAX_RANGE,
                raise_for_status=True
            )
        except exceptions.ValidatorException as err:
            LOGGER.warning(
                'ERROR: unable to validate type/region ids' +
                '\n\targs={0}'.format(args),
                exc_info=True
            )
            return err.message, err.status
        except Exception: #pragma: no cover
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
        LOGGER.debug(cache_data)
        if cache_data is not None:
            LOGGER.info('returning cached forecast')
            message = forecast_reporter(
                cache_data,
                forecast_range,
                return_type,
                LOGGER
            )

            return message

        ## No cache, get data ##
        try:
            data = forecast_utils.fetch_extended_history(
                args.get('regionID'),
                args.get('typeID'),
                mode=mode,
                data_range=api_config.MAX_RANGE,
                config=api_config.CONFIG,
                logger=LOGGER
            )
            data = forecast_utils.build_forecast(
                data,
                api_config.MAX_RANGE
            )
        except exceptions.ValidatorException as err:
            LOGGER.warning(
                'ERROR: unable to generate forecast' +
                '\n\targs={0}'.format(args),
                exc_info=True
            )
            return err.message, err.status
        except Exception: #pragma: no cover
            LOGGER.error(
                'ERROR: unable to generate forecast' +
                '\n\targs={0}'.format(args),
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
        try:
            message = forecast_reporter(
                data,
                forecast_range,
                return_type,
                LOGGER
            )
        except Exception as err_msg:    #pragma: no cover
            LOGGER.error(
                'invalid format requested' +
                '\n\targs={0}'.format(args) +
                '\n\treturn_type={0}'.format(return_type),
                exc_info=True
            )
            return 'UNABLE TO GENERATE REPORT', 500
        return message

def forecast_reporter(
        data,
        forecast_range,
        return_type,
        logger=LOGGER
):
    """prepares forecast response for Flask

    Args:
        data (:obj:`pandas.DataFrame`): Prediction data to report
        forecast_range (int): range requested for return
        return_type (:enum:`AcceptedDataFormat`): format of return
        logger (:obj:`logging.logger`, optional): logging handle

    Returns:
        Flask-ready return object

    """
    report_data = forecast_utils.trim_prediction(
        data,
        forecast_range
    )
    print(report_data)
    if return_type == AcceptedDataFormat.JSON.value:
        logger.info('rolling json response')
        data_str = report_data.to_json(
            path_or_buf=None,
            orient='records'
        )
        message = json.loads(data_str)
    elif return_type == AcceptedDataFormat.CSV.value:
        logger.info('rolling csv response')
        data_str = report_data.to_csv(
            path_or_buf=None,
            header=True,
            index=False,
            columns=[
                'date',
                'avgPrice',
                'yhat',
                'yhat_low',
                'yhat_high',
                'prediction'
            ]
        )
        message = output_csv(data_str, 200)
    else:   #pragma: no cover
        raise exceptions.UnsupportedFormat(
            status=500,
            message='UNABLE TO GENERATE REPORT'
        )

    return message

## Flask Endpoints ##
API.add_resource(
    OHLC_endpoint,
    '/CREST/OHLC.<return_type>'
)

API.add_resource(
    ProphetEndpoint,
    '/CREST/prophet.<return_type>'
)
