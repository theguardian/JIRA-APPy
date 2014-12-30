JIRA-APPy
=========

Pronounced "JIRA A.P.Py" - A python-based WebApp to interact with JIRA's API. Leverages CherryStrap framework.

This program is intended to be used by a single JIRA Administrator with administrator-level global permissions in JIRA. 
When logging in via OAuth, token/secret credentials are stored for the user currently logged into JIRA in the same 
desktop environment. For that reason, a username/password combination is recommended for access to this WebApp.

## Why?
JIRA has a fairly [comprehensive API](https://docs.atlassian.com/jira/REST/latest/) that can perform a great many functions. 
Instead of installing dozens(!) of small add-ons that perform very specific functions or writing your own add-ons, 
it often makes sense to make use of the API instead. It keeps your JIRA install clean, and the API can be utilized 
1:1 for OnDemand or Server instances. For example...
* You want to click a single button to generate multiple issues according to a template you define
* You want to bulk-process issues according to your own algorithms.  Blue Sky.
* You want to automate API tasks on a schedule. Cron +.
* You want an action in JIRA to fire another action that you can custom define (Webhooks / Listeners)

Many of these features don't yet exist, but with a proper framework in place - further development should be fairly
straightforward.

## Backend Features
* WebApp framework in place (CherryPy + Mako Templates + Bootstrap = CherryStrap)
* Python packages / libraries included so user-installed dependencies are few
* Restart/Shutdown the WebApp from UI
* https:// (SSL) option
* Configuration form for JIRA integration complete (no hardcode)

## Frontend Features
This software is in very early stages of development, so the feature list is fairly short for now.
* Easy OAuth login/logout with JIRA when integration successfully configured
* Reindex (currently errors in Status Code 415 - see the [Issues](https://github.com/theguardian/JIRA-APPy/issues) list)
* Bulk Delete Worklogs

## Developers
If you're a WebApp developer familiar with Python, we would love for you to contribute! The framework and handshaking
are already in place, so it's really just a matter of seeing how existing functions are implemented and writing your own.

If you simply want to add Frontend Features, the easiest way to do so is in the following two files:
* /cherrystrap/WebServe.py => python algorithms to process API calls/returns
* /data/interfaces/default/*.html => HTML to display I/O for algorithms

# Installation & Configuration
## Required Dependencies
1. Python 2.7
2. OpenSSL to generate RSA private and public keys

## Optional Dependencies (if enabling https://)
1. pyOpenSSL required if you would like JIRA-APPy to auto-generate a self-signed certificate
2. Alternatively, you may choose to install your own self-signed SSL certificate. [This guide](https://www.digitalocean.com/community/tutorials/how-to-create-a-ssl-certificate-on-nginx-for-ubuntu-12-04) should set you on the right path.

## Initial Setup
1. `git clone https://github.com/theguardian/JIRA-APPy`
2. `cd JIRA-APPy`
3. Generate RSA private and public keys on the server where JIRA-APPy is located
	* `mkdir keys`
	* `cd keys`
	* `openssl genrsa -out RSA.pem 1024`
	* `openssl rsa -in RSA.pem -pubout -out RSA.pub`
4. `python JIRA-APPy.py` (use `sudo` if running on Port 80 or 443)
	* Runs in foreground. To run as daemon, append flag `--daemon`
5. Visit http://YOUR.SERVER.IP.ADDRESS:7889 though any browser
6. Click 'Config -> Configuration'
	* Give your instance a name
	* Set an absolute path for the log file if you wish
	* Change the port number if you wish
	* If https:// is enabled, change to Port 443
	* If you generated your own SSL certificate, point the HTTPS Key and HTTPS Cert fields towards the relative path where these files are located, 
	or move the keys to JIRA-APPy/keys
	* Give your site a username and password
	* Populate `Consumer Key` with text (this is your unique identifier to handshake with JIRA later)
	* Populate `Consumer Secret` with text (the contents don't matter)
	* Populate `JIRA Base URL` with the URL to your JIRA instance (don't forget http:// or https://!)
7. Click 'Config -> Restart' to load changes
	* If you changed the port number, remember to visit the new URL
	* If you changed to port 80 or 443, restart will fail (see Step #4)

## Configuring JIRA
1. In JIRA's navbar, click the cog wheel and choose `Add-Ons`. Click `Application Links`
2. In the `Application` field, enter the base URL for JIRA-APPy and click `Create New Link`
3. A `Link Applications` modal will pop up
	* Give your Application a name, and declare it a 'Generic Application'
	* Leave everything else blank and click `Continue` (Communication is currently one-way only)
4. Your Application Link should now be listed.  Click `Edit`. Click `Incoming Authentication` in the modal
	* Enter the `Consumer Key` from Step #6 of Initial Setup
	* Enter some text in `Consumer Name` (the contents don't particularly matter - call it JIRA-APPy)
	* Copy the contents of RSA.pub that was generated in Step #3 of Initial Setup and paste it in `Public Key`
	* Enter the base URL for JIRA-APPy in the `Consumer Callback URL` field

## Handshaking
1. Go back to JIRA-APPpy and click `Login with JIRA`. Allow the link on the redirect page. You should receive confirmation that
handshake was a success!
2. If you receive any errors, check the JIRA-APPy log file

# License
GNU General Public License, v2.  Free to use, distribute and modify for all purposes.  See LICENSE file for more information. 