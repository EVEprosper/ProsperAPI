'''sso_endpoint.py: CREST centric REST API endpoints'''

import os
from flask import Flask, request, session, render_template, url_for, redirect
from flask_oauthlib.client import OAuth
import configparser
from configparser import ExtendedInterpolation

#TODO: external config
config = configparser.ConfigParser(
    interpolation  = ExtendedInterpolation(),
    allow_no_value = True,
    delimiters     = ('=')
)
CONFIG_FILE_LOCAL   = 'prosperSSO_local.cfg'
CONFIG_FILE_DEFAULT = 'prosperSSO.cfg'

#load cfg file (this is bad, and you should feel bad)
if os.path.isfile(CONFIG_FILE_LOCAL):
    config.read(CONFIG_FILE_LOCAL)
else:
    config.read(CONFIG_FILE_DEFAULT)


app = Flask(__name__)

oauth = OAuth()
#sso = oauth.remote_app('EVE Prosper', app_key='EVEPROSPER')
app.secret_key = config.get('OAUTH', 'secret_key')
sso = oauth.remote_app(
    'EVE Prosper',
    consumer_key        = config.get('OAUTH', 'client_id'),
    consumer_secret     = config.get('OAUTH', 'secret_key'),
    base_url            = config.get('OAUTH', 'base_url'),
    access_token_url    = config.get('OAUTH', 'token_url'),
    access_token_method = 'POST',
    authorize_url       = config.get('OAUTH', 'authorize_url')
)
oauth.init_app(app)

@app.route('/')
def index():
    '''index page goes here'''
    return "NO PLACE LIKE HOME"

@app.route(config.get('ENDPOINTS', 'logout_path'))
def logout():
    '''logout command/logic'''
    session.clear()
    return redirect(url_for('index'))

@app.route(config.get('ENDPOINTS', 'login_path'))
def login():
    '''login command/logic'''
    return sso.authorize(
        callback=url_for(
            'authorized',
            _external=True,
            _scheme='http'
        )
    )

@app.route(config.get('ENDPOINTS', 'callback_path'))
def authorized():
    '''handling callback request'''
    resp = sso.authorized_response()
    if resp is None:
        return 'Access denied: reason=%s error=%s' % (
            request.args['error_reason'],
            request.args['error_description']
        )
    if isinstance(resp, Exception):
        return 'Access denied: error=%s' % str(resp)

    session['evesso_token'] = (resp['access_token'], '')
    print(session)
    verify = sso.get('verify')
    session['character'] = verify.data
    return redirect(url_for('index'))


@sso.tokengetter
def get_sso_oauth_token():
    '''Fetches token off sso session object'''
    None

if __name__ == "__main__":
    app.run(
        debug = bool(config.get('FLASK', 'debug_enabled')),
        port  =  int(config.get('FLASK', 'sso_api_port'))
    )
