'''
Router Audit
Author Siggi Bjarnason Copyright 2017
Website http://www.ipcalc.us/ and http://www.icecomputing.com

Description:
This is script that will discover all the BGP peers on a particular Cisco Router running
and caputer all the routes being received over each peer.

Following packages need to be installed as administrator
pip install pypiwin32
pip install paramiko
pip install playsound
pip install pymysql

'''

strSummarySheet = "BGP Summary"
strDetailSheet  = "By Router"
strPrefixeSheet = "By Prefix"
iMaxError = 6 # How many times can we experience an error on a single device before marking the device failed and moving on, 0 based
iMaxAuthFail = 2 # How many auth failures can happen in a row. Zero based.
dictBaseCmd = {
		"IOS-XR":{
			"Match":"IOS XR",
			"IPv4-GT-Summary":"show bgp ipv4 unicast summary",
			"IPv4-VRF-Summary":"show bgp vrf {} ipv4 unicast summary",
			"IPv4-GT-Advertise":"show bgp ipv4 unicast neighbors {} routes",
			"IPv4-VRF-Advertise":"show bgp vrf {} ipv4 unicast neighbors {} routes",
			"IPv4-GT-Description":"show bgp ipv4 unicast neighbors {} | include Description:",
			"IPv4-VRF-Description":"show bgp vrf {} ipv4 unicast neighbors {} | include Description:",
			"IPv6-GT-Summary":"show bgp ipv6 unicast summary",
			"IPv6-VRF-Summary":"show bgp vrf {} ipv6 unicast summary",
			"IPv6-GT-Advertise":"show bgp ipv6 unicast neighbors {} routes",
			"IPv6-VRF-Advertise":"show bgp vrf {} ipv6 unicast neighbors {} routes",
			"IPv6-GT-Description":"show bgp ipv6 unicast neighbors {} | include Description:",
			"IPv6-VRF-Description":"show bgp vrf {} ipv6 unicast neighbors {} | include Description:",
			"shVRF":"show vrf all"
		},
		"IOS-XE":{
			"Match":"IOS XE",
			"IPv4-GT-Summary":"show bgp ipv4 unicast summary",
			"IPv4-VRF-Summary":"show bgp vrf {} vpnv4 unicast summary",
			"IPv4-GT-Advertise":"show bgp ipv4 unicast neighbors {} routes",
			"IPv4-VRF-Advertise":"show bgp vrf {} vpnv4 unicast neighbors {} routes",
			"IPv4-GT-Description":"show bgp ipv4 unicast neighbors {} | include Description:",
			"IPv4-VRF-Description":"show bgp vrf {} vpnv4 unicast neighbors {} | include Description:",
			"IPv6-GT-Summary":"show bgp ipv6 unicast summary",
			"IPv6-VRF-Summary":"show bgp vrf {} vpnv6 unicast summary",
			"IPv6-GT-Advertise":"show bgp ipv6 unicast neighbors {} routes",
			"IPv6-VRF-Advertise":"show bgp vrf {} vpnv4 unicast neighbors {} routes",
			"IPv6-GT-Description":"show bgp ipv6 unicast neighbors {} | include Description:",
			"IPv6-VRF-Description":"show bgp vrf {} vpnv4 unicast neighbors {} | include Description:",
			"shVRF":"show vrf brief"
		}
	}

def CollectVRFs():
	strOut = ValidateRetry(strHostname,dictBaseCmd[strHostVer]["shVRF"])
	strOutputList = strOut.splitlines()
	bInSection = False
	lstVRFs = []
	LogEntry ("There are {} lines in the show vrf output".format(len(strOutputList)))
	for strLine in strOutputList:
		if "Exception:" in strLine:
			bFoundABFACL = True
			LogEntry ("Found an exception message, aborting analysis")
			break
		if len(strLine) > 0:
			if strLine[0] == "%":
				LogEntry ("Error: {}".format(strLine))
				break
		strLineTokens = strLine.split()
		if len(strLineTokens) > 1:
				if strHostVer == "IOS-XR":
					if bInSection and strLineTokens[0] != "import" and strLineTokens[0] != "export" and "not set" not in strLine:
						lstVRFs.append(strLineTokens[0])
					if strLineTokens[0]== "VRF" and strLineTokens[1]== "RD" and strLineTokens[2]== "RT":
						bInSection = True
				if strHostVer == "IOS-XE":
					if bInSection and "not set" not in strLine:
						lstVRFs.append(strLineTokens[0])
					if strLineTokens[0]== "Name" and strLineTokens[1]== "Default" and strLineTokens[2]== "RD":
						bInSection = True
	LogEntry ("VRF's Collected: {}".format(lstVRFs))
	return lstVRFs

