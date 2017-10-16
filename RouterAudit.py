'''
Router Audit
Author Siggi Bjarnason Copyright 2017
Website http://www.ipcalc.us/ and http://www.icecomputing.com

Description:
This is script that will execute a command defined in variable strCommand, on every router listed in a provided spreadsheet.
The output of that command will be saved to per router file in a folder name, specified by variable strOutFolderName, in the same folder as the spreadsheet.
That ouput will also be passed to function AnalyzeResults for parsing. The parsed results will be stored in a seperate sheet in the spreadsheet.
The name of the sheet with the results is defined by variable strResultSheetName, the header row for that sheet gets created by function ResultHeaders.
No changes or custimization should be needed past the function AnalyzeResults.

If you need to feed a variable into the command, put {0} for the first variable {1} for the second, etc.
For example:
strCommand = "show run {0} access-list {1}"
where {0} represent the IP version (ipv4/ipv6) and {1} reprsents the ACL name that will be fed in through the Excel file.

Following packages need to be installed as administrator
pip install pypiwin32
pip install paramiko
pip install playsound

'''

strResultSheetName = "MyOutput3"
strCommand = "show run ipv6 access-list"
iMaxError = 6 # How many times can we experience an error on a single device before marking the device failed and moving on, 0 based
iMaxAuthFail = 2 # How many auth failures can happen in a row. Zero based.

def ResultHeaders():
	wsResult.Cells(1,1).Value  = "primaryIPAddress"
	wsResult.Cells(1,2).Value  = "hostName"
	wsResult.Cells(1,3).Value  = "ABFACLName"
	wsResult.Cells(1,4).Value  = "CNO1"
	wsResult.Cells(1,5).Value  = "CNO2"
	wsResult.Cells(1,6).Value  = "CNO3"
	wsResult.Cells(1,7).Value  = "CNO4"
	wsResult.Cells(1,8).Value  = "CNO5"
	wsResult.Cells(1,9).Value  = "PDNS"
	wsResult.Cells(1,10).Value = "SDNS"
	wsResult.Cells(1,11).Value = "NextHopIP"
	wsResult.Cells(1,12).Value = "NextHopIP2"

def AnalyzeResults(strOutputList):
	global iOutLineNum
	bFoundABFACL = False
	bInACL = False
	try:
		wsResult.Cells(iOutLineNum,1).Value = socket.gethostbyname(strHostname)
	except OSError as err:
		LogEntry ("Socket Exception: {0}".format(err))
		wsResult.Cells(iOutLineNum,1).Value  = "Socket Exception: {0}".format(err)
	except Exception as err:
		LogEntry ("Generic Exception: {0}".format(err))
		wsResult.Cells(iOutLineNum,1).Value  = "Generic Exception: {0}".format(err)

	wsResult.Cells(iOutLineNum,2).Value = strHostname
	LogEntry ("There are {} number of lines in the output".format(len(strOutputList)))
	for strLine in strOutputList:
		if "Exception:" in strLine:
			wsResult.Cells(iOutLineNum,3).Value = strLine
			bFoundABFACL = True
			LogEntry ("Found an exception message, aborting analysis")
			break

		strLineTokens = strLine.split(" ")
		if len(strLineTokens) > 1:
			if strLineTokens[2][:11]== "ABF-NAT-PAT":
				if bFoundABFACL:
					iOutLineNum += 1
					wsResult.Cells(iOutLineNum,1).Value = socket.gethostbyname(strHostname)
					wsResult.Cells(iOutLineNum,2).Value = strHostname
				bFoundABFACL = True
				bInACL = True
				wsResult.Cells(iOutLineNum,3).Value = strLineTokens[2]
			elif strLineTokens[1] == "access-list":
				bInACL = False
			if bInACL:
				if len(strLineTokens) > 5:
					if strLineTokens[1] == "70":
						wsResult.Cells(iOutLineNum,4).Value = strLineTokens[6]
					if strLineTokens[1] == "80":
						wsResult.Cells(iOutLineNum,5).Value = strLineTokens[6]
					if strLineTokens[1] == "90":
						wsResult.Cells(iOutLineNum,6).Value = strLineTokens[6]
					if strLineTokens[1] == "100":
						wsResult.Cells(iOutLineNum,7).Value = strLineTokens[6]
					if strLineTokens[1] == "110":
						wsResult.Cells(iOutLineNum,8).Value = strLineTokens[6]
				if len(strLineTokens) > 8:
					if strLineTokens[1] == "140":
						wsResult.Cells(iOutLineNum,9).Value = strLineTokens[5]
						wsResult.Cells(iOutLineNum,12).Value = strLineTokens[10]
					if strLineTokens[1] == "130":
						# print (strLine)
						wsResult.Cells(iOutLineNum,10).Value = strLineTokens[5]
						wsResult.Cells(iOutLineNum,11).Value = strLineTokens[10]
	if bFoundABFACL == False:
		wsResult.Cells(iOutLineNum,3).Value = "Not found"
	iOutLineNum += 1
