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
			"shVRF":"show vrf all"
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
			"shVRF":"show vrf brief"
		}
	}

def ResultHeaders():
	try:
		wsResult.Cells(1,1).Value   = "Router"
		wsResult.Cells(1,2).Value   = "Version"
		wsResult.Cells(1,3).Value   = "Neighbor"
		wsResult.Cells(1,4).Value   = "Remote AS"
		wsResult.Cells(1,5).Value   = "VRF"
		wsResult.Cells(1,6).Value   = "Recv count"
		wsResult.Cells(1,7).Value   = "Adv count"
		wsResult.Cells(1,8).Value   = "Description"
		wsDetails.Cells(1,1).Value  = "Router"
		wsDetails.Cells(1,2).Value  = "Neighbor"
		wsDetails.Cells(1,3).Value  = "VRF"
		wsDetails.Cells(1,4).Value  = "Adv Prefix"
		wsDetails.Cells(1,5).Value  = "Description"
		wsPrefixes.Cells(1,1).Value = "Prefix"
		wsPrefixes.Cells(1,2).Value = "VRFs"
		wsPrefixes.Cells(1,3).Value = "Peer Count"
		wsPrefixes.Cells(1,4).Value = "Router-VRF-PeerIP"
	except Exception as err:
		LogEntry ("Generic Exception: {0}".format(err))

