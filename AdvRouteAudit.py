'''
Router Audit
Author Siggi Bjarnason Copyright 2017
Website http://www.ipcalc.us/ and http://www.icecomputing.com

Description:
This is script that will discover all the BGP peers on a particular Cisco Router running
and caputer all the routes being advertised over each peer.

Following packages need to be installed as administrator
pip install pypiwin32
pip install paramiko

'''

strSummarySheet = "BGPSummary"
strDetailSheet  = "By Router"
strPrefixeSheet = "By Prefix"
iMaxError = 4
dictBaseCmd = {
		"IOS-XR":{
			"Match":"IOS XR",
			"IPv4-GT-Summary":"show bgp ipv4 unicast summary",
			"IPv4-VRF-Summary":"show bgp vrf all ipv4 unicast summary",
			"IPv4-GT-Advertise":"show bgp ipv4 unicast neighbors {} advertised-routes",
			"IPv4-VRF-Advertise":"show bgp vrf {} ipv4 unicast neighbors {} advertised-routes",
			"IPv4-GT-Description":"show bgp ipv4 unicast neighbors {} | include Description:",
			"IPv4-VRF-Description":"show bgp vrf {} ipv4 unicast neighbors {} | include Description:",
		},
		"IOS-XE":{
			"Match":"IOS XE",
			"IPv4-GT-Summary":"show bgp ipv4 unicast summary",
			"IPv4-VRF-Summary":"show bgp vrf all ipv4 unicast summary",
			"IPv4-GT-Advertise":"show bgp ipv4 unicast neighbors {} advertised-routes",
			"IPv4-VRF-Advertise":"show bgp vrf {} ipv4 unicast neighbors {} advertised-routes",
			"IPv4-GT-Description":"show bgp ipv4 unicast neighbors {} | include Description:",
			"IPv4-VRF-Description":"show bgp vrf {} ipv4 unicast neighbors {} | include Description:",
		}
	}

def ResultHeaders():
	wsResult.Cells(1,1).Value   = "Router"
	wsResult.Cells(1,2).Value   = "Version"
	wsResult.Cells(1,3).Value   = "Neighbor"
	wsResult.Cells(1,4).Value   = "Remote AS"
	wsResult.Cells(1,5).Value   = "VRF"
	wsResult.Cells(1,6).Value   = "Recv count"
	wsResult.Cells(1,7).Value   = "Description"
	wsDetails.Cells(1,1).Value  = "Router"
	wsDetails.Cells(1,2).Value  = "Neighbor"
	wsDetails.Cells(1,3).Value  = "VRF"
	wsDetails.Cells(1,4).Value  = "Adv Prefix"
	wsPrefixes.Cells(1,1).Value = "Prefix"
	wsPrefixes.Cells(1,2).Value = "VRFs"
	wsPrefixes.Cells(1,3).Value = "Peer Count"
	wsPrefixes.Cells(1,4).Value = "Router-VRF-PeerIP"

def AnalyzeResults(strOutputList):
	global iOutLineNum
	dictPeers = {}
	bNeighborSection = False
	strVRF = "Global Table"

	LogEntry ("There are {} lines in the output".format(len(strOutputList)))
	for strLine in strOutputList:
		if "Exception:" in strLine:
			wsResult.Cells(iOutLineNum,3).Value = strLine
			bFoundABFACL = True
			LogEntry ("Found an exception message, aborting analysis")
			break

		if strHostVer == "IOS-XR":
			if "local AS number " in strLine:
				iLoc = strLine.find("number ")+7
				iLocalAS = strLine[iLoc:]
			strLineTokens = strLine.split()
			strPeerIP = ""
			if len(strLineTokens) > 1:
				if strLineTokens[0]== "VRF:":
					strVRF = strLineTokens[1]
				if bNeighborSection:
					if len(strLineTokens) > 8:
						iRemoteAS = strLineTokens[2]
						strCount = str(strLineTokens[9])
						strPeerIP = strLineTokens[0]
						if iRemoteAS != iLocalAS and strCount != "Idle" and strCount != "Active" :
							iOutLineNum += 1
							wsResult.Cells(iOutLineNum,1).Value = strHostname
							wsResult.Cells(iOutLineNum,2).Value = strHostVer
							wsResult.Cells(iOutLineNum,3).Value = strPeerIP
							wsResult.Cells(iOutLineNum,4).Value = strLineTokens[2]
							wsResult.Cells(iOutLineNum,5).Value = strVRF
							wsResult.Cells(iOutLineNum,6).Value = strLineTokens[9]
							dictPeers[strPeerIP] = {}
							dictPeers[strPeerIP]["VRF"] = strVRF
							dictPeers[strPeerIP]["LineID"] = iOutLineNum
					else:
						wsResult.Cells(iOutLineNum,2).Value = "Line {} was unexpectedly short".format(strLine)
				if strLineTokens[0]== "Neighbor":
					bNeighborSection = True
			else:
				bNeighborSection = False
		if strHostVer == "IOS-XE":
			wsResult.Cells(iOutLineNum,1).Value = strHostname
			wsResult.Cells(iOutLineNum,2).Value = strHostVer
			wsResult.Cells(iOutLineNum,3).Value = "Parsing not implemented yet"
		if strHostVer == "IOS":
			wsResult.Cells(iOutLineNum,1).Value = strHostname
			wsResult.Cells(iOutLineNum,2).Value = strHostVer
			wsResult.Cells(iOutLineNum,3).Value = "Parsing not implemented yet"
		if strHostVer == "Unknown":
			wsResult.Cells(iOutLineNum,1).Value = strHostname
			wsResult.Cells(iOutLineNum,2).Value = strHostVer
			wsResult.Cells(iOutLineNum,3).Value = "Can't parse output for unknown platform"
	return dictPeers