# end function AnalyzeResults

#No customization should be nessisary past this point.

import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox
import win32com.client as win32 #pip install pypiwin32
from playsound import playsound, PlaysoundException #pip install playsound
import getpass
import time
import sys
import paramiko #pip install paramiko
import socket
import os

dictSheets={}
dictDevices={}
iResultNum = 0
tStart=time.time()
iInputColumn = 1
strOutFolderName = strResultSheetName
iResultColNum = 1

xlSrcExternal = 0 #External data source
xlSrcModel = 4 #PowerPivot Model
xlSrcQuery = 3 #Query
xlSrcRange = 1 #Range
xlSrcXml = 2 #XML
xlGuess = 0 # Excel determines whether there is a header, and where it is, if there is one.
xlNo = 2 # Default. The entire range should be sorted.
xlYes = 1 # The entire range should not be sorted.

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
		strOut += stderr.read()
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
			strPWD = getpass.getpass(prompt="what is the password for {0}: ".format(strUserName))
			if strPWD == "":
				LogEntry ("empty password, next device")
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

DefUserName = getpass.getuser()
print ("This is a router audit script. Your default username is {3}. This is running under Python Version {0}.{1}.{2}".format(sys.version_info[0],sys.version_info[1],sys.version_info[2],DefUserName))
now = time.asctime()
print ("The time now is {}".format(now))
print ("This script will read a source excel sheet and log into each router listed in the identified column,\n"
		"starting with row 2, execute defined command and write results on tab called '{}' which gets created if it does not exists.".format(strResultSheetName))

getInput ("Press enter to bring up a file open dialog so you may choose the source Excel file")

root = tk.Tk()
root.withdraw()
strWBin = filedialog.askopenfilename(title = "Select spreadsheet",filetypes = (("Excel files","*.xlsx"),("Text Files","*.txt"),("All Files","*.*")))
if strWBin =="":
	print ("You cancelled so I'm exiting")
	sys.exit(2)

print ("You selected: " + strWBin)
print ("File extention is:{}".format(strWBin[-4:]))
if strWBin[-4:] != "xlsx" :
	print ("I was expecting an excel input file xlsx extension. Don't know what do to except exit")
	sys.exit(2)
iLoc = strWBin.rfind("/")
strPath = strWBin[:iLoc]
strOutPath = strPath+"/"+strOutFolderName+"/"
iLoc = strWBin.rfind(".")
strLogFile = strWBin[:iLoc]+".log"
objLogOut = open(strLogFile,"w",1)
LogEntry("Started logging to {}".format(strLogFile))
if not os.path.exists (strOutPath) :
	os.makedirs(strOutPath)
	LogEntry ("\nPath '{0}' for output files didn't exists, so I create it!\n".format(strOutPath))
