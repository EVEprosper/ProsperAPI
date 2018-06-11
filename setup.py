"""Setup.py for ProsperAPI Flask project"""
from codecs import open
import importlib
from os import path, listdir

from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand

HERE = path.abspath(path.dirname(__file__))
__package_name__ = 'ProsperAPI'
__app_name__ = 'publicAPI'

def get_version(package_name):
    """find __version__ for making package

    Args:
        package_name (str): path to _version.py folder (abspath > relpath)

    Returns:
        str: __version__ value

    """
    module = package_name + '._version'
    package = importlib.import_module(module)

    version = package.__version__

    return version

def hack_find_packages(include_str):
    """patches setuptools.find_packages issue

    setuptools.find_packages(path='') doesn't work as intended

    Returns:
        list: append <include_str>. onto every element of setuptools.find_pacakges() call

    """
    new_list = [include_str]
    for element in find_packages(include_str):
        new_list.append(include_str + '.' + element)

    return new_list

def include_all_subfiles(*args):
    """Slurps up all files in a directory (non recursive) for data_files section

    Note:
        Not recursive, only includes flat files

    Returns:
        list: list of all non-directories in a file

    """
    file_list = []
    for path_included in args:
        local_path = path.join(HERE, path_included)

        for file in listdir(local_path):
            file_abspath = path.join(local_path, file)
            if path.isdir(file_abspath):        #do not include sub folders
                continue
            file_list.append(path_included + '/' + file)

    return file_list

class PyTest(TestCommand):
    """PyTest cmdclass hook for test-at-buildtime functionality

    http://doc.pytest.org/en/latest/goodpractices.html#manual-integration

    """
    user_options = [('pytest-args=', 'a', 'Arguments to pass to pytest')]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = [
            '-rx',
            'tests',
            '--cov=publicAPI/',
            '--cov-report=term-missing',
            '--cov-config=.coveragerc',
        ]

    def run_tests(self):
        import shlex
        import pytest
        pytest_commands = []
        try:
            pytest_commands = shlex.split(self.pytest_args)
        except AttributeError:
            pytest_commands = self.pytest_args
        errno = pytest.main(pytest_commands)
        exit(errno)

with open('README.rst', 'r', 'utf-8') as f:
    README = f.read()

setup(
    name=__package_name__,
    description='REST API for exposing Prosper data',
    long_description=README,
    author='John Purcell',
    author_email='prospermarketshow@gmail.com',
    url='https://github.com/EVEprosper/ProsperAPI',
    download_url='https://github.com/EVEprosper/' + __package_name__ + '/tarball/v' + get_version(__app_name__),
    version=get_version(__app_name__),
    license='MIT',
    classifiers=[
        'Programming Language :: Python :: 3.5'
    ],
    keywords='prosper eveonline api CREST',
    packages=find_packages(),
    data_files=[
        ('services', include_all_subfiles('services')),
        ('docs', include_all_subfiles('docs')),
        ('tests', include_all_subfiles('tests')),
        ('scripts', include_all_subfiles('scripts'))
    ],
    package_data={
        '': ['LICENSE', 'README.rst'],
        'publicAPI':[
            'split_info.json',
            'cache/prosperAPI.json',    #including key file for installer
            'cache/splitcache.json',
        ]
    },
    python_requires='>=3.5',
    install_requires=[
        'ProsperCommon~=1.4.0',
        'Flask',
        'Flask-RESTful',
        'flask-script',
        'requests',             #intelpython3 == 2.10.0
        'pandas',               #intelpython3 == 0.18.1
        'numpy',                #intelpython3 == 1.11.1
        'cython>=0.24',         #intelpython3 == 0.24
        'matplotlib>=2.0.0',    #required for building fbprophet (intel==1.5.1)
        'pystan==2.15.0',
        'fbprophet>=0.3.post1', #order matters: need pystan/cython first
        'tinydb',
        'tinymongo',
        'ujson',
        'plumbum',
        'shortuuid',
        'retrying',
    ],
    tests_require=[
        'pytest',  # >=3.0.0,<3.2.0',
        'pytest_cov',        #requires requests==2.13.0
        'pytest-flask',
        'pymysql',
    ],
    cmdclass={
        'test':PyTest,
    },
)