def CollectVRFs():
	strOut = ValidateRetry(strHostname,dictBaseCmd[strHostVer]["shVRF"])
	strOutputList = strOut.splitlines()
	bInSection = False
	lstVRFs = []
	LogEntry ("There are {} lines in the show vrf output".format(len(strOutputList)))
	for strLine in strOutputList:
		if "Exception:" in strLine:
			wsResult.Cells(iOutLineNum,3).Value = strLine
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
				if strHostVer == "Nexus":
					if bInSection and strLineTokens[0] != "default" and strLineTokens[0] != "management" :
						lstVRFs.append(strLineTokens[0])
					if strLineTokens[0]== "VRF-Name" and strLineTokens[1]== "VRF-ID" and strLineTokens[2]== "State":
						bInSection = True
				if strHostVer == "IOS":
					if bInSection and len(strLineTokens) > 2 :
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
			try:
				iOutLineNum += 1
				wsResult.Cells(iOutLineNum,3).Value = strLine
			except Exception as err:
				LogEntry ("Generic Exception: {0}".format(err))

			bFoundABFACL = True
			LogEntry ("Found an exception message, aborting analysis")
			break
		if len(strLine) > 0:
			if strLine[0] == "%":
				LogEntry ("Error: {}".format(strLine))
				break
		strLineTokens = strLine.split()
		if strHostVer == "IOS-XR" or strHostVer == "IOS-XE" or strHostVer == "IOS" or strHostVer == "Nexus":
			# LogEntry("Finding local AS")
			if "local AS number " in strLine:
				iLoc = strLine.find("number ")+7
				iLocalAS = strLine[iLoc:]
				LogEntry ("Local AS:{}".format(iLocalAS))
			if len(strLineTokens) > 1:
				if bNeighborSection:
					if len(strLineTokens) > 8:
						iRemoteAS = strLineTokens[2]
						strCount = str(strLineTokens[9])
						strPeerIP = strLineTokens[0]
						if iRemoteAS != iLocalAS and strCount != "Idle" and strCount != "Active" :
							try:
								iOutLineNum += 1
								wsResult.Cells(iOutLineNum,1).Value = strHostname
								wsResult.Cells(iOutLineNum,2).Value = strHostVer
								wsResult.Cells(iOutLineNum,3).Value = strPeerIP
								wsResult.Cells(iOutLineNum,4).Value = strLineTokens[2]
								wsResult.Cells(iOutLineNum,5).Value = strVRF
								wsResult.Cells(iOutLineNum,6).Value = strLineTokens[9]
							except Exception as err:
								LogEntry ("Generic Exception: {0}".format(err))
							dictIPv4Peers[strPeerIP] = {"VRF":strVRF,"LineID":iOutLineNum}
					else:
						try:
							iOutLineNum += 1
							wsResult.Cells(iOutLineNum,2).Value = "Line {} was unexpectedly short".format(strLine)
						except Exception as err:
							LogEntry ("Generic Exception: {0}".format(err))

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
			try:
				iOutLineNum += 1
				wsResult.Cells(iOutLineNum,3).Value = strLine
			except Exception as err:
				LogEntry ("Generic Exception: {0}".format(err))
			bFoundABFACL = True
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
						if iRemoteAS != iLocalAS and strCount != "Idle" and strCount != "Active" and strPeerIP != "":
							try:
								iOutLineNum += 1
								wsResult.Cells(iOutLineNum,1).Value = strHostname
								wsResult.Cells(iOutLineNum,2).Value = strHostVer
								wsResult.Cells(iOutLineNum,3).Value = strPeerIP
								wsResult.Cells(iOutLineNum,4).Value = iRemoteAS
								wsResult.Cells(iOutLineNum,5).Value = strVRF
								wsResult.Cells(iOutLineNum,6).Value = strCount
							except Exception as err:
								LogEntry ("Generic Exception: {0}".format(err))
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

	LogEntry ("Analyzing received IPv4 routes. There are {} lines in the output".format(len(strOutList)))
	if len(strOutList) > 0:
		if "Exception:" in strOutList[0]:
			iOut2Line += 1
			wsResult.Cells(iOut2Line,3).Value = strOutList[0]
			bFoundABFACL = True
			LogEntry ("Found an exception message, aborting analysis")
			return
	for strLine in strOutList:
		if len(strLine) > 0:
			if strLine[0] == "%":
				LogEntry ("Error: {}".format(strLine))
				break

		iCurLine = iOut2Line - iStartLine + 1
		if iCurLine%500 == 0:
			print ("Completed  {:.1%}".format(iCurLine/len(strOutList)))
		if strHostVer == "IOS-XR":
			strLineTokens = strLine.split()
			if len(strLineTokens) > 1:
				if bInSection and strLineTokens[0] != "Route"  and strLineTokens[0] != "Processed":
					strRcvdPrefix = strLineTokens[1]
					try:
						iOut2Line += 1
						wsDetails.Cells(iOut2Line,1).Value = strHostname
						wsDetails.Cells(iOut2Line,2).Value = strPeerIP
						wsDetails.Cells(iOut2Line,3).Value = strVRF
						wsDetails.Cells(iOut2Line,4).Value = strRcvdPrefix
						wsDetails.Cells(iOut2Line,5).Value = strDescr
					except Exception as err:
						LogEntry ("Generic Exception: {0}".format(err))

					strRouterVRFPeer = strHostname + "-" + strVRF + "-" + strPeerIP
					if strRcvdPrefix in dictPrefixes:
						dictPrefixes[strRcvdPrefix]["Peer"].append(strRouterVRFPeer)
						if strVRF not in dictPrefixes[strRcvdPrefix]["VRF"]:
							dictPrefixes[strRcvdPrefix]["VRF"].append(strVRF)
					else:
						dictPrefixes[strRcvdPrefix]={"VRF":[strVRF],"Peer":[strRouterVRFPeer]}
				if strLineTokens[0] == "Network":
					bInSection = True
				if strLineTokens[0] == "Processed":
					try:
						wsResult.Cells(iLineNum,7).Value = strLineTokens[1]
					except Exception as err:
						LogEntry ("Generic Exception: {0}".format(err))
		if strHostVer == "IOS-XE" or strHostVer == "IOS":
			strLineTokens = strLine.split()
			if len(strLineTokens) > 1:
				if bInSection and strLineTokens[0] != "Total" and strLineTokens[0] != "Network" and strLineTokens[1].count(".") == 3 :
					strRcvdPrefix = strLineTokens[1]
					try:
						iOut2Line += 1
						wsDetails.Cells(iOut2Line,1).Value = strHostname
						wsDetails.Cells(iOut2Line,2).Value = strPeerIP
						wsDetails.Cells(iOut2Line,3).Value = strVRF
						wsDetails.Cells(iOut2Line,4).Value = strRcvdPrefix
						wsDetails.Cells(iOut2Line,5).Value = strDescr
					except Exception as err:
						LogEntry ("Generic Exception: {0}".format(err))

					strRouterVRFPeer = strHostname + "-" + strVRF + "-" + strPeerIP
					if strRcvdPrefix in dictPrefixes:
						dictPrefixes[strRcvdPrefix]["Peer"].append(strRouterVRFPeer)
						if strVRF not in dictPrefixes[strRcvdPrefix]["VRF"]:
							dictPrefixes[strRcvdPrefix]["VRF"].append(strVRF)
					else:
						dictPrefixes[strRcvdPrefix]={"VRF":[strVRF],"Peer":[strRouterVRFPeer]}
				if strLineTokens[0] == "Network":
					bInSection = True
				if strLineTokens[0] == "Total":
					try:
						wsResult.Cells(iLineNum,7).Value = strLineTokens[4]
					except Exception as err:
						LogEntry ("Generic Exception: {0}".format(err))
		if strHostVer == "Nexus":
			strLineTokens = strLine[3:].split()
			if len(strLineTokens) > 1:
				if bInSection and strLineTokens[0] != "Total" and strLineTokens[0] != "Network" and strLineTokens[0].count(".") == 3 :
					strRcvdPrefix = strLineTokens[0]
					try:
						iOut2Line += 1
						wsDetails.Cells(iOut2Line,1).Value = strHostname
						wsDetails.Cells(iOut2Line,2).Value = strPeerIP
						wsDetails.Cells(iOut2Line,3).Value = strVRF
						wsDetails.Cells(iOut2Line,4).Value = strRcvdPrefix
						wsDetails.Cells(iOut2Line,5).Value = strDescr
					except Exception as err:
						LogEntry ("Generic Exception: {0}".format(err))

					strRouterVRFPeer = strHostname + "-" + strVRF + "-" + strPeerIP
					if strRcvdPrefix in dictPrefixes:
						dictPrefixes[strRcvdPrefix]["Peer"].append(strRouterVRFPeer)
						if strVRF not in dictPrefixes[strRcvdPrefix]["VRF"]:
							dictPrefixes[strRcvdPrefix]["VRF"].append(strVRF)
					else:
						dictPrefixes[strRcvdPrefix]={"VRF":[strVRF],"Peer":[strRouterVRFPeer]}
				if strLineTokens[0] == "Network":
					bInSection = True
				if strLineTokens[0] == "Total":
					try:
						wsResult.Cells(iLineNum,7).Value = strLineTokens[4]
					except Exception as err:
						LogEntry ("Generic Exception: {0}".format(err))
	print ("Completed {:.1%}".format(1))
