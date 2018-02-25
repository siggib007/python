'''
Script to calculate the integer value for every IP in the table and update the appropriate field in the database
Author Siggi Bjarnason Copyright 2018
Website http://www.ipcalc.us/ and http://www.icecomputing.com

Following packages need to be installed as administrator
pip install requests
pip install pymysql

'''
# Import libraries
import sys
import requests
import json
import os
import string
import pymysql
# End imports

iLoc = sys.argv[0].rfind(".")
strConf_File = sys.argv[0][:iLoc] + ".ini"

def processConf():
  global strServer
  global strDBUser
  global strDBPWD
  global strInitialDB
  global strTableName

  if os.path.isfile(strConf_File):
    print ("Configuration File exists")
  else:
    print ("Can't find configuration file {}, make sure it is the same directory as this script".format(strConf_File))
    sys.exit(4)

  strLine = "  "
  print ("Reading in configuration")
  objINIFile = open(strConf_File,"r")
  strLines = objINIFile.readlines()
  objINIFile.close()

  for strLine in strLines:
    strLine = strLine.strip()
    iCommentLoc = strLine.find("#")
    if iCommentLoc > -1:
      strLine = strLine[:iCommentLoc].strip()
    else:
      strLine = strLine.strip()
    if "=" in strLine:
      strConfParts = strLine.split("=")
      strVarName = strConfParts[0].strip()
      strValue = strConfParts[1].strip()
      strConfParts = strLine.split("=")

      if strVarName == "Server":
        strServer = strValue
      if strVarName == "dbUser":
        strDBUser = strValue
      if strVarName == "dbPWD":
        strDBPWD = strValue
      if strVarName == "InitialDB":
        strInitialDB = strValue
      if strVarName == "TableName":
        strTableName = strValue

  print ("Done processing configuration, moving on")

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
		dictIPInfo['iDecIPAddr'] = iDecIPAddr
		dictIPInfo['Subnet'] = DotDecGen(iDecSubID)
		dictIPInfo['Broadcast'] = DotDecGen(iDecBroad)
	else:
		dictIPInfo['IPError'] = "'" + strIPAddress + "' is not a valid IP!"
	# End if
	return dictIPInfo
# end function


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
    if strSQL[:6].lower() == "select" or strSQL[:4].lower() == "call":
      dbResults = dbCursor.fetchall()
    else:
      db.commit()
      dbResults = ()
    return [iRowCount,dbResults]
  except pymysql.err.InternalError as err:
    if strSQL[:6].lower() != "select":
      db.rollback()
    return "Internal Error: unable to execute: {}\n{}".format(err,strSQL)
  except pymysql.err.ProgrammingError as err:
    if strSQL[:6].lower() != "select":
      db.rollback()
    return "Programing Error: unable to execute: {}\n{}".format(err,strSQL)
  except pymysql.err.OperationalError as err:
    if strSQL[:6].lower() != "select":
      db.rollback()
    return "Programing Error: unable to execute: {}\n{}".format(err,strSQL)
  except pymysql.err.IntegrityError as err:
    if strSQL[:6].lower() != "select":
      db.rollback()
    return "Integrity Error: unable to execute: {}\n{}".format(err,strSQL)
  except pymysql.err.DataError as err:
    if strSQL[:6].lower() != "select":
      db.rollback()
    return "Data Error: unable to execute: {}\n{}".format(err,strSQL)

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

def FindMask(iDecSubID,iDecBroad):
	strIPAddress = DotDecGen(iDecSubID)
	for x in range(1,32):
		strSubnet = "{}/{}".format(strIPAddress,x)
		dictIPInfo = IPCalc (strSubnet)
		print (dictIPInfo)
		print ("iDecBroad 1:{}".format(iDecBroad))
		print ("iDecBroad 2:{}".format(dictIPInfo['iDecBroad']))
		if iDecBroad == dictIPInfo['iDecBroad']:
			return strSubnet
		if iDecBroad < dictIPInfo['iDecBroad']:
			return "Partial match:{}".format(strSubnet)
	return "{}/{}".format(strIPAddress,32)

dbConn = ""
processConf()
dbConn = SQLConn (strServer,strDBUser,strDBPWD,strInitialDB)
strSQL = ("SELECT DISTINCT vcIPaddress FROM {} WHERE vcIPaddress IS NOT NULL ;".format(strTableName))
lstSubnets = SQLQuery (strSQL,dbConn)
iRowCount = lstSubnets[0]
if not ValidReturn(lstSubnets):
	print ("Unexpected: {}".format(lstSubnets))
	sys.exit(8)
else:
	print ("Fetched {} rows".format(lstSubnets[0]))

if lstSubnets[0] == 0:
	print ("Nothing to do, exiting")
	sys.exit(9)

iRowNum = 1
for dbRow in lstSubnets[1]:
	strIPAddr = dbRow[0]
	dictIPInfo = IPCalc (strIPAddr)
	iDecIPAddr = DotDec2Int(strIPAddr)
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
		print ("\n\n {}".format(dictIPInfo['IPError']))
	if iDecSubID > 0:
		# strIPAddr = FindMask(iDecSubID,iDecBroad)
		iRowNum += 1
		print ("Completed {:.1%}".format(iRowNum/iRowCount),end="\r")
		# print(".", end="")
		strSQL = "UPDATE {2} SET iIPAddr = {0} WHERE vcIPaddress = '{1}';".format(iDecIPAddr,strIPAddr,strTableName)
		lstReturn = SQLQuery (strSQL,dbConn)
		if not ValidReturn(lstReturn):
			print ("\n\nUnexpected: {}".format(lstReturn))
			break
		# elif lstReturn[0] != 1:
			# print ("{} \n Records affected {}, expected 1 record affected".format(strSQL, lstReturn[0]))

print ("\n\n All Done !!!! ")