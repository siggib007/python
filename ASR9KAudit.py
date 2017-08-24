strResultSheetName = "Results"
strCommand = "show access-lists ipv6"
strOutFolderName = "Testing"

import tkinter as tk
from tkinter import filedialog
import win32com.client as win32 #pip install pypiwin32
import getpass
import time
import sys
import paramiko #pip install paramiko
import socket
import os

root = tk.Tk()
root.withdraw()
dictSheets={}

def getInput(strPrompt):
    if sys.version_info[0] > 2 :
        return input(strPrompt)
    else:
        return raw_input(strPrompt)
# end getInput

DefUserName = getpass.getuser()
print ("This is a Cisco ASR9K Audit script. Your default username is {3}. This is running under Python Version {0}.{1}.{2}".format(sys.version_info[0],sys.version_info[1],sys.version_info[2],DefUserName))
now = time.asctime()
print ("The time now is {}".format(now))
print ("This script will read a source excel sheet and log into each router listed in column A,\n"
		"starting with row 2, execute defined command and write results on tab called '{}' which gets created if it does not exists.".format(strResultSheetName))
print ("Using the file open dialog please open the source excel file")
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
	print ("\nPath '{0}' didn't exists, so I create it!\n".format(strOutPath))

app = win32.gencache.EnsureDispatch('Excel.Application')
app.Visible = True
wbin = app.Workbooks.Open (strWBin,0,False)
iSheetCount = wbin.Worksheets.Count
# print ("Please select which sheet is the input sheet:")
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
# if "Input" in dictSheets:
# 	print ("Input Sheet exists, we're all good there")
# 	wsInput = wbin.Worksheets("Input")
# else:
# 	print ("I need the input sheet to be named 'input'")
# 	sys.exit(2)
if strResultSheetName in dictSheets:
	print ("Results Sheet exists, we're all good there")
	wsResult = wbin.Worksheets(strResultSheetName)
else:
	print ("No results sheet found, creating one")
	wbin.Sheets.Add()
	wbin.Worksheets(1).Name = strResultSheetName
	wsResult = wbin.Worksheets(strResultSheetName)
# End if valid input sheet

strUserName = getInput("Please provide username for use when login into the routers, enter to use {}: ".format(DefUserName))
if strUserName == "":
	strUserName = DefUserName
# end if username is empty

strPWD = getpass.getpass(prompt="what is the password for {0}: ".format(strUserName))

wsResult.Cells(1,1).Value = "primaryIPAddress"
wsResult.Cells(1,2).Value = "hostName"
wsResult.Cells(1,3).Value = "ABFACLName"
wsResult.Cells(1,4).Value = "CNO1"
wsResult.Cells(1,5).Value = "CNO2"
wsResult.Cells(1,6).Value = "CNO3"
wsResult.Cells(1,7).Value = "CNO4"
wsResult.Cells(1,8).Value = "CNO5"
wsResult.Cells(1,9).Value = "PDNS"
wsResult.Cells(1,10).Value = "SDNS"
wsResult.Cells(1,11).Value = "NextHopIP"
iLineNum = 2
strHostname = wsInput.Cells(iLineNum,1).Value
while strHostname != "" and strHostname != None :
	print ("Processing {} ...".format(strHostname))
	wsResult.Cells(iLineNum,1).Value = socket.gethostbyname(strHostname)
	wsResult.Cells(iLineNum,2).Value = wsInput.Cells(iLineNum,1).Value
	try:
		SSH = paramiko.SSHClient()
		SSH.set_missing_host_key_policy(paramiko.AutoAddPolicy())
		SSH.connect(strHostname, username=strUserName, password=strPWD, look_for_keys=False, allow_agent=False)
		stdin, stdout, stderr = SSH.exec_command(strCommand)
		print ("show command sent")
		strOut = stdout.read()
		strOut = strOut.decode("utf-8")
		strOutFile = strOutPath + strHostname + ".txt"
		objFileOut = open(strOutFile,"w")
		objFileOut.write (strOut)
		objFileOut.close()
		print ("Show command output written to file "+strOutFile)
		# print ("Received type: {}".format(type(strOut)))
		# print ("Command Output:\n{}".format(strOut))
		SSH.close()
	except paramiko.ssh_exception.AuthenticationException as err:
		print ("Auth Exception: {0}".format(err))
		sys.exit(1)
	except paramiko.SSHException as err:
		print ("SSH Exception: {0}".format(err))
	except OSError as err:
		print ("socket Exception: {0}".format(err))
	except Exception as err:
		print ("{0}".format(err))

	iLineNum += 1
	strHostname = wsInput.Cells(iLineNum,1).Value
# End while hostname
wsResult.Range(wsResult.Cells(1, 1),wsResult.Cells(iLineNum,12)).EntireColumn.AutoFit()
wbin.Save()
now = time.asctime()
print ("Completed at {}".format(now))