LogEntry ("Opening that spreadsheet, please stand by ...")
app = win32.gencache.EnsureDispatch('Excel.Application')
app.Visible = True
wbin = app.Workbooks.Open (strWBin,0,False)
LogEntry ("I will be executing the following command on a list of routers from one of the sheets in this spreadsheet:\n{}".format(strCommand))
LogEntry ("Here is a list of sheets in this spreadsheet:")
iSheetCount = wbin.Worksheets.Count
for i in range(1,iSheetCount+1):
	strTemp = wbin.Worksheets(i).Name
	dictSheets[strTemp]=i
	if strTemp == strResultSheetName :
		iResultNum = i
		continue
	LogEntry ("{0}) {1}".format(i,strTemp))
# end for loop
i += 1
LogEntry ("{}) So sorry, wrong file, please exist".format(i))
strSelect = getInput("Which of the above choices is the input sheet: ")
try:
    iSelect = int(strSelect)
except ValueError:
    LogEntry("Invalid choice: '{}'".format(strSelect))
    iSelect = i
if iSelect < 1 or iSelect > i :
	LogEntry("Invalid choice: {}".format(iSelect))
	iSelect = i
if iSelect == iResultNum:
	LogEntry("Sorry that is the results sheet, not the input sheet.")
	iSelect = i
if iSelect == i :
	sys.exit(1)
wsInput = wbin.Worksheets(iSelect)
LogEntry ("Input sheet '{}' activated".format(wsInput.Name))

LogEntry ("Here is a preview of the data in that sheet")
iCol = 1
while wsInput.Cells(1,iCol).Value != "" and wsInput.Cells(1,iCol).Value != None :
	LogEntry ("{0}) {1}".format(iCol,wsInput.Cells(1,iCol).Value))
	LogEntry ("     {0}".format(wsInput.Cells(2,iCol).Value))
	LogEntry ("     {0}".format(wsInput.Cells(3,iCol).Value))
	iCol += 1
LogEntry ("{}) So sorry, wrong file, please exist".format(iCol))
strSelect = getInput("Please select the column with the list of router: ")
try:
    iInputColumn = int(strSelect)
except ValueError:
    LogEntry("Invalid choice: '{}'".format(strSelect))
    iInputColumn = iCol
if iInputColumn < 1 or iInputColumn > iCol :
	LogEntry("Invalid choice: {}".format(iInputColumn))
	iInputColumn = iCol
if iInputColumn == iCol :
	sys.exit(1)

iCmdVars = 0
strTemp = "{" + str(iCmdVars) + "}"
while strTemp in strCommand:
	iCmdVars += 1
	strTemp = "{" + str(iCmdVars) + "}"

iCmdCol = []
if iCmdVars < iCol-1:
	for x in range(iCmdVars):
		iCol = 1
		while wsInput.Cells(1,iCol).Value != "" and wsInput.Cells(1,iCol).Value != None :
			LogEntry ("{0}) {1}".format(iCol,wsInput.Cells(1,iCol).Value))
			LogEntry ("     {0}".format(wsInput.Cells(2,iCol).Value))
			LogEntry ("     {0}".format(wsInput.Cells(3,iCol).Value))
			iCol += 1
		LogEntry ("{}) So sorry, wrong file, please exist".format(iCol))
		strSelect = getInput("Please select the column with the content of variable {}: ".format(x))
		try:
		    iCmdCol.append (int(strSelect))
		except ValueError:
		    LogEntry("Invalid choice: '{}'".format(strSelect))
		    iCmdCol.append (iCol)
		if iCmdCol[x] < 1 or iCmdCol[x] > iCol :
			LogEntry("Invalid choice: {}".format(iCmdCol[x]))
			iCmdCol[x] = iCol
		if iCmdCol[x] == iCol :
			sys.exit(1)
else:
	LogEntry ("Input sheet '{0}' only has {1} columns, you have {2} variables in your command and thus need {3} columns.".format(
			wsInput.Name,iCol-1,iCmdVars,iCmdVars+1))
	sys.exit(1)


