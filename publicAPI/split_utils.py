"""split_utils.py: tool for handling type_id split/remapping"""
from os import path, makedirs

import ujson as json
import pandas as pd
from tinydb import TinyDB, Query

import publicAPI.config as api_config
import publicAPI.exceptions as exceptions

HERE = path.abspath(path.dirname(__file__))

SPLIT_TYPES = [
    29668,  #PLEX
    44992   #Mini-PLEX
]
class SplitInfo(object):
    """utility for managing split information"""
    def __init__(self):
        self.type_id = -1
        self.original_id = -1
        self.new_id = -1
        self.split_rate = -1
        self.bool_mult_div = None
        self.type_name = ''
        self.split_date = None

    #int(SplitInfo) = "what does the type_id switch to?"
    def __int__(self):
        return self.new_id

    #bool(SplitInfo) = "is this type_id the currently released item?"
    def __bool__(self):
        pass

    #new_price = old_price * SplitInfo()
    def __mul__(self, other):
        if self.bool_mult_div:
            return other * self.split_rate
        else:
            return other / self.split_rate

    #new_count = old_count / SplitInfo()
    def __div__(self, other):
        if self.bool_mult_div:
            return other / self.split_rate
        else:
            return other * self.split_rate

    #type_name for reasons
    def __str__(self):
        return self.type_name

SPLIT_INFO = {}
def read_split_info(
        split_info_file=path.join(HERE, 'split_info.json'),
        logger=api_config.LOGGER
):
    """initialize SPLIT_INFO for project

    Notes:
        Does not update global SPLIT_INFO (use `main` scope)

    Args:
        split_info_file (str, optional): path to split_info.json
        logger (:obj:`logging.logger`, optional): logging handle

    Returns:
        (:obj:`dict`) dict of type_id:SplitInfo

    """
    pass


