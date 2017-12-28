# Import libraries
import sys
import requests
import os
import time
import xmltodict
import urllib.parse as urlparse
# End imports

strConf_File = "QSInput.ini"


def isInt (CheckValue):
	# function to safely check if a value can be interpreded as an int
	if isinstance(CheckValue,int):
		return True
	elif isinstance(CheckValue,str):
		if CheckValue.isnumeric():
			return True
		else:
			return False
	else:
		return False


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

if os.path.isfile(strConf_File):
	print ("Configuration File exists")
else:
	print ("Can't find configuration file QSInput.ini, make sure it is the same directory as this script")
	sys.exit(4)

strLine = "  "
print ("Reading in configuration")
objINIFile = open(strConf_File,"r")
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
			if isInt(strConfParts[1]):
				iNumDays = int(strConfParts[1])
			else:
				print ("Invalid value: {}".format(strLine))
				sys.exit(5)
		if strConfParts[0] == "ShowStartTime":
			strTimeLastNight = str(strConfParts[1])
		if strConfParts[0] == "QUserID":
			strUserName = strConfParts[1]
		if strConfParts[0] == "QUserPWD":
			strPWD = strConfParts[1]
		if strConfParts[0] == "FilterByUser":
			strFilterUser = strConfParts[1]
		if strConfParts[0] == "SecondsBeetweenChecks":
			if isInt(strConfParts[1]):
				iSecSleep = int(strConfParts[1])
			else:
				print ("Invalid value: {}".format(strLine))
				sys.exit(5)
		if strConfParts[0] == "ReportSaveLocation":
			strSaveLoc = strConfParts[1]

def isInt (CheckValue):
	# function to safely check if a value can be interpreded as an int
	if isinstance(CheckValue,int):
		return True
	elif isinstance(CheckValue,str):
		if CheckValue.isnumeric():
			return True
		else:
			return False
	else:
		return False

strFileDT = time.strftime("%m-%d-%Y-%H-%M")
if strSaveLoc[-1:] != "\\":
	strSaveLoc += "\\"
strOutFile = "{}Qualys Report {} {}".format(strSaveLoc,strSearchCrit,strFileDT)
strOutFile += ".csv"
print (strOutFile)