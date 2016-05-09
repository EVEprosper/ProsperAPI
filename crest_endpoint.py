from flask import Flask, Response, jsonify, abort
from flask_restful import reqparse, Api, Resource, request
import datetime
import os
import json
import configparser
import requests

#### CONFIG PARSER ####
#DEV_CONFIGFILE = os.getcwd() + "/init.ini" #TODO: figure out multi-file configparser in py35
ALT_CONFIGFILE = os.getcwd() + '/init_local.ini'
config = configparser.ConfigParser()
config.read(ALT_CONFIGFILE)

BOOL_DEBUG_ENABLED = bool(config.get('GLOBAL', 'debug_enabled'))
CREST_FLASK_PORT   =  int(config.get('CREST', 'flask_port'))

app = Flask(__name__)
api = Api(app)

if __name__ == '__main__'
    if BOOL_DEBUG_ENABLED:
        app.run(debug=True)
    else:
        app.run(
            host='0.0.0.0',
            port=CREST_FLASK_PORT)