def AnalyzeIPv4Results(strOutputList, strVRF):
	global iOutLineNum
	dictIPv4Peers = {}
	bNeighborSection = False

	LogEntry ("There are {} lines in the show bgp IPv4 summary output".format(len(strOutputList)))
	for strLine in strOutputList:
		if "Exception:" in strLine:
			bFoundABFACL = True
			LogEntry ("Found an exception message, aborting analysis")
			break
		if len(strLine) > 0:
			if strLine[0] == "%":
				LogEntry ("Error: {}".format(strLine))
				break
		strLineTokens = strLine.split()
		if strHostVer == "IOS-XR" or strHostVer == "IOS-XE":
			if "local AS number " in strLine:
				iLoc = strLine.find("number ")+7
				iLocalAS = strLine[iLoc:]
			if len(strLineTokens) > 1:
				if bNeighborSection:
					if len(strLineTokens) > 8:
						iRemoteAS = strLineTokens[2]
						strCount = str(strLineTokens[9])
						strPeerIP = strLineTokens[0]
						if iRemoteAS != iLocalAS and strCount != "Idle" and strCount != "Active" :
							strSQL = ("INSERT INTO networks.tblneighbors (iRouterID,vcNeighborIP,iRemoteAS,vcVRF,iRcvdCount)"
								" VALUES ({0},'{1}',{2},'{3}',{4});".format(iHostID,strPeerIP,iRemoteAS,strVRF,strCount))
							# print (strSQL)
							lstReturn = SQLQuery (strSQL,dbConn)
							if not ValidReturn(lstReturn):
								print ("Unexpected: {}".format(lstReturn))
							elif lstReturn[0] != 1:
								print ("Records affected {}, expected 1 record affected".format(lstReturn[0]))

							dictIPv4Peers[strPeerIP] = {"VRF":strVRF,"LineID":iOutLineNum}

				if strLineTokens[0]== "Neighbor":
					bNeighborSection = True
			else:
				bNeighborSection = False

	return dictIPv4Peers

# end function AnalyzeIPv4Results

def AnalyzeIPv6Results(strOutputList, strVRF):
	global iOutLineNum
	dictPeers = {}
	bNeighborSection = False
	strPeerIP = ""

	LogEntry ("There are {} lines in the show bgp IPv6 summary output".format(len(strOutputList)))
	for strLine in strOutputList:
		if "Exception:" in strLine:
			bFoundABFACL = True
			LogEntry ("Found an exception message, aborting analysis")
			break
		if len(strLine) > 0:
			if strLine[0] == "%":
				LogEntry ("Error: {}".format(strLine))
				break

		strLineTokens = strLine.split()
		if strHostVer == "IOS-XR" or strHostVer == "IOS-XE":
			if "local AS number " in strLine:
				iLoc = strLine.find("number ")+7
				iLocalAS = strLine[iLoc:]
			if len(strLineTokens) > 0:
				if bNeighborSection:
					if strLineTokens[0].find(":") == 4:
						strPeerIP = strLineTokens[0]
						bLine2 = False
					else:
						bLine2 = True
					if len(strLineTokens) > 8:
						if bLine2:
							iRemoteAS = strLineTokens[1]
							strCount = str(strLineTokens[8])
						else:
							iRemoteAS = strLineTokens[2]
							strCount = str(strLineTokens[9])
						if iRemoteAS != iLocalAS and strCount != "Idle" and strCount != "Active" and strPeerIP != "":
							strSQL = ("INSERT INTO networks.tblneighbors (iRouterID,vcNeighborIP,iRemoteAS,vcVRF,iRcvdCount)"
								" VALUES ({0},'{1}',{2},'{3}',{4});".format(iHostID,strPeerIP,iRemoteAS,strVRF,strCount))
							lstReturn = SQLQuery (strSQL,dbConn)
							if not ValidReturn(lstReturn):
								print ("Unexpected: {}".format(lstReturn))
							elif lstReturn[0] != 1:
								print ("Records affected {}, expected 1 record affected".format(lstReturn[0]))
							dictPeers[strPeerIP] = {"VRF":strVRF,"LineID":iOutLineNum}
				if strLineTokens[0]== "Neighbor":
					bNeighborSection = True
			else:
				bNeighborSection = False

	return dictPeers
# end function AnalyzeIPv6Results

