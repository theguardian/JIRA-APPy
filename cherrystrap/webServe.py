import os, cherrypy, urllib, base64
from cherrypy import request

from lib import simplejson as json
from lib.tlslite.utils import keyfactory
from lib.httplib2 import urlparse
from lib import oauth2 as oauth
# from lib import flask
# from flask import request
# from flask import jsonify

from mako.template import Template
from mako.lookup import TemplateLookup
from mako import exceptions

import threading, time
import csv

import cherrystrap

from cherrystrap import logger, formatter, database, backend
from cherrystrap.formatter import checked

# @app.route("/get_my_ip", methods=["GET"])
# def get_my_ip():
# 	return jsonify({'ip': request.environ['REMOTE_ADDR']}), 200

def serve_template(templatename, **kwargs):

	interface_dir = os.path.join(str(cherrystrap.PROG_DIR), 'data/interfaces/')
	template_dir = os.path.join(str(interface_dir), cherrystrap.HTTP_LOOK)

	_hplookup = TemplateLookup(directories=[template_dir])

	try:
		template = _hplookup.get_template(templatename)
		return template.render(**kwargs)
	except:
		return exceptions.html_error_template().render()

class WebInterface(object):

	def index(self, oauth_token=None):
		if oauth_token:
			status, status_msg = backend.validate_oauth(oauth_token)
		else:
			status, status_msg = '', ''

		return serve_template(templatename="index.html", title="Home", status=status, status_msg=status_msg)
	index.exposed=True

	def oauth_request(self):
		authorize_token_url, status, status_msg = backend.redirect_oauth()
		if authorize_token_url == "home":
			return serve_template(templatename="index.html", title="Home", status=status, status_msg=status_msg)
		else:
			raise cherrypy.HTTPRedirect(authorize_token_url)
	oauth_request.exposed = True

	def oauth_logout(self):
		cherrystrap.JIRA_OAUTH_TOKEN = None
		cherrystrap.JIRA_OAUTH_SECRET = None
		cherrystrap.config_write()
		cherrystrap.JIRA_LOGIN_STATUS = None
		cherrystrap.JIRA_LOGIN_USER = None
		status, status_msg = backend.ajaxMSG('success', 'Successfully logged out of JIRA OAuth')
		return serve_template(templatename="index.html", title="Home", status=status, status_msg=status_msg)
	oauth_logout.exposed = True

	def listener(self):
		return serve_template(templatename="listener.html", title="Webhooks")
	listener.exposed = True

	def caller(self, call=None, action=None):
		if cherrystrap.JIRA_LOGIN_STATUS:
			consumer, client = backend.stored_oauth()
			status, status_msg = '', ''
			
			# Reindex JIRA
			if call=='reindex':
				if action=='POST':
					data_url = os.path.join(cherrystrap.JIRA_BASE_URL, 'rest/api/2/reindex?type=BACKGROUND&indexComments=true&indexChangeHistory=true')
					try:
						resp, content = client.request(data_url, "POST")
						if resp['status'] != '202':
							status, status_msg = backend.ajaxMSG('failure', 'Call for JIRA Reindex failed with status code '+resp['status'])
						else:
							status, status_msg = backend.ajaxMSG('success', 'JIRA is now reindexing')
					except:
						status, status_msg = backend.ajaxMSG('failure', 'Could not connect to '+data_url)
				
				elif action=='GET':
					data_url = os.path.join(cherrystrap.JIRA_BASE_URL, 'rest/api/2/reindex')
					try:
						resp, content = client.request(data_url, "GET")
						if resp['status'] != '200':
							status, status_msg = backend.ajaxMSG('failure', 'Call for JIRA Reindex status failed with status code '+resp['status'])
						else:
							resp_dict = json.loads(content)
							currentProgress = resp_dict['currentProgress']
							status, status_msg = backend.ajaxMSG('success', 'JIRA reindex is '+str(currentProgress)+'% complete')
					except:
						status, status_msg = backend.ajaxMSG('failure', 'Could not connect to '+data_url)
			# End Reindex

		else:
			status, status_msg = backend.ajaxMSG('failure', 'Can not call JIRA without being logged in')

		return serve_template(templatename="caller.html", title="Call JIRA", status=status, status_msg=status_msg)
	caller.exposed = True

	def operations(self, script=None, issue_list_input=None):
		if cherrystrap.JIRA_LOGIN_STATUS:
			consumer, client = backend.stored_oauth()

			if request.method == 'POST':
				script = request.params['script']
				issue_list_input = request.params['issue_list_input']
				issue_list = [x.strip() for x in issue_list_input.split(',')]

				if script=='bulk-delete-worklogs' and issue_list_input:
					num_issues = 0
					num_worklogs = 0
					for issue in issue_list:
						num_issues+=1
						data_url = os.path.join(cherrystrap.JIRA_BASE_URL, 'rest/api/2/issue/'+issue+'/worklog')
						try:
							resp, content = client.request(data_url, "GET")
							if resp['status'] != '200':
								logger.warn("Request for %s failed with status code %s - %s" (data_url, resp['status'], content))
							else:
								resp_dict = json.loads(content)
								num_results = resp_dict['total']
								if num_results != 0:
									for result in range(0, num_results):
										worklog_id = resp_dict['worklogs'][result]['id']
										data_url = os.path.join(cherrystrap.JIRA_BASE_URL, 'rest/api/2/issue/'+issue+'/worklog/'+worklog_id+'?adjustEstimate=leave')
										try:
											resp, content = client.request(data_url, "DELETE")
											if resp['status'] != '204':
												logger.warn("Request for %s failed with status code %s - %s" (data_url, resp['status'], content))
											else:
												num_worklogs+=1
												logger.info("Worklog ID %s for issue %s has been deleted" % (worklog_id, issue))
										except:
											logger.warn("Could not connect to %s" % data_url)
								else:
									logger.info("No worklogs found for issue %s" % issue)
						except:
							logger.warn("Could not connect to %s" % data_url)
					status, status_msg = backend.ajaxMSG('success', '%d worklog(s) have been deleted for %d issues' % (num_worklogs, num_issues))
				else:
					status, status_msg = backend.ajaxMSG('failure', 'No issues entered for processing')
			else:
				status, status_msg = '', ''
		else:
			status, status_msg = backend.ajaxMSG('failure', 'Can not operate on JIRA without being logged in')

		return serve_template(templatename="operations.html", title="Bulk Operations", status=status, status_msg=status_msg)
	operations.exposed = True

	def config(self):
		http_look_dir = os.path.join(cherrystrap.PROG_DIR, 'data/interfaces/')
		http_look_list = [ name for name in os.listdir(http_look_dir) if os.path.isdir(os.path.join(http_look_dir, name)) ]

		config = {
					"server_name":      cherrystrap.SERVER_NAME,
					"http_host":        cherrystrap.HTTP_HOST,
					"https_enabled":	checked(cherrystrap.HTTPS_ENABLED),
					"https_key":		cherrystrap.HTTPS_KEY,
					"https_cert":		cherrystrap.HTTPS_CERT,
					"http_user":        cherrystrap.HTTP_USER,
					"http_port":        cherrystrap.HTTP_PORT,
					"http_pass":        cherrystrap.HTTP_PASS,
					"http_look":        cherrystrap.HTTP_LOOK,
					"http_look_list":   http_look_list,
					"launch_browser":   checked(cherrystrap.LAUNCH_BROWSER),
					"logdir":           cherrystrap.LOGDIR,
					"rsa_private_key":	cherrystrap.RSA_PRIVATE_KEY,
					"rsa_public_key":	cherrystrap.RSA_PUBLIC_KEY,
					"consumer_key":		cherrystrap.CONSUMER_KEY,
					"consumer_secret":	cherrystrap.CONSUMER_SECRET,
					"jira_base_url":	cherrystrap.JIRA_BASE_URL,
				}
		return serve_template(templatename="config.html", title="Settings", config=config)    
	config.exposed = True

	def configUpdate(self, server_name="Server", http_host='0.0.0.0', http_user=None, http_port=7889, http_pass=None, http_look=None, launch_browser=0, logdir=None, 
		consumer_key=None, consumer_secret=None, jira_base_url=None, https_enabled=0, https_key=None, https_cert=None, rsa_private_key=None, rsa_public_key=None):

		cherrystrap.SERVER_NAME = server_name
		cherrystrap.HTTP_HOST = http_host
		cherrystrap.HTTP_PORT = http_port
		cherrystrap.HTTPS_ENABLED = https_enabled
		cherrystrap.HTTPS_KEY = https_key
		cherrystrap.HTTPS_CERT = https_cert
		cherrystrap.HTTP_USER = http_user
		cherrystrap.HTTP_PASS = http_pass
		cherrystrap.HTTP_LOOK = http_look
		cherrystrap.LAUNCH_BROWSER = launch_browser
		cherrystrap.LOGDIR = logdir

		cherrystrap.RSA_PRIVATE_KEY = rsa_private_key
		cherrystrap.RSA_PUBLIC_KEY = rsa_public_key
		cherrystrap.CONSUMER_KEY = consumer_key
		cherrystrap.CONSUMER_SECRET = consumer_secret
		cherrystrap.JIRA_BASE_URL = jira_base_url

		cherrystrap.config_write()
		logger.info("Configuration saved successfully")

	configUpdate.exposed = True

	def logs(self):
		 return serve_template(templatename="logs.html", title="Log", lineList=cherrystrap.LOGLIST)
	logs.exposed = True

	def getLog(self,iDisplayStart=0,iDisplayLength=100,iSortCol_0=0,sSortDir_0="desc",sSearch="",**kwargs):

		iDisplayStart = int(iDisplayStart)
		iDisplayLength = int(iDisplayLength)

		filtered = []
		if sSearch == "":
			filtered = cherrystrap.LOGLIST[::]
		else:
			filtered = [row for row in cherrystrap.LOGLIST for column in row if sSearch in column]

		sortcolumn = 0
		if iSortCol_0 == '1':
			sortcolumn = 2
		elif iSortCol_0 == '2':
			sortcolumn = 1
		filtered.sort(key=lambda x:x[sortcolumn],reverse=sSortDir_0 == "desc")

		rows = filtered[iDisplayStart:(iDisplayStart+iDisplayLength)]
		rows = [[row[0],row[2],row[1]] for row in rows]

		dict = {'iTotalDisplayRecords':len(filtered),
				'iTotalRecords':len(cherrystrap.LOGLIST),
				'aaData':rows,
				}
		s = json.dumps(dict)
		return s
	getLog.exposed = True

	def template(self):
		return serve_template(templatename="template.html", title="Template")
	template.exposed=True

	def shutdown(self):
		cherrystrap.config_write()
		cherrystrap.SIGNAL = 'shutdown'
		message = 'shutting down ...'
		return serve_template(templatename="shutdown.html", title="Exit", message=message, timer=10)
		return page
	shutdown.exposed = True

	def restart(self):
		cherrystrap.SIGNAL = 'restart'
		message = 'restarting ...'
		return serve_template(templatename="shutdown.html", title="Restart", message=message, timer=10)
	restart.exposed = True