'''
Qualys Appliance API Script
Author Siggi Bjarnason Copyright 2017
Website http://www.icecomputing.com

Description:
This is script where I start to explore Qualys API calls, parsing the XML responses, etc.

Following packages need to be installed as administrator
pip install requests
pip install xmltodict
pip install pymysql

'''
# Import libraries
import sys
import requests
import os
import xmltodict
import pymysql
# End imports

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
		if strSQL[:6].lower() == "select":
			dbResults = dbCursor.fetchall()
		else:
			db.commit()
			dbResults = ()
		return [iRowCount,dbResults]
	except pymysql.err.InternalError as err:
		if strSQL[:6].lower() != "select":
			db.rollback()
		return "Internal Error: unable to execute: {}".format(err)
	except pymysql.err.ProgrammingError as err:
		if strSQL[:6].lower() != "select":
			db.rollback()
		return "Programing Error: unable to execute: {}".format(err)
	except pymysql.err.OperationalError as err:
		if strSQL[:6].lower() != "select":
			db.rollback()
		return "Programing Error: unable to execute: {}".format(err)
	except pymysql.err.IntegrityError as err:
		if strSQL[:6].lower() != "select":
			db.rollback()
		return "Integrity Error: unable to execute: {}".format(err)

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

def isInt (CheckValue):
	# function to safely check if a value can be interpreded as an int
	if isinstance(CheckValue,int):
		return True
	elif isinstance(CheckValue,str):
		if CheckValue.isnumeric():
			return True
		else:
			return False
	else:
		return False

def DotDec2Int (strValue):
	strHex = ""
	if ValidateIP(strValue) == False:
		return -10
	# end if

	Quads = strValue.split(".")
	for Q in Quads:
		QuadHex = hex(int(Q))
		strwp = "00"+ QuadHex[2:]
		strHex = strHex + strwp[-2:]
	# next

	return int(strHex,16)

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

def ValidMask(strToCheck):
	iNumBits=0
	if ValidateIP(strToCheck) == False:
		return 0
	# end if

	iDecValue = DotDec2Int(strToCheck)
	strBinary = bin(iDecValue)

	strTemp = "0"*32 + strBinary[2:]
	strBinary = strTemp[-32:]
	cBit = strBinary[0]
	bFound = False
	x=0
	for c in strBinary:
		x=x+1
		if cBit != c:
			iNumBits = x-1
			if bFound:
				return 0
			else:
				cBit=c
				bFound = True
			# end if
		# end if
	# next
	if iNumBits==0:
		iNumBits = x
	# end if
	return iNumBits
# end function

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
		dictIPInfo['iDecIPAddr'] = iDecIPAddr
		dictIPInfo['iDecSubID'] = iDecSubID
		dictIPInfo['iDecBroad'] = iDecBroad
		dictIPInfo['Subnet'] = DotDecGen(iDecSubID)
		dictIPInfo['Broadcast'] = DotDecGen(iDecBroad)
	else:
		dictIPInfo['IPError'] = "'" + strIPAddress + "' is not a valid IP!"
	# End if
	return dictIPInfo

def MakeAPICall (strURL, strHeader, strUserName,strPWD):

	iErrCode = ""
	iErrText = ""

	print ("Doing a get to URL: \n {}\n".format(strURL))
	try:
		WebRequest = requests.get(strURL, headers=strHeader, auth=(strUserName, strPWD))
	except:
		print ("Failed to connect to Qualys")
		sys.exit(7)
	# end try

	if isinstance(WebRequest,requests.models.Response)==False:
		print ("response is unknown type")
		sys.exit(5)
	# end if

	dictResponse = xmltodict.parse(WebRequest.text)
	if isinstance(dictResponse,dict):
		if "SIMPLE_RETURN" in dictResponse:
			try:
				if "CODE" in dictResponse["SIMPLE_RETURN"]["RESPONSE"]:
					iErrCode = dictResponse["SIMPLE_RETURN"]["RESPONSE"]["CODE"]
					iErrText = dictResponse["SIMPLE_RETURN"]["RESPONSE"]["TEXT"]
			except KeyError as e:
				print ("KeyError: {}".format(e))
				print (WebRequest.text)
				iErrCode = "Unknown"
				iErrText = "Unexpected error"
	else:
		print ("Response not a dictionary")
		sys.exit(8)

	if iErrCode != "" or WebRequest.status_code !=200:
		return "There was a problem with your request. HTTP error {} code {} {}".format(WebRequest.status_code,iErrCode,iErrText)
	else:
		return dictResponse

