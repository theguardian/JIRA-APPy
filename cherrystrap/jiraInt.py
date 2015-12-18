import os
import cherrystrap
from lib import simplejson as json
from cherrystrap import logger, formatter, backend

def reindex(action=None):
    status, msg = '', ''

    consumer, client = backend.stored_oauth()

    if action=='POST':
        data_url = os.path.join(cherrystrap.JIRA_BASE_URL, 'rest/api/2/reindex?type=BACKGROUND&indexComments=true&indexChangeHistory=true')
        try:
            resp, content = client.request(data_url, "POST")
            if resp['status'] != '202':
                status, msg = backend.ajaxMSG('failure', 'Call for JIRA Reindex failed with status code '+resp['status'])
            else:
                status, msg = backend.ajaxMSG('success', 'JIRA is now reindexing')
        except:
            status, msg = backend.ajaxMSG('failure', 'Could not connect to '+data_url)

    elif action=='GET':
        data_url = os.path.join(cherrystrap.JIRA_BASE_URL, 'rest/api/2/reindex')
        try:
            resp, content = client.request(data_url, "GET")
            if resp['status'] != '200':
                status, msg = backend.ajaxMSG('failure', 'Call for JIRA Reindex status failed with status code '+resp['status'])
            else:
                resp_dict = json.loads(content)
                currentProgress = resp_dict['currentProgress']
                status, msg = backend.ajaxMSG('success', 'JIRA reindex is '+str(currentProgress)+'% complete')
        except:
            status, msg = backend.ajaxMSG('failure', 'Could not connect to '+data_url)

    else:
        pass

    return status, msg

def bulkDeleteWorklogs(issue_list=None):
    status, msg = '', ''

    consumer, client = backend.stored_oauth()

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
                    status, msg = backend.ajaxMSG('success', '%d worklog(s) have been deleted for %d issues' % (num_worklogs, num_issues))
                else:
                    logger.info("No worklogs found for issue %s" % issue)
        except:
            logger.warn("Could not connect to %s" % data_url)

    return status, msg
