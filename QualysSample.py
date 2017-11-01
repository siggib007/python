'''
Qualys API Sample Script
Author Siggi Bjarnason Copyright 2017
Website http://www.ipcalc.us/ and http://www.icecomputing.com

Description:
This is script where I start to explore Qualys API calls, parsing the XML responses, etc.

Following packages need to be installed as administrator
pip install requests
pip install xmltodict

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
import xmltodict
# End imports

if os.path.isfile("QSInput.txt"):
	print ("Configuration File exists")
else:
	print ("Can't find configuration file QSInput.txt, make sure it is the same directory as this script")
	sys.exit(4)

strLine = "  "
print ("Reading in configuration")
objINIFile = open("QSInput.txt","r")
strLines = objINIFile.readlines()
objINIFile.close()

for strLine in strLines:
	strLine = strLine.strip()
	if "=" in strLine:
		strConfParts = strLine.split("=")
		if strConfParts[0] == "APIBaseURL":
			strBaseURL = strConfParts[1]
			print ("Found {}".format(strLine))
		if strConfParts[0] == "APIRequestHeader":
			strHeadReq = strConfParts[1]
			print ("Found {}".format(strLine))
		if strConfParts[0] == "ShowNumDays":
			iNumDays = int(strConfParts[1])
			print ("Found {}".format(strLine))
		if strConfParts[0] == "ShowStartTime":
			strTimeLastNight = str(strConfParts[1])
			print ("Found {}".format(strLine))
		if strConfParts[0] == "QUserID":
			strUserName = strConfParts[1]
			print ("Found {}".format(strLine))
		if strConfParts[0] == "QUserPWD":
			strPWD = strConfParts[1]
			print ("Found {}".format(strLine))


strHeader={'X-Requested-With': strHeadReq}
strScanAPI = "api/2.0/fo/scan/?"
iSecInDays = 86400
iSecDays = iSecInDays * iNumDays

timeNow = time.localtime(time.time())
iGMT_offset = timeNow.tm_gmtoff
iErrCode = ""
iErrText = ""

def getInput(strPrompt):
    if sys.version_info[0] > 2 :
        return input(strPrompt)
    else:
        return raw_input(strPrompt)
# end getInput

timeLastNightLocal = time.strftime("%Y-%m-%d",time.localtime(time.time()-iSecDays)) + " " + strTimeLastNight
timeLastNightGMT = time.localtime(time.mktime(time.strptime(timeLastNightLocal,"%Y-%m-%d %H:%M"))-iGMT_offset)
strQualysTime = time.strftime("%Y-%m-%dT%H:%M:%SZ",timeLastNightGMT)

DefUserName = getpass.getuser()
print ("This is a Qualys API Sample script. Your windows username is {3}. This is running under Python Version {0}.{1}.{2}".format(sys.version_info[0],sys.version_info[1],sys.version_info[2],DefUserName))
now = time.asctime()
print ("The time now is {}".format(now))
# strUserName = getInput("Please provide your Qualys username: ")
# if strUserName == "":
# 	print ("no username, exiting")
# 	sys.exit(5)

# strPWD = getpass.getpass(prompt="what is the password for {0}: ".format(strUserName))
# if strPWD == "":
# 	print ("empty password, exiting")
# 	sys.exit(5)


strListScans = "action=list&user_login={}&launched_after_datetime={}".format(strUserName,strQualysTime)
strURL = strBaseURL + strScanAPI + strListScans
print ("Doing a get to URL: {}".format(strURL))
try:
	WebRequest = requests.get(strURL, headers=strHeader, auth=(strUserName, strPWD))
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
dictResponse = xmltodict.parse(WebRequest.text)
if isinstance(dictResponse,dict):
	if "SIMPLE_RETURN" in dictResponse:
		try:
			if "CODE" in dictResponse["SIMPLE_RETURN"]["RESPONSE"]:
				iErrCode = dictResponse["SIMPLE_RETURN"]["RESPONSE"]["CODE"]
				iErrText = dictResponse["SIMPLE_RETURN"]["RESPONSE"]["TEXT"]
		except KeyError as e:
			print ("KeyError: {}".format(e))
			print (WebRequest.text)
			iErrCode = "Unknown"
			iErrText = "Unexpected error"
	else:
		print (WebRequest.text)
else:
	print ("Response not a dictionary")

if iErrCode != "" or WebRequest.status_code !=200:
	print ("There was a problem with your request. HTTP error {} code {} {}".format(WebRequest.status_code,iErrCode,iErrText))

# print ("Dict Response: \n {}".format(dictResponse))
# print ("Root Node: {}".format(root.tag))
# for node in root.iter():
#     print ("{} : {}".format(node.tag, node.text))
if root.tag == "SIMPLE_RETURN" and WebRequest.status_code !=200:
	print ("Error {} Code {} : {}".format(WebRequest.status_code, root[0][1].text,root[0][2].text))
else:
	print (WebRequest.text)