# end function AnalyzeIPv4Routes

def AnalyzeIPv6Routes(strOutList,strVRF,strPeerIP,strHostname,strDescr,iLineNum):
	global iOut2Line
	global dictPrefixes
	iPrefixCount = 0
	strNextHop = ""
	iStartLine = iOut2Line

	LogEntry ("Analyzing received IPv6 routes. There are {} lines in the output".format(len(strOutList)))
	if len(strOutList) > 0:
		if "Exception:" in strOutList[0]:
			iOut2Line += 1
			wsResult.Cells(iOut2Line,3).Value = strOutList[0]
			bFoundABFACL = True
			LogEntry ("Found an exception message, aborting analysis")
			return
	for strLine in strOutList:
		if len(strLine) > 0:
			if strLine[0] == "%":
				LogEntry ("Error: {}".format(strLine))
				break

		iCurLine = iOut2Line - iStartLine + 1
		if iCurLine%500 == 0:
			print ("Completed  {:.1%}".format(iCurLine/len(strOutList)))
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
						try:
							iOut2Line += 1
							wsDetails.Cells(iOut2Line,1).Value = strHostname
							wsDetails.Cells(iOut2Line,2).Value = strPeerIP
							wsDetails.Cells(iOut2Line,3).Value = strVRF
							wsDetails.Cells(iOut2Line,4).Value = strRcvdPrefix
							wsDetails.Cells(iOut2Line,5).Value = strDescr
						except Exception as err:
							LogEntry ("Generic Exception: {0}".format(err))

						strRouterVRFPeer = strHostname + "-" + strVRF + "-" + strPeerIP
						if strRcvdPrefix in dictPrefixes:
							dictPrefixes[strRcvdPrefix]["Peer"].append(strRouterVRFPeer)
							if strVRF not in dictPrefixes[strRcvdPrefix]["VRF"]:
								dictPrefixes[strRcvdPrefix]["VRF"].append(strVRF)
						else:
							dictPrefixes[strRcvdPrefix]={"VRF":[strVRF],"Peer":[strRouterVRFPeer]}
				if strLineTokens[0] == "Processed":
					try:
						wsResult.Cells(iLineNum,7).Value = strLineTokens[1]
					except Exception as err:
						LogEntry ("Generic Exception: {0}".format(err))
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
						try:
							iOut2Line += 1
							wsDetails.Cells(iOut2Line,1).Value = strHostname
							wsDetails.Cells(iOut2Line,2).Value = strPeerIP
							wsDetails.Cells(iOut2Line,3).Value = strVRF
							wsDetails.Cells(iOut2Line,4).Value = strRcvdPrefix
							wsDetails.Cells(iOut2Line,5).Value = strDescr
						except Exception as err:
							LogEntry ("Generic Exception: {0}".format(err))

						strRouterVRFPeer = strHostname + "-" + strVRF + "-" + strPeerIP
						if strRcvdPrefix in dictPrefixes:
							dictPrefixes[strRcvdPrefix]["Peer"].append(strRouterVRFPeer)
							if strVRF not in dictPrefixes[strRcvdPrefix]["VRF"]:
								dictPrefixes[strRcvdPrefix]["VRF"].append(strVRF)
						else:
							dictPrefixes[strRcvdPrefix]={"VRF":[strVRF],"Peer":[strRouterVRFPeer]}# end function AnalyzeIPv6Routes
				if strLineTokens[0] == "Total":
					try:
						wsResult.Cells(iLineNum,7).Value = strLineTokens[4]
					except Exception as err:
						LogEntry ("Generic Exception: {0}".format(err))
		if strHostVer == "Nexus":
			strLineTokens = strLine[3:].split()
			if len(strLineTokens) > 0:
				if (strLineTokens[0].find(":") == 4 and "/" in strLineTokens[0]) or strLineTokens[0]=="0::/0" :
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
						try:
							iOut2Line += 1
							wsDetails.Cells(iOut2Line,1).Value = strHostname
							wsDetails.Cells(iOut2Line,2).Value = strPeerIP
							wsDetails.Cells(iOut2Line,3).Value = strVRF
							wsDetails.Cells(iOut2Line,4).Value = strRcvdPrefix
							wsDetails.Cells(iOut2Line,5).Value = strDescr
						except Exception as err:
							LogEntry ("Generic Exception: {0}".format(err))

						strRouterVRFPeer = strHostname + "-" + strVRF + "-" + strPeerIP
						if strRcvdPrefix in dictPrefixes:
							dictPrefixes[strRcvdPrefix]["Peer"].append(strRouterVRFPeer)
							if strVRF not in dictPrefixes[strRcvdPrefix]["VRF"]:
								dictPrefixes[strRcvdPrefix]["VRF"].append(strVRF)
						else:
							dictPrefixes[strRcvdPrefix]={"VRF":[strVRF],"Peer":[strRouterVRFPeer]}
				if strLineTokens[0] == "Processed":
					try:
						wsResult.Cells(iLineNum,7).Value = strLineTokens[1]
					except Exception as err:
						LogEntry ("Generic Exception: {0}".format(err))
	print ("Completed {:.1%}".format(1))

