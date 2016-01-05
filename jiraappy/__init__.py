from cherrystrap import logger
from cherrystrap.configCheck import CheckSection, check_setting_int, check_setting_bool, check_setting_str
from jiraappy import backend

RSA_PRIVATE_KEY = None
RSA_PUBLIC_KEY = None
CONSUMER_KEY = None
CONSUMER_SECRET = None
JIRA_BASE_URL = None
JIRA_OAUTH_TOKEN = None
JIRA_OAUTH_SECRET = None
JIRA_LOGIN_STATUS = False
JIRA_LOGIN_USER = None

def injectVarCheck(CFG):

    global RSA_PRIVATE_KEY, RSA_PUBLIC_KEY, CONSUMER_KEY, CONSUMER_SECRET, \
        JIRA_BASE_URL, JIRA_OAUTH_TOKEN, JIRA_OAUTH_SECRET, \
        JIRA_LOGIN_STATUS, JIRA_LOGIN_USER

    CheckSection(CFG, 'JIRA')

    RSA_PRIVATE_KEY = check_setting_str(CFG, 'JIRA', 'rsa_private_key', 'keys/RSA.pem')
    RSA_PUBLIC_KEY = check_setting_str(CFG, 'JIRA', 'rsa_public_key', 'keys/RSA.pub')
    CONSUMER_KEY = check_setting_str(CFG, 'JIRA', 'consumer_key', '')
    CONSUMER_SECRET = check_setting_str(CFG, 'JIRA', 'consumer_secret', '')
    JIRA_BASE_URL = check_setting_str(CFG, 'JIRA', 'jira_base_url', '')
    JIRA_OAUTH_TOKEN = check_setting_str(CFG, 'JIRA', 'jira_oauth_token', '')
    JIRA_OAUTH_SECRET = check_setting_str(CFG, 'JIRA', 'jira_oauth_secret', '')

    JIRA_LOGIN_STATUS = False
    JIRA_LOGIN_USER = None

    # Test OAuth for logged in user
    try:
        backend.check_oauth()
    except Exception, e:
        logger.error("Can't verify OAuth user: %s" % e)

def injectDbSchema():

    schema = {}
    schema['exampleTable'] = {} #this is a table name
    schema['exampleTable']['columnName'] = 'TEXT' #this is a column name and format

    return schema

def injectApiConfigGet():

    injection = {
        "jira": {
                "rsaPublicKey": RSA_PUBLIC_KEY,
                "rsaPrivateKey": RSA_PRIVATE_KEY,
                "jiraBaseUrl": JIRA_BASE_URL,
                "consumerKey": CONSUMER_KEY,
                "consumerSecret": CONSUMER_SECRET
        }
    }

    return injection

def injectApiConfigPut(kwargs, errorList):
    global RSA_PRIVATE_KEY, RSA_PUBLIC_KEY, CONSUMER_KEY, CONSUMER_SECRET, \
        JIRA_BASE_URL, JIRA_OAUTH_TOKEN, JIRA_OAUTH_SECRET, \
        JIRA_LOGIN_STATUS, JIRA_LOGIN_USER

    if 'rsaPublicKey' in kwargs:
        RSA_PUBLIC_KEY = kwargs.pop('rsaPublicKey', None)
    if 'rsaPrivateKey' in kwargs:
        RSA_PRIVATE_KEY = kwargs.pop('rsaPrivateKey', None)
    if 'jiraBaseUrl' in kwargs:
        JIRA_BASE_URL = kwargs.pop('jiraBaseUrl', None)
    if 'consumerKey' in kwargs:
        CONSUMER_KEY = kwargs.pop('consumerKey', None)
    if 'consumerSecret' in kwargs:
        CONSUMER_SECRET = kwargs.pop('consumerSecret', None)

    return kwargs, errorList

def injectVarWrite(new_config):
    new_config['JIRA'] = {}
    new_config['JIRA']['rsa_private_key'] = RSA_PRIVATE_KEY
    new_config['JIRA']['rsa_public_key'] = RSA_PUBLIC_KEY
    new_config['JIRA']['consumer_key'] = CONSUMER_KEY
    new_config['JIRA']['consumer_secret'] = CONSUMER_SECRET
    new_config['JIRA']['jira_base_url'] = JIRA_BASE_URL
    new_config['JIRA']['jira_oauth_token'] = JIRA_OAUTH_TOKEN
    new_config['JIRA']['jira_oauth_secret'] = JIRA_OAUTH_SECRET

    return new_config
