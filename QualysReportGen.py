'''
Qualys API Sample Script
Author Siggi Bjarnason Copyright 2017
Website http://www.ipcalc.us/ and http://www.icecomputing.com

Description:
This is script will search for scans launched by certain user, during certain time period, who's name matches supplied keyword
and will generate a Qualys Scan based Template report in CSV format. The CSV will be based on template "PROJECT - Technical Report (Scan Based)"

Following packages need to be installed as administrator from a windows command line.
pip install requests
pip install xmltodict

'''
# Import libraries
import sys
import requests
import os
import time
import xmltodict
import urllib.parse as urlparse
# End imports

print ("This is a Qualys Scan Report generator. This is running under Python Version {0}.{1}.{2}".format(sys.version_info[0],sys.version_info[1],sys.version_info[2]))
now = time.asctime()
print ("The time now is {}".format(now))
sa = sys.argv
lsa = len(sys.argv)
if lsa > 1:
	strSearchCrit = sa[1]
else:
	print ("Project keyword was not provided and is required to continue. Project keyword can be partial but unique string.\n REQ1234 and 1234 are both acceptable.")
	strSearchCrit = input("Please provide project keyword: ")

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
		if strConfParts[0] == "APIRequestHeader":
			strHeadReq = strConfParts[1]
		if strConfParts[0] == "ShowNumDays":
			iNumDays = int(strConfParts[1])
		if strConfParts[0] == "ShowStartTime":
			strTimeLastNight = str(strConfParts[1])
		if strConfParts[0] == "QUserID":
			strUserName = strConfParts[1]
		if strConfParts[0] == "QUserPWD":
			strPWD = strConfParts[1]
		if strConfParts[0] == "FilterByUser":
			strFilterUser = strConfParts[1]
		if strConfParts[0] == "SecondsBeetweenChecks":
			iSecSleep = int(strConfParts[1])


def MakeAPICall (strURL, strHeader, strUserName,strPWD, strMethod):

	iErrCode = ""
	iErrText = ""

	try:
		if strMethod.lower() == "get":
			WebRequest = requests.get(strURL, headers=strHeader, auth=(strUserName, strPWD))
		if strMethod.lower() == "post":
			WebRequest = requests.post(strURL, headers=strHeader, auth=(strUserName, strPWD))
	except Exception as err:
		print ("Issue with API call. {}".format(err))
		sys.exit(7)
	# end try

	if isinstance(WebRequest,requests.models.Response)==False:
		print ("response is unknown type")
		sys.exit(5)
	# end if

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
		print ("Response not a dictionary")
		sys.exit(8)

	if iErrCode != "" or WebRequest.status_code !=200:
		return "There was a problem with your request. HTTP error {} code {} {}".format(WebRequest.status_code,iErrCode,iErrText)
	else:
		return dictResponse

def LaunchReport (strTitle,strScanRef):
	strNow = strLastNight = time.strftime("%m/%d/%Y %H:%M")
	strAPIFunction = "api/2.0/fo/report/?"
	dictParams.clear()
	dictParams["action"] = "launch"
	dictParams["template_id"] = 895325
	dictParams["report_title"] = strTitle + " " + strNow
	dictParams["output_format"] = "csv"
	dictParams["report_refs"] = strScanRef
	strListScans = urlparse.urlencode(dictParams)

	strURL = strBaseURL + strAPIFunction + strListScans

	APIResponse = MakeAPICall(strURL,strHeader,strUserName,strPWD,"post")
	if isinstance(APIResponse,str):
		print(APIResponse)
		return "Errror: {}".format(APIResponse)
	if isinstance(APIResponse,dict):
		if "ITEM_LIST" in APIResponse["SIMPLE_RETURN"]["RESPONSE"]:
			print ("{} for {}".format(APIResponse["SIMPLE_RETURN"]["RESPONSE"]["TEXT"],strTitle))
			# print ("report ID: {}".format(APIResponse["SIMPLE_RETURN"]["RESPONSE"]["ITEM_LIST"]["ITEM"]["VALUE"]))
			return APIResponse["SIMPLE_RETURN"]["RESPONSE"]["ITEM_LIST"]["ITEM"]["VALUE"]
		else:
			# print (APIResponse["SIMPLE_RETURN"]["RESPONSE"]["TEXT"])
			return "Errror: {}".format(APIResponse["SIMPLE_RETURN"]["RESPONSE"]["TEXT"])

