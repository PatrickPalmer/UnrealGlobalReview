
"""

Lambda @ Edge Event Structure
    https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/lambda-event-structure.html

Lambda @ Edge logs
    https://repost.aws/knowledge-center/lambda-edge-logs

Cognito @ Edge Javascript library
    https://github.com/awslabs/cognito-at-edge

"""

import json
import base64
import urllib.parse
import urllib.request
import traceback
import boto3


# %VAR% swapped in at CDK build
REGION = "%REGION%"
USER_POOL_ID = "%USER_POOL_ID%"
USER_POOL_APP_ID = "%USER_POOL_APP_ID%"
USER_POOL_DOMAIN_NAME= "%USER_POOL_DOMAIN_NAME%"
USER_POOL_CLOUDFRONT_DOMAIN = "%USER_POOL_CLOUDFRONT_DOMAIN%"


class Authenticator():

    def __init__(self, *, 
        region='us-east-1',         # user pool region
        user_pool_id=None,
        user_pool_domain_name=None,
        user_pool_app_id=None,
        user_pool_app_secret=None,
        logout_endpoint='/logout',
    ):

        self.region = region
        self.user_pool_id = user_pool_id
        self.user_pool_domain_name = user_pool_domain_name
        self.user_pool_app_id = user_pool_app_id
        self.user_pool_app_secret = user_pool_app_secret
        self.logout_endpoint = logout_endpoint

        self.user_pool_domain = f'{user_pool_domain_name}.auth.{region}.amazoncognito.com'


    def _get_authorization(self):
        if self.user_pool_app_secret:
            auth = base64.b64encode(f'{self.user_pool_app_id}:{self.user_pool_app_secret}'.encode('utf-8'))
            return f'Basic {auth}'
        return None


    def _fetch_tokens(self, grant, redirect_uri):
        query = {
            'client_id': self.user_pool_app_id,
            'redirect_uri': redirect_uri,
        }
        data = urllib.parse.urlencode(query | grant).encode()

        headers = {
            'Content-Type':'application/x-www-form-urlencoded',
        }
        auth = self._get_authorization()
        if auth:
            headers['Authorization'] = auth

        req = urllib.request.Request(f'https://{self.user_pool_domain}/oauth2/token', data, headers)

        with urllib.request.urlopen(req) as response:
            content = response.read()

        return json.loads(content)


    def _fetch_tokens_from_code(self, authorization_code, redirect_uri):
        grant = {
            'grant_type': "authorization_code",
            'code': authorization_code
        }
        return self._fetch_tokens(grant, redirect_uri)


    def _fetch_tokens_from_refresh_token(self, refresh_token, redirect_uri):
        grant = {
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token,
        }
        return self._fetch_tokens(grant, redirect_uri)


    def _get_redirect_response(self, tokens, location):
        response = {
            'status': '302',
            'headers': {
                'location': [{
                    'key': 'Location',
                    'value': location,
                }],
                'cache-control': [{
                    'key': 'Cache-Control',
                    'value': 'no-cache, no-store, max-age=0, must-revalidate',
                }],
                'pragma': [{
                    'key': 'Pragma',
                    'value': 'no-cache',
                }],
                'set-cookie': [{'key': "Set-Cookie", 'value': f"{k}={v}"} for k,v in tokens.items()],
            }
        }
    
        return response


    def _get_tokens_from_cookie(self, cookies):
        if not cookies:
            return {}
        tokens = {}
        for c in cookies:
            parts = c['value'].split(';')
            for part in parts:
                assign = part.split('=')
                if len(assign) != 2:
                    continue
                tokens[assign[0].strip()] = assign[1].strip()
        return tokens


    def handle(self, event):
        request = event['Records'][0]['cf']['request']
        headers = request['headers']
        domain = headers["host"][0]["value"]

        redirect_uri = f'https://{domain}{request["uri"]}'

        tokens = {}

        if request["uri"] != self.logout_endpoint:
            querystring = request.get('querystring', '')
            if 'code' in querystring:
                authorization_code = querystring.split('code=')[1].split('&')[0]
                tokens = self._fetch_tokens_from_code(authorization_code, redirect_uri)
                return self._get_redirect_response(tokens, redirect_uri)

            elif 'cookie' in headers:
                tokens = self._get_tokens_from_cookie(headers['cookie'])
                access_token = tokens['access_token'] if 'access_token' in tokens else None
            
                if access_token:
                    cognito_client = boto3.client('cognito-idp', region_name=self.region)
        
                    try:
                        # Verify the token
                        cognito_client.get_user(AccessToken=access_token)
                        return request
                    except:
                        # otherwise redirect to login
                        pass

        op = "logout" if request["uri"] == self.logout_endpoint else "login"
        location = f'https://{self.user_pool_domain}/{op}?response_type=code&client_id={self.user_pool_app_id}&redirect_uri={redirect_uri}'
    
        return self._get_redirect_response(tokens, location)


g_authenticator = None

def lambda_handler(event, context):
    global g_authenticator
    try:
        if not g_authenticator:
            g_authenticator = Authenticator(
                region=REGION,
                user_pool_id=USER_POOL_ID,
                user_pool_app_id=USER_POOL_APP_ID,
                user_pool_domain_name=USER_POOL_DOMAIN_NAME)
        return g_authenticator.handle(event)
    except Exception as e:
        tb = traceback.format_exc().replace('\n', '<br/>')
        return {
            'body': f'<h1>Unauthorized</h1><h2>Exception</h2>{e}<h2>Traceback</h2><br/>{tb}',
            'status': 401
        }
    
