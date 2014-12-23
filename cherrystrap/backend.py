import os, base64, urllib

from lib.tlslite.utils import keyfactory
from lib.httplib2 import urlparse
from lib import oauth2 as oauth
from lib import simplejson as json

import cherrystrap

from cherrystrap import logger

def redirect_oauth():

    consumer = oauth.Consumer(cherrystrap.CONSUMER_KEY, cherrystrap.CONSUMER_SECRET)
    client = oauth.Client(consumer)
    client.set_signature_method(SignatureMethod_RSA_SHA1())

    request_token_url = os.path.join(cherrystrap.JIRA_BASE_URL, 'plugins/servlet/oauth/request-token')
    authorize_url = os.path.join(cherrystrap.JIRA_BASE_URL, 'plugins/servlet/oauth/authorize')

    try:
        resp, content = client.request(request_token_url, "POST")
        if resp['status'] != '200':
            authorize_token_url = "home"
            status, status_msg = ajaxMSG('failure', 'Invalid Consumer Key, RSA Keys, or JIRA App Link - please check configuration')
        else:
            request_token = dict(urlparse.parse_qsl(content))
            request_token_info = {
                "oauth_token": request_token['oauth_token'],
                "oauth_token_secret": request_token['oauth_token_secret'],
                "authorize_token_url": "%s?oauth_token=%s" % (authorize_url, request_token['oauth_token'])
            }
            authorize_token_url = request_token_info['authorize_token_url']
            status, status_msg = ajaxMSG('success', 'JIRA Credentials recognized! Redirecting to JIRA login')
    except:
        authorize_token_url = "home"
        status, status_msg = ajaxMSG('failure', 'Invalid Consumer Key, RSA Keys, or JIRA App Link - please check configuration')

    return authorize_token_url, status, status_msg

def request_oauth(oauth_token):
    consumer = oauth.Consumer(cherrystrap.CONSUMER_KEY, cherrystrap.CONSUMER_SECRET)
    token = oauth.Token(oauth_token, oauth_token)
    client = oauth.Client(consumer, token)
    client.set_signature_method(SignatureMethod_RSA_SHA1())

    return consumer, client

def verified_oauth(oauth_token, oauth_token_secret):
    consumer = oauth.Consumer(cherrystrap.CONSUMER_KEY, cherrystrap.CONSUMER_SECRET)
    accessToken = oauth.Token(oauth_token, oauth_token_secret)
    client = oauth.Client(consumer, accessToken)
    client.set_signature_method(SignatureMethod_RSA_SHA1())

    return consumer, client

def validate_oauth(oauth_token):
    consumer, client = request_oauth(oauth_token)
    
    access_token_url = os.path.join(cherrystrap.JIRA_BASE_URL, 'plugins/servlet/oauth/access-token')
    data_url = os.path.join(cherrystrap.JIRA_BASE_URL, 'rest/api/2/myself')

    resp, content = client.request(access_token_url, "POST")
    access_token = dict(urlparse.parse_qsl(content))

    consumer, client = verified_oauth(access_token['oauth_token'], access_token['oauth_token_secret'])

    resp, content = client.request(data_url, "GET")
    if resp['status'] != '200':
        cherrystrap.JIRA_OAUTH_TOKEN = None
        cherrystrap.JIRA_OAUTH_SECRET = None
        cherrystrap.config_write()
        cherrystrap.JIRA_LOGIN_STATUS = None
        cherrystrap.JIRA_LOGIN_USER = None
        status, status_msg = ajaxMSG('failure', 'Could not handshake with JIRA Server. Tokens reset')
    else:
        resp_dict = json.loads(content)
        cherrystrap.JIRA_OAUTH_TOKEN = access_token['oauth_token']
        cherrystrap.JIRA_OAUTH_SECRET = access_token['oauth_token_secret']
        cherrystrap.config_write()
        cherrystrap.JIRA_LOGIN_STATUS = True
        cherrystrap.JIRA_LOGIN_USER = resp_dict['name']
        status, status_msg = ajaxMSG('success', 'JIRA OAuth Tokens successfully saved to configuration file')

    return status, status_msg

