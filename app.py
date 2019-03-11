import falcon
import falcon_jsonify
import mongoengine as mongo
import settings
import hvac
import os
import re
import requests
from requests.auth import HTTPBasicAuth
from xml.etree import ElementTree

class AuthMiddleware(object):

    def process_request(self, req, resp):
        token = req.get_header('Authorization')
        account_id = req.get_header('Account-ID')

        challenges = ['Token type="Fernet"']

        if token is None:
            description = ('Please provide an auth token '
                           'as part of the request.')

            raise falcon.HTTPUnauthorized('Auth token required',
                                          description,
                                          challenges)

        if not self._token_is_valid(token, account_id):
            description = ('The provided auth token is not valid. '
                           'Please request a new token and try again.')

            raise falcon.HTTPUnauthorized('Authentication required',
                                          description,
                                          challenges)

    def _token_is_valid(self, token, account_id):
        try:
            vclient = hvac.Client(url=settings.VAULT['ADDR'], token=os.environ['VAULT_TOKEN'], verify=False)
            apitoken_data = vclient.read('/secret/assetsapi')
            apitoken = apitoken_data["data"]["apitoken"]
            vclient.logout()
        except:
            raise falcon.HTTPError(falcon.HTTP_725, 'Auth error', 'Cannot connect to the auth store.')
        
        if token == apitoken and account_id == settings.AUTH['ID']:
            return True
        else:
            return False

# Get password for the local database connection
try:
    vclient = hvac.Client(url=settings.VAULT['ADDR'], token=os.environ['VAULT_TOKEN'], verify=False)
    localdb_data = vclient.read('/secret/assetsapi/localdb')
    localdb_pass = localdb_data["data"]["assetsdb"]
    vclient.logout()
except:
    raise falcon.HTTPError(falcon.HTTP_725, 'Auth error', 'Cannot connect to the auth store.')

api = falcon.API(middleware=[falcon_jsonify.Middleware(help_messages=settings.DEBUG),AuthMiddleware()])

mongo.connect(
    settings.ASSETSDB['DATABASE'],
    host = settings.ASSETSDB['HOST'],
    port = settings.ASSETSDB['PORT'],
    username = settings.ASSETSDB['USERNAME'],
    password = localdb_pass
)
