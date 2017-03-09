"""crest_endpoint.py: collection of public crest endpoints for Prosper"""

from os import path
from datetime import datetime

import ujson as json
import requests
from flask import Flask, Response, jsonify
from flask_restful import reqparse, Api, Resource, request
import pandas
from pandas.io.json import json_normalize

requests.models.json = json

import crest_utils
import prosper.common.prosper_logging as p_logging
import prosper.common.prosper_config as p_config


HERE = path.abspath(path.dirname(__file__))
CONFIG_FILEPATH = path.join(HERE, 'prosperAPI.cfg')

CONFIG = p_config.ProsperConfig(CONFIG_FILEPATH)
LOGGER = p_logging.DEFAULT_LOGGER


