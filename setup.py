"""Setup.py for ProsperAPI Flask project"""

from os import path, listdir
from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand
from codecs import open

HERE = path.abspath(path.dirname(__file__))
__version__ = '1.1.4'

def hack_find_packages(include_str):
    """patches setuptools.find_packages issue

    setuptools.find_packages(path='') doesn't work as intended

    Returns:
        (:obj:`list` :obj:`str`) append <include_str>. onto every element of setuptools.find_pacakges() call

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
        (:obj:`list` :obj:`str`) list of all non-directories in a file

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
    user_options = [('pytest-args=', 'a', "Arguments to pass to pytest")]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = [
            '-rx',
            'tests',
            '--cov=publicAPI/',
            '--cov-report=term-missing'
        ]    #load defaults here

    def run_tests(self):
        import shlex
        #import here, cause outside the eggs aren't loaded
        import pytest
        pytest_commands = []
        try:    #read commandline
            pytest_commands = shlex.split(self.pytest_args)
        except AttributeError:  #use defaults
            pytest_commands = self.pytest_args
        errno = pytest.main(pytest_commands)
        exit(errno)

with open('README.rst', 'r', 'utf-8') as f:
    readme = f.read()

setup(
    name='ProsperAPI',
    author='John Purcell',
    author_email='prospermarketshow@gmail.com',
    url='https://github.com/EVEprosper/ProsperAPI',
    download_url='https://github.com/EVEprosper/ProsperAPI/tarball/v' + __version__,
    version=__version__,
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
            'cache/prosperAPI.json'    #including key file for installer
        ]
    },
    install_requires=[
        'ProsperCommon',
        'Flask~=0.12',
        'Flask-RESTful~=0.3.5',
        'flask-script~=2.0.5',
        'requests~=2.13.0',         #intelpython3 == 2.10.0
        'pandas==0.18.1',           #intelpython3 == 0.18.1
        'numpy==1.11.1',            #intelpython3 == 1.11.1
        'cython==0.24',             #intelpython3 == 0.24
        'matplotlib~=2.0.0',        #required for building fbprophet (intel==1.5.1)
        'pystan~=2.14.0',
        'fbprophet~=0.1.post1',     #order matters: need pystan/cython first
        'tinydb~=3.2.2',
        'tinymongo~=0.1.8',
        'ujson~=1.35',
        'plumbum~=1.6.3',
        'shortuuid~=0.5.0'
    ],
    tests_require=[
        'pytest~=3.0.0',
        'pytest_cov~=2.4.0',        #requires requests==2.13.0
        'pytest-flask~=0.10.0',
        'pymysql~=0.7.10'
    ],
    cmdclass={
        'test':PyTest
    }
)