def AnalyzeIPv4Routes(strOutList,strVRF,strPeerIP,strHostname,strDescr,iLineNum):
	global iOut2Line
	global dictPrefixes
	bInSection = False
	iStartLine = iOut2Line

	strSQL = "select iNeighborID from networks.tblneighbors where vcNeighborIP = '{}'".format(strPeerIP)
	lstReturn = SQLQuery (strSQL,dbConn)
	if not ValidReturn(lstReturn):
		print ("Unexpected: {}".format(lstReturn))
		return lstReturn
	elif lstReturn[0] != 1:
		print ("Records affected {}, expected 1 record affected".format(lstReturn[0]))
		# return lstReturn
	else:
		iNeighborID = lstReturn[1][0][0]
	strSQL = "update networks.tblneighbors set vcDescription = '{}' where iNeighborID = {}".format(strDescr,iNeighborID)
	lstReturn = SQLQuery (strSQL,dbConn)
	if not ValidReturn(lstReturn):
		print ("Unexpected: {}".format(lstReturn))
	elif lstReturn[0] != 1:
		print ("Records affected {}, expected 1 record affected".format(lstReturn[0]))

	LogEntry ("Analyzing received IPv4 routes. There are {} lines in the output".format(len(strOutList)))
	if len(strOutList) > 0:
		if "Exception:" in strOutList[0]:
			bFoundABFACL = True
			LogEntry ("Found an exception message, aborting analysis")
			return
	for strLine in strOutList:
		if len(strLine) > 0:
			if strLine[0] == "%":
				LogEntry ("Error: {}".format(strLine))
				break
		strLineTokens = strLine.split()
		iCurLine = iOut2Line - iStartLine + 1
		if iCurLine%500 == 0:
			print ("Completed  {:.1%}".format(iCurLine/len(strOutList)))
		if strHostVer == "IOS-XR":
			if len(strLineTokens) > 1:
				if bInSection and strLineTokens[0] != "Route"  and strLineTokens[0] != "Processed":
					strRcvdPrefix = strLineTokens[1]
					strSQL = ("INSERT INTO networks.tblsubnets (iNeighborID,vcSubnet,vcIPver)"
						" VALUES ({0},'{1}','{2}');".format(iNeighborID,strRcvdPrefix,"IPv4"))
					lstReturn = SQLQuery (strSQL,dbConn)
					if not ValidReturn(lstReturn):
						print ("Unexpected: {}".format(lstReturn))
					elif lstReturn[0] != 1:
						print ("Records affected {}, expected 1 record affected".format(lstReturn[0]))
					strRouterVRFPeer = strHostname + "-" + strVRF + "-" + strPeerIP
					if strRcvdPrefix in dictPrefixes:
						dictPrefixes[strRcvdPrefix]["Peer"].append(strRouterVRFPeer)
						if strVRF not in dictPrefixes[strRcvdPrefix]["VRF"]:
							dictPrefixes[strRcvdPrefix]["VRF"].append(strVRF)
					else:
						dictPrefixes[strRcvdPrefix]={"VRF":[strVRF],"Peer":[strRouterVRFPeer]}
				if strLineTokens[0] == "Network":
					bInSection = True
		if strHostVer == "IOS-XE":
			if len(strLineTokens) > 1:
				if bInSection and strLineTokens[0] != "Total" and strLineTokens[0] != "Network" and strLineTokens[1].count(".") == 3 :
					strRcvdPrefix = strLineTokens[1]
					strSQL = ("INSERT INTO networks.tblsubnets (iNeighborID,vcSubnet,vcIPver)"
						" VALUES ({0},'{1}','{2}');".format(iNeighborID,strRcvdPrefix,"IPv4"))
					lstReturn = SQLQuery (strSQL,dbConn)
					if not ValidReturn(lstReturn):
						print ("Unexpected: {}".format(lstReturn))
					elif lstReturn[0] != 1:
						print ("Records affected {}, expected 1 record affected".format(lstReturn[0]))
					strRouterVRFPeer = strHostname + "-" + strVRF + "-" + strPeerIP
					if strRcvdPrefix in dictPrefixes:
						dictPrefixes[strRcvdPrefix]["Peer"].append(strRouterVRFPeer)
						if strVRF not in dictPrefixes[strRcvdPrefix]["VRF"]:
							dictPrefixes[strRcvdPrefix]["VRF"].append(strVRF)
					else:
						dictPrefixes[strRcvdPrefix]={"VRF":[strVRF],"Peer":[strRouterVRFPeer]}
				if strLineTokens[0] == "Network":
					bInSection = True
	print ("Completed {:.1%}".format(1))
# end function AnalyzeIPv4Routes

