"""split_utils.py: tool for handling type_id split/remapping"""
from os import path, makedirs
from datetime import datetime

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
    def __init__(self, json_entry=None):
        self.type_id = -1
        self.original_id = -1
        self.new_id = -1
        self.split_rate = -1
        self.bool_mult_div = None
        self.type_name = ''
        self.split_date = None
        if json_entry:
            self.load_object(json_entry)
        self.now = datetime.utcnow()

    #int(SplitInfo) = "what does the type_id switch to?"
    def __int__(self):
        return self.new_id

    #bool(SplitInfo) = "is this type_id the currently released item?"
    def __bool__(self):
        return bool(self.split_date < self.now)

    #new_price = old_price * SplitInfo()
    def multiply(self, other):
        """wrap multiply for mul/rmul"""
        if self.bool_mult_div:
            return other * self.split_rate
        else:
            return other / self.split_rate
    def __rmul__(self, other):
        return self.multiply(other)
    def __mul__(self, other):
        return self.multiply(other)

    #new_count = old_count / SplitInfo()
    def divide(self, other):
        """wrap divide for div/rdiv"""
        if self.bool_mult_div:
            return other / self.split_rate
        else:
            return other * self.split_rate
    def __rtruediv__(self, other):
        return self.divide(other)
    def __truediv__(self, other):
        return self.divide(other)

    #type_name for reasons
    def __str__(self):
        return self.type_name

    def load_object(self, json_entry):
        """loads info from json object into helper

        Args:
            json_entry (:obj:`dict`): one item to be parsed
                {'type_id', 'type_name', 'original_id', 'new_id',
                'split_date', 'bool_mult_div', 'split_rate'}

        Returns:
            None

        """
        #TODO: bonus points for inserting with __dict__
        try:
            self.type_id = int(json_entry['type_id'])
            self.type_name = json_entry['type_name']
            self.original_id = int(json_entry['original_id'])
            self.new_id = int(json_entry['new_id'])
            self.split_date = datetime.strptime(
                json_entry['split_date'],
                '%Y-%m-%d'
            )
            self.split_rate = int(json_entry['split_rate'])
        except Exception as err_msg:
            raise exceptions.InvalidSplitConfig(
                'Unable to parse config {0}'.format(repr(err_msg))
            )
        if json_entry['bool_mult_div'].lower() == 'true':
            self.bool_mult_div = True
        elif json_entry['bool_mult_div'].lower() == 'false':
            self.bool_mult_div = False
        else:
            raise exceptions.InvalidSplitConfig(
                'Unable to parse `bool_mult_div`={0}'.format(json_entry['bool_mult_div'])
            )

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


