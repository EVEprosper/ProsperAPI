"""crest_endpoint.py: collection of public crest endpoints for Prosper"""

from os import path
from datetime import datetime

import ujson as json
#import requests
from flask import Flask, Response, jsonify
from flask_restful import reqparse, Api, Resource, request
#import pandas
#from pandas.io.json import json_normalize
from plumbum import cli

#requests.models.json = json

import crest_utils
import prosper.common.prosper_logging as p_logging
import prosper.common.prosper_config as p_config


HERE = path.abspath(path.dirname(__file__))
CONFIG_FILEPATH = path.join(HERE, 'prosperAPI.cfg')

CONFIG = p_config.ProsperConfig(CONFIG_FILEPATH)
LOGGER = p_logging.DEFAULT_LOGGER
DEBUG = False

## Flask Handles ##
APP = Flask(__name__)
API = Api(app)

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

## Flask Endpoints ##
APP.add_resource(
    OHLC_endpoint,
    CONFIG.get('ENDPOINTS', 'OHLC') + '.<return_type>'
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
        global LOGGER, DEBUG
        DEBUG = self.debug
        if not DEBUG:
            self._log_builder.configure_discord_logger()

        LOGGER = self._log_builder.get_logger()
        #TODO: push logger out to helper lib

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

if __name__ == '__main__':
    PublicAPIRunner.run()
