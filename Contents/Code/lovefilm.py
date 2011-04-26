import httplib
import time
import oauth as oauth

# settings for the local test consumer
SERVER = 'openapi.lovefilm.com'
PORT = 80

CONSUMER_KEY = 'tu6date7xu8a8mtps4xr4c8n'
CONSUMER_SECRET = 'mFt7Px4Cm7'

class LoveFilmRequest(object):
    server = SERVER
    port = PORT
    request_token_url = None
    access_token_url = None
    api_url = None
    signature_method = oauth.OAuthSignatureMethod_HMAC_SHA1()

    def __init__(self, consumer_key = CONSUMER_KEY, consumer_secret = CONSUMER_SECRET):
    
        # Obtain the URL for the current localization
        self.api_url = str(Locale.LocalString('API_URL'))
        self.request_token_url = str(Locale.LocalString('REQUEST_TOKEN_URL'))
        self.access_token_url = str(Locale.LocalString('ACCESS_TOKEN_URL'))
        
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret

        self.connection = httplib.HTTPConnection("%s:%d" % (self.server, self.port))
        self.consumer = oauth.OAuthConsumer(self.consumer_key, self.consumer_secret)

        self.queue_etag = None

    def get_request_token(self):
        req = oauth.OAuthRequest.from_consumer_and_token(
                  self.consumer, http_url=self.request_token_url)

        # This parameter indicates that no HTTP redirects will be issued, and
        # that the user will need to manually enter authorisation tokens.
        req.set_parameter("oauth_callback", "oob")

        req.sign_request(self.signature_method, self.consumer, None)

        self.connection.request(req.http_method, self.request_token_url, headers=req.to_header())
        response = self.connection.getresponse()

        tmp = response.read()
        token = oauth.OAuthToken.from_string(tmp)
        self.connection.close()

        return token

    def get_access_token(self, req_token):
        req = oauth.OAuthRequest.from_consumer_and_token(
                  self.consumer, 
                  token=req_token,
                  verifier=req_token.verifier,
                  http_url=self.access_token_url)

        req.sign_request(self.signature_method, self.consumer, req_token)

        Log(req.to_header())
        self.connection.request(req.http_method, self.access_token_url, headers=req.to_header())
        response = self.connection.getresponse()

        data = response.read()
        token = oauth.OAuthToken.from_string(data)
        self.connection.close()

        return token

    def make_query_internal(self, access_token=None, method='GET', query="", params=None, expand=True, returnURL=True):
        if params is None:
            params = {}

        if query.startswith('http://'):
            url = query
        else:
            url = self.api_url + query

        if expand:
            params['expand'] = "all"
        params['oauth_consumer_key'] = self.consumer_key
        
        req = oauth.OAuthRequest.from_consumer_and_token(
                  self.consumer, token=access_token, http_method=method,
                  http_url=url, parameters=params)
        req.sign_request(self.signature_method, self.consumer, access_token)
        if method == 'GET' or method == 'PUT' or method == 'DELETE':
            if returnURL:
              return req.to_url()
            else:  
              self.connection.request(method, req.to_url())
        elif method == 'POST':
            body_data = req.to_postdata()
            headers = {'Content-Type': 'application/x-www-form-urlencoded'}
            self.connection.request(method, url, body = body_data, headers = headers)
        else:
            return None

        return self.connection.getresponse()

    def make_query(self, access_token, query="", method='GET', params=None, expand=True, returnURL=True):
        return self.make_query_internal(access_token=access_token, query=query, method=method, params=params, expand=expand, returnURL=returnURL)
        
    def set_page(self, params, start_index=1, max_results=25):
    
        params['start_index'] = start_index
        params['items_per_page'] = max_results
    
        return params

    def search_titles_query(self, term="", id=None, genre=None):
        params = {'term': term }
        url = '/catalog/video'  
        
        if id is not None:
            params['id'] = id
        
        if genre is not None:
        	params['genre'] = genre

        return (url, params)
        
    def user_titles_query(self, user, type):
    
        url = '/users'
        url = url + '/' + user + '/' + type
        
        return (url, {})

    def title_query(self, title, type):
        url = '/catalog/title'
        url = url + '/' + title + '/' + type
        
        return (url, {})
    
    def getUser(self, access_token):
        url = '/users'
        
        response = self.make_query(access_token, url, method = 'GET')
        return (response)