def stored_oauth():
    consumer = oauth.Consumer(cherrystrap.CONSUMER_KEY, cherrystrap.CONSUMER_SECRET)
    accessToken = oauth.Token(cherrystrap.JIRA_OAUTH_TOKEN, cherrystrap.JIRA_OAUTH_SECRET)
    client = oauth.Client(consumer, accessToken)
    client.set_signature_method(SignatureMethod_RSA_SHA1())

    return consumer, client

def check_oauth():
    consumer = oauth.Consumer(cherrystrap.CONSUMER_KEY, cherrystrap.CONSUMER_SECRET)
    accessToken = oauth.Token(cherrystrap.JIRA_OAUTH_TOKEN, cherrystrap.JIRA_OAUTH_SECRET)
    client = oauth.Client(consumer, accessToken)
    client.set_signature_method(SignatureMethod_RSA_SHA1())

    data_url = os.path.join(cherrystrap.JIRA_BASE_URL, 'rest/api/2/myself')

    resp, content = client.request(data_url, "GET")
    if resp['status'] != '200':
        cherrystrap.JIRA_LOGIN_STATUS = None
        cherrystrap.JIRA_LOGIN_USER = None
        logger.warn("OAuth credentials missing or invalid")
    else:
        resp_dict = json.loads(content)
        cherrystrap.JIRA_LOGIN_STATUS = True
        cherrystrap.JIRA_LOGIN_USER = resp_dict['name']
        logger.info("JIRA user %s verified login" % resp_dict['name'])

def create_https_certificates(ssl_cert, ssl_key):
    """
    Create a pair of self-signed HTTPS certificares and store in them in
    'ssl_cert' and 'ssl_key'. Method assumes pyOpenSSL is installed.
    """
    import os
    from cherrystrap import logger

    from OpenSSL import crypto
    from lib.certgen import createKeyPair, createCertRequest, createCertificate, \
        TYPE_RSA, serial

    # Create the CA Certificate
    cakey = createKeyPair(TYPE_RSA, 2048)
    careq = createCertRequest(cakey, CN="Certificate Authority")
    cacert = createCertificate(careq, (careq, cakey), serial, (0, 60 * 60 * 24 * 365 * 10)) # ten years

    pkey = createKeyPair(TYPE_RSA, 2048)
    req = createCertRequest(pkey, CN="CherryStrap")
    cert = createCertificate(req, (cacert, cakey), serial, (0, 60 * 60 * 24 * 365 * 10)) # ten years

    # Save the key and certificate to disk
    try:
        if not os.path.exists('keys'):
            os.makedirs('keys')
        with open('keys/server.key', "w+") as fp:
            fp.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, pkey))
        with open('keys/server.crt', "w+") as fp:
            fp.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert))
    except IOError:
        logger.error("Error creating SSL key and certificate")
        return False

    return True

class SignatureMethod_RSA_SHA1(oauth.SignatureMethod):
    name = 'RSA-SHA1'

    def signing_base(self, request, consumer, token):
        if not hasattr(request, 'normalized_url') or request.normalized_url is None:
            logger.warn("Base URL for request is not set.")

        sig = (
            oauth.escape(request.method),
            oauth.escape(request.normalized_url),
            oauth.escape(request.get_normalized_parameters()),
        )

        key = '%s&' % oauth.escape(consumer.secret)
        if token:
            key += oauth.escape(token.secret)
        raw = '&'.join(sig)
        return key, raw

    def sign(self, request, consumer, token):
        """Builds the base signature string."""
        key, raw = self.signing_base(request, consumer, token)

        try:
            with open(cherrystrap.RSA_PRIVATE_KEY, 'r') as f:
                data = f.read()
            privateKeyString = data.strip()
            privatekey = keyfactory.parsePrivateKey(privateKeyString)
            signature = str(privatekey.hashAndSign(raw))
            return base64.b64encode(signature)
        except:
            logger.warn('Private Key File not found on server at location %s' % cherrystrap.RSA_PRIVATE_KEY)


def ajaxMSG(status, status_msg):
    if status == 'success':
        logger.info(status_msg)
    elif status == 'failure':
        logger.warn(status_msg)

    return status, status_msg