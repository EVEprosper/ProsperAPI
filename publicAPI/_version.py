"""_version.py: track package version information"""
from os import path
import warnings

INSTALLED = True
try:    #pragma: no cover
    import prosper.common.prosper_version as p_version
except ImportError:
    INSTALLED = False

HERE = path.abspath(path.dirname(__file__))

def get_version():
    """find current version information

    Returns:
        (str): version information

    """
    if not INSTALLED:
        warnings.warn(
            'Unable to resolve package version until installed',
            UserWarning
        )
        return '0.0.0'  #can't parse version without stuff installed

    return p_version.get_version(HERE)

__version__ = get_version()