# end function AnalyzeResults

def AnalyzeRoutes(strOutList,strVRF,strPeerIP,strHostname):
	global iOut2Line
	global dictPrefixes
	bInSection = False

	LogEntry ("Analyzing route table. There are {} lines in the output".format(len(strOutList)))
	for strLine in strOutList:
		if "Exception:" in strLine:
			wsResult.Cells(iOutLineNum,3).Value = strLine
			bFoundABFACL = True
			LogEntry ("Found an exception message, aborting analysis")
			break

		strLineTokens = strLine.split()
		if len(strLineTokens) > 1:
			if bInSection and strLineTokens[0] != "Route"  and strLineTokens[0] != "Processed":
				iOut2Line += 1
				strAdvPrefix = strLineTokens[0]
				wsDetails.Cells(iOut2Line,1).Value = strHostname
				wsDetails.Cells(iOut2Line,2).Value = strPeerIP
				wsDetails.Cells(iOut2Line,3).Value = strVRF
				wsDetails.Cells(iOut2Line,4).Value = strAdvPrefix
				strRouterVRFPeer = strHostname + "-" + strVRF + "-" + strPeerIP
				if strAdvPrefix in dictPrefixes:
					dictPrefixes[strAdvPrefix]["Peer"].append(strRouterVRFPeer)
					if strVRF not in dictPrefixes[strAdvPrefix]["VRF"]:
						dictPrefixes[strAdvPrefix]["VRF"].append(strVRF)
				else:
					dictPrefixes[strAdvPrefix]={}
					dictPrefixes[strAdvPrefix]["VRF"]=[strVRF]
					dictPrefixes[strAdvPrefix]["Peer"]=[strRouterVRFPeer]
			if strLineTokens[0] == "Network":
				bInSection = True
# end function AnalyzeRoutes

def ParseDescr(strOutList,iLineNum):
	LogEntry ("Grabbing peer description. There are {} lines in the output".format(len(strOutList)))
	for strLine in strOutList:
		if "Exception:" in strLine:
			wsResult.Cells(iLineNum,7).Value = strLine
			bFoundABFACL = True
			LogEntry ("Found an exception message, aborting analysis")
			break

		if "Description" in strLine:
			wsResult.Cells(iLineNum,7).Value = strLine[14:]
#end function ParseDescr

import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox
import win32com.client as win32 #pip install pypiwin32
import getpass
import time
import sys
import paramiko #pip install paramiko
import socket
import os

