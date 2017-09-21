'''
Router Audit
Author Siggi Bjarnason Copyright 2017
Website http://www.ipcalc.us/ and http://www.icecomputing.com

Description:
This is script that will discover all the BGP peers on a particular Cisco Router running IOS-XR
and caputer all the routes being advertised over each peer.

Following packages need to be installed as administrator
pip install pypiwin32
pip install paramiko

'''

strSummarySheet = "BGPSummary"
strDetailSheet = "BGPAdv"
strCommand1 = "show bgp summary"
strCommand2 = "show bgp vrf all summary"
iMaxError = 4

def ResultHeaders():
	wsResult.Cells(1,1).Value   = "Router"
	wsResult.Cells(1,2).Value   = "Neighbor"
	wsResult.Cells(1,3).Value   = "Remote AS"
	wsResult.Cells(1,4).Value   = "VRF"
	wsResult.Cells(1,5).Value   = "Recv count"
	wsResult.Cells(1,6).Value   = "Description"
	wsDetails.Cells(1,1).Value  = "Router"
	wsDetails.Cells(1,2).Value  = "Neighbor"
	wsDetails.Cells(1,3).Value  = "VRF"
	wsDetails.Cells(1,4).Value  = "Adv Prefix"

def AnalyzeResults(strOutputList):
	global iOutLineNum
	dictPeers = {}
	bNeighborSection = False
	strVRF = "Global Table"

	print ("There are {} lines in the output".format(len(strOutputList)))
	for strLine in strOutputList:
		if "Exception:" in strLine:
			wsResult.Cells(iOutLineNum,3).Value = strLine
			bFoundABFACL = True
			print ("Found an exception message, aborting analysis")
			break

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
					if iRemoteAS != iLocalAS and strCount != "Idle" :
						iOutLineNum += 1
						wsResult.Cells(iOutLineNum,1).Value = strHostname
						wsResult.Cells(iOutLineNum,2).Value = strPeerIP
						wsResult.Cells(iOutLineNum,3).Value = strLineTokens[2]
						wsResult.Cells(iOutLineNum,4).Value = strVRF
						wsResult.Cells(iOutLineNum,5).Value = strLineTokens[9]
						dictPeers[strPeerIP] = {}
						dictPeers[strPeerIP]["VRF"] = strVRF
						dictPeers[strPeerIP]["LineID"] = iOutLineNum
				else:
					wsResult.Cells(iOutLineNum,2).Value = "Line {} was unexpectedly short".format(strLine)
			if strLineTokens[0]== "Neighbor":
				bNeighborSection = True
		else:
			bNeighborSection = False
	return dictPeers

# end function AnalyzeResults

def AnalyzeRoutes(strOutList,strVRF,strPeerIP,strHostname):
	global iOut2Line
	bInSection = False

	print ("Analyzing route table. There are {} lines in the output".format(len(strOutList)))
	for strLine in strOutList:
		if "Exception:" in strLine:
			wsResult.Cells(iOutLineNum,3).Value = strLine
			bFoundABFACL = True
			print ("Found an exception message, aborting analysis")
			break

		strLineTokens = strLine.split()
		if len(strLineTokens) > 1:
			if bInSection and strLineTokens[0] != "Route"  and strLineTokens[0] != "Processed":
				iOut2Line += 1
				wsDetails.Cells(iOut2Line,1).Value = strHostname
				wsDetails.Cells(iOut2Line,2).Value = strPeerIP
				wsDetails.Cells(iOut2Line,3).Value = strVRF
				wsDetails.Cells(iOut2Line,4).Value = strLineTokens[0]
			if strLineTokens[0] == "Network":
				bInSection = True
# end function AnalyzeRoutes

def ParseDescr(strOutList,iLineNum):
	print ("Analyzing route table. There are {} lines in the output".format(len(strOutList)))
	for strLine in strOutList:
		if "Exception:" in strLine:
			wsResult.Cells(iLineNum,6).Value = strLine
			bFoundABFACL = True
			print ("Found an exception message, aborting analysis")
			break

		if "Description" in strLine:
			wsResult.Cells(iLineNum,6).Value = strLine[14:]
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
dictPeers={}
iResultNum = 0
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
		print ("sent {0} to {1}".format(strCmd,strHostname))
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
		print ("output written to "+strOutFile)
	except paramiko.ssh_exception.AuthenticationException as err:
		print ("Auth Exception: {0}".format(err))
		sys.exit(1)
	except paramiko.SSHException as err:
		print ("SSH Exception: {0}".format(err))
		strOut = "SSH Exception: {0}".format(err)
	except OSError as err:
		print ("Socket Exception: {0}".format(err))
		strOut = "Socket Exception: {0}".format(err)
	except Exception as err:
		print ("Generic Exception: {0}".format(err))
		strOut = "Generic Exception: {0}".format(err)
	return strOut
