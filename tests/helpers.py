"""helpers.py: a collection of helpful utilities for tests"""
from os import path
import configparser
from datetime import datetime, timedelta

import pymysql.cursors

import prosper.common.prosper_config as p_config
CONN = None
def get_config(config_filename):
    """parse test config file

    Args:
        config_filename (str): path to config file

    Returns:
        (:obj:`configparser.ConfigParser`)

    """
    config = p_config.ProsperConfig(config_filename)
    #config = configparser.ConfigParser(
    #    interpolation=configparser.ExtendedInterpolation(),
    #    allow_no_value=True,
    #    delimiters=('='),
    #    inline_comment_prefixes=('#')
    #)
#
    #local_filename = config_filename.replace('.cfg', '_local.cfg')
    #if path.isfile(local_filename):
    #    config_filename = local_filename
#
    #with open(config_filename, 'r') as file:
    #    config.read_file(file)

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
        return None

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
