'''
Script add integer version of an IP address to the service now csv feed.
Author Siggi Bjarnason Copyright 2018
Website http://www.ipcalc.us/ and http://www.icecomputing.com

Following packages need to be installed as administrator
pip install requests
pip install xmltodict
pip install pymysql

'''
strFilein = "C:/temp/cmdb_ci_server.csv"
strOutFile = "C:/temp/cmdb_ci_server-fixed.csv"

import sys
import os
import getpass
import time

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
	else:
		iIPAddr = 0
	objFileOut.write ("{},{}\n".format(strLine[:-1],iIPAddr))
#end while
print ("All Done, make sure you import {}".format(strOutFile))