def AnalyzeIPv6Routes(strOutList,strVRF,strPeerIP,strHostname,strDescr,iLineNum):
	global iOut2Line
	global dictPrefixes
	iPrefixCount = 0
	strNextHop = ""
	iStartLine = iOut2Line
	strSQL = "select iNeighborID from networks.tblneighbors where vcNeighborIP = '{}'".format(strPeerIP)
	lstReturn = SQLQuery (strSQL,dbConn)
	if not ValidReturn(lstReturn):
		print ("Unexpected: {}".format(lstReturn))
		return lstReturn
	elif lstReturn[0] != 1:
		print ("Records affected {}, expected 1 record affected".format(lstReturn[0]))
	else:
		iNeighborID = lstReturn[1][0][0]
	strSQL = "update networks.tblneighbors set vcDescription = '{}' where iNeighborID = {}".format(strDescr,iNeighborID)
	lstReturn = SQLQuery (strSQL,dbConn)
	if not ValidReturn(lstReturn):
		print ("Unexpected: {}".format(lstReturn))
	elif lstReturn[0] != 1:
		print ("Records affected {}, expected 1 record affected".format(lstReturn[0]))

	LogEntry ("Analyzing received IPv6 routes. There are {} lines in the output".format(len(strOutList)))
	if len(strOutList) > 0:
		if "Exception:" in strOutList[0]:
			bFoundABFACL = True
			LogEntry ("Found an exception message, aborting analysis")
			return
	for strLine in strOutList:
		if len(strLine) > 0:
			if strLine[0] == "%":
				LogEntry ("Error: {}".format(strLine))
				break
		strLineTokens = strLine.split()
		iCurLine = iOut2Line - iStartLine + 1
		if iCurLine%500 == 0:
			print ("Completed  {:.1%}".format(iCurLine/len(strOutList)))
		if strHostVer == "IOS-XR":
			if len(strLineTokens) > 0:
				if strLineTokens[0].find(":") == 4 and "/" in strLineTokens[0] :
					if iPrefixCount == 0:
						if len(strLineTokens) > 1:
							strNextHop = strLineTokens[1]
						strRcvdPrefix = strLineTokens[0]
						iPrefixCount += 1
					if iPrefixCount == 1 and strNextHop == "":
						strNextHop = strLineTokens[0]
					if strNextHop != "" and strNextHop != strLineTokens[0]:
						strRcvdPrefix = strLineTokens[0]
						iPrefixCount += 1
						strSQL = ("INSERT INTO networks.tblsubnets (iNeighborID,vcSubnet,vcIPver)"
							" VALUES ({0},'{1}','{2}');".format(iNeighborID,strRcvdPrefix,"IPv6"))
						lstReturn = SQLQuery (strSQL,dbConn)
						if not ValidReturn(lstReturn):
							print ("Unexpected: {}".format(lstReturn))
						elif lstReturn[0] != 1:
							print ("Records affected {}, expected 1 record affected".format(lstReturn[0]))
						strRouterVRFPeer = strHostname + "-" + strVRF + "-" + strPeerIP
						if strRcvdPrefix in dictPrefixes:
							dictPrefixes[strRcvdPrefix]["Peer"].append(strRouterVRFPeer)
							if strVRF not in dictPrefixes[strRcvdPrefix]["VRF"]:
								dictPrefixes[strRcvdPrefix]["VRF"].append(strVRF)
						else:
							dictPrefixes[strRcvdPrefix]={"VRF":[strVRF],"Peer":[strRouterVRFPeer]}
		if strHostVer == "IOS-XE":
			if len(strLineTokens) > 1:
				if strLineTokens[1].find(":") == 4:
					if iPrefixCount == 0:
						if len(strLineTokens) > 1:
							strNextHop = strLineTokens[1]
						strRcvdPrefix = strLineTokens[1]
						iPrefixCount += 1
					if iPrefixCount == 1 and strNextHop == "":
						strNextHop = strLineTokens[1]
					if strNextHop != "" and strNextHop != strLineTokens[1]:
						strRcvdPrefix = strLineTokens[1]
						iPrefixCount += 1
						strSQL = ("INSERT INTO networks.tblsubnets (iNeighborID,vcSubnet,vcIPver)"
							" VALUES ({0},'{1}','{2}');".format(iNeighborID,strRcvdPrefix,"IPv6"))
						lstReturn = SQLQuery (strSQL,dbConn)
						if not ValidReturn(lstReturn):
							print ("Unexpected: {}".format(lstReturn))
						elif lstReturn[0] != 1:
							print ("Records affected {}, expected 1 record affected".format(lstReturn[0]))
						strRouterVRFPeer = strHostname + "-" + strVRF + "-" + strPeerIP
						if strRcvdPrefix in dictPrefixes:
							dictPrefixes[strRcvdPrefix]["Peer"].append(strRouterVRFPeer)
							if strVRF not in dictPrefixes[strRcvdPrefix]["VRF"]:
								dictPrefixes[strRcvdPrefix]["VRF"].append(strVRF)
						else:
							dictPrefixes[strRcvdPrefix]={"VRF":[strVRF],"Peer":[strRouterVRFPeer]}# end function AnalyzeIPv6Routes
	print ("Completed {:.1%}".format(1))

def ParseDescr(strOutList,iLineNum):
	LogEntry ("Grabbing peer description. There are {} lines in the output".format(len(strOutList)))
	for strLine in strOutList:
		if "Exception:" in strLine:
			bFoundABFACL = True
			LogEntry ("Found an exception message, aborting analysis")
			break
		if len(strLine) > 0:
			if strLine[0] == "%":
				LogEntry ("Error: {}".format(strLine))
				break
		if strHostVer == "IOS-XR" or strHostVer == "IOS-XE":
			if "Description" in strLine:
				return strLine[14:]
