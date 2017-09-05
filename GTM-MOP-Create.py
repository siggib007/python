'''
Router Audit
Author Siggi Bjarnason Copyright 2017
Website http://www.ipcalc.us/ and http://www.icecomputing.com

Description:
This script will create a GTM script for you based on a data in a spreadsheet.
Results will be in a text file that you can inlude in your MOP or send to the lab as applicable


Following packages need to be installed as administrator
pip install pypiwin32
pip install paramiko

'''
import tkinter as tk
from tkinter import filedialog
import win32com.client as win32 #pip install pypiwin32
import getpass
import time
import sys
import paramiko #pip install paramiko
import socket
import os

dictSheets={}
tStart=time.time()
iInputColumn = 1
dictServers={}
PoolList = []

def getInput(strPrompt):
    if sys.version_info[0] > 2 :
        return input(strPrompt)
    else:
        return raw_input(strPrompt)
# end getInput

DefUserName = getpass.getuser()
print ("This is a GTM MOP creator. Your default username is {3}. This is running under Python Version {0}.{1}.{2}".format(sys.version_info[0],sys.version_info[1],sys.version_info[2],DefUserName))
now = time.asctime()
print ("The time now is {}".format(now))

getInput ("Press enter to bring up a file open dialog so you may choose the source Excel file")

root = tk.Tk()
root.withdraw()
strWBin = filedialog.askopenfilename(title = "Select spreadsheet",filetypes = (("Excel files","*.xlsx"),("All Files","*.*")))

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
print ("Opening that spreadsheet, please stand by ...")
app = win32.gencache.EnsureDispatch('Excel.Application')
app.Visible = True
wbin = app.Workbooks.Open (strWBin,0,False)
iSheetCount = wbin.Worksheets.Count
print ("Validating the spreadsheet. It has {0} sheets".format(iSheetCount))
for i in range(1,iSheetCount+1):
	strTemp = wbin.Worksheets(i).Name
	print ("Sheet #{0} is called {1}".format(i,strTemp))
	dictSheets[strTemp]=i
# end for loop
if "OverView" in dictSheets:
	print ("OverView is good!")
	wsOverView = wbin.Worksheets("OverView")
else:
	print ("This seems like the wrong file, no sheet called Overview. Aborting!")
	sys.exit(1)
if "FQDNs" in dictSheets:
	print ("FQDNs is good!")
	wsFQDNs = wbin.Worksheets("FQDNs")
else:
	print ("This seems like the wrong file, no sheet called FQDNs. Aborting!")
	sys.exit(1)
if "Pools" in dictSheets:
	print ("Pools is good!")
	wsPools = wbin.Worksheets("Pools")
else:
	print ("This seems like the wrong file, no sheet called Pools. Aborting!")
	sys.exit(1)
if "Topologies" in dictSheets:
	print ("Topologies is good!")
	wsTopologies = wbin.Worksheets("Topologies")
else:
	print ("This seems like the wrong file, no sheet called Topologies. Aborting!")
	sys.exit(1)
strSyncGroupName = wsOverView.Cells(2,2).Value
strPartition = wsOverView.Cells(3,2).Value
strLBMode = wsOverView.Cells(4,2).Value
strAppName = wsOverView.Cells(5,2).Value
print ("Working with sync group {}, looking for device names in that group.".format(strSyncGroupName))
x=5
while wsOverView.Cells(x,1).Value != strSyncGroupName and x < 50:
	x += 1
iSyncGroupRow = x
if iSyncGroupRow < 50:
	print ("Found {} sync group on line {}".format(strSyncGroupName,iSyncGroupRow))
else:
	print ("unable to find the definition for sync group {}, exiting!".format(strSyncGroupName))
	sys.exit(1)
x = 2
strSyncGroupMembers = []
while wsOverView.Cells(iSyncGroupRow,x).Value != "" and wsOverView.Cells(iSyncGroupRow,x).Value != None :
	strSyncGroupMembers.append(wsOverView.Cells(iSyncGroupRow,x).Value)
	x += 1
print ("**** IMPLEMENT ON {} ****".format(strSyncGroupMembers))
strOutFile = strPath+"/"+strAppName+"-GTM-Implement.txt"
objFileOut = open(strOutFile,"w")
objFileOut.write ("**** IMPLEMENT ON {} ****\n".format(strSyncGroupMembers))
objFileOut.write ("cd /Common\n")
x=2