def ParseDescr(strOutList,iLineNum):
	LogEntry ("Grabbing peer description. There are {} lines in the output".format(len(strOutList)))
	for strLine in strOutList:
		if "Exception:" in strLine:
			wsResult.Cells(iLineNum,7).Value = strLine
			bFoundABFACL = True
			LogEntry ("Found an exception message, aborting analysis")
			break
		if len(strLine) > 0:
			if strLine[0] == "%":
				LogEntry ("Error: {}".format(strLine))
				break
		if strHostVer == "IOS-XR" or strHostVer == "IOS-XE" or strHostVer == "IOS" or strHostVer == "Nexus":
			if "Description" in strLine:
				# print ("Descr line: {}".format(strLine))
				try:
					wsResult.Cells(iLineNum,8).Value = strLine[14:]
				except Exception as err:
					LogEntry ("Generic Exception: {0}".format(err))

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
lstRequiredElements=["Match","IPv4-GT-Summary","IPv4-VRF-Summary","IPv4-GT-Receive","IPv4-VRF-Receive","IPv4-GT-Description","IPv4-VRF-Description",
				     "shVRF","IPv6-GT-Summary","IPv6-VRF-Summary","IPv6-GT-Receive","IPv6-VRF-Receive","IPv6-GT-Description","IPv6-VRF-Description"]

iResultNum = 0
iResult2Num = 0
iResult3Num = 0
iResultColNum = 1
iDetailsColNum = 1
iPrefixColNum = 1
tStart=time.time()
iInputColumn = 1
strOutFolderName = strSummarySheet

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
		strOutFile = strOutPath + strHostname + ".txt"
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
	except Exception as err:
		LogEntry ("Generic Exception: {0}".format(err))
		strOut = "Generic Exception: {0}".format(err)
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
	strTimeStamp = time.strftime("%m-%d-%Y %H:%M:%S")
	objLogOut.write("{0} : {1}\n".format(strTimeStamp,strMsg))
	print (strMsg)

def StatusUpdate():
	tElapse = time.time()
	iElapseSec = tElapse - tStart
	ieMin, ieSec = divmod(iElapseSec, 60)
	ieHours, ieMin = divmod(ieMin, 60)
	if ieHours == 0:
		if ieMin == 0:
			strElapse = "Elapse time {:.2f} seconds.".format(ieSec)
		else:
			strElapse = "Elapse time {} minutes.".format(int(ieMin))
	else:
		strElapse = "Elapse time {} hours and {} minutes.".format(int(ieHours),int(ieMin))

	if iPercentComplete > 0:
		iEstRemainSec = (iElapseSec/iPercentComplete)-iElapseSec
		iMin, iSec = divmod(iEstRemainSec, 60)
		iHours, iMin = divmod(iMin, 60)
		if iHours == 0:
			if iMin == 0:
				strEstRemain = "Estimated time left {:.2f} seconds. ".format(iSec)
			else:
				strEstRemain = "Estimated time left {} minutes. ".format(int(iMin))
		else:
			strEstRemain = "Estimated time left {} hours and {} minutes. ".format(int(iHours),int(iMin))
	else:
		strEstRemain = ""
	return strEstRemain + strElapse