#end function ParseDescr

import tkinter as tk
from tkinter import filedialog, messagebox
from playsound import playsound, PlaysoundException
import win32com.client as win32 #pip install pypiwin32
import getpass
import time
import sys
import paramiko #pip install paramiko
import socket
import os
import pymysql

xlSrcExternal = 0 #External data source
xlSrcModel = 4 #PowerPivot Model
xlSrcQuery = 3 #Query
xlSrcRange = 1 #Range
xlSrcXml = 2 #XML
xlGuess = 0 # Excel determines whether there is a header, and where it is, if there is one.
xlNo = 2 # Default. The entire range should be sorted.
xlYes = 1 # The entire range should not be sorted.

dictSheets={}
dictDevices={}
dictPrefixes={}

lstVRFs=[]
lstRequiredElements=["Match","IPv4-GT-Summary","IPv4-VRF-Summary","IPv4-GT-Advertise","IPv4-VRF-Advertise","IPv4-GT-Description","IPv4-VRF-Description",
				     "shVRF","IPv6-GT-Summary","IPv6-VRF-Summary","IPv6-GT-Advertise","IPv6-VRF-Advertise","IPv6-GT-Description","IPv6-VRF-Description"]

iResultNum = 0
iResult2Num = 0
iResult3Num = 0
iResultColNum = 1
iDetailsColNum = 1
iPrefixColNum = 1
tStart=time.time()
iInputColumn = 1
strOutFolderName = strSummarySheet

if os.path.isfile("Routes.txt"):
	print ("Configuration File exists")
else:
	print ("Can't find configuration file Routes.txt, make sure it is the same directory as this script")
	sys.exit(4)

strLine = "  "
print ("Reading in configuration")
objINIFile = open("Routes.txt","r")
strLines = objINIFile.readlines()
objINIFile.close()

for strLine in strLines:
	strLine = strLine.strip()
	if "=" in strLine:
		strConfParts = strLine.split("=")
		if strConfParts[0] == "Server":
			strServer = strConfParts[1]
		if strConfParts[0] == "Database":
			strInitialDB = strConfParts[1]
		if strConfParts[0] == "dbUser":
			strDBUser = strConfParts[1]
		if strConfParts[0] == "dbPWD":
			strDBPWD = strConfParts[1]
		if strConfParts[0] == "SSHLogFolder":
			strSaveLoc = strConfParts[1]
		if strConfParts[0] == "BatchSize":
			iBatchSize = strConfParts[1]
		if strConfParts[0] == "NumWeeksBreak":
			iNumWeeks = strConfParts[1]
		if strConfParts[0] == "CollectIPv4":
			bCollectv4 = bool(strConfParts[1].lower()=="yes")
		if strConfParts[0] == "CollectIPv6":
			bCollectv6 = bool(strConfParts[1].lower()=="yes")

if not bCollectv6 and not bCollectv4:
	print ("neither IPv4 nor IPv6 is set to collect so nothing to do. Exiting!!")
	sys.exit(8)

if strSaveLoc[-1:] != "\\":
	strSaveLoc += "\\"

if not os.path.isdir(strSaveLoc):
	print ("{} doesn't exists, creating it".format(strSaveLoc))
	os.makedirs(strSaveLoc)
else:
	print ("Will save output logs to {}".format(strSaveLoc))

def SQLConn (strServer,strDBUser,strDBPWD,strInitialDB):
	try:
		# Open database connection
		return pymysql.connect(strServer,strDBUser,strDBPWD,strInitialDB)
	except pymysql.err.InternalError as err:
		print ("Error: unable to connect: {}".format(err))
		sys.exit(5)
	except pymysql.err.OperationalError as err:
		print ("Operational Error: unable to connect: {}".format(err))
		sys.exit(5)
	except pymysql.err.ProgrammingError as err:
		print ("Programing Error: unable to connect: {}".format(err))
		sys.exit(5)

def SQLQuery (strSQL,db):
	try:
		# prepare a cursor object using cursor() method
		dbCursor = db.cursor()
		# Execute the SQL command
		dbCursor.execute(strSQL)
		# Count rows
		iRowCount = dbCursor.rowcount
		if strSQL[:6].lower() == "select":
			dbResults = dbCursor.fetchall()
		else:
			db.commit()
			dbResults = ()
		return [iRowCount,dbResults]
	except pymysql.err.InternalError as err:
		if strSQL[:6].lower() != "select":
			db.rollback()
		return "Internal Error: unable to execute: {}".format(err)
	except pymysql.err.ProgrammingError as err:
		if strSQL[:6].lower() != "select":
			db.rollback()
		return "Programing Error: unable to execute: {}".format(err)
	except pymysql.err.OperationalError as err:
		if strSQL[:6].lower() != "select":
			db.rollback()
		return "Programing Error: unable to execute: {}".format(err)
	except pymysql.err.IntegrityError as err:
		if strSQL[:6].lower() != "select":
			db.rollback()
		return "Integrity Error: unable to execute: {}".format(err)

