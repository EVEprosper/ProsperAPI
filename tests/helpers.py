"""helpers.py: a collection of helpful utilities for tests"""
from os import path
import configparser

def get_config(config_filename):
    """parse test config file

    Args:
        config_filename (str): path to config file

    Returns:
        (:obj:`configparser.ConfigParser`)

    """
    config = configparser.ConfigParser(
        interpolation=configparser.ExtendedInterpolation(),
        allow_no_value=True,
        delimiters=('='),
        inline_comment_prefixes=('#')
    )

    local_filename = config_filename.replace('.cfg', '_local.cfg')
    if path.isfile(local_filename):
        config_filename = local_filename

    with open(config_filename, 'r') as file:
        config.read_file(file)

    return config
