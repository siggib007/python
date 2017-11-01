'''
Qualys API Sample Script
Author Siggi Bjarnason Copyright 2017
Website http://www.ipcalc.us/ and http://www.icecomputing.com

Description:
This is script where I start to explore Qualys API calls, parsing the XML responses, etc.

Following packages need to be installed as administrator
pip install requests

'''
# Import libraries
import sys
import requests
import json
import os
import string
import getpass
import time
import xml.etree.ElementTree as ET
# End imports

strBaseURL="https://qualysapi.qg2.apps.qualys.com/"
strHeader={'X-Requested-With': 'VMAS'}
strScanAPI = "api/2.0/fo/scan/?"

strTimeLastNight = " 22:00"
timeNow = time.localtime(time.time())
iGMT_offset = timeNow.tm_gmtoff

def getInput(strPrompt):
    if sys.version_info[0] > 2 :
        return input(strPrompt)
    else:
        return raw_input(strPrompt)
# end getInput

timeLastNightLocal = time.strftime("%Y-%m-%d",time.localtime(time.time()-86400)) + strTimeLastNight
timeLastNightGMT = time.localtime(time.mktime(time.strptime(timeLastNightLocal,"%Y-%m-%d %H:%M"))-iGMT_offset)
strQualysTime = time.strftime("%Y-%m-%dT%H:%M:%SZ",timeLastNightGMT)

DefUserName = getpass.getuser()
print ("This is a Qualys API Sample script. Your windows username is {3}. This is running under Python Version {0}.{1}.{2}".format(sys.version_info[0],sys.version_info[1],sys.version_info[2],DefUserName))
now = time.asctime()
print ("The time now is {}".format(now))
strUserName = getInput("Please provide your Qualys username: ")
if strUserName == "":
	print ("no username, exiting")
	sys.exit(5)

strPWD = getpass.getpass(prompt="what is the password for {0}: ".format(strUserName))
if strPWD == "":
	print ("empty password, exiting")
	sys.exit(5)


strListScans = "action=list&user_login={}&launched_after_datetime={}".format(strUserName,strQualysTime)
strURL = strBaseURL + strScanAPI + strListScans
print ("Doing a get to URL: {}".format(strURL))
try:
	WebRequest = requests.get(strURL, headers=strHeader)
except:
	print ("Failed to connect to Qualys")
# end try
if WebRequest.status_code !=200:
	print ("Request response error code " + str(WebRequest.status_code))
if isinstance(WebRequest,requests.models.Response)==False:
	print ("response is unknown type")
# end if

# print (WebRequest.text)
try:
	root = ET.fromstring(WebRequest.text)
	# print (WebRequest.text)
except:
	print ("Failed to decode the response")
# end try

print ("Root Node: ".format(root.tag))
# for node in root.iter():
#     print ("{} : {}".format(node.tag, node.text))
if root.tag == "SIMPLE_RETURN" and WebRequest.status_code !=200:
	print ("Error {} Code {} : {}".format(WebRequest.status_code, root[0][1].text,root[0][2].text))
else:
	print (WebRequest.text)