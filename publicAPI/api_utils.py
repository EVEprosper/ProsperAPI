from os import path, makedirs
from datetime import datetime

import ujson as json
from tinydb import TinyDB, Query

import prosper.common.prosper_logging as p_logging
import publicAPI.exceptions as exceptions

LOGGER = p_logging.DEFAULT_LOGGER
HERE = path.abspath(path.dirname(__file__))

CACHE_PATH = path.join(HERE, 'cache')
makedirs(CACHE_PATH, exist_ok=True)

def check_key(
        api_key,
        cache_path=CACHE_PATH,
        api_file='apikeys.json',
        throw_on_fail=False,
        logger=LOGGER
):
    """check if API key is valid

    Args:
        api_key (str): given API key
        cache_path (str, optional): override for cache_path
        api_file (str, optional): tinydb filename
        throw_on_fail (bool, optional): raise exception if API key fails
        logger (:obj:`logging.logger`): logging handle

    Returns:
        (bool) access allowed or not

    """
    api_db = TinyDB(path.join(cache_path, api_file))

    api_value = api_db.search(
        Query().api_key == api_key
    )

    access_allowed = False
    if api_value:
        logger.info(
            'accessed service - {0}:{1}'.format(
                api_value[0]['user_name'],
                api_value[0]['user_info']
            )
        )
        logger.debug(api_value[0])

        api_db.update(
            {'last_accessed': datetime.now().isoformat()},
            Query().api_key == api_key
        )
        access_allowed = True
    else:
        logger.warning('Invalid API key: {0}'.format(api_key))
        if throw_on_fail:
            raise exceptions.APIKeyInvalid(
                status=401,
                message='Invalid API key'
            )
    api_db.close()

    return access_allowed