def CollectApplianceData (dictTemp):
	dictOut = {}
	dictInt1 = dictTemp["INTERFACE_SETTINGS"][0]
	dictInt2 = dictTemp["INTERFACE_SETTINGS"][1]
	dictOut["name"] = dictTemp["NAME"]
	dictOut["ID"] = dictTemp["ID"]
	dictOut["UUID"] = dictTemp["UUID"]
	dictOut["state"] = dictTemp["STATUS"]
	dictOut["model"] = dictTemp["MODEL_NUMBER"]
	dictOut["type"] = dictTemp["TYPE"]
	dictOut["SN"] = dictTemp["SERIAL_NUMBER"]
	strIPAddr1 = dictInt1["IP_ADDRESS"] + "/" + str(ValidMask(dictInt1["NETMASK"]))
	iIPAddr1 = DotDec2Int(dictInt1["IP_ADDRESS"])
	dictOut["IPaddr1"] = strIPAddr1
	dictOut["intIP1"] = str(iIPAddr1)
	dictOut["GW1"] = dictInt1["GATEWAY"]
	dictOut["intGW1"] = str(DotDec2Int(dictInt1["GATEWAY"]))
	dictOut["Int2State"] = dictInt2["SETTING"]
	if isinstance(dictInt2["IP_ADDRESS"],str):
		strIPAddr2 = dictInt2["IP_ADDRESS"] + "/" + str(ValidMask(dictInt2["NETMASK"]))
		iIPAddr2 = DotDec2Int(dictInt2["IP_ADDRESS"])
		strGWaddr = dictInt2["GATEWAY"]
		iIPGW = DotDec2Int(dictInt2["GATEWAY"])
	else:
		strIPAddr2 = ""
		iIPAddr2 = 0
		iIPGW = 0
		strGWaddr = ""
	dictOut["IPaddr2"] = strIPAddr2
	dictOut["intIP2"] = str(iIPAddr2)
	dictOut["GW2"] = strGWaddr
	dictOut["intGW2"] = str(iIPGW)
	dictOut["StaticRoute"] = []
	dictStatic = {}
	dictOut["ScanInt"] = "indeterment"
	if isinstance(dictTemp["STATIC_ROUTES"],type(None)):
		iStaticCount = 0
	elif isinstance(dictTemp["STATIC_ROUTES"]["ROUTE"],list):
		iStaticCount = len (dictTemp["STATIC_ROUTES"]["ROUTE"])
		for dictRoute in dictTemp["STATIC_ROUTES"]["ROUTE"]:
			dictStatic.clear()
			if dictRoute["GATEWAY"] == dictOut["GW1"]:
				if dictOut["ScanInt"] == "Int2":
					dictOut["ScanInt"] = "Both"
				if dictOut["ScanInt"] == "indeterment":
					dictOut["ScanInt"] = "Int1"
			if dictRoute["GATEWAY"] == dictOut["GW2"]:
				if dictOut["ScanInt"] == "Int1":
					dictOut["ScanInt"] = "Both"
				if dictOut["ScanInt"] == "indeterment":
					dictOut["ScanInt"] = "Int2"
			dictStatic["NetBlock"] = dictRoute["IP_ADDRESS"] + "/" + str(ValidMask(dictRoute["NETMASK"]))
			dictStatic["intSubnetID"] = DotDec2Int(dictRoute["IP_ADDRESS"])
			dictStatic["NextHop"] = dictRoute["GATEWAY"]
			dictStatic["intGW"] = DotDec2Int(dictRoute["GATEWAY"])
			dictOut["StaticRoute"].append(dictStatic.copy())
	else:
		iStaticCount = 1
		dictRoute = dictTemp["STATIC_ROUTES"]["ROUTE"]
		dictStatic.clear()
		if dictRoute["GATEWAY"] == dictOut["GW1"]:
			if dictOut["ScanInt"] == "Int2":
				dictOut["ScanInt"] = "Both"
			if dictOut["ScanInt"] == "indeterment":
				dictOut["ScanInt"] = "Int1"
		if dictRoute["GATEWAY"] == dictOut["GW2"]:
			if dictOut["ScanInt"] == "Int1":
				dictOut["ScanInt"] = "Both"
			if dictOut["ScanInt"] == "indeterment":
				dictOut["ScanInt"] = "Int2"
		dictStatic["NetBlock"] = dictRoute["IP_ADDRESS"] + "/" + str(ValidMask(dictRoute["NETMASK"]))
		dictStatic["intSubnetID"] = DotDec2Int(dictRoute["IP_ADDRESS"])
		dictStatic["NextHop"] = dictRoute["GATEWAY"]
		dictStatic["intGW"] = DotDec2Int(dictRoute["GATEWAY"])
		dictOut["StaticRoute"].append(dictStatic.copy())

	# print ("{} is {} and is a {} device, it has {} static routes.".format(dictOut["name"],dictOut["state"],dictOut["type"],iStaticCount))
	return dictOut