def OSDetect():
	strHostVer = "Unknown"
	strOut = ValidateRetry(strHostname,"show version")
	for strOS in dictBaseCmd:
		if dictBaseCmd[strOS]["Match"] in strOut:
			strHostVer = strOS
		if strOS == "IOS":
			continue
	if strHostVer == "Unknown" :
		if dictBaseCmd["IOS"]["Match"] in strOut:
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
	if bFailedDev:
		LogEntry ("Retrying {}, {} failed devices left to retry.".format(strHostname,len(lstFailedDevsName)-1))
	else:
		LogEntry ("{0} is device {1} out of {2}. Completed {3:.1%} {4}".format(strHostname,iInputLineNum - 1,iDevCount,iPercentComplete,StatusUpdate()))
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
			strOut = ValidateRetry(strHostname,dictBaseCmd[strHostVer]["IPv4-GT-Receive"].format(strPeerIP))
			AnalyzeIPv4Routes(strOut.splitlines(),strVRF,strPeerIP,strHostname,strDescr,iLineNum)
		else:
			strOut = ValidateRetry(strHostname,dictBaseCmd[strHostVer]["IPv4-VRF-Description"].format(strVRF,strPeerIP))
			strDescr = ParseDescr(strOut.splitlines(), iLineNum)
			strOut = ValidateRetry(strHostname,dictBaseCmd[strHostVer]["IPv4-VRF-Receive"].format(strVRF,strPeerIP))
			AnalyzeIPv4Routes(strOut.splitlines(),strVRF,strPeerIP,strHostname,strDescr,iLineNum)
		if bFailedDev:
			LogEntry ("Retrying {}, {} failed devices left to retry.".format(strHostname,len(lstFailedDevsName)-1))
		else:
			LogEntry ("{} is device {} out of {}. Completed {:.1%} {}".format(strHostname,iInputLineNum - 1,iDevCount,iPercentComplete,StatusUpdate()))

def IPv6Peers():
	dictIPv6Peers={}
	strOut = ValidateRetry(strHostname,dictBaseCmd[strHostVer]["IPv6-GT-Summary"])
	dictIPv6Peers = AnalyzeIPv6Results(strOut.splitlines(),"Global Table")

	for strVRF in lstVRFs:
		strOut = ValidateRetry(strHostname,dictBaseCmd[strHostVer]["IPv6-VRF-Summary"].format(strVRF))
		dictTemp = AnalyzeIPv6Results(strOut.splitlines(),strVRF)
		dictIPv6Peers.update(dictTemp)
	if bFailedDev:
		LogEntry ("Retrying {}, {} failed devices left to retry.".format(strHostname,len(lstFailedDevsName)-1))
	else:
		LogEntry ("{} is device {} out of {}. Completed {:.1%} {}".format(strHostname,iInputLineNum - 1,iDevCount,iPercentComplete,StatusUpdate()))

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
			strOut = ValidateRetry(strHostname,dictBaseCmd[strHostVer]["IPv6-GT-Receive"].format(strPeerIP))
			AnalyzeIPv6Routes(strOut.splitlines(),strVRF,strPeerIP,strHostname,strDescr,iLineNum)
		else:
			strOut = ValidateRetry(strHostname,dictBaseCmd[strHostVer]["IPv6-VRF-Description"].format(strVRF,strPeerIP))
			strDescr = ParseDescr(strOut.splitlines(), iLineNum)
			strOut = ValidateRetry(strHostname,dictBaseCmd[strHostVer]["IPv6-VRF-Receive"].format(strVRF,strPeerIP))
			AnalyzeIPv6Routes(strOut.splitlines(),strVRF,strPeerIP,strHostname,strDescr,iLineNum)
		if bFailedDev:
			LogEntry ("Retrying {}, {} failed devices left to retry.".format(strHostname,len(lstFailedDevsName)-1))
		else:
			LogEntry ("{} is device {} out of {}. Completed {:.1%} {}".format(strHostname,iInputLineNum - 1,iDevCount,iPercentComplete,StatusUpdate()))


DefUserName = getpass.getuser()
print ("This is a router audit script. Your default username is {3}. This is running under Python Version {0}.{1}.{2}".format(sys.version_info[0],sys.version_info[1],sys.version_info[2],DefUserName))
now = time.asctime()
print ("The time now is {}".format(now))
print ("This script will read a source excel sheet and log into each router listed in the identified column,\n"
		"starting with row 2, execute defined command and write results across multiple tabs")
