# Import libraries
import sys
import requests
import json
import os
import string
import pymysql
# End imports

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
    dictIPInfo['DecIP'] = iDecIPAddr
    iDecSubID = iDecIPAddr-(iDecIPAddr%iHostcount)
    iDecBroad = iDecSubID + iHostcount - 1
    dictIPInfo['iDecSubID'] = iDecSubID
    dictIPInfo['iDecBroad'] = iDecBroad
    dictIPInfo['Subnet'] = DotDecGen(iDecSubID)
    dictIPInfo['Broadcast'] = DotDecGen(iDecBroad)
  else:
    dictIPInfo['IPError'] = "'" + strIPAddress + "' is not a valid IP!"
  # End if
  return dictIPInfo

def SQLConn (strServer,strDBUser,strDBPWD,strInitialDB):
  try:
    # Open database connection
    return pymysql.connect(host=strServer,user=strDBUser,password=strDBPWD,db=strInitialDB)
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

def FindMask(iDecSubID,iDecBroad):
  strIPAddress = DotDecGen(iDecSubID)
  for x in range(1,32):
    strSubnet = "{}/{}".format(strIPAddress,x)
    dictIPInfo = IPCalc (strSubnet)
    # print (dictIPInfo)
    # print ("iDecBroad 1:{}".format(iDecBroad))
    # print ("iDecBroad 2:{}".format(dictIPInfo['iDecBroad']))
    if iDecBroad == dictIPInfo['iDecBroad']:
      return strSubnet
    if iDecBroad < dictIPInfo['iDecBroad']:
      return "Partial match:{}".format(strSubnet)
  return "{}/{}".format(strIPAddress,32)

iLoc = sys.argv[0].rfind(".")
strConf_File = sys.argv[0][:iLoc] + ".ini"

strLine = "  "
print ("Reading in configuration")
objINIFile = open(strConf_File,"r")
strLines = objINIFile.readlines()
objINIFile.close()

for strLine in strLines:
  iCommentLoc = strLine.find("#")
  if iCommentLoc > -1:
    strLine = strLine[:iCommentLoc].strip()
  else:
    strLine = strLine.strip()
  if "=" in strLine:
    strConfParts = strLine.split("=")
    strVarName = strConfParts[0].strip()
    strValue = strConfParts[1].strip()
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
    if strVarName == "RecordID":
      strRecordID = strValue
    if strVarName == "IPField":
      strIPField = strValue
    if strVarName == "NetID":
      strNetIDField = strValue
    if strVarName == "BroadCast":
      strBroadCastField = strValue
    if strVarName == "IntIPAddr":
      strIntIPField = strValue
    if strVarName == "HostCount":
      strHostCountField = strValue
    if strVarName == "BitMask":
      strBitMaskField = strValue

dbConn = SQLConn (strServer,strDBUser,strDBPWD,strInitialDB)
strSQL = ("SELECT {},{} FROM {}.{};".format(strRecordID,strIPField,strInitialDB,strTableName))
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
  strSubnet = dbRow[1]
  iSubnetID = dbRow[0]
  dictIPInfo = IPCalc (strSubnet)
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
  if "DecIP" in dictIPInfo:
    iDecIP = dictIPInfo['DecIP']
  else:
    iDecIP = -10
  if "BitMask" in dictIPInfo:
    iBitMask = dictIPInfo['BitMask']
  else:
    iBitMask = -10
  
  if "IPError" in dictIPInfo:
    print (dictIPInfo['IPError'])
  if iDecSubID > 0:
    strSubnet = FindMask(iDecSubID,iDecBroad)
    iRowNum += 1
    print ("Completed {:.1%}".format(iRowNum/iRowCount),end="\r")
    print(".", end="")
    strSQL = ("UPDATE {db}.{table} SET {NetIDField} = {NetIDValue}, {BroadcastField} = {BroadcastValue},"
              " {iIPField} = {iIPValue}, {HostCountField} = {HostCountValue},"
              " {BitMaskField} = {BitMaskValue} WHERE {IDField} = {IDValue};".format(
                NetIDValue=iDecSubID, BroadcastValue=iDecBroad, HostCountValue=iHostcount,
                IDValue=iSubnetID, db=strInitialDB, table=strTableName, NetIDField=strNetIDField,
                BroadcastField=strBroadCastField, iIPField=strIntIPField, IDField=strRecordID,
                HostCountField=strHostCountField, BitMaskField=strBitMaskField, BitMaskValue=iBitMask,
                iIPValue=iDecIP))
    lstReturn = SQLQuery (strSQL,dbConn)
    if not ValidReturn(lstReturn):
      print ("Unexpected: {}".format(lstReturn))
      break
    # elif lstReturn[0] != 1:
    #   print ("{} \n Records affected {}, expected 1 record affected".format(strSQL, lstReturn[0]))