def UpdateDB (dictAppliance):
	strSQL = "delete from networks.tblappliances where iApplianceID = {};".format(dictAppliance["ID"])
	lstReturn = SQLQuery (strSQL,dbConn)
	if not ValidReturn(lstReturn):
		print ("Unexpected: {}".format(lstReturn))
	elif lstReturn[0] > 1:
		print ("Records affected {}, expected 1 record affected".format(lstReturn[0]))

	strSQL = ("INSERT INTO networks.tblappliances (iApplianceID,vcUUID,vcName,vcState,vcModel,vcType,vcSerialNum,vcIPAddr1,vcGW1,iIPaddr1,iGW1,vcInt2State,vcIPAddr2,vcGW2,iIPAddr2,iGW2,vcScanningInt) "
				"VALUES({0},'{1}','{2}','{3}','{4}','{5}','{6}','{7}','{8}','{9}','{10}','{11}','{12}','{13}','{14}','{15}','{16}');".format(dictAppliance["ID"],dictAppliance["UUID"],dictAppliance["name"],dictAppliance["state"],
					dictAppliance["model"],dictAppliance["type"],dictAppliance["SN"],dictAppliance["IPaddr1"],dictAppliance["GW1"],dictAppliance["intIP1"],dictAppliance["intGW1"],
					dictAppliance["Int2State"],dictAppliance["IPaddr2"],dictAppliance["GW2"],dictAppliance["intIP2"],dictAppliance["intGW2"],dictAppliance["ScanInt"])
			  )
	lstReturn = SQLQuery (strSQL,dbConn)
	if not ValidReturn(lstReturn):
		print ("Unexpected: {}".format(lstReturn))
	elif lstReturn[0] != 1:
		print ("Records affected {}, expected 1 record affected".format(lstReturn[0]))
	for dictRoute in dictAppliance["StaticRoute"]:
		strSQL = ("INSERT INTO networks.tblscan_routes (iApplianceID,vcNetBlock,vcNextHop,iNetBlock,iNextHop) "
					"VALUES ({0},'{1}','{2}',{3},{4}) ".format(dictAppliance["ID"],dictRoute["NetBlock"],dictRoute["NextHop"],dictRoute["intSubnetID"],dictRoute["intGW"]))
		lstReturn = SQLQuery (strSQL,dbConn)
		if not ValidReturn(lstReturn):
			print ("Unexpected: {}".format(lstReturn))
		elif lstReturn[0] != 1:
			print ("Records affected {}, expected 1 record affected".format(lstReturn[0]))

print ("This is a Qualys Appliance API script. This is running under Python Version {0}.{1}.{2}".format(sys.version_info[0],sys.version_info[1],sys.version_info[2]))


if os.path.isfile("QSInput.txt"):
	print ("Configuration File exists")
else:
	print ("Can't find configuration file QSInput.txt, make sure it is the same directory as this script")
	sys.exit(4)

strLine = "  "
print ("Reading in configuration")
objINIFile = open("QSAppliance.txt","r")
strLines = objINIFile.readlines()
objINIFile.close()

for strLine in strLines:
	strLine = strLine.strip()
	if "=" in strLine:
		strConfParts = strLine.split("=")
		if strConfParts[0] == "APIBaseURL":
			strBaseURL = strConfParts[1]
		if strConfParts[0] == "APIRequestHeader":
			strHeadReq = strConfParts[1]
		if strConfParts[0] == "QUserID":
			strUserName = strConfParts[1]
		if strConfParts[0] == "QUserPWD":
			strPWD = strConfParts[1]
		if strConfParts[0] == "Server":
			strServer = strConfParts[1]
		if strConfParts[0] == "Database":
			strInitialDB = strConfParts[1]
		if strConfParts[0] == "dbUser":
			strDBUser = strConfParts[1]
		if strConfParts[0] == "dbPWD":
			strDBPWD = strConfParts[1]

dbConn = SQLConn (strServer,strDBUser,strDBPWD,strInitialDB)

strHeader={'X-Requested-With': strHeadReq}
strAPI = "api/2.0/fo/appliance/?"
strAction = "action=list&output_mode=full"
# strAction = "action=list&output_mode=full&name=SCNPOL03"
strURL = strBaseURL + strAPI + strAction
APIResponse = MakeAPICall(strURL,strHeader,strUserName,strPWD)
if isinstance(APIResponse,str):
	print(APIResponse)
elif isinstance(APIResponse,dict):
	if "APPLIANCE_LIST" in APIResponse["APPLIANCE_LIST_OUTPUT"]["RESPONSE"]:
		if isinstance(APIResponse["APPLIANCE_LIST_OUTPUT"]["RESPONSE"]["APPLIANCE_LIST"]["APPLIANCE"],list):
			print ("Number of appliances: {}".format(len(APIResponse["APPLIANCE_LIST_OUTPUT"]["RESPONSE"]["APPLIANCE_LIST"]["APPLIANCE"])))
			for dictTemp in APIResponse["APPLIANCE_LIST_OUTPUT"]["RESPONSE"]["APPLIANCE_LIST"]["APPLIANCE"]:
				UpdateDB(CollectApplianceData(dictTemp))
		else:
			print ("Number of appliances: 1")
			UpdateDB(CollectApplianceData (APIResponse["APPLIANCE_LIST_OUTPUT"]["RESPONSE"]["APPLIANCE_LIST"]["APPLIANCE"]))
	else:
		print ("There are no appliances")
else:
	print ("API Response neither a dictionary nor a string. Here is what I got: {}".format(APIResponse))

print ("Done processing")