if strResultSheetName in dictSheets:
	strSelect = getInput("Results sheet '{}' exists and some data will be overwritten, OK (y/n): ".format(strResultSheetName))
	strSelect = strSelect.lower()
	if strSelect == "":
		strSelect = "y"
		print ("Blank input assuming yes")
	if strSelect[0] == "y":
		wsResult = wbin.Worksheets(strResultSheetName)
		wsResult.Cells.Clear()
	else:
		print ("No problem at all, exiting so you can rename, etc.")
		sys.exit(1)
else:
	LogEntry ("No results sheet found, creating one")
	wbin.Sheets.Add(After=wsInput)
	wsResult = wbin.ActiveSheet
	wsResult.Name = strResultSheetName

iInputLineNum = 2
while wsInput.Cells(iInputLineNum,iInputColumn).Value != "" and wsInput.Cells(iInputLineNum,iInputColumn).Value != None :
	iInputLineNum += 1
iDevCount = iInputLineNum-2
wsResult.Select()
LogEntry("Results tab activated")


strUserName = getInput("Please provide username for use when login into the routers, enter to use {}: ".format(DefUserName))
if strUserName == "":
	strUserName = DefUserName

strPWD = getpass.getpass(prompt="what is the password for {0}: ".format(strUserName))
if strPWD == "":
	print ("empty password, exiting")
	sys.exit(5)

ResultHeaders()

iInputLineNum = 2
iOutLineNum = 2
strHostname = wsInput.Cells(iInputLineNum,iInputColumn).Value
strCmdVars = []
FailedDevs = []
lstFailedDevsName = []
bDevOK = True
bFailedDev = False


for x in range(iCmdVars):
	strCmdVars.append(wsInput.Cells(iInputLineNum,iCmdCol[x]).Value)

while strHostname != "" and strHostname != None :
	iErrCount = 0
	iAuthFail = 0
	strHostname = strHostname.upper()
	LogEntry ("Processing {} ...".format(strHostname))
	iPercentComplete = (iInputLineNum - 2)/iDevCount

	LogEntry ("Device {0} out of {1}. Completed {2:.1%} {3}".format(iInputLineNum - 1,iDevCount,iPercentComplete,StatusUpdate()))
	if iCmdVars > 0:
		strCmd = strCommand.format(*strCmdVars)
	else:
		strCmd = strCommand
	LogEntry ("Processing {} ...".format(strHostname))
	dictDevices[strHostname] = strCmd
	strOut = ValidateRetry(strHostname,strCmd)
	AnalyzeResults(strOut.splitlines())
	time.sleep(1)
	iInputLineNum += 1
	strHostname = wsInput.Cells(iInputLineNum,iInputColumn).Value
	for x in range(iCmdVars):
		strCmdVars[x] = (wsInput.Cells(iInputLineNum,iCmdCol[x]).Value)

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
		dictDevices[strHostname] = strCmd
		if bDevOK:
			lstFailedDevsName.remove(strHostname)

		for x in range(iCmdVars):
			strCmdVars[x] = (wsInput.Cells(iInputLineNum,iCmdCol[x]).Value)
		if iCmdVars > 0:
			strCmd = strCommand.format(*strCmdVars)
		else:
			strCmd = strCommand
		strOut = ValidateRetry(strHostname,strCmd)
		AnalyzeResults(strOut.splitlines())

LogEntry ("Done processing...")
while wsResult.Cells(1,iResultColNum).Value != "" and wsResult.Cells(1,iResultColNum).Value != None :
	iResultColNum += 1
iResultColNum -= 1
wsResult.ListObjects.Add(xlSrcRange, wsResult.Range(wsResult.Cells(1,1),wsResult.Cells(iOutLineNum,iResultColNum)),"",xlYes,"","TableStyleLight1").Name = wsResult.Name
wsResult.Range(wsResult.Cells(1, 1),wsResult.Cells(iOutLineNum,iResultColNum)).EntireColumn.AutoFit()
wbin.Save()
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
LogEntry ("Took {0:.2f} seconds to complete, which is {1} hours, {2} minutes and {3:.2f} seconds.".format(iElapseSec,iHours,iMin,iSec))

objLogOut.close
print ("Log file {} closed".format(strLogFile))