def ValidReturn(lsttest):
	if isinstance(lsttest,list):
		if len(lsttest) == 2:
			if isinstance(lsttest[0],int) and isinstance(lsttest[1],tuple):
				return True
			else:
				return False
		else:
			return False
	else:
		return False


def getInput(strPrompt):
    if sys.version_info[0] > 2 :
        return input(strPrompt)
    else:
        return raw_input(strPrompt)
# end getInput

def GetResults(strHostname,strCmd):
	try:
		SSH = paramiko.SSHClient()
		SSH.set_missing_host_key_policy(paramiko.AutoAddPolicy())
		SSH.connect(strHostname, username=strUserName, password=strPWD, look_for_keys=False, allow_agent=False)
		stdin, stdout, stderr = SSH.exec_command(strCmd)
		LogEntry ("sent {0} to {1}".format(strCmd,strHostname))
		strOut = stdout.read()
		SSH.close()
		strOut = strOut.decode("utf-8")
		strOutFile = strSaveLoc + strHostname + ".txt"
		if strHostname in dictDevices:
			objFileOut = open(strOutFile,"a")
		else:
			objFileOut = open(strOutFile,"w")
		objFileOut.write (strCmd + "\n" + strOut + "\n")
		objFileOut.close()
		LogEntry ("output written to "+strOutFile)
	except paramiko.ssh_exception.AuthenticationException as err:
		LogEntry ("Auth Exception: {0}".format(err))
		strOut = "Auth Exception: {0}".format(err)
	except paramiko.SSHException as err:
		LogEntry ("SSH Exception: {0}".format(err))
		strOut = "SSH Exception: {0}".format(err)
	except OSError as err:
		LogEntry ("Socket Exception: {0}".format(err))
		strOut = "Socket Exception: {0}".format(err)
	# except Exception as err:
	# 	LogEntry ("Generic Exception: {0}".format(err))
	# 	strOut = "Generic Exception: {0}".format(err)
	return strOut
#end function GetResults

def ValidateRetry(strHostname,strCmd):
	global iErrCount
	global FailedDevs
	global lstFailedDevsName
	global iAuthFail
	global strPWD
	global strUserName
	global bDevOK

	strOut = GetResults(strHostname,strCmd)
	while "Exception" in strOut and iErrCount < iMaxError:
		if "SSH Exception:" in strOut or "Socket Exception:" in strOut:
			iErrCount += 1
			LogEntry ("Trying again in 5 sec")
			time.sleep(5)
		elif "Auth Exception" in strOut:
			playsound(r'c:\windows\media\tada.wav')
			strUserName = getInput("Please provide username for use when login into the routers, enter to use {}: ".format(DefUserName))
			if strUserName == "":
				strUserName = DefUserName
			# end if username is empty
			strPWD = getpass.getpass(prompt="what is the password for {0}: ".format(strUserName))
			if strPWD == "":
				print ("empty password, next device")
				iErrCount = iMaxError
				break
			iAuthFail += 1
			if iAuthFail == iMaxAuthFail:
				iErrCount = iMaxError
		else:
			LogEntry("Unknown exception {}\n Next Device!".format(strOut))
			iErrCount = iMaxError
			break
		strOut = GetResults(strHostname,strCmd)


	if "Exception" in strOut:
		if not bFailedDev:
			FailedDevs.append(iInputLineNum)
			lstFailedDevsName.append(strHostname)
		bDevOK = False
		LogEntry ("Exceeded Max Retry's, next device!")
	else:
		bDevOK = True
	return strOut
# end function ValidateRetry

def LogEntry(strMsg):
	lstReturn=SQLQuery("insert into networks.tbllogs (vcRouterName,vcLogEntry,iSessionID) VALUES('{}','{}',{});".format(strHostname,strMsg.replace("'","") ,iSessID),dbConn)
	if not ValidReturn(lstReturn):
		print ("Unexpected: {}".format(lstReturn))
	elif lstReturn[0] != 1:
		print ("Records affected {}, expected 1 record affected".format(lstReturn[0]))

	print (strMsg)

def OSDetect():
	strHostVer = "Unknown"
	strOut = ValidateRetry(strHostname,"show version")
	for strOS in dictBaseCmd:
		if dictBaseCmd[strOS]["Match"] in strOut:
			strHostVer = strOS
		if strOS == "IOS":
			continue
	if strHostVer == "Unknown" :
		if "IOS" in dictBaseCmd:
			if dictBaseCmd["IOS"]["Match"] in strOut:
				strHostVer = "IOS"
	return strHostVer

