'''
Script add integer version of an IP address to the service now csv feed.
Author Siggi Bjarnason Copyright 2018
Website http://www.ipcalc.us/ and http://www.icecomputing.com

Following packages need to be installed as administrator
pip install requests
pip install xmltodict
pip install pymysql

'''
# strFilein = "C:/temp/cmdb_ci_server.csv"
# strOutFile = "C:/temp/cmdb_ci_server-fixed.csv"

import sys
import os
import getpass
import time
try:
	import tkinter as tk
	from tkinter import filedialog
	btKinterOK = True
except:
	print ("Failed to load tkinter, CLI only mode.")
	btKinterOK = False

def getInput(strPrompt):
    if sys.version_info[0] > 2 :
        return input(strPrompt)
    else:
        return raw_input(strPrompt)
# end getInput

strFilein = ""

sa = sys.argv

lsa = len(sys.argv)
if lsa > 1:
	strFilein = sa[1]

if strFilein == "":
	if btKinterOK:
		print ("File name to be processed is missing. Opening up a file open dialog box, please select the file you wish to process.")
		root = tk.Tk()
		root.withdraw()
		strFilein = filedialog.askopenfilename(title = "Select CSV file",filetypes = (("CSV files","*.csv"),("Text files","*.txt"),("all files","*.*")))
	else:
		strFilein = getInput("Please provide full path and filename for the CSV file to be processed: ")

if strFilein == "":
	print ("No filename provided unable to continue")
	sys.exit()

if os.path.isfile(strFilein):
	print ("OK found {}".format(strFilein))
else:
	print ("Can't find CSV file {}".format(strFilein))
	sys.exit(4)


iLoc = strFilein.rfind(".")
strOutFile = strFilein[:iLoc] + "-fixed" + strFilein[iLoc:]

def DotDec2Int (strValue):
	strHex = ""
	if ValidateIP(strValue) == False:
		# print ("{} is invalid IP".format(strValue))
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

objFileIn  = open(strFilein,"r")
objFileOut = open(strOutFile,"w")
strLine = objFileIn.readline()
objFileOut.write (strLine[:-1] + ",iIPAddr\n")

while strLine:
	strLine = objFileIn.readline()
	strLineParts = strLine.split(",")
	if len(strLineParts)>2:
		strIPAddr = strLineParts[2]
		strIPAddr = strIPAddr.replace('"' ,"")
		iIPAddr = DotDec2Int(strIPAddr)
		# iIPAddr = strLineParts[2]
		objFileOut.write ("{},{}\n".format(strLine[:-1],iIPAddr))
#end while
print ("All Done, make sure you import {}".format(strOutFile))