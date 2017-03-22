from os import path, makedirs, rmdir
from shutil import rmtree
from datetime import datetime, timedelta
import time
import pandas as pd
import numpy as np
import requests
from tinydb import TinyDB, Query

import pytest

import publicAPI.crest_endpoint as crest_endpoint
import publicAPI.exceptions as exceptions
import helpers

HERE = path.abspath(path.dirname(__file__))
ROOT = path.dirname(HERE)

CONFIG_FILENAME = path.join(HERE, 'test_config.cfg')
CONFIG = helpers.get_config(CONFIG_FILENAME)
ROOT_CONFIG = helpers.get_config(
    path.join(ROOT, 'publicAPI', 'publicAPI.cfg'))

TEST_CACHE_PATH = path.join(HERE, 'cache')
@pytest.mark.incremental
class TestStatsDB:
    """test framework for collecting endpoint stats"""
    def collect_stats_happypath(self):
        """exercise `collect_stats`"""
        pass
