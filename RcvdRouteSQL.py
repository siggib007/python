'''
Router Audit
Author Siggi Bjarnason Copyright 2017
Website http://www.icecomputing.com

Description:
This is script that will discover all the BGP peers on a particular Cisco Router running
and caputer all the routes being received over each peer.

Following packages need to be installed as administrator
pip install pypiwin32
pip install paramiko
pip install playsound
pip install pymysql

'''

iMaxError = 6 # How many times can we experience an error on a single device before marking the device failed and moving on, 0 based
iMaxAuthFail = 2 # How many auth failures can happen in a row. Zero based.
iMaxDevAuthFail = 2 # If running non interactively after how many devive experiencing auth failure does the script bail, zero based
dictBaseCmd = {
		"IOS-XR":{
			"Match":"IOS XR",
			"IPv4-GT-Summary":"show bgp ipv4 unicast summary",
			"IPv4-VRF-Summary":"show bgp vrf {} ipv4 unicast summary",
			"IPv4-GT-Receive":"show bgp ipv4 unicast neighbors {} routes",
			"IPv4-VRF-Receive":"show bgp vrf {} ipv4 unicast neighbors {} routes",
			"IPv4-GT-Description":"show bgp ipv4 unicast neighbors {} | include Description:",
			"IPv4-VRF-Description":"show bgp vrf {} ipv4 unicast neighbors {} | include Description:",
			"IPv6-GT-Summary":"show bgp ipv6 unicast summary",
			"IPv6-VRF-Summary":"show bgp vrf {} ipv6 unicast summary",
			"IPv6-GT-Receive":"show bgp ipv6 unicast neighbors {} routes",
			"IPv6-VRF-Receive":"show bgp vrf {} ipv6 unicast neighbors {} routes",
			"IPv6-GT-Description":"show bgp ipv6 unicast neighbors {} | include Description:",
			"IPv6-VRF-Description":"show bgp vrf {} ipv6 unicast neighbors {} | include Description:",
			"IPv4-GT-Direct":"show route ipv4 connected",
			"IPv4-VRF-Direct":"show route vrf {} ipv4 connected",
			"IPv6-GT-Direct":"show route ipv6 connected",
			"IPv6-VRF-Direct":"show route vrf {} ipv6 connected",
			"shVRF":"show vrf all"
		},
		"IOS-XE":{
			"Match":"IOS XE",
			"IPv4-GT-Summary":"show bgp ipv4 unicast summary",
			"IPv4-VRF-Summary":"show bgp vrf {} vpnv4 unicast summary",
			"IPv4-GT-Receive":"show bgp ipv4 unicast neighbors {} routes",
			"IPv4-VRF-Receive":"show bgp vrf {} vpnv4 unicast neighbors {} routes",
			"IPv4-GT-Description":"show bgp ipv4 unicast neighbors {} | include Description:",
			"IPv4-VRF-Description":"show bgp vrf {} vpnv4 unicast neighbors {} | include Description:",
			"IPv6-GT-Summary":"show bgp ipv6 unicast summary",
			"IPv6-VRF-Summary":"show bgp vrf {} vpnv6 unicast summary",
			"IPv6-GT-Receive":"show bgp ipv6 unicast neighbors {} routes",
			"IPv6-VRF-Receive":"show bgp vrf {} vpnv4 unicast neighbors {} routes",
			"IPv6-GT-Description":"show bgp ipv6 unicast neighbors {} | include Description:",
			"IPv6-VRF-Description":"show bgp vrf {} vpnv4 unicast neighbors {} | include Description:",
			"IPv4-GT-Direct":"show ip route connected",
			"IPv4-VRF-Direct":"show ip route vrf {} connected",
			"IPv6-GT-Direct":"show ipv6 route connected",
			"IPv6-VRF-Direct":"show ipv6 route vrf {} connected",
			"shVRF":"show vrf brief"
		},
		"Nexus":{
			"Match":"NX-OS",
			"IPv4-GT-Summary":"show ip bgp summary",
			"IPv4-VRF-Summary":"show ip bgp vrf {} summary",
			"IPv4-GT-Receive":"show ip bgp neighbors {} routes",
			"IPv4-VRF-Receive":"show ip bgp vrf {} neighbors {} routes",
			"IPv4-GT-Description":"show ip bgp neighbors {} | include Description:",
			"IPv4-VRF-Description":"show ip bgp vrf {} neighbors {} | include Description:",
			"IPv6-GT-Summary":"show ipv6 bgp summary",
			"IPv6-VRF-Summary":"show ipv6 bgp vrf {} summary",
			"IPv6-GT-Receive":"show ipv6 bgp neighbors {} routes",
			"IPv6-VRF-Receive":"show ipv6 bgp vrf CORESEC neighbors {} routes ",
			"IPv6-GT-Description":"show ipv6 bgp neighbors {} | include Description:",
			"IPv6-VRF-Description":"show ipv6 bgp vrf CORESEC neighbors {} | include Description:",
			"IPv4-GT-Direct":"show ip route direct",
			"IPv4-VRF-Direct":"show ip route vrf {} direct",
			"IPv6-GT-Direct":"show ipv6 route direct",
			"IPv6-VRF-Direct":"show ipv6 route vrf {} direct",
			"shVRF":"show vrf all",
		},
		"IOS":{
			"Match":" IOS ",
			"IPv4-GT-Summary":"show ip bgp summary",
			"IPv4-VRF-Summary":"show ip bgp vpnv4 vrf {} summary",
			"IPv4-GT-Receive":"show ip bgp neighbors {} routes",
			"IPv4-VRF-Receive":"show ip bgp vpnv4 vrf {} neighbors {} routes",
			"IPv4-GT-Description":"show ip bgp neighbors {} | include Description:",
			"IPv4-VRF-Description":"show ip bgp vpnv4 vrf {} neighbors {} | include Description:",
			"IPv6-GT-Summary":"show bgp ipv6 unicast summary",
			"IPv6-VRF-Summary":"show ip bgp vpnv6 unicast vrf {} summary",
			"IPv6-GT-Receive":"show ip bgp ipv6 unicast neighbors {} routes",
			"IPv6-VRF-Receive":"show ip bgp vpnv6 unicast vrf {} neighbors {} routes",
			"IPv6-GT-Description":"show ip bgp ipv6 unicast neighbors {} | include Description:",
			"IPv6-VRF-Description":"show ip bgp vpnv6 unicast vrf {} neighbors {} | include Description:",
			"IPv4-GT-Direct":"show ip route connected",
			"IPv4-VRF-Direct":"show ip route vrf {} connected",
			"IPv6-GT-Direct":"show ipv6 route connected",
			"IPv6-VRF-Direct":"show ipv6 route vrf {} connected",
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
				if strHostVer == "IOS":
					if bInSection and len(strLineTokens) > 2 :
						lstVRFs.append(strLineTokens[0])
					if strLineTokens[0]== "Name" and strLineTokens[1]== "Default" and strLineTokens[2]== "RD":
						bInSection = True
				if strHostVer == "Nexus":
					if bInSection and strLineTokens[0] != "default" and strLineTokens[0] != "management" :
						lstVRFs.append(strLineTokens[0])
					if strLineTokens[0]== "VRF-Name" and strLineTokens[1]== "VRF-ID" and strLineTokens[2]== "State":
						bInSection = True
	LogEntry ("VRF's Collected: {}".format(lstVRFs))
	return lstVRFs

def ProcessDirectIPv4 (strOutputList, strVRF):
	i = 0
	iNeighborID = 0

	LogEntry ("There are {} lines in the show ip route connected output".format(len(strOutputList)))
	strSQL = "select iNeighborID from networks.tblneighbors where vcNeighborIP = '{}-{}-directly'".format(strHostname,strVRF)
	lstReturn = SQLQuery (strSQL,dbConn)
	if not ValidReturn(lstReturn):
		LogEntry ("Unexpected: {}".format(lstReturn))
		return lstReturn
	elif lstReturn[0] != 1:
		LogEntry ("Records affected {}, expected 1 record affected".format(lstReturn[0]))
	else:
		iNeighborID = lstReturn[1][0][0]

	for strLine in strOutputList:
		strSubnet = ""
		if "Exception:" in strLine:
			LogEntry ("Found an exception message, aborting analysis")
			break
		if len(strLine) > 0:
			if strLine[0] == "%":
				LogEntry ("Error: {}".format(strLine))
				break
		if strHostVer == "IOS-XR" or strHostVer == "IOS-XE" or strHostVer == "IOS":
			strLineTokens = strLine.split()
			if len(strLineTokens) > 5:
				if strLineTokens[1].count(".") == 3 and "/" in strLineTokens[1] and strLineTokens[3] == "directly" and strLineTokens[0].strip()=="C" :
					strSubnet = strLineTokens[1].strip()
		if strHostVer == "Nexus" :
			strLineTokens = strLine.split(",")
			if len(strLineTokens) > 1:
				if strLineTokens[0].count(".") == 3 and "/" in strLineTokens[0] :
					strSubnet = strLineTokens[0].strip()

		if iNeighborID > 0 and strSubnet !="":
			dictIPInfo = IPCalc (strSubnet)
			if "iDecSubID" in dictIPInfo:
				iDecSubID = dictIPInfo['iDecSubID']
			else:
				iDecSubID = -10
			if "iDecBroad" in dictIPInfo:
				iDecBroad = dictIPInfo['iDecBroad']
			else:
				iDecBroad = -10
			if "Hostcount" in dictIPInfo:
				iHostcount = dictIPInfo['Hostcount']
			else:
				iHostcount = -10
			if "IPError" in dictIPInfo:
				LogEntry (dictIPInfo['IPError'])
			if iDecSubID > 0 and iHostcount > 4:
				strSQL = ("INSERT INTO networks.tblsubnets (iNeighborID,vcSubnet,vcIPver,iSubnetStart,iSubnetEnd, iHostCount)"
				" VALUES ({0},'{1}','{2}',{3},{4},{5});".format(iNeighborID,strSubnet,"IPv4",iDecSubID,iDecBroad,iHostcount))
				lstReturn = SQLQuery (strSQL,dbConn)
				if not ValidReturn(lstReturn):
					LogEntry ("Unexpected: {}".format(lstReturn))
				elif lstReturn[0] != 1:
					LogEntry ("Records affected {}, expected 1 record affected".format(lstReturn[0]))
				i += 1

	LogEntry ("Collected {} directly connected routes".format(i))
	strSQL = "update networks.tblneighbors set iRcvdCount = '{}' where iNeighborID = {}".format(i,iNeighborID)
	lstReturn = SQLQuery (strSQL,dbConn)
	if not ValidReturn(lstReturn):
		LogEntry ("Unexpected: {}".format(lstReturn))
	elif lstReturn[0] != 1:
		LogEntry ("Records affected {}, expected 1 record affected".format(lstReturn[0]))

def AnalyzeIPv4Results(strOutputList, strVRF):
	dictIPv4Peers = {}
	bNeighborSection = False

	strSQL = ("INSERT INTO networks.tblneighbors (iRouterID,vcNeighborIP,iRemoteAS,vcVRF,iRcvdCount,vcDescription)"
		" VALUES ({0},'{1}-{3}-directly',{2},'{3}',{4},'{1} VRF {3} directly connected routes');".format(iHostID,strHostname,0,strVRF,0))
	lstReturn = SQLQuery (strSQL,dbConn)
	if not ValidReturn(lstReturn):
		LogEntry ("Unexpected: {}".format(lstReturn))
	elif lstReturn[0] != 1:
		LogEntry ("Records affected {}, expected 1 record affected".format(lstReturn[0]))
	else:
		LogEntry ("Successfully added entry to tblneighbors for direct connected")

	LogEntry ("There are {} lines in the show bgp IPv4 summary output".format(len(strOutputList)))
	for strLine in strOutputList:
		if "Exception:" in strLine:
			LogEntry ("Found an exception message, aborting analysis")
			break
		if len(strLine) > 0:
			if strLine[0] == "%":
				LogEntry ("Error: {}".format(strLine))
				break
		strLineTokens = strLine.split()
		if strHostVer == "IOS-XR" or strHostVer == "IOS-XE" or strHostVer == "IOS" or strHostVer == "Nexus":
			if "local AS number " in strLine:
				iLoc = strLine.find("number ")+7
				iLocalAS = strLine[iLoc:]
			if len(strLineTokens) > 1:
				if bNeighborSection:
					if len(strLineTokens) > 8:
						iRemoteAS = strLineTokens[2]
						strCount = str(strLineTokens[9])
						strPeerIP = strLineTokens[0]
						if iRemoteAS != iLocalAS and isInt(strCount) and iRemoteAS !=65137:
							strSQL = ("INSERT INTO networks.tblneighbors (iRouterID,vcNeighborIP,iRemoteAS,vcVRF,iRcvdCount)"
								" VALUES ({0},'{1}',{2},'{3}',{4});".format(iHostID,strPeerIP,iRemoteAS,strVRF,strCount))
							lstReturn = SQLQuery (strSQL,dbConn)
							if not ValidReturn(lstReturn):
								LogEntry ("Unexpected: {}".format(lstReturn))
							elif lstReturn[0] != 1:
								LogEntry ("Records affected {}, expected 1 record affected".format(lstReturn[0]))

							dictIPv4Peers[strPeerIP] = {"VRF":strVRF}

				if strLineTokens[0]== "Neighbor":
					bNeighborSection = True
			else:
				bNeighborSection = False

	return dictIPv4Peers

# end function AnalyzeIPv4Results

def AnalyzeIPv6Results(strOutputList, strVRF):
	dictPeers = {}
	bNeighborSection = False
	strPeerIP = ""

	LogEntry ("There are {} lines in the show bgp IPv6 summary output".format(len(strOutputList)))
	for strLine in strOutputList:
		if "Exception:" in strLine:
			LogEntry ("Found an exception message, aborting analysis")
			break
		if len(strLine) > 0:
			if strLine[0] == "%":
				LogEntry ("Error: {}".format(strLine))
				break

		strLineTokens = strLine.split()
		if strHostVer == "IOS-XR" or strHostVer == "IOS-XE" or strHostVer == "IOS" or strHostVer == "Nexus":
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
						if iRemoteAS != iLocalAS and isInt(strCount) and iRemoteAS !=65137:
							strSQL = ("INSERT INTO networks.tblneighbors (iRouterID,vcNeighborIP,iRemoteAS,vcVRF,iRcvdCount)"
								" VALUES ({0},'{1}',{2},'{3}',{4});".format(iHostID,strPeerIP,iRemoteAS,strVRF,strCount))
							lstReturn = SQLQuery (strSQL,dbConn)
							if not ValidReturn(lstReturn):
								LogEntry ("Unexpected: {}".format(lstReturn))
							elif lstReturn[0] != 1:
								LogEntry ("Records affected {}, expected 1 record affected".format(lstReturn[0]))
							dictPeers[strPeerIP] = {"VRF":strVRF}
				if strLineTokens[0]== "Neighbor":
					bNeighborSection = True
			else:
				bNeighborSection = False

	return dictPeers
# end function AnalyzeIPv6Results

def AnalyzeIPv4Routes(strOutList,strVRF,strPeerIP,strHostname,strDescr):
	bInSection = False
	iNeighborID = 0
	strRcvdPrefix = ""

	strSQL = "select iNeighborID from networks.tblneighbors where vcNeighborIP = '{}'".format(strPeerIP)
	lstReturn = SQLQuery (strSQL,dbConn)
	if not ValidReturn(lstReturn):
		LogEntry ("Unexpected: {}".format(lstReturn))
		return lstReturn
	elif lstReturn[0] != 1:
		LogEntry ("Records affected {}, expected 1 record affected".format(lstReturn[0]))
		# return lstReturn
	else:
		iNeighborID = lstReturn[1][0][0]
	strSQL = "update networks.tblneighbors set vcDescription = '{}' where iNeighborID = {}".format(strDescr,iNeighborID)
	lstReturn = SQLQuery (strSQL,dbConn)
	if not ValidReturn(lstReturn):
		LogEntry ("Unexpected: {}".format(lstReturn))
	elif lstReturn[0] != 1:
		LogEntry ("Records affected {}, expected 1 record affected".format(lstReturn[0]))

	LogEntry ("Analyzing received IPv4 routes. There are {} lines in the output".format(len(strOutList)))
	if len(strOutList) > 0:
		if "Exception:" in strOutList[0]:
			LogEntry ("Found an exception message, aborting analysis")
			return
	for strLine in strOutList:
		if len(strLine) > 0:
			if strLine[0] == "%":
				LogEntry ("Error: {}".format(strLine))
				break
		if strHostVer == "IOS-XR":
			strLineTokens = strLine.split()
			if len(strLineTokens) > 1:
				if bInSection and strLineTokens[0] != "Route"  and strLineTokens[0] != "Processed":
					strRcvdPrefix = strLineTokens[1]
				if strLineTokens[0] == "Network":
					bInSection = True
		if strHostVer == "IOS-XE" or strHostVer == "IOS":
			strLineTokens = strLine.split()
			if len(strLineTokens) > 1:
				if bInSection and strLineTokens[0] != "Total" and strLineTokens[0] != "Network" and strLineTokens[1].count(".") == 3 :
					strRcvdPrefix = strLineTokens[1]
				if strLineTokens[0] == "Network":
					bInSection = True
		if strHostVer == "Nexus":
			strLineTokens = strLine[3:].split()
			if len(strLineTokens) > 1:
				if bInSection and strLineTokens[0] != "Total" and strLineTokens[0] != "Network" and strLineTokens[0].count(".") == 3 :
					strRcvdPrefix = strLineTokens[0]
				if strLineTokens[0] == "Network":
					bInSection = True
		if iNeighborID > 0 and strRcvdPrefix !="":
			dictIPInfo = IPCalc (strRcvdPrefix)
			if "iDecSubID" in dictIPInfo:
				iDecSubID = dictIPInfo['iDecSubID']
			else:
				iDecSubID = -10
			if "iDecBroad" in dictIPInfo:
				iDecBroad = dictIPInfo['iDecBroad']
			else:
				iDecBroad = -10
			if "Hostcount" in dictIPInfo:
				iHostcount = dictIPInfo['Hostcount']
			else:
				iHostcount = -10
			if "IPError" in dictIPInfo:
				LogEntry (dictIPInfo['IPError'])
			if iDecSubID > 0 and iHostcount > 4:
				strSQL = ("INSERT INTO networks.tblsubnets (iNeighborID,vcSubnet,vcIPver,iSubnetStart,iSubnetEnd, iHostCount)"
					" VALUES ({0},'{1}','{2}',{3},{4},{5});".format(iNeighborID,strRcvdPrefix,"IPv4",iDecSubID,iDecBroad,iHostcount))
				lstReturn = SQLQuery (strSQL,dbConn)
				if not ValidReturn(lstReturn):
					LogEntry ("Unexpected: {}\n{}".format(lstReturn,strSQL))
				elif lstReturn[0] != 1:
					LogEntry ("Records affected {}, expected 1 record affected".format(lstReturn[0]))

# end function AnalyzeIPv4Routes

def AnalyzeIPv6Routes(strOutList,strVRF,strPeerIP,strHostname,strDescr):
	iPrefixCount = 0
	strNextHop = ""
	strSQL = "select iNeighborID from networks.tblneighbors where vcNeighborIP = '{}'".format(strPeerIP)
	lstReturn = SQLQuery (strSQL,dbConn)
	if not ValidReturn(lstReturn):
		LogEntry ("Unexpected: {}".format(lstReturn))
		return lstReturn
	elif lstReturn[0] != 1:
		LogEntry ("Records affected {}, expected 1 record affected".format(lstReturn[0]))
	else:
		iNeighborID = lstReturn[1][0][0]
	strSQL = "update networks.tblneighbors set vcDescription = '{}' where iNeighborID = {}".format(strDescr,iNeighborID)
	lstReturn = SQLQuery (strSQL,dbConn)
	if not ValidReturn(lstReturn):
		LogEntry ("Unexpected: {}".format(lstReturn))
	elif lstReturn[0] != 1:
		LogEntry ("Records affected {}, expected 1 record affected".format(lstReturn[0]))

	LogEntry ("Analyzing received IPv6 routes. There are {} lines in the output".format(len(strOutList)))
	if len(strOutList) > 0:
		if "Exception:" in strOutList[0]:
			LogEntry ("Found an exception message, aborting analysis")
			return
	for strLine in strOutList:
		if len(strLine) > 0:
			if strLine[0] == "%":
				LogEntry ("Error: {}".format(strLine))
				break

		if strHostVer == "IOS-XR":
			strLineTokens = strLine.split()
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
							LogEntry ("Unexpected: {}".format(lstReturn))
						elif lstReturn[0] != 1:
							LogEntry ("Records affected {}, expected 1 record affected".format(lstReturn[0]))

		if strHostVer == "IOS-XE" or strHostVer == "IOS":
			strLineTokens = strLine.split()
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
							LogEntry ("Unexpected: {}".format(lstReturn))
						elif lstReturn[0] != 1:
							LogEntry ("Records affected {}, expected 1 record affected".format(lstReturn[0]))
		if strHostVer == "Nexus":
			strLineTokens = strLine[3:].split()
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
							LogEntry ("Unexpected: {}".format(lstReturn))
						elif lstReturn[0] != 1:
							LogEntry ("Records affected {}, expected 1 record affected".format(lstReturn[0]))
# end function AnalyzeIPv6Routes

def ParseDescr(strOutList):
	LogEntry ("Grabbing peer description. There are {} lines in the output".format(len(strOutList)))
	for strLine in strOutList:
		if "Exception:" in strLine:
			LogEntry ("Found an exception message, aborting analysis")
			break
		if len(strLine) > 0:
			if strLine[0] == "%":
				LogEntry ("Error: {}".format(strLine))
				break
		if strHostVer == "IOS-XR" or strHostVer == "IOS-XE" or strHostVer == "IOS" or strHostVer == "Nexus":
			if "Description" in strLine:
				return strLine[14:]
#end function ParseDescr

from playsound import playsound, PlaysoundException
import getpass
import time
import sys
import paramiko #pip install paramiko
import socket
import os
import pymysql

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
	# 	sys.exit(9)
	return strOut
#end function GetResults

def ValidateRetry(strHostname,strCmd):
	global iErrCount
	global lstFailedDevsName
	global iAuthFail
	global strPWD
	global strUserName
	global bDevOK
	global iDevAuthFail

	if not bDevOK:
		return "Exception: Bad device"

	strOut = GetResults(strHostname,strCmd)
	while "Exception" in strOut and iErrCount < iMaxError:
		if "SSH Exception:" in strOut or "Socket Exception:" in strOut:
			iErrCount += 1
			LogEntry ("Trying again in 5 sec")
			time.sleep(5)
		elif "Auth Exception" in strOut:
			iDevAuthFail += 1
			if bInteractive:
				playsound(r'c:\windows\media\tada.wav')
				strUserName = getInput("Please provide username for use when login into the routers, enter to use {}: ".format(DefUserName))
				if strUserName == "":
					strUserName = DefUserName
				strPWD = getpass.getpass(prompt="what is the password for {0}: ".format(strUserName))
				if strPWD == "":
					print ("empty password, next device")
					iErrCount = iMaxError
					break
				iAuthFail += 1
				if iAuthFail == iMaxAuthFail:
					iErrCount = iMaxError
					break
			else:
				iErrCount = iMaxError
				break
		else:
			LogEntry("Unknown exception {}\n Next Device!".format(strOut))
			iErrCount = iMaxError
			break
		strOut = GetResults(strHostname,strCmd)


	if "Exception" in strOut:
		lstFailedDevsName.append(strHostname)
		bDevOK = False
		LogEntry ("Exceeded Max Retry's, next device!")
	else:
		bDevOK = True
	return strOut
# end function ValidateRetry

def LogEntry(strMsg):
	if bInteractive:
		print (strMsg)
	strMsg = strMsg.replace("\\","\\\\")
	strMsg = strMsg.replace("'","\\'")
	lstReturn=SQLQuery("insert into networks.tbllogs (vcRouterName,vcLogEntry,iSessionID) VALUES('{}','{}',{});".format(strHostname,strMsg,iSessID),dbConn)
	if not ValidReturn(lstReturn):
		print ("Unexpected: {}".format(lstReturn))
	elif lstReturn[0] != 1:
		print ("Records affected {}, expected 1 record affected".format(lstReturn[0]))

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
	strOut = ValidateRetry(strHostname,dictBaseCmd[strHostVer]["IPv4-GT-Direct"].format("Global Table"))
	ProcessDirectIPv4(strOut.splitlines(),"Global Table")

	for strVRF in lstVRFs:
		strOut = ValidateRetry(strHostname,dictBaseCmd[strHostVer]["IPv4-VRF-Summary"].format(strVRF))
		dictTemp = AnalyzeIPv4Results(strOut.splitlines(),strVRF)
		dictIPv4Peers.update(dictTemp)
		strOut = ValidateRetry(strHostname,dictBaseCmd[strHostVer]["IPv4-VRF-Direct"].format(strVRF))
		ProcessDirectIPv4(strOut.splitlines(),strVRF)

	LogEntry ("Gathering details on {} IPv4 Peers.".format(len(dictIPv4Peers)))
	iCurPeer = 0
	for strPeerIP in dictIPv4Peers:
		iCurPeer += 1
		LogEntry ("IPv4 Peer {} out of {}".format(iCurPeer,len(dictIPv4Peers)))
		strVRF = dictIPv4Peers[strPeerIP]["VRF"]
		if strVRF == "Global Table":
			strOut = ValidateRetry(strHostname,dictBaseCmd[strHostVer]["IPv4-GT-Description"].format(strPeerIP))
			strDescr = ParseDescr(strOut.splitlines())
			strOut = ValidateRetry(strHostname,dictBaseCmd[strHostVer]["IPv4-GT-Receive"].format(strPeerIP))
			AnalyzeIPv4Routes(strOut.splitlines(),strVRF,strPeerIP,strHostname,strDescr)
		else:
			strOut = ValidateRetry(strHostname,dictBaseCmd[strHostVer]["IPv4-VRF-Description"].format(strVRF,strPeerIP))
			strDescr = ParseDescr(strOut.splitlines())
			strOut = ValidateRetry(strHostname,dictBaseCmd[strHostVer]["IPv4-VRF-Receive"].format(strVRF,strPeerIP))
			AnalyzeIPv4Routes(strOut.splitlines(),strVRF,strPeerIP,strHostname,strDescr)

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
		if strVRF == "Global Table":
			strOut = ValidateRetry(strHostname,dictBaseCmd[strHostVer]["IPv6-GT-Description"].format(strPeerIP))
			strDescr = ParseDescr(strOut.splitlines())
			strOut = ValidateRetry(strHostname,dictBaseCmd[strHostVer]["IPv6-GT-Receive"].format(strPeerIP))
			AnalyzeIPv6Routes(strOut.splitlines(),strVRF,strPeerIP,strHostname,strDescr)
		else:
			strOut = ValidateRetry(strHostname,dictBaseCmd[strHostVer]["IPv6-VRF-Description"].format(strVRF,strPeerIP))
			strDescr = ParseDescr(strOut.splitlines())
			strOut = ValidateRetry(strHostname,dictBaseCmd[strHostVer]["IPv6-VRF-Receive"].format(strVRF,strPeerIP))
			AnalyzeIPv6Routes(strOut.splitlines(),strVRF,strPeerIP,strHostname,strDescr)

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

def DotDecGen (iDecValue):
	if iDecValue < 1 or iDecValue > 4294967295:
		return "Invalid"
	# end if

	# Convert decimal to hex
	HexValue = hex(iDecValue)

	#Ensure the results is 8 hex digits long.
	#IP's lower than 16.0.0.0 have trailing 0's that get trimmed off by hex function
	HexValue = "0"*8+HexValue[2:]
	HexValue = "0x"+HexValue[-8:]
	# Convert Hex to dot dec
	strTemp = str(int(HexValue[2:4],16)) + "." + str(int(HexValue[4:6],16)) + "."
	strTemp = strTemp + str(int(HexValue[6:8],16)) + "." + str(int(HexValue[8:10],16))
	return strTemp
# End Function

def DotDec2Int (strValue):
	strHex = ""
	if ValidateIP(strValue) == False:
		return 0
	# end if

	Quads = strValue.split(".")
	for Q in Quads:
		QuadHex = hex(int(Q))
		strwp = "00"+ QuadHex[2:]
		strHex = strHex + strwp[-2:]
	# next

	return int(strHex,16)
# end function

# Function ValidateIP
# Takes in a string and validates that it follows standard IP address format
# Should be four parts with period deliniation
# Each nubmer should be a number from 0 to 255.
def ValidateIP(strToCheck):
	Quads = strToCheck.split(".")
	if len(Quads) != 4:
		return False
	# end if

	for Q in Quads:
		try:
			iQuad = int(Q)
		except ValueError:
			return False
		# end try

		if iQuad > 255 or iQuad < 0:
			return False
		# end if

	return True
# end function

# Function IPCalc
# This function takes in a string of IP address and does the actual final colculation
def IPCalc (strIPAddress):
	strIPAddress=strIPAddress.strip()
	strIPAddress=strIPAddress.replace("\t"," ")
	strIPAddress=strIPAddress.replace("  "," ")
	strIPAddress=strIPAddress.replace(" /","/")
	dictIPInfo={}
	iBitMask=0
	if "/" in strIPAddress:
		IPAddrParts = strIPAddress.split("/")
		strIPAddress=IPAddrParts[0]
		try:
			iBitMask=int(IPAddrParts[1])
		except ValueError:
			iBitMask=32
		# end try
	else:
		iBitMask = 32
	# end if

	if ValidateIP(strIPAddress):
		dictIPInfo['IPAddr'] = strIPAddress
		dictIPInfo['BitMask'] = str(iBitMask)
		iHostcount = 2**(32 - iBitMask)
		dictIPInfo['Hostcount'] = iHostcount
		iDecIPAddr = DotDec2Int(strIPAddress)
		iDecSubID = iDecIPAddr-(iDecIPAddr%iHostcount)
		iDecBroad = iDecSubID + iHostcount - 1
		dictIPInfo['iDecSubID'] = iDecSubID
		dictIPInfo['iDecBroad'] = iDecBroad
		dictIPInfo['Subnet'] = DotDecGen(iDecSubID)
		dictIPInfo['Broadcast'] = DotDecGen(iDecBroad)
	else:
		dictIPInfo['IPError'] = "'" + strIPAddress + "' is not a valid IP!"
	# End if
	return dictIPInfo
# end function


#Start main script
dictDevices={}

lstVRFs=[]
lstFailedDevsName = []
lstRequiredElements=["Match","IPv4-GT-Summary","IPv4-VRF-Summary","IPv4-GT-Receive","IPv4-VRF-Receive","IPv4-GT-Description","IPv4-VRF-Description",
				     "shVRF","IPv6-GT-Summary","IPv6-VRF-Summary","IPv6-GT-Receive","IPv6-VRF-Receive","IPv6-GT-Description","IPv6-VRF-Description",
				     "IPv4-GT-Direct","IPv4-VRF-Direct","IPv6-GT-Direct","IPv6-VRF-Direct"]

strHostname = ""
strLine = "  "
iDevAuthFail = 0
bAbort = False

tStart=time.time()

if os.path.isfile("Routes.txt"):
	print ("Configuration File exists")
else:
	print ("Can't find configuration file Routes.txt, make sure it is the same directory as this script")
	sys.exit(4)

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
		if strConfParts[0] == "NumDaysBreak":
			iNumDays = strConfParts[1]
		if strConfParts[0] == "CollectIPv4":
			bCollectv4 = bool(strConfParts[1].lower()=="yes")
		if strConfParts[0] == "CollectIPv6":
			bCollectv6 = bool(strConfParts[1].lower()=="yes")
		if strConfParts[0] == "RouterUser":
			strUserName = strConfParts[1]
		if strConfParts[0] == "RouterPWD":
			strPWD = strConfParts[1]
		if strConfParts[0] == "RunInteractive":
			bInteractive = bool(strConfParts[1].lower()=="yes")

if bInteractive:
	DefUserName = getpass.getuser()
	print ("This is a router audit script. Your default username is {3}. This is running under Python Version {0}.{1}.{2}".format(sys.version_info[0],sys.version_info[1],sys.version_info[2],DefUserName))
	now = time.asctime()
	print ("The time now is {}".format(now))
	print ("This script will read a router list from a database and log into each router listed in the router list table,\n")

dbConn = SQLConn (strServer,strDBUser,strDBPWD,strInitialDB)
strSQL = "SELECT ifnull(max(iSessionID),0) FROM networks.tbllogs;"
lstReturn = SQLQuery (strSQL,dbConn)
if not ValidReturn(lstReturn):
	LogEntry ("Unexpected: {}".format(lstReturn))
	sys.exit(8)
else:
	iSessID =lstReturn[1][0][0]+1

for strOS in dictBaseCmd:
	for attr in lstRequiredElements:
		if attr not in dictBaseCmd[strOS]:
			LogEntry ("{} is missing definition for {}.\n *** Each OS version requires definitions for the following:\n{}".format(strOS,attr,lstRequiredElements))
			sys.exit(5)
LogEntry ("Starting session {}".format(iSessID))
if not bInteractive:
	print ("Starting session {}".format(iSessID))

if not bCollectv6 and not bCollectv4:
	LogEntry ("neither IPv4 nor IPv6 is set to collect so nothing to do. Exiting!!")
	sys.exit(8)

LogEntry ("Batch size is {} devices".format(iBatchSize))
strSQL = ("SELECT iRouterID,vcHostName FROM networks.tblrouterlist"
	" where dtUpdateCompleted < now() - interval {} day or dtUpdateCompleted is null"
	" order by dtUpdateCompleted limit {};".format(iNumDays, iBatchSize))
lstRouters = SQLQuery (strSQL,dbConn)
if not ValidReturn(lstRouters):
	LogEntry ("Unexpected: {}".format(lstRouters))
	sys.exit(8)
else:
	LogEntry ("Fetched {} rows".format(lstRouters[0]))

if lstRouters[0] == 0:
	LogEntry ("Nothing to do, exiting")
	sys.exit(9)

if strSaveLoc[-1:] != "\\":
	strSaveLoc += "\\"

if not os.path.isdir(strSaveLoc):
	LogEntry ("{} doesn't exists, creating it".format(strSaveLoc))
	os.makedirs(strSaveLoc)
else:
	LogEntry ("Will save output logs to {}".format(strSaveLoc))

if bInteractive:
	LogEntry ("Running Interactively, prompting for router login credentials")
	strUserName = getInput("Please provide username for use when login into the routers, enter to use {}: ".format(DefUserName))
	if strUserName == "":
		strUserName = DefUserName
	# end if username is empty

	strPWD = getpass.getpass(prompt="what is the password for {0}: ".format(strUserName))
	if strPWD == "":
		LogEntry ("empty password, exiting")
		sys.exit(5)
else:
	LogEntry("Running non-interactive")

for dbRow in lstRouters[1]:
	if iDevAuthFail > iMaxDevAuthFail and not bInteractive:
		LogEntry("Too many auth failures in non interactive mode, aborting.")
		bAbort = True
		break
	bDevOK = True
	iErrCount = 0
	iAuthFail = 0
	strHostname = dbRow[1]
	iHostID = dbRow[0]
	strSQL = "delete from networks.tblneighbors where iRouterID = {};".format(iHostID)
	lstReturn = SQLQuery (strSQL,dbConn)
	if not ValidReturn(lstReturn):
		LogEntry ("Unexpected: {}".format(lstReturn))
		bAbort = True
		break
	else:
		LogEntry ("Deleted {} neighbors".format(lstReturn[0]))

	strHostname = strHostname.upper()
	LogEntry ("Processing {} ...".format(strHostname))

	strHostVer = OSDetect()
	LogEntry ("Found Router OS version to be {}".format(strHostVer))
	dictDevices[strHostname] = strHostVer
	strSQL = "update networks.tblrouterlist set dtUpdateStarted = now(), dtUpdateCompleted=null, vcOS = '{}', iSessionID={} where iRouterID = {};".format(strHostVer,iSessID,iHostID)
	lstReturn = SQLQuery (strSQL,dbConn)
	if not ValidReturn(lstReturn):
		LogEntry ("Unexpected: {}".format(lstReturn))
		bAbort = True
		break
	elif lstReturn[0] != 1:
		LogEntry ("Records affected {}, expected 1 record affected".format(lstReturn[0]))

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
			LogEntry ("Unexpected: {}".format(lstReturn))
			break
		elif lstReturn[0] != 1:
			LogEntry ("Records affected {}, expected 1 record affected".format(lstReturn[0]))

LogEntry ("Done processing...")

now = time.asctime()
tStop = time.time()
iElapseSec = tStop - tStart
iMin, iSec = divmod(iElapseSec, 60)
iHours, iMin = divmod(iMin, 60)

if not bAbort:
	if len(lstFailedDevsName) > 0:
		if len(lstFailedDevsName) == 1:
			strdev = "device"
		else:
			strdev = "devices"
		LogEntry ("Failed to complete {} {}, {}, due to errors.".format(len(lstFailedDevsName),strdev,",".join(lstFailedDevsName)))
	else:
		LogEntry ("All devices in the batch completed successfully")

LogEntry ("Completed at {}".format(now))
LogEntry ("Took {0:.2f} seconds to complete, which is {1} hours, {2} minutes and {3:.2f} seconds.".format(iElapseSec,int(iHours),int(iMin),iSec))
if not bInteractive:
	if bAbort:
		print ("Aborted abnormally at {}".format(now))
	else:
		print ("Completed at {}".format(now))
	print ("Took {0:.2f} seconds to complete, which is {1} hours, {2} minutes and {3:.2f} seconds.".format(iElapseSec,int(iHours),int(iMin),iSec))