for strOS in dictBaseCmd:
	for attr in lstRequiredElements:
		if attr not in dictBaseCmd[strOS]:
			print ("{} is missing definition for {}.\n *** Each OS version requires definitions for the following:\n{}".format(strOS,attr,lstRequiredElements))
			sys.exit(5)

getInput ("Press enter to bring up a file open dialog so you may choose the source Excel file")

root = tk.Tk()
root.withdraw()
strWBin = filedialog.askopenfilename(title = "Select spreadsheet",filetypes = (("Excel files","*.xlsx"),("Text Files","*.txt"),("All Files","*.*")))
if strWBin =="":
	print ("You cancelled so I'm exiting")
	sys.exit(2)
#end if no file
strWBin = strWBin.replace("/","\\")
print ("You selected: " + strWBin)
print ("File extention is:{}".format(strWBin[-4:]))
if strWBin[-4:] != "xlsx" :
	print ("I was expecting an excel input file with xlsx extension. Don't know what do to except exit")
	sys.exit(2)
#end if xlsx
iLoc = strWBin.rfind("\\")
strPath = strWBin[:iLoc]
iLoc = strWBin.rfind(".")
strLogFile = strWBin[:iLoc]+".log"
objLogOut = open(strLogFile,"w",1)
LogEntry("Started logging to {}".format(strLogFile))
strOutPath = strPath+"\\"+strOutFolderName+"\\"
if not os.path.exists (strOutPath) :
	os.makedirs(strOutPath)
	print ("\nPath '{0}' for output files didn't exists, so I create it!\n".format(strOutPath))
print ("Opening that spreadsheet, please stand by ...")
app = win32.gencache.EnsureDispatch('Excel.Application')
app.Visible = True
wbin = app.Workbooks.Open (strWBin,0,False)
print ("I will be gathering all BGP peers and what is being received over them:\n")
print ("Here is a list of sheets in this spreadsheet:")
iSheetCount = wbin.Worksheets.Count
for i in range(1,iSheetCount+1):
	strTemp = wbin.Worksheets(i).Name
	dictSheets[strTemp]=i
	if strTemp == strSummarySheet :
		iResultNum = i
		continue
	if strTemp == strDetailSheet :
		iResult2Num = i
		continue
	if strTemp == strPrefixeSheet :
		iResult3Num = i
		continue
	print ("{0}) {1}".format(i,strTemp))
# end for loop
i += 1
print ("{}) So sorry, wrong file, please exist".format(i))
strSelect = getInput("Which of the above choices is the input sheet: ")
try:
    iSelect = int(strSelect)
except ValueError:
    print("Invalid choice: '{}'".format(strSelect))
    iSelect = i
if iSelect < 1 or iSelect > i :
	print("Invalid choice: {}".format(iSelect))
	iSelect = i
if iSelect == iResultNum or iSelect == iResult2Num or iSelect == iResult3Num:
	print("Sorry that is the results sheet, not the input sheet.")
	iSelect = i
if iSelect == i :
	sys.exit(1)
wsInput = wbin.Worksheets(iSelect)
print ("Input sheet '{}' activated".format(wsInput.Name))

print ("Here is a preview of the data in that sheet")
iCol = 1
while wsInput.Cells(1,iCol).Value != "" and wsInput.Cells(1,iCol).Value != None :
	print ("{0}) {1}".format(iCol,wsInput.Cells(1,iCol).Value))
	print ("     {0}".format(wsInput.Cells(2,iCol).Value))
	print ("     {0}".format(wsInput.Cells(3,iCol).Value))
	iCol += 1
print ("{}) So sorry, wrong file, please exist".format(iCol))
strSelect = getInput("Please select the column with the list of router: ")
try:
    iInputColumn = int(strSelect)
except ValueError:
    print("Invalid choice: '{}'".format(strSelect))
    iInputColumn = iCol
if iInputColumn < 1 or iInputColumn > iCol :
	print("Invalid choice: {}".format(iInputColumn))
	iInputColumn = iCol
if iInputColumn == iCol :
	sys.exit(1)
# wbin.Worksheets(1).Activate
if strSummarySheet in dictSheets:
	strSelect = getInput("Summary sheet '{}' exists, is it OK to overwrite (y/n): ".format(strSummarySheet))
	strSelect = strSelect.lower()
	if strSelect == "":
		strSelect = "y"
		print ("Blank input assuming yes")
	if strSelect[0] == "y":
		wsResult = wbin.Worksheets(strSummarySheet)
		wsResult.Range(wsResult.Columns(1),wsResult.Columns(15)).Clear()
	else:
		print ("No problem at all, exiting so you can rename, etc.")
		sys.exit(1)