dictSheets={}
dictDevices={}
dictPrefixes={}
dictPeers={}
iResultNum = 0
iResult2Num = 0
iResult3Num = 0
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
		objFileOut.write (strOut)
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
	global iAuthFail
	global strPWD
	global strUserName

	strOut = GetResults(strHostname,strCmd)
	if "Auth Exception" in strOut:
		while iAuthFail < 3:
			strUserName = getInput("Please provide username for use when login into the routers, enter to use {}: ".format(DefUserName))
			if strUserName == "":
				strUserName = DefUserName
			# end if username is empty
			strPWD = getpass.getpass(prompt="what is the password for {0}: ".format(strUserName))
			if strPWD == "":
				print ("empty password, exiting")
				sys.exit(5)
			iAuthFail += 1
			strOut = GetResults(strHostname,strCmd)
			if "Auth Exception" not in strOut:
				iAuthFail = 0
				break
		if iAuthFail == 3:
			sys.exit(5)


	if "SSH Exception:" in strOut or "Socket Exception:" in strOut:
		while iErrCount < iMaxError:
			LogEntry ("Trying again in 5 sec")
			time.sleep(5)
			strOut = GetResults(strHostname,strCmd)
			if "SSH Exception:" in strOut or "Socket Exception:" in strOut:
				iErrCount += 1
			else:
				break
		if iErrCount == iMaxError:
			FailedDevs.append(iInputLineNum)
	return strOut
# end function ValidateRetry

def LogEntry(strMsg):
	strTimeStamp = time.strftime("%m-%d-%Y %H:%M:%S")
	objLogOut.write("{0} : {1}\n".format(strTimeStamp,strMsg))
	print (strMsg)

DefUserName = getpass.getuser()
print ("This is a router audit script. Your default username is {3}. This is running under Python Version {0}.{1}.{2}".format(sys.version_info[0],sys.version_info[1],sys.version_info[2],DefUserName))
now = time.asctime()
print ("The time now is {}".format(now))
print ("This script will read a source excel sheet and log into each router listed in the identified column,\n"
		"starting with row 2, execute defined command and write results on tab called '{}' which gets created if it does not exists.".format(strSummarySheet))

getInput ("Press enter to bring up a file open dialog so you may choose the source Excel file")

root = tk.Tk()
root.withdraw()
strWBin = filedialog.askopenfilename(title = "Select spreadsheet",filetypes = (("Excel files","*.xlsx"),("Text Files","*.txt"),("All Files","*.*")))
if strWBin =="":
	print ("You cancelled so I'm exiting")
	sys.exit(2)
#end if no file

print ("You selected: " + strWBin)
print ("File extention is:{}".format(strWBin[-4:]))
if strWBin[-4:] != "xlsx" :
	print ("I was expecting an excel input file with xlsx extension. Don't know what do to except exit")
	sys.exit(2)
#end if xlsx
iLoc = strWBin.rfind("/")
strPath = strWBin[:iLoc]
iLoc = strWBin.rfind(".")
strLogFile = strWBin[:iLoc]+".log"
objLogOut = open(strLogFile,"w",1)
LogEntry("Started logging to {}".format(strLogFile))
strOutPath = strPath+"/"+strOutFolderName+"/"
if not os.path.exists (strOutPath) :
	os.makedirs(strOutPath)
	print ("\nPath '{0}' for output files didn't exists, so I create it!\n".format(strOutPath))
print ("Opening that spreadsheet, please stand by ...")
app = win32.gencache.EnsureDispatch('Excel.Application')
app.Visible = True
wbin = app.Workbooks.Open (strWBin,0,False)
print ("I will be gathering all BGP peers and what is being advertised over them:\n")
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
	wbin.Sheets.Add(After=wbin.Worksheets(iSheetCount))
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
# End if valid input sheet

strUserName = getInput("Please provide username for use when login into the routers, enter to use {}: ".format(DefUserName))
if strUserName == "":
	strUserName = DefUserName
# end if username is empty

strPWD = getpass.getpass(prompt="what is the password for {0}: ".format(strUserName))

ResultHeaders()