while wsPools.Cells(x,1).Value != "" and wsPools.Cells(x,1).Value != None :
	strPortNumber = str(int(wsPools.Cells(x,4).Value))
	strMemberName = wsPools.Cells(x,3).Value
	strMemberName = strMemberName.replace(".","_")
	strMemberName =  wsPools.Cells(x,2).Value + "_VS(" + strMemberName + "_" + strPortNumber + ")"
	if wsPools.Cells(x,2).Value in dictServers:
		strBase = "modify gtm server " + wsPools.Cells(x,2).Value
		if wsPools.Cells(x,3).Value in dictServers[wsPools.Cells(x,2).Value]:
			strBase += (" virtual-servers add { " + strMemberName + " { destination " + wsPools.Cells(x,3).Value + ":" +
						strPortNumber + " monitor min 1 of { tcp_half_open } } }\n")
		else:
			strBase += (" addresses add { " + wsPools.Cells(x,3).Value + " } product generic-host datacenter " +
						wsPools.Cells(x,5).Value + " virtual-servers add { " + strMemberName + " { destination " +
						wsPools.Cells(x,3).Value + ":" + strPortNumber + " monitor min 1 of { tcp_half_open } } }\n")
			dictServers[wsPools.Cells(x,2).Value].append(wsPools.Cells(x,3).Value)
	else:
		strBase = ("create gtm server " + wsPools.Cells(x,2).Value + " addresses add { " + wsPools.Cells(x,3).Value +
		" } product generic-host datacenter " + wsPools.Cells(x,5).Value + " virtual-servers add { " + strMemberName +
		" { destination " + wsPools.Cells(x,3).Value + ":" + strPortNumber + " monitor min 1 of { tcp_half_open } } }\n")
		dictServers[wsPools.Cells(x,2).Value]=[wsPools.Cells(x,3).Value]
	objFileOut.write (strBase)
	x += 1
objFileOut.write ("\ncd /{}\n".format(strPartition))
x=2
while wsPools.Cells(x,1).Value != "" and wsPools.Cells(x,1).Value != None :
	strPortNumber = str(int(wsPools.Cells(x,4).Value))
	strMemberName = wsPools.Cells(x,3).Value
	strMemberName = strMemberName.replace(".","_")
	strMemberName =  wsPools.Cells(x,2).Value + "_VS(" + strMemberName + "_" + strPortNumber + ")"
	if wsPools.Cells(x,1).Value in PoolList:
		strBase = "modify gtm pool " + wsPools.Cells(x,1).Value + " { members add { /Common/" + wsPools.Cells(x,2).Value + ":" + strMemberName + " } ttl 180 }\n"
	else:
		strBase = ("create gtm pool " + wsPools.Cells(x,1).Value + " { alternate-mode none fallback-mode none members add { /Common/" +
		wsPools.Cells(x,2).Value + ":" + strMemberName + " } ttl 180 }\n")
		PoolList.append(wsPools.Cells(x,1).Value)
	objFileOut.write (strBase)
	x += 1

objFileOut.write ("\n")
x=2
while wsTopologies.Cells(x,1).Value != "" and wsTopologies.Cells(x,1).Value != None :
	objFileOut.write ("create gtm topology ldns: region \"/Common/" + wsTopologies.Cells(x,2).Value + "\" server: pool /" + strPartition +
		"/" + wsTopologies.Cells(x,1).Value + " { score " + str(int(wsTopologies.Cells(x,3).Value)) + " }\n")
	x += 1

objFileOut.write ("\n")
x=2
while wsFQDNs.Cells(x,1).Value != "" and wsFQDNs.Cells(x,1).Value != None :
	if wsFQDNs.Cells(x,2).Value == "Yes":
		strEnable = "enabled"
	else:
		strEnable = "disabled"
	strBase = "create gtm wideip " + wsFQDNs.Cells(x,1).Value + " { ipv6-no-error-response " + strEnable + " pool-lb-mode " + strLBMode + " pools add {"
	y = 0
	strTemp = ""
	while wsFQDNs.Cells(x,y+3).Value != "" and wsFQDNs.Cells(x,y+3).Value != None :
		strTemp += " " + wsFQDNs.Cells(x,y+3).Value + " { order " + str(y) + " }"
		y += 1
	objFileOut.write (strBase + strTemp + " } }\n")
	x += 1

objFileOut.close
now = time.asctime()
tStop = time.time()
iElapseSec = tStop - tStart
iMin, iSec = divmod(iElapseSec, 60)
iHours, iMin = divmod(iMin, 60)
print ("Completed at {}".format(now))
print ("Took {0:.1f} seconds to complete, which is {1} hours, {2} minutes and {3:.1f} seconds.".format(iElapseSec,iHours,iMin,iSec))