#end function GetResults

def ValidateRetry(strHostname,strCmd):
	global iErrCount
	global FailedDevs

	strOut = GetResults(strHostname,strCmd)
	if "SSH Exception:" in strOut or "Socket Exception:" in strOut:
		while iErrCount < iMaxError:
			print ("Trying again in 5 sec")
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
	print ("I was expecting an excel input file xlsx extension. Don't know what do to except exit")
	sys.exit(2)
#end if xlsx
iLoc = strWBin.rfind("/")
strPath = strWBin[:iLoc]
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
if iSelect == iResultNum:
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

if strSummarySheet in dictSheets:
	strSelect = getInput("Summary sheet '{}' exists and some data will be overwritten, OK (y/n): ".format(strSummarySheet))
	strSelect = strSelect.lower()
	if strSelect[0] == "y":
		wsResult = wbin.Worksheets(strSummarySheet)
	else:
		sys.exit(1)
else:
	print ("Summary sheet not found, creating one")
	wbin.Sheets.Add()
	wsResult = wbin.ActiveSheet
	wsResult.Name = strSummarySheet

if strDetailSheet in dictSheets:
	strSelect = getInput("Detail sheet '{}' exists and some data will be overwritten, OK (y/n): ".format(strDetailSheet))
	strSelect = strSelect.lower()
	if strSelect[0] == "y":
		wsDetails = wbin.Worksheets(strDetailSheet)
	else:
		sys.exit(1)
else:
	print ("Detail sheet not found, creating one")
	wbin.Sheets.Add()
	wsDetails = wbin.ActiveSheet
	wsDetails.Name = strDetailSheet
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
strHostname = wsInput.Cells(iInputLineNum,iInputColumn).Value
FailedDevs = []

while strHostname != "" and strHostname != None :
	iErrCount = 0
	print ("Processing {} ...".format(strHostname))
	dictDevices[strHostname] = strCommand1
	strOut = ValidateRetry(strHostname,strCommand1)
	strOut += ValidateRetry(strHostname,strCommand2)
	dictPeers = AnalyzeResults(strOut.splitlines())

	for strPeerIP in dictPeers:
		strVRF = dictPeers[strPeerIP]["VRF"]
		iLineNum = dictPeers[strPeerIP]["LineID"]
		if strVRF == "Global Table":
			strCmd = "show bgp neighbors {} advertised-routes".format(strPeerIP)
			strCmd2 = "show bgp neighbors {} | include Description:".format(strPeerIP)
		else:
			strCmd = "show bgp vrf {} neighbors {} advertised-routes".format(strVRF,strPeerIP)
			strCmd2 = "show bgp vrf {} neighbors {} | include Description:".format(strVRF,strPeerIP)
		strOut = ValidateRetry(strHostname,strCmd2)
		ParseDescr(strOut.splitlines(), iLineNum)
		strOut = ValidateRetry(strHostname,strCmd)
		AnalyzeRoutes(strOut.splitlines(),strVRF,strPeerIP,strHostname)

	time.sleep(1)
	iInputLineNum += 1
	strHostname = wsInput.Cells(iInputLineNum,iInputColumn).Value
# End while hostname
if len(FailedDevs) == 0:
	print ("All devices are successful")
else:
	print ("Failed to complete {} lines {} due to errors.".format(len(FailedDevs),FailedDevs))
	print ("Retrying them one more time")
	for iInputLineNum in FailedDevs:
		strHostname = wsInput.Cells(iInputLineNum,iInputColumn).Value
		print ("Processing {} ...".format(strHostname))
		dictDevices[strHostname] = strCommand1
		strOut = GetResults(strHostname,strCommand1)
		strOut += GetResults(strHostname,strCommand2)
		if "Exception:"	not in strOut:
			FailedDevs.remove(iInputLineNum)
			dictPeers = AnalyzeResults(strOut.splitlines())

wsResult.Range(wsResult.Cells(1, 1),wsResult.Cells(iOutLineNum,12)).EntireColumn.AutoFit()
wsDetails.Range(wsDetails.Cells(1, 1),wsDetails.Cells(iOut2Line,12)).EntireColumn.AutoFit()
wbin.Save()
now = time.asctime()
tStop = time.time()
iElapseSec = tStop - tStart
iMin, iSec = divmod(iElapseSec, 60)
iHours, iMin = divmod(iMin, 60)
if len(FailedDevs) > 0:
	print ("Failed to complete lines {} due to errors.".format(FailedDevs))
print ("Completed at {}".format(now))
print ("Took {0:.2f} seconds to complete, which is {1} hours, {2} minutes and {3:.2f} seconds.".format(iElapseSec,iHours,iMin,iSec))

# messagebox.showinfo("All Done","Processing has completed, return to the command window for details")