iInputLineNum = 2
iOutLineNum = 1
iOut2Line = 1
strHostVer = "Unknown"
strHostname = wsInput.Cells(iInputLineNum,iInputColumn).Value
FailedDevs = []
while strHostname != "" and strHostname != None :
	iErrCount = 0
	iAuthFail = 0
	LogEntry ("Processing {} ...".format(strHostname))
	dictDevices[strHostname] = strHostVer
	strOut = ValidateRetry(strHostname,"show version")
	for strOS in dictBaseCmd:
		if strOS == "IOS":
			if "IOS" in strOut and strHostVer == "Unknown" :
				strHostVer = "IOS"
		else:
			if dictBaseCmd[strOS]["Match"] in strOut:
				strHostVer = strOS
	LogEntry ("Found IOS version to be {}".format(strHostVer))

	strOut = ValidateRetry(strHostname,dictBaseCmd[strHostVer]["IPv4-GT-Summary"])
	strOut += ValidateRetry(strHostname,dictBaseCmd[strHostVer]["IPv4-VRF-Summary"])
	dictPeers = AnalyzeResults(strOut.splitlines())

	for strPeerIP in dictPeers:
		strVRF = dictPeers[strPeerIP]["VRF"]
		iLineNum = dictPeers[strPeerIP]["LineID"]
		if strVRF == "Global Table":
			strOut = ValidateRetry(strHostname,dictBaseCmd[strHostVer]["IPv4-GT-Description"].format(strPeerIP))
			ParseDescr(strOut.splitlines(), iLineNum)
			strOut = ValidateRetry(strHostname,dictBaseCmd[strHostVer]["IPv4-GT-Advertise"].format(strVRF,strPeerIP))
			AnalyzeRoutes(strOut.splitlines(),strVRF,strPeerIP,strHostname)
		else:
			strOut = ValidateRetry(strHostname,dictBaseCmd[strHostVer]["IPv4-VRF-Description"].format(strVRF,strPeerIP))
			ParseDescr(strOut.splitlines(), iLineNum)
			strOut = ValidateRetry(strHostname,dictBaseCmd[strHostVer]["IPv4-VRF-Advertise"].format(strVRF,strPeerIP))
			AnalyzeRoutes(strOut.splitlines(),strVRF,strPeerIP,strHostname)

	time.sleep(1)
	iInputLineNum += 1
	strHostname = wsInput.Cells(iInputLineNum,iInputColumn).Value
# End while hostname

if len(FailedDevs) == 0:
	LogEntry ("All devices are successful")
	bFailedDev = False
else:
	bFailedDev = True
	LogEntry ("Failed to complete {} lines {} due to errors.".format(len(FailedDevs),FailedDevs))
	LogEntry ("Retrying them one more time")
	for iInputLineNum in FailedDevs:
		strHostname = wsInput.Cells(iInputLineNum,iInputColumn).Value
		LogEntry ("Processing {} ...".format(strHostname))
		dictDevices[strHostname] = dictBaseCmd[strHostVer]["IPv4-GT-Summary"]
		strOut = GetResults(strHostname,dictBaseCmd[strHostVer]["IPv4-GT-Summary"])
		strOut += GetResults(strHostname,dictBaseCmd[strHostVer]["IPv4-VRF-Summary"])
		if "Exception:"	not in strOut:
			FailedDevs.remove(iInputLineNum)
			dictPeers = AnalyzeResults(strOut.splitlines())

iOut3Line  = 2
for strPrefix in dictPrefixes:
	iColNumber = 4
	wsPrefixes.Cells(iOut3Line,1).Value = strPrefix
	wsPrefixes.Cells(iOut3Line,2).Value = ";".join(dictPrefixes[strPrefix]["VRF"])
	wsPrefixes.Cells(iOut3Line,3).Value = len(dictPrefixes[strPrefix]["Peer"])
	for strRouter in dictPrefixes[strPrefix]["Peer"]:
		wsPrefixes.Cells(iOut3Line,iColNumber).Value = strRouter
		iColNumber += 1
	iOut3Line += 1
wsResult.Range(wsResult.Cells(1,1),wsResult.Cells(iOutLineNum,12)).EntireColumn.AutoFit()
wsDetails.Range(wsDetails.Cells(1,1),wsDetails.Cells(iOut2Line,12)).EntireColumn.AutoFit()
wsPrefixes.Range(wsPrefixes.Cells(1,1),wsPrefixes.Cells(iOut3Line,312)).EntireColumn.AutoFit()
wbin.Save()
now = time.asctime()
tStop = time.time()
iElapseSec = tStop - tStart
iMin, iSec = divmod(iElapseSec, 60)
iHours, iMin = divmod(iMin, 60)
if bFailedDev and len(FailedDevs) == 0:
	LogEntry ("All devices successful after final retries")
if len(FailedDevs) > 0:
	LogEntry ("Failed to complete lines {} due to errors.".format(FailedDevs))
LogEntry ("Completed at {}".format(now))
LogEntry ("Took {0:.2f} seconds to complete, which is {1} hours, {2} minutes and {3:.2f} seconds.".format(iElapseSec,int(iHours),int(iMin),iSec))
objLogOut.close
print ("Log file {} closed".format(strLogFile))