def IPv4Peers():
	dictIPv4Peers={}

	strOut = ValidateRetry(strHostname,dictBaseCmd[strHostVer]["IPv4-GT-Summary"])
	dictIPv4Peers = AnalyzeIPv4Results(strOut.splitlines(),"Global Table")

	for strVRF in lstVRFs:
		strOut = ValidateRetry(strHostname,dictBaseCmd[strHostVer]["IPv4-VRF-Summary"].format(strVRF))
		dictTemp = AnalyzeIPv4Results(strOut.splitlines(),strVRF)
		dictIPv4Peers.update(dictTemp)
	LogEntry ("Gathering details on {} IPv4 Peers.".format(len(dictIPv4Peers)))
	iCurPeer = 0
	for strPeerIP in dictIPv4Peers:
		iCurPeer += 1
		LogEntry ("IPv4 Peer {} out of {}".format(iCurPeer,len(dictIPv4Peers)))
		strVRF = dictIPv4Peers[strPeerIP]["VRF"]
		iLineNum = dictIPv4Peers[strPeerIP]["LineID"]
		if strVRF == "Global Table":
			strOut = ValidateRetry(strHostname,dictBaseCmd[strHostVer]["IPv4-GT-Description"].format(strPeerIP))
			strDescr = ParseDescr(strOut.splitlines(), iLineNum)
			strOut = ValidateRetry(strHostname,dictBaseCmd[strHostVer]["IPv4-GT-Advertise"].format(strPeerIP))
			AnalyzeIPv4Routes(strOut.splitlines(),strVRF,strPeerIP,strHostname,strDescr,iLineNum)
		else:
			strOut = ValidateRetry(strHostname,dictBaseCmd[strHostVer]["IPv4-VRF-Description"].format(strVRF,strPeerIP))
			strDescr = ParseDescr(strOut.splitlines(), iLineNum)
			strOut = ValidateRetry(strHostname,dictBaseCmd[strHostVer]["IPv4-VRF-Advertise"].format(strVRF,strPeerIP))
			AnalyzeIPv4Routes(strOut.splitlines(),strVRF,strPeerIP,strHostname,strDescr,iLineNum)

def IPv6Peers():
	dictIPv6Peers={}
	strOut = ValidateRetry(strHostname,dictBaseCmd[strHostVer]["IPv6-GT-Summary"])
	dictIPv6Peers = AnalyzeIPv6Results(strOut.splitlines(),"Global Table")

	for strVRF in lstVRFs:
		strOut = ValidateRetry(strHostname,dictBaseCmd[strHostVer]["IPv6-VRF-Summary"].format(strVRF))
		dictTemp = AnalyzeIPv6Results(strOut.splitlines(),strVRF)
		dictIPv6Peers.update(dictTemp)

	LogEntry ("Gathering details on {} IPv6 Peers.".format(len(dictIPv6Peers)))
	iCurPeer = 0
	for strPeerIP in dictIPv6Peers:
		iCurPeer += 1
		LogEntry ("IPv6 Peer {} out of {}".format(iCurPeer,len(dictIPv6Peers)))
		if strPeerIP == "":
			continue
		strVRF = dictIPv6Peers[strPeerIP]["VRF"]
		iLineNum = dictIPv6Peers[strPeerIP]["LineID"]
		if strVRF == "Global Table":
			strOut = ValidateRetry(strHostname,dictBaseCmd[strHostVer]["IPv6-GT-Description"].format(strPeerIP))
			strDescr = ParseDescr(strOut.splitlines(), iLineNum)
			strOut = ValidateRetry(strHostname,dictBaseCmd[strHostVer]["IPv6-GT-Advertise"].format(strPeerIP))
			AnalyzeIPv6Routes(strOut.splitlines(),strVRF,strPeerIP,strHostname,strDescr,iLineNum)
		else:
			strOut = ValidateRetry(strHostname,dictBaseCmd[strHostVer]["IPv6-VRF-Description"].format(strVRF,strPeerIP))
			strDescr = ParseDescr(strOut.splitlines(), iLineNum)
			strOut = ValidateRetry(strHostname,dictBaseCmd[strHostVer]["IPv6-VRF-Advertise"].format(strVRF,strPeerIP))
			AnalyzeIPv6Routes(strOut.splitlines(),strVRF,strPeerIP,strHostname,strDescr,iLineNum)

DefUserName = getpass.getuser()
print ("This is a router audit script. Your default username is {3}. This is running under Python Version {0}.{1}.{2}".format(sys.version_info[0],sys.version_info[1],sys.version_info[2],DefUserName))
now = time.asctime()
print ("The time now is {}".format(now))
print ("This script will read a router list from a database and log into each router listed in the router list table,\n")
for strOS in dictBaseCmd:
	for attr in lstRequiredElements:
		if attr not in dictBaseCmd[strOS]:
			print ("{} is missing definition for {}.\n *** Each OS version requires definitions for the following:\n{}".format(strOS,attr,lstRequiredElements))
			sys.exit(5)

