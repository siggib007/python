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

'''

strResultSheetName = "Aggregates"
strCommand = "show running-config | include aggregate"
iMaxError = 4

def ResultHeaders():
	wsResult.Cells(1,1).Value  = "primaryIPAddress"
	wsResult.Cells(1,2).Value  = "hostName"
	wsResult.Cells(1,3).Value  = "Aggr1"
	wsResult.Cells(1,4).Value  = "Aggr2"
	wsResult.Cells(1,5).Value  = "Aggr3"
	wsResult.Cells(1,6).Value  = "Aggr4"
	wsResult.Cells(1,7).Value  = "Aggr5"

def AnalyzeResults(strOutputList):
	global iOutLineNum
	iIntNum = 0
	try:
		wsResult.Cells(iOutLineNum,1).Value = socket.gethostbyname(strHostname)
	except OSError as err:
		print ("Socket Exception: {0}".format(err))
		wsResult.Cells(iOutLineNum,1).Value  = "Socket Exception: {0}".format(err)
	except Exception as err:
		print ("Generic Exception: {0}".format(err))
		wsResult.Cells(iOutLineNum,1).Value  = "Generic Exception: {0}".format(err)

	wsResult.Cells(iOutLineNum,2).Value = strHostname

	print ("There are {} number of lines in the output".format(len(strOutputList)))
	for strLine in strOutputList:
		if "Exception:" in strLine:
			print ("Found an exception message, aborting analysis")
			wsResult.Cells(iOutLineNum,3).Value = strLine
			break

		if "aggregate-address 26" in strLine :
			wsResult.Cells(iOutLineNum,3+iIntNum).Value = strLine[21:]
			iIntNum += 1
	iOutLineNum += 1
# end function AnalyzeResults

#No customization should be nessisary past this point.

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
iResultNum = 0
tStart=time.time()
iInputColumn = 1
strOutFolderName = strResultSheetName

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
print ("I will be executing the following command on a list of routers from one of the sheets in this spreadsheet:\n{}".format(strCommand))
print ("Here is a list of sheets in this spreadsheet:")
iSheetCount = wbin.Worksheets.Count
for i in range(1,iSheetCount+1):
	strTemp = wbin.Worksheets(i).Name
	dictSheets[strTemp]=i
	if strTemp == strResultSheetName :
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
			print ("{0}) {1}".format(iCol,wsInput.Cells(1,iCol).Value))
			print ("     {0}".format(wsInput.Cells(2,iCol).Value))
			print ("     {0}".format(wsInput.Cells(3,iCol).Value))
			iCol += 1
		print ("{}) So sorry, wrong file, please exist".format(iCol))
		strSelect = getInput("Please select the column with the content of variable {}: ".format(x))
		try:
		    iCmdCol.append (int(strSelect))
		except ValueError:
		    print("Invalid choice: '{}'".format(strSelect))
		    iCmdCol.append (iCol)
		if iCmdCol[x] < 1 or iCmdCol[x] > iCol :
			print("Invalid choice: {}".format(iCmdCol[x]))
			iCmdCol[x] = iCol
		if iCmdCol[x] == iCol :
			sys.exit(1)
else:
	print ("Input sheet '{0}' only has {1} columns, you have {2} variables in your command and thus need {3} columns.".format(
			wsInput.Name,iCol-1,iCmdVars,iCmdVars+1))
	sys.exit(1)


if strResultSheetName in dictSheets:
	strSelect = getInput("Results sheet '{}' exists and some data will be overwritten, OK (y/n): ".format(strResultSheetName))
	strSelect = strSelect.lower()
	if strSelect[0] == "y":
		wsResult = wbin.Worksheets(strResultSheetName)
	else:
		sys.exit(1)
else:
	print ("No results sheet found, creating one")
	wbin.Sheets.Add()
	wsResult = wbin.ActiveSheet
	wsResult.Name = strResultSheetName
# End if valid input sheet

strUserName = getInput("Please provide username for use when login into the routers, enter to use {}: ".format(DefUserName))
if strUserName == "":
	strUserName = DefUserName
# end if username is empty

strPWD = getpass.getpass(prompt="what is the password for {0}: ".format(strUserName))

ResultHeaders()

iInputLineNum = 2
iOutLineNum = 2
strHostname = wsInput.Cells(iInputLineNum,iInputColumn).Value
strCmdVars = []
FailedDevs = []

for x in range(iCmdVars):
	strCmdVars.append(wsInput.Cells(iInputLineNum,iCmdCol[x]).Value)

while strHostname != "" and strHostname != None :
	iErrCount = 0
	if iCmdVars > 0:
		strCmd = strCommand.format(*strCmdVars)
	else:
		strCmd = strCommand
	print ("Processing {} ...".format(strHostname))
	dictDevices[strHostname] = strCmd
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
	AnalyzeResults(strOut.splitlines())
	time.sleep(1)
	iInputLineNum += 1
	strHostname = wsInput.Cells(iInputLineNum,iInputColumn).Value
	for x in range(iCmdVars):
		strCmdVars[x] = (wsInput.Cells(iInputLineNum,iCmdCol[x]).Value)
# End while hostname
print ("Failed to complete lines {} due to errors.".format(FailedDevs))
print ("Retrying them one more time")
for iInputLineNum in FailedDevs:
	for x in range(iCmdVars):
		strCmdVars[x] = (wsInput.Cells(iInputLineNum,iCmdCol[x]).Value)
	strHostname = wsInput.Cells(iInputLineNum,iInputColumn).Value
	if iCmdVars > 0:
		strCmd = strCommand.format(*strCmdVars)
	else:
		strCmd = strCommand
	print ("Processing {} ...".format(strHostname))
	dictDevices[strHostname] = strCmd
	strOut = GetResults(strHostname,strCmd)
	if "Exception:"	not in strOut:
		FailedDevs.remove(iInputLineNum)
		AnalyzeResults(strOut.splitlines())

wsResult.Range(wsResult.Cells(1, 1),wsResult.Cells(iOutLineNum,12)).EntireColumn.AutoFit()
wbin.Save()
now = time.asctime()
tStop = time.time()
iElapseSec = tStop - tStart
iMin, iSec = divmod(iElapseSec, 60)
iHours, iMin = divmod(iMin, 60)
print ("Failed to complete lines {} due to errors.".format(FailedDevs))
print ("Completed at {}".format(now))
print ("Took {0:.2f} seconds to complete, which is {1} hours, {2} minutes and {3:.2f} seconds.".format(iElapseSec,iHours,iMin,iSec))

# messagebox.showinfo("All Done","Processing has completed, return to the command window for details")