else:
	print ("Summary sheet not found, creating one")
	wbin.Sheets.Add(After=wsInput)
	wsResult = wbin.ActiveSheet
	wsResult.Name = strSummarySheet

if strDetailSheet in dictSheets:
	strSelect = getInput("Detail sheet '{}' exists, is it OK to overwrite (y/n): ".format(strDetailSheet))
	strSelect = strSelect.lower()
	if strSelect == "":
		strSelect = "y"
		print ("Blank input assuming yes")
	if strSelect[0] == "y":
		wsDetails = wbin.Worksheets(strDetailSheet)
		wsDetails.Range(wsDetails.Columns(1),wsDetails.Columns(15)).Clear()
	else:
		print ("No problem at all, exiting so you can rename, etc.")
		sys.exit(1)
else:
	print ("Detail sheet not found, creating one")
	wbin.Sheets.Add(After=wsResult)
	wsDetails = wbin.ActiveSheet
	wsDetails.Name = strDetailSheet

if strPrefixeSheet in dictSheets:
	strSelect = getInput("Prefix sheet '{}' exists, is it OK to overwrite (y/n): ".format(strPrefixeSheet))
	strSelect = strSelect.lower()
	if strSelect == "":
		strSelect = "y"
		print ("Blank input assuming yes")
	if strSelect[0] == "y":
		wsPrefixes = wbin.Worksheets(strPrefixeSheet)
		wsPrefixes.Range(wsPrefixes.Columns(1),wsPrefixes.Columns(555)).Clear()
	else:
		print ("No problem at all, exiting so you can rename, etc.")
		sys.exit(1)
else:
	print ("Prefix sheet not found, creating one")
	wbin.Sheets.Add(After=wsDetails)
	wsPrefixes = wbin.ActiveSheet
	wsPrefixes.Name = strPrefixeSheet

iInputLineNum = 2
while wsInput.Cells(iInputLineNum,iInputColumn).Value != "" and wsInput.Cells(iInputLineNum,iInputColumn).Value != None :
	iInputLineNum += 1
iDevCount = iInputLineNum-2
wsResult.Select()
LogEntry("BGP Summary tab activated")

print ("There are {} devices listed in sheet '{}' column {}".format(iDevCount,wsInput.Name,iInputColumn))

strUserName = getInput("Please provide username for use when login into the routers, enter to use {}: ".format(DefUserName))
if strUserName == "":
	strUserName = DefUserName
# end if username is empty

strPWD = getpass.getpass(prompt="what is the password for {0}: ".format(strUserName))
if strPWD == "":
	print ("empty password, exiting")
	sys.exit(5)

ResultHeaders()

iInputLineNum = 2
iOutLineNum = 1
iOut2Line = 1
strHostname = wsInput.Cells(iInputLineNum,iInputColumn).Value
FailedDevs = []
lstFailedDevsName = []
bDevOK = True
bFailedDev = False


while strHostname != "" and strHostname != None :
	iErrCount = 0
	iAuthFail = 0
	strHostname = strHostname.upper()
	LogEntry ("Processing {} ...".format(strHostname))
	iPercentComplete = (iInputLineNum - 2)/iDevCount

	LogEntry ("Device {0} out of {1}. Completed {2:.1%} {3}".format(iInputLineNum - 1,iDevCount,iPercentComplete,StatusUpdate()))
	strHostVer = OSDetect()

	LogEntry ("Found IOS version to be {}".format(strHostVer))
	dictDevices[strHostname] = strHostVer
	if strHostVer == "Unknown":
		LogEntry("Can't process unknown platform")
		if bDevOK:
			try:
				iOutLineNum += 1
				wsResult.Cells(iOutLineNum,1).Value = strHostname
				wsResult.Cells(iOutLineNum,2).Value = strHostVer
			except Exception as err:
				LogEntry ("Generic Exception: {0}".format(err))
		iInputLineNum += 1
		strHostname = wsInput.Cells(iInputLineNum,iInputColumn).Value
		continue

	if bDevOK:
		lstVRFs = CollectVRFs()
		IPv4Peers()
		IPv6Peers()

	iInputLineNum += 1
	strHostname = wsInput.Cells(iInputLineNum,iInputColumn).Value
# End while hostname
LogEntry ("{} out of {} Completed. Completed {:.1%}".format(iDevCount,iDevCount,1))

if len(FailedDevs) == 0:
	LogEntry ("All devices are successful")
	bFailedDev = False