print ("Grabbing next {} devices".format(iBatchSize))
strSQL = ("SELECT iRouterID,vcHostName FROM networks.tblrouterlist"
	" where dtUpdateCompleted < now() - interval {} week or dtUpdateCompleted is null"
	" order by dtUpdateCompleted limit {};".format(iNumWeeks, iBatchSize))
dbConn = SQLConn (strServer,strDBUser,strDBPWD,strInitialDB)
lstRouters = SQLQuery (strSQL,dbConn)
if not ValidReturn(lstRouters):
	print ("Unexpected: {}".format(lstRouters))
	sys.exit(8)
else:
	print ("Fetched {} rows".format(lstRouters[0]))


strSQL = "SELECT ifnull(max(iSessionID),0) FROM networks.tbllogs;"
lstReturn = SQLQuery (strSQL,dbConn)
if not ValidReturn(lstReturn):
	print ("Unexpected: {}".format(lstReturn))
	sys.exit(8)
else:
	iSessID =lstReturn[1][0][0]+1

strUserName = getInput("Please provide username for use when login into the routers, enter to use {}: ".format(DefUserName))
if strUserName == "":
	strUserName = DefUserName
# end if username is empty

strPWD = getpass.getpass(prompt="what is the password for {0}: ".format(strUserName))
if strPWD == "":
	print ("empty password, exiting")
	sys.exit(5)

iInputLineNum = 2
iOutLineNum = 1
iOut2Line = 1
strHostname = ""
FailedDevs = []
lstFailedDevsName = []
bDevOK = True
bFailedDev = False


for dbRow in lstRouters[1]:
	iErrCount = 0
	iAuthFail = 0
	strHostname = dbRow[1]
	iHostID = dbRow[0]
	strSQL = "delete from networks.tblneighbors where iRouterID = {};".format(iHostID)
	lstReturn = SQLQuery (strSQL,dbConn)
	if not ValidReturn(lstReturn):
		print ("Unexpected: {}".format(lstReturn))
		break
	else:
		print ("Deleted {} neighbors".format(lstReturn[0]))

	# strSQL = "delete from networks.tblsubnets where iRouterID = {};".format(iHostID)
	# lstReturn = SQLQuery (strSQL,dbConn)
	strHostname = strHostname.upper()
	LogEntry ("Processing {} ...".format(strHostname))

	strHostVer = OSDetect()
	LogEntry ("Found IOS version to be {}".format(strHostVer))
	dictDevices[strHostname] = strHostVer
	strSQL = "update networks.tblrouterlist set dtUpdateStarted = now(), dtUpdateCompleted=null, vcOS = '{}', iSessionID={} where iRouterID = {};".format(strHostVer,iSessID,iHostID)
	lstReturn = SQLQuery (strSQL,dbConn)
	if not ValidReturn(lstReturn):
		print ("Unexpected: {}".format(lstReturn))
		break
	elif lstReturn[0] != 1:
		print ("Records affected {}, expected 1 record affected".format(lstReturn[0]))

	if strHostVer == "Unknown":
		LogEntry("Can't process unknown platform")
		continue
	if bDevOK:
		lstVRFs = CollectVRFs()
	if bCollectv4 and bDevOK:
		IPv4Peers()
	if bCollectv6 and bDevOK:
		IPv6Peers()
	if bDevOK:
		strSQL = "update networks.tblrouterlist set dtLastSuccess = now(), dtUpdateCompleted=now() where iRouterID = {};".format(iHostID)
		lstReturn = SQLQuery (strSQL,dbConn)
		if not ValidReturn(lstReturn):
			print ("Unexpected: {}".format(lstReturn))
			break
		elif lstReturn[0] != 1:
			print ("Records affected {}, expected 1 record affected".format(lstReturn[0]))

LogEntry ("Done processing...")

now = time.asctime()
tStop = time.time()
iElapseSec = tStop - tStart
iMin, iSec = divmod(iElapseSec, 60)
iHours, iMin = divmod(iMin, 60)
if bFailedDev and len(lstFailedDevsName) == 0:
	LogEntry ("All devices successful after final retries")
if len(lstFailedDevsName) > 0:
	if len(lstFailedDevsName) == 1:
		strdev = "device"
	else:
		strdev = "devices"
	LogEntry ("Failed to complete {} {}, {}, due to errors.".format(len(lstFailedDevsName),strdev,",".join(lstFailedDevsName)))

LogEntry ("Completed at {}".format(now))
LogEntry ("Took {0:.2f} seconds to complete, which is {1} hours, {2} minutes and {3:.2f} seconds.".format(iElapseSec,int(iHours),int(iMin),iSec))

