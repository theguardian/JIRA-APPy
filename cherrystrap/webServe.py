import os, cherrypy, urllib, collections
from cherrypy import _cperror, request
from lib import simplejson as json
from auth import AuthController, require, member_of, name_is
from templating import serve_template

import threading, time

import cherrystrap
import jiraappy

from cherrystrap import logger, formatter, database
from jiraappy import backend, jiraInt

SESSION_KEY = '_cp_username'

class WebInterface(object):

    def error_page_404(status, message, traceback, version):
        status_msg = "%s - %s" % (status, message)
        return serve_template(templatename="index.html", title="404 - Page Not Found", msg=status_msg)
    cherrypy.config.update({'error_page.404': error_page_404})

    def handle_error():
        cherrypy.response.status = 500
        logger.error("500 Error: %s" % _cperror.format_exc())
        cherrypy.response.body = ["<html><body>Sorry, an error occured</body></html>"]

    _cp_config = {
        'tools.sessions.on': True,
	'tools.sessions.timeout': 10080,
        'tools.auth.on': True,
        'error_page.404': error_page_404,
        'request.error_response': handle_error
    }

    auth = AuthController()

    @require()
    def index(self, oauth_token=None):
		if oauth_token:
			status, msg = backend.validate_oauth(oauth_token)
		else:
			status, msg = '', ''

		return serve_template(templatename="index.html", title="Home", status=status, msg=msg)
    index.exposed = True

    @require()
    def oauth_request(self):
		authorize_token_url, status, msg = backend.redirect_oauth()
		if not authorize_token_url:
			return serve_template(templatename="index.html", title="Home", status=status, msg=msg)
		else:
			raise cherrypy.HTTPRedirect(authorize_token_url)
    oauth_request.exposed = True

    @require()
    def oauth_logout(self):
		jiraappy.JIRA_OAUTH_TOKEN = None
		jiraappy.JIRA_OAUTH_SECRET = None
		cherrystrap.config_write()
		jiraappy.JIRA_LOGIN_STATUS = None
		jiraappy.JIRA_LOGIN_USER = None
		status, msg = backend.ajaxMSG('success', 'Successfully logged out of JIRA OAuth')
		return serve_template(templatename="index.html", title="Home", status=status, msg=msg)
    oauth_logout.exposed = True

    @require()
    def listener(self):
		return serve_template(templatename="listener.html", title="Webhooks")
    listener.exposed = True

    @require()
    def caller(self, call=None, action=None):
        status, msg = '', ''
        if call=='reindex':
            status, msg = jiraInt.reindex(action)
        return serve_template(templatename="caller.html", title="Call JIRA", status=status, msg=msg)
    caller.exposed = True

    @require()
    def operations(self, script=None, issue_list_input=None):
        status, msg = '', ''
        if jiraappy.JIRA_LOGIN_STATUS:
            consumer, client = backend.stored_oauth()

            if request.method == 'POST':
                script = request.params['script']
                issue_list_input = request.params['issue_list_input']
                issue_list = [x.strip() for x in issue_list_input.split(',')]

                if script == 'bulk-delete-worklogs' and issue_list_input:
                    status, msg = jiraInt.bulkDeleteWorklogs(issue_list)
                else:
                    status, msg = backend.ajaxMSG('failure', 'No issues entered for processing')
            else:
                pass
        else:
            status, msg = backend.ajaxMSG('failure', 'Can not operate on JIRA without being logged in')

        return serve_template(templatename="operations.html", title="Bulk Operations", status=status, msg=msg)
    operations.exposed = True

    @require()
    def config(self):
        http_look_dir = os.path.join(cherrystrap.PROG_DIR, 'static/interfaces/')
        http_look_list = [ name for name in os.listdir(http_look_dir) if os.path.isdir(os.path.join(http_look_dir, name)) ]

        config = {
            "http_look_list":   http_look_list
        }

        return serve_template(templatename="config.html", title="Settings", config=config)
    config.exposed = True

    @require()
    def logs(self):
        return serve_template(templatename="logs.html", title="Log", lineList=cherrystrap.LOGLIST)
    logs.exposed = True

    @require()
    def shutdown(self):
        cherrystrap.config_write()
        cherrystrap.SIGNAL = 'shutdown'
        message = 'shutting down ...'
        return serve_template(templatename="shutdown.html", title="Exit", message=message, timer=10)
        return page
    shutdown.exposed = True

    @require()
    def restart(self):
        cherrystrap.SIGNAL = 'restart'
        message = 'restarting ...'
        return serve_template(templatename="shutdown.html", title="Restart", message=message, timer=15)
    restart.exposed = True

    @require()
    def shutdown(self):
        cherrystrap.config_write()
        cherrystrap.SIGNAL = 'shutdown'
        message = 'shutting down ...'
        return serve_template(templatename="shutdown.html", title="Exit", message=message, timer=15)
        return page
    shutdown.exposed = True

    @require()
    def update(self):
        cherrystrap.SIGNAL = 'update'
        message = 'updating ...'
        return serve_template(templatename="shutdown.html", title="Update", message=message, timer=30)
    update.exposed = True

    # Safe to delete this def, it's just there as a reference
    def template(self):
        return serve_template(templatename="template.html", title="Template Reference")
    template.exposed=True

    def checkGithub(self):
        # Make sure this is requested via ajax
        request_type = cherrypy.request.headers.get('X-Requested-With')
        if str(request_type).lower() == 'xmlhttprequest':
            pass
        else:
            status_msg = "This page exists, but is not accessible via web browser"
            return serve_template(templatename="index.html", title="404 - Page Not Found", msg=status_msg)

        from cherrystrap import versioncheck
        versioncheck.checkGithub()
        cherrystrap.IGNORE_UPDATES = False
    checkGithub.exposed = True

    def ignoreUpdates(self):
        # Make sure this is requested via ajax
        request_type = cherrypy.request.headers.get('X-Requested-With')
        if str(request_type).lower() == 'xmlhttprequest':
            pass
        else:
            status_msg = "This page exists, but is not accessible via web browser"
            return serve_template(templatename="index.html", title="404 - Page Not Found", msg=status_msg)

        cherrystrap.IGNORE_UPDATES = True
    ignoreUpdates.exposed = True

    def ajaxUpdate(self):
        # Make sure this is requested via ajax
        request_type = cherrypy.request.headers.get('X-Requested-With')
        if str(request_type).lower() == 'xmlhttprequest':
            pass
        else:
            status_msg = "This page exists, but is not accessible via web browser"
            return serve_template(templatename="index.html", title="404 - Page Not Found", msg=status_msg)

        return serve_template(templatename="ajaxUpdate.html")
    ajaxUpdate.exposed = True