else:
	bFailedDev = True
	if len(FailedDevs) == 1:
		strdev = "device"
	else:
		strdev = "devices"
	LogEntry ("Failed to complete {} {}, {}, due to errors.".format(len(FailedDevs),strdev,",".join(lstFailedDevsName)))
	LogEntry ("Retrying them one more time")
	for iRetryLine in FailedDevs:
		iErrCount = 0
		iAuthFail = 0
		strHostname = wsInput.Cells(iRetryLine,iInputColumn).Value
		LogEntry ("Retrying {} ...".format(strHostname))
		strHostVer = OSDetect()
		LogEntry ("Found IOS version to be {}".format(strHostVer))
		dictDevices[strHostname] = strHostVer
		if bDevOK:
			lstFailedDevsName.remove(strHostname)
		if strHostVer != "Unknown" :
			lstVRFs = CollectVRFs()
			IPv4Peers()
			# IPv6Peers()
		else:
			if not bDevOK:
				strHostVer = "Failed to connect"
			try:
				iOutLineNum += 1
				wsResult.Cells(iOutLineNum,1).Value = strHostname
				wsResult.Cells(iOutLineNum,2).Value = strHostVer
				if bDevOK:
					LogEntry("Can't processess unknown platform")
				else:
					LogEntry("Failed to connect on retry")
			except Exception as err:
				LogEntry ("Generic Exception: {0}".format(err))

LogEntry ("Done processing...")
while wsResult.Cells(1,iResultColNum).Value != "" and wsResult.Cells(1,iResultColNum).Value != None :
	iResultColNum += 1
while wsDetails.Cells(1,iDetailsColNum).Value != "" and wsDetails.Cells(1,iDetailsColNum).Value != None :
	iDetailsColNum += 1

iResultColNum -= 1
iDetailsColNum -= 1

iOut3Line  = 2
iPrefixCount = len(dictPrefixes)
LogEntry ("Starting on 'By Prefix' tab...")
# iPrefixColNum = 4
try:
	for strPrefix in dictPrefixes:
		iColNumber = 4
		wsPrefixes.Cells(iOut3Line,1).Value = strPrefix
		wsPrefixes.Cells(iOut3Line,2).Value = ";".join(dictPrefixes[strPrefix]["VRF"])
		wsPrefixes.Cells(iOut3Line,3).Value = len(dictPrefixes[strPrefix]["Peer"])
		for strRouter in dictPrefixes[strPrefix]["Peer"]:
			wsPrefixes.Cells(iOut3Line,iColNumber).Value = strRouter
			iColNumber += 1
		if iColNumber > iPrefixColNum:
			iPrefixColNum = iColNumber
		iOut3Line += 1
		if iOut3Line%500 == 0:
			print ("Completed {} lines, {:.1%} complete".format(iOut3Line,iOut3Line/iPrefixCount))
except Exception as err:
	LogEntry ("Generic Exception: {0}".format(err))

LogEntry ("Prefix tab completed. Formating ...")
iColNumber = 4
if iColNumber > iPrefixColNum:
	iPrefixColNum = iColNumber
while iColNumber < iPrefixColNum:
	wsPrefixes.Cells(1,iColNumber).Value = "Router-VRF-PeerIP #{}".format(iColNumber-3)
	LogEntry("Prefix tab: added header Router-VRF-PeerIP #{} to column {}".format(iColNumber-3,iColNumber))
	iColNumber += 1

iPrefixColNum -= 1


wsResult.ListObjects.Add(xlSrcRange, wsResult.Range(wsResult.Cells(1,1),wsResult.Cells(iOutLineNum,iResultColNum)),"",xlYes,"","TableStyleLight1").Name = wsResult.Name
wsDetails.ListObjects.Add(xlSrcRange, wsDetails.Range(wsDetails.Cells(1,1),wsDetails.Cells(iOut2Line,iDetailsColNum)),"",xlYes,"","TableStyleLight1").Name = wsDetails.Name
print ("Formating Prefix tab. Out3={} iPrefixColNum={}".format(iOut3Line,iPrefixColNum))
wsPrefixes.ListObjects.Add(xlSrcRange, wsPrefixes.Range(wsPrefixes.Cells(1,1),wsPrefixes.Cells(iOut3Line,iPrefixColNum)),"",xlYes,"","TableStyleLight1").Name = wsPrefixes.Name
try:
	wsResult.Range(wsResult.Cells(1,1),wsResult.Cells(iOutLineNum,iResultColNum)).EntireColumn.AutoFit()
	wsDetails.Range(wsDetails.Cells(1,1),wsDetails.Cells(iOut2Line,iDetailsColNum)).EntireColumn.AutoFit()
	wsPrefixes.Range(wsPrefixes.Cells(1,1),wsPrefixes.Cells(iOut3Line,iPrefixColNum)).EntireColumn.AutoFit()
	wbin.Save()
except Exception as err:
	LogEntry ("Generic Exception: {0}".format(err))

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
objLogOut.close
print ("Log file {} closed".format(strLogFile))

