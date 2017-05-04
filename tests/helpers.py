"""helpers.py: a collection of helpful utilities for tests"""
from os import path, listdir, remove
import configparser
from datetime import datetime, timedelta
import json

from tinymongo import TinyMongoClient
import pymysql.cursors

import prosper.common.prosper_config as p_config

HERE = path.abspath(path.dirname(__file__))
ROOT = path.dirname(HERE)
PROD_CACHE_PATH = path.join(ROOT, 'publicAPI', 'cache')
TEST_CACHE_PATH = path.join(HERE, 'cache')
CONN = None
SPECIAL_CACHE_FILES = [
    'prosperAPI.json',
    'splitcache.json',
    'travis_splitcache.json'
]
SPECIAL_CACHE_COLLECTIONS = [
    'users'
]
def clear_caches(bool_prod=False):
    """remove cache files for testing"""
    cache_path = TEST_CACHE_PATH
    if bool_prod:
        cache_path = PROD_CACHE_PATH

    for file in listdir(cache_path):
        if file in SPECIAL_CACHE_FILES:
            continue

        remove(path.join(cache_path, file))

def clear_tinymongo_cache(bool_prod=False):
    """tinymongo uses all collections in one file, clearing requires direct access"""
    if not bool_prod:
        remove(path.join(TEST_CACHE_PATH, 'prosperAPI.json'))
        return

    with open(path.join(PROD_CACHE_PATH, 'prosperAPI.json'), 'r') as tdb_fh:
        raw_json = json.load(tdb_fh)

    collections = raw_json.keys()
    tdb = TinyMongoClient(PROD_CACHE_PATH)
    for collection in collections:
        if collection in SPECIAL_CACHE_COLLECTIONS:
            #skip special tables
            continue

        tdb.prosperAPI[collection].delete_many({})  #nuke it from orbit

    tdb.close()

def get_config(config_filename):
    """parse test config file

    Args:
        config_filename (str): path to config file

    Returns:
        (:obj:`configparser.ConfigParser`)

    """
    config = p_config.ProsperConfig(config_filename)

    return config

def check_db_values(
        region_id,
        type_id,
        data_range,
        config
):
    """check prosperdb for validation

    Args:
        region_id (int): EVE Online region identifier
        type_id (int): EVE Online type/item identifier
        date_range (int): number of days to fetch
        config (:obj:`configparser.ConfigParser`): db info

    Returns:
        (:obj:`list`) data from db (or None if no creds)

    """
    try:
        con = pymysql.connect(
            host=config.get_option('DB', 'host'),
            user=config.get_option('DB', 'user'),
            port=int(config.get_option('DB', 'port')),
            password=config.get_option('DB', 'password'),
            db=config.get_option('DB', 'schema')
        )
    except Exception:
        raise

    query_date = datetime.today() - timedelta(days=int(data_range))

    query = \
    """SELECT *
    FROM {history_table}
    WHERE itemid = {type_id}
    AND regionid = {region_id}
    AND price_date > '{query_date}'
    ORDER BY price_date ASC""".format(
        history_table=config.get('DB', 'history_table'),
        type_id=type_id,
        region_id=region_id,
        query_date=query_date.strftime('%Y-%m-%d')

    )

    data = None
    try:
        with con.cursor() as cur:
            cur.execute(query)
            data = cur.fetchall()
    finally:
        con.close()

    return data

def compare_dates(
        rest_data,
        db_data
    ):
    """compare dates between two data sets

    Args:
        rest_data (:obj:`list`): data from the internet
        db_data (:obj:`list`): data from database

    Returns:
        (:obj:`list`) mismatched values

    """
    rest_dates = []
    for row in rest_data:
        rest_dates.append(row['row']['date'])

    db_dates = []
    for row in db_data:
        db_dates.append(row[0].strftime('%Y-%m-%d'))

    mismatch = set(rest_dates) - set(db_dates)

    return list(mismatch)
