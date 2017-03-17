from os import path
from datetime import datetime

import pytest

import publicAPI.forecast_utils as forecast_utils
import helpers

HERE = path.abspath(path.dirname(__file__))
ROOT = path.dirname(HERE)

CONFIG_FILENAME = path.join(HERE, 'test_config.cfg')

CONFIG = helpers.get_config(CONFIG_FILENAME)


def test_fetch_emd_history(config=CONFIG):
    """happypath test for `fetch_market_history_emd`"""
    data = forecast_utils.fetch_market_history_emd(
        region_id=config.get('TEST', 'region_id'),
        type_id=config.get('TEST', 'type_id'),
        data_range=config.get('TEST', 'history_count'),
        config=config
    )

    ## validate contents ##
    assert data['version'] == 2
    data_keys = data['columns'].split(',')
    for entry in data['result']:
        assert set(data_keys) == set(entry['row'].keys())

    ## validate count ##
    db_data = helpers.check_db_values(
        region_id=config.get('TEST', 'region_id'),
        type_id=config.get('TEST', 'type_id'),
        data_range=config.get('TEST', 'history_count'),
        config=config
    )
    if db_data:
        mismatch_dates = helpers.compare_dates(
            data['result'],
            db_data
        )
        assert len(mismatch_dates) <= int(config.get('TEST', 'miss_budget'))
    #expected_count = int(config.get('TEST', 'history_count'))
    #if not (
    #        len(data['result']) == expected_count or
    #        len(data['result']) == expected_count - 1
    #):
    #    pytest.xfail('EMD endpoint not complete: {0}'.format(len(data['result'])))
