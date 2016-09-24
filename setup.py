'''wheel setup for public prosper API's'''

from os import path, listdir
from setuptools import setup, find_packages


HERE = path.abspath(path.dirname(__file__))

def include_all_subfiles(path_included):
    '''for data_files {path_included}/*'''
    local_path = path.join(HERE, path_included)
    file_list = []

    for file in listdir(local_path):
        file_list.append(path_included + '/' + file)

    return file_list

def hack_find_packages(include_str):
    '''setuptools.find_packages({include_str}) does not work.  Adjust pathing'''
    new_list = [include_str]
    for element in find_packages(include_str):
        new_list.append(include_str + '.' + element)

    return new_list

setup(
    name='ProsperAPI',
    version='0.1.0',
    license='MIT',
    classifiers=[
        'Programming Language :: Python :: 3.5'
    ],
    keywords='prosper eveonline api CREST',
    packages=hack_find_packages('prosper'),
    package_data={
        'prosper':[
            'publicAPI/prosperAPI.cfg'
        ]
    },
    install_requires=[
        'aniso8601==1.1.0',
        'astroid==1.4.5',
        'colorama==0.3.7',
        'Flask==0.10.1',
        'Flask-Cache==0.13.1',
        'Flask-Markdown==0.3',
        'Flask-RESTful==0.3.5',
        'itsdangerous==0.24',
        'Jinja2==2.8',
        'lazy-object-proxy==1.2.2',
        'Markdown==2.6.6',
        'MarkupSafe==0.23',
        'numpy==1.11.0',
        'pandas==0.18.1',
        'pylint==1.5.5',
        'pypyodbc==1.3.3',
        'python-dateutil==2.5.3',
        'pytz==2016.4',
        'requests==2.10.0',
        'six==1.10.0',
        'Werkzeug==0.11.9',
        'wrapt==1.10.8'
    ],
    dependency_links=[
        'https://github.com/EVEprosper/ProsperWarehouse.git#egg=ProsperWarehouse' #not quite right
    ]
)