def GetReportStatus (strReportID):
	dictResponse ={}
	dictParams.clear()
	dictParams["action"] = "list"
	dictParams["id"] = strReportID
	strListScans = urlparse.urlencode(dictParams)
	strAPIFunction = "api/2.0/fo/report/?"
	strURL = strBaseURL + strAPIFunction + strListScans

	APIResponse = MakeAPICall(strURL,strHeader,strUserName,strPWD,"Get")
	if isinstance(APIResponse,str):
		print(APIResponse)
		return "Errror: {}".format(APIResponse)
	if isinstance(APIResponse,dict):
		if "REPORT_LIST" in APIResponse["REPORT_LIST_OUTPUT"]["RESPONSE"]:
			if "REPORT" in APIResponse["REPORT_LIST_OUTPUT"]["RESPONSE"]["REPORT_LIST"]:
				if "SIZE" in APIResponse["REPORT_LIST_OUTPUT"]["RESPONSE"]["REPORT_LIST"]["REPORT"]:
					dictResponse["size"]=APIResponse["REPORT_LIST_OUTPUT"]["RESPONSE"]["REPORT_LIST"]["REPORT"]["SIZE"]
				if "STATUS" in APIResponse["REPORT_LIST_OUTPUT"]["RESPONSE"]["REPORT_LIST"]["REPORT"]:
					dictResponse["state"]=APIResponse["REPORT_LIST_OUTPUT"]["RESPONSE"]["REPORT_LIST"]["REPORT"]["STATUS"]["STATE"]
					print ("Current state of report ID {} is {}".format(strReportID,dictResponse["state"]))
					if dictResponse["state"] != "Finished":
						dictResponse["msg"]=APIResponse["REPORT_LIST_OUTPUT"]["RESPONSE"]["REPORT_LIST"]["REPORT"]["STATUS"]["MESSAGE"]
						dictResponse["perc"]=APIResponse["REPORT_LIST_OUTPUT"]["RESPONSE"]["REPORT_LIST"]["REPORT"]["STATUS"]["PERCENT"]
						print ("{} {}% complete".format(dictResponse["msg"],dictResponse["perc"]))
	return dictResponse

print ("calculating stuff ...")
strHeader={'X-Requested-With': strHeadReq}
iSecInDays = 86400
iSecDays = iSecInDays * iNumDays

timeNow = time.localtime(time.time())
iGMT_offset = timeNow.tm_gmtoff

timeLastNightLocal = time.strftime("%Y-%m-%d",time.localtime(time.time()-iSecDays)) + " " + strTimeLastNight
timeLastNightGMT = time.localtime(time.mktime(time.strptime(timeLastNightLocal,"%Y-%m-%d %H:%M"))-iGMT_offset)
strQualysTime = time.strftime("%Y-%m-%dT%H:%M:%SZ",timeLastNightGMT)
strLastNight = time.strftime("%m/%d/%Y %H:%M %Z",time.localtime(time.mktime(time.strptime(timeLastNightLocal,"%Y-%m-%d %H:%M"))))
dictParams = {}
listReportIDs = []

strAPIFunction = "api/2.0/fo/scan/?"
dictParams.clear()
dictParams["action"] = "list"
dictParams["user_login"] = strFilterUser
dictParams["launched_after_datetime"] = strQualysTime
strListScans = urlparse.urlencode(dictParams)

strURL = strBaseURL + strAPIFunction + strListScans

APIResponse = MakeAPICall(strURL,strHeader,strUserName,strPWD,"Get")
if isinstance(APIResponse,str):
	print(APIResponse)
if isinstance(APIResponse,dict):
	if "SCAN_LIST" in APIResponse["SCAN_LIST_OUTPUT"]["RESPONSE"]:
		print ("Here are the scans since {}".format(strLastNight))
		for scan in APIResponse["SCAN_LIST_OUTPUT"]["RESPONSE"]["SCAN_LIST"]["SCAN"]:
			print ("Title: {} Ref: {}".format(scan["TITLE"],scan["REF"]))
			if strSearchCrit in scan["TITLE"]:
				print ("  matches {}".format(strSearchCrit))
				strReportID=LaunchReport(scan["TITLE"],scan["REF"])
				listReportIDs.append(strReportID)
				print ("Report ID: {}".format(strReportID))
			else:
				print ("  does not match {}".format(strSearchCrit))
	else:
		print ("There are no scans since {}".format(strLastNight))

# print ("Giving the reports {} seconds to generate.".format(iSecSleep))
# time.sleep(iSecSleep)
print ("Now checking the status of those reports...")
dictTemp = {}
bFinished = False
while not bFinished:
	bFinished = True
	for strReportID in listReportIDs:
		print ("Checking status on report ID {}".format(strReportID))
		if strReportID in dictTemp:
			if "state" in dictTemp[strReportID]:
				if dictTemp[strReportID]["state"] == "Running" :
					dictTemp[strReportID] = GetReportStatus(strReportID)
		else:
			dictTemp[strReportID] = GetReportStatus(strReportID)
		if isinstance(dictTemp[strReportID],str):
			strError = dictTemp[strReportID]
			dictTemp[strReportID]={"state":"Error","msg":strError}
			print("{} \n exiting !!!".format(dictTemp[strReportID]))
			break
		if isinstance(dictTemp[strReportID],dict):
			if not dictTemp[strReportID]:
				print ("Received an empty reponse when checking on report {}".format(strReportID))
				dictTemp[strReportID]["state"]="Error"
				dictTemp[strReportID]["msg"]="Empty response from report list"
				bFinished = False
			if "state" in dictTemp[strReportID]:
				if dictTemp[strReportID]["state"] == "Running":
					bFinished = False
				if dictTemp[strReportID]["state"] == "Finished" and "report" not in dictTemp[strReportID] :
					print ("pretending to download completed report ID {}".format(strReportID))
					dictTemp[strReportID]["report"] = "fake report"
			else:
				bFinished = False
	if isinstance(dictTemp,str):
		print ("exiting due to error when checking on report")
		break
	if not bFinished:
		print ("Waiting for all reports to complete, checking again in {} seconds".format(iSecSleep))
		time.sleep(iSecSleep)
