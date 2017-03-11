"""crest_endpoint.py: collection of public crest endpoints for Prosper"""

from os import path
from datetime import datetime
from enum import Enum

import ujson as json
from flask import Flask, Response, jsonify
from flask_restful import reqparse, Api, Resource, request
from flask_mysqldb import MySQL
from plumbum import cli

import crest_utils
import forecast_utils
import prosper.common.prosper_logging as p_logging
import prosper.common.prosper_config as p_config


HERE = path.abspath(path.dirname(__file__))
CONFIG_FILEPATH = path.join(HERE, 'prosperAPI.cfg')

CONFIG = p_config.ProsperConfig(CONFIG_FILEPATH)
LOGGER = p_logging.DEFAULT_LOGGER
DEBUG = False

## Flask Handles ##
APP = Flask(__name__)
API = Api(APP)
MYSQL = None

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

def raise_for_status(
        status_value
):
    """raise exception for non-good status"""
    pass

## Flask Endpoints ##
@api.representation('text/csv')
def output_csv(data, status, headers=None):
    """helper for sending out CSV instead of JSON"""
    resp = APP.make_response(data)
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
        LOGGER.info(
            'OHLC?regionID={0}&typeID={1}'.format(
                args.get('regionID'), args.get('typeID')
        ))
        LOGGER.debug(args)

        ## Validate inputs ##
        #TODO: error piping
        status = crest_utils.validate_id(
            'regions',
            args.get('regionID')
        )
        status = crest_utils.validate_id(
            'types',
            args.get('typeID')
        )
        #TODO: validate range
        #TODO: validate API key

        ## Fetch CREST ##
        #TODO: error piping
        data = crest_utils.fetch_market_history(
            args.get('regionID'),
            args.get('typeID')
        )

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

    def get(self):
        args = self.reqparse.parse_args()
        LOGGER.info(
            'OHLC?regionID={0}&typeID={1}'.format(
                args.get('regionID'), args.get('typeID')
        ))
        LOGGER.debug(args)

        ## Validate inputs ##
        #TODO: error piping
        status = crest_utils.validate_id(
            'regions',
            args.get('regionID')
        )
        status = crest_utils.validate_id(
            'types',
            args.get('typeID')
        )

        #TODO: validate range
        forecast_range = DEFAULT_RANGE
        ## Fetch CREST ##
        #TODO: error piping
        try:
            curr = MYSQL.connection.cursor()
            data = forecast_utils.fetch_extended_history(
                args.get('regionID'),
                args.get('typeID'),
                curr
            )
        except Exception as err:
            LOGGER.warning(
                'Unable to fetch data from archive',
                exc_info=True
            )
            data = crest_utils.fetch_market_history(
                args.get('regionID'),
                args.get('typeID')
            )
        data = forecast_utils.build_forecast(
            data,
            forecast_range
        )
        ## Format output ##
        message = forecast_utils.data_to_format(
            data,
            return_type
        )

        return message
## Flask Endpoints ##
APP.add_resource(
    OHLC_endpoint,
    CONFIG.get('ENDPOINTS', 'OHLC') + '.<return_type>'
)
APP.add_resource(
    ProphetEndpoint,
    CONFIG.get('ENDPOINTS', 'prophet')
)
class PublicAPIRunner(cli.Application):
    """CLI wrapper for starting up/debugging Flask application"""
    _log_builder = p_logging.ProsperLogger(
        'ProsperAPI',
        CONFIG.get('LOGGING', 'log_path'),   #TODO, remove log_path?
        CONFIG
    )

    @cli.switch(
        ['v', '--verbose'],
        help='enable verbose logging'
    )
    def enable_verbose(self):
        """verbose logging: log to stdout"""
        self._log_builder.configure_debug_logger()

    debug = cli.Flag(
        ['d', '--debug'],
        help='run in headless/debug mode, do not connect to internet'
    )

    port = int(CONFIG.get('CREST', 'port'))

    def main(self):
        """__main__ section for launching Flask app"""
        global LOGGER, DEBUG, MYSQL
        DEBUG = self.debug
        if not DEBUG:
            self._log_builder.configure_discord_logger()

        LOGGER = self._log_builder.get_logger()
        #TODO: push logger out to helper lib

        APP.config['MYSQL_USER']     = CONFIG.get('DB', 'user')
        APP.config['MYSQL_PASSWORD'] = CONFIG.get('DB', 'passwd')
        APP.config['MYSQL_DB']       = CONFIG.get('DB', 'schema')
        APP.config['MYSQL_PORT']     = CONFIG.get('DB', 'port')
        APP.config['MYSQL_HOST']     = CONFIG.get('DB', 'host')

        MYSQL = MySQL(APP)

        try:
            if DEBUG:
                APP.run(
                    debug=True,
                    port=self.port
                )
            else:
                APP.run(
                    host='0.0.0.0',
                    port=self.port
                )
        except Exception as err:
            LOGGER.critical(
                __name__ + ' exiting unexpectedly',
                exc_info=True
            )

class CrestEndpointException(Exception):
    """baseclass for crest_endpoint exceptions"""
    pass
class BadStatus(CrestEndpointException):
    """unexpected status raised"""
    pass

if __name__ == '__main__':
    PublicAPIRunner.run()
