'''
Script to import Security ScoreCard footprint exports and process for customer details
Author Siggi Bjarnason Copyright 2021
Website https://supergeek.us/ 

Following packages need to be installed as administrator
pip install pymysql
pip install requests
pip install jason


'''
# Import libraries
import sys
import os
import time
import pymysql
import csv
from pymysql.err import Error
import requests
import json

try:
  import tkinter as tk
  from tkinter import filedialog
  btKinterOK = True
except:
  print ("Failed to load tkinter, CLI only mode.")
  btKinterOK = False
# End imports

#Default values, overwrite these in the ini file
strDelim = ","          # what is the field seperate in the input file

def getInput(strPrompt):
    if sys.version_info[0] > 2 :
        return input(strPrompt)
    else:
        return raw_input(strPrompt)

def LogEntry(strMsg):
  print (strMsg)

def CleanExit(strMsg):
  print (strMsg)
  sys.exit(9)

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
    if strSQL[:6].lower() == "select" or strSQL[:4].lower() == "call" or strSQL[:4].lower() == "show" or strSQL[:8].lower() == "describe":
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
  except Exception as err:
    if strSQL[:6].lower() != "select":
      db.rollback()
    return "unknown Error: unable to execute: {}\n{}".format(err,strSQL)

def DBClean(strText):
  if strText.strip() == "":
    return "NULL"
  elif isInt(strText):
    return strText #int(strText)
  elif isFloat(strText):
    return strText # float(strText)
  else:
    strTemp = strText.encode("ascii","ignore")
    strTemp = strTemp.decode("ascii","ignore")
    strTemp = strTemp.replace("\\","\\\\")
    strTemp = strTemp.replace("'","\\'")
    try:
      strTemp = time.strftime("%Y-%m-%d",time.localtime(time.mktime(time.strptime(strTemp,strDTFormat))))
    except ValueError:
      pass
    return "'" + strTemp + "'"

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

def isFloat (fValue):
  if isinstance(fValue,(float,int,str)):
    try:
      fTemp = float(fValue)
    except ValueError:
      fTemp = "NULL"
  else:
    fTemp = "NULL"
  return fTemp != "NULL"

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

def QueryNCC (strIPAddress):
  #execute Whois Query against ARIN.
  dictResp={}
  strURL="http://whois.arin.net/rest/ip/"+strIPAddress
  strHeader={'Accept': 'application/json'}
  try:
    WebRequest = requests.get(strURL, headers=strHeader)
  except:
    return "Failed to connect to ARIN"
  
  if WebRequest.status_code !=200:
    return "ARIN returned error code " + str(WebRequest.status_code)
  if isinstance(WebRequest,requests.models.Response)==False:
    return "ARIN response is unknown type"

  try:
    jsonWebResult = json.loads(WebRequest.text)
  except:
    return "Failed to decode the response from ARIN"

  if "net" not in jsonWebResult:
    return "ARIN Response not a Net Object"

  dictResp['Org'] = jsonWebResult['net']['orgRef']['@name']
  dictResp['Handle'] = jsonWebResult['net']['orgRef']['@handle']
  dictResp['Ref'] = jsonWebResult['net']['ref']['$']
  dictResp['Name'] = jsonWebResult['net']['name']['$']
  
  if dictResp['Org'] == "RIPE Network Coordination Centre":
    #execute Whois Query against RIPE.
    strURL = "https://rest.db.ripe.net/search.json?query-string="+strIPAddress
    try:
      WebRequest = requests.get(strURL, headers=strHeader)
    except:
      return "Failed to connect to RIPE"
    
    if WebRequest.status_code !=200:
      return "RIPE returned error code " + str(WebRequest.status_code)
    if isinstance(WebRequest,requests.models.Response)==False:
      return "RIPE response is unknown type"

    try:
      jsonWebResult = json.loads(WebRequest.text)
    except:
      return "Failed to decode the response from RIPE"
    try:
      dictResp['Org'] = jsonWebResult['objects']['object'][0]['attributes']['attribute'][1]["value"]
      for dictObject in jsonWebResult['objects']['object'][0]['attributes']['attribute']:
        if dictObject["name"] == "remarks":
          dictResp['Handle'] = dictObject["value"]
      for dictObject in jsonWebResult['objects']['object'][1]['attributes']['attribute']:
        if dictObject["name"] == "mnt-by":
          dictResp['Name'] = dictObject["value"]
      if len(jsonWebResult['objects']['object']) > 2:
        dictResp['Ref'] = jsonWebResult['objects']['object'][2]['attributes']['attribute'][1]["value"]
    except Exception as err:
      print ("Error when parsing RIPE response for {}. Error: {}".format(strIPAddress,err))

  return dictResp

def processConf(strConf_File):

  LogEntry("Looking for configuration file: {}".format(strConf_File))
  if os.path.isfile(strConf_File):
    LogEntry("Configuration File exists")
  else:
    LogEntry("Can't find configuration file {}, make sure it is the same directory "
      "as this script and named the same with ini extension".format(strConf_File))
    sys.exit(9)

  strLine = "  "
  dictConfig = {}
  LogEntry("Reading in configuration")
  objINIFile = open(strConf_File, "r", encoding='utf8')
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
      dictConfig[strVarName] = strValue
      if strVarName == "include":
        LogEntry("Found include directive: {}".format(strValue))
        strValue = strValue.replace("\\","/")
        if strValue[:1] == "/" or strValue[1:3] == ":/":
          LogEntry("include directive is absolute path, using as is")
        else:
          strValue = strBaseDir + strValue
          LogEntry("include directive is relative path,"
            " appended base directory. {}".format(strValue))
        if os.path.isfile(strValue):
          LogEntry("file is valid")
          objINIFile = open(strValue,"r")
          strLines += objINIFile.readlines()
          objINIFile.close()
        else:
          LogEntry("invalid file in include directive")

  LogEntry("Done processing configuration, moving on")
  return dictConfig


# Initialize stuff
iLoc = sys.argv[0].rfind(".")
strCSVName = ""
strConf_File = sys.argv[0][:iLoc] + ".ini"
localtime = time.localtime(time.time())
strBaseDir = os.path.dirname(sys.argv[0])
iLoc = sys.argv[0].rfind(".")
strConf_File = sys.argv[0][:iLoc] + ".ini"
strDBUser = ""
strDBPWD = ""


#Start doing stuff
print ("This is a script to import Security Scorecard footprint export. "
        " This is running under Python Version {0}.{1}.{2}".format(
            sys.version_info[0],sys.version_info[1],sys.version_info[2]))
now = time.asctime()
print ("The time now is {}".format(now))

dictConfig = processConf(strConf_File)

if "Server" in dictConfig:
  strServer = dictConfig["Server"]
else:
  CleanExit("No database server info provided, that is required so I'm bailing.")

if "dbUser" in dictConfig:
  strDBUser = dictConfig["dbUser"]
else:
  CleanExit("No dbUser info provided, that is required so I'm bailing.")

if "dbPWD" in dictConfig:
  strDBPWD = dictConfig["dbPWD"]
else:
  CleanExit("No dbPWD info provided, that is required so I'm bailing.")

if "TableName" in dictConfig:
  strTableName = dictConfig["TableName"]
else:
  CleanExit("No TableName info provided, that is required so I'm bailing.")

if "CSVFileName" in dictConfig:
  strCSVName = dictConfig["CSVFileName"]
else:
  strCSVName = ""

if "FieldDelim" in dictConfig:
  strDelim = dictConfig["FieldDelim"]
else:
  strDelim = ","

if "InitialDB" in dictConfig:
  strInitialDB = dictConfig["InitialDB"]
else:
  strInitialDB = "mysql"

if "DateTimeFormat" in dictConfig:
  strDTFormat = dictConfig["DateTimeFormat"]
else:
  strDTFormat = "%Y-%m-%d"

sa = sys.argv

lsa = len(sys.argv)
if lsa > 1:
  strCSVName = sa[1]

if strCSVName == "":
  if btKinterOK:
    print ("File name to be imported is missing. Opening up a file open dialog box, please select the file you wish to import.")
    root = tk.Tk()
    root.withdraw()
    strCSVName = filedialog.askopenfilename(title = "Select CSV file",filetypes = (("CSV files","*.csv"),("Text files","*.txt"),("all files","*.*")))
  else:
    strCSVName = getInput("Please provide full path and filename for the CSV file to be imported: ")

if strCSVName == "":
  print ("No filename provided unable to continue")
  sys.exit()

if os.path.isfile(strCSVName):
  print ("OK found {}".format(strCSVName))
else:
  print ("Can't find CSV file {}".format(strCSVName))
  sys.exit(4)

strCompanyURL,strext = os.path.splitext(os.path.basename(strCSVName))
strCompanyURL = strCompanyURL.replace(".footprint","")

dbConn = SQLConn (strServer,strDBUser,strDBPWD,strInitialDB)
LogEntry("Starting the import of {} into database on {}".format(strCSVName,strServer))
LogEntry("Date Time format set to: {}".format(strDTFormat))
LogEntry ("Truncating exiting table")
strSQL = "delete from {} where vcCompanyURL = '{}';".format(strTableName,strCompanyURL)
lstReturn = SQLQuery (strSQL,dbConn)
if not ValidReturn(lstReturn):
  print ("Unexpected: {}".format(lstReturn))
  sys.exit(9)
else:
  LogEntry ("Deleted {} old records".format(lstReturn[0]))

iLine = 0
with open(strCSVName,newline="") as hCSV:
  myReader = csv.reader(hCSV, delimiter=strDelim)
  lstLine = next(myReader)
  LogEntry ("Starting import...")

  for lstLine in myReader :
    lstValues = []
    lstBitMask = []
    lstDescr = []
    strCustomer = ""
    if "-" in lstLine[1]:
      lstIPRange = lstLine[1].split("-")
      dictIPInfo = IPCalc(lstIPRange[0])
      strIPStart = dictIPInfo["iDecSubID"]
      dictIPInfo = IPCalc(lstIPRange[1])
      strIPEnd = dictIPInfo["iDecBroad"]
      dictNCC = QueryNCC(lstIPRange[0])
    else:
      dictIPInfo = IPCalc(lstLine[1])
      strIPStart = dictIPInfo["DecIP"]
      strIPEnd = strIPStart
      dictNCC = QueryNCC(lstLine[1])
    strSQL = ("SELECT vcCustomer,vcDescription,iBitMask FROM tbl_ipam"
              " WHERE iNetID <= {} AND iBroadcast >= {} "
              " ORDER BY iHostCount;".format(strIPStart,strIPEnd))
    lstReturn = SQLQuery (strSQL,dbConn)
    if not ValidReturn(lstReturn):
      print ("Unexpected: {}".format(lstReturn))
      sys.exit(9)
    else:
      for dbRow in lstReturn[1]:
        strCustomer = dbRow[0]
        if strCustomer is None:
          strCustomer = ""
        strDescription = dbRow[1]
        if strDescription is None:
          strDescription = ""
        iBitMask = int(dbRow[2])
        if iBitMask > 6:
          lstBitMask.append(str(iBitMask))
          if strDescription != "":
            lstDescr.append(strDescription)
          if strCustomer != "":
            break

    strBitMask = ";".join(lstBitMask)
    strDescription = ";".join(lstDescr)

    iLine += 1
    strSQL = ("insert into {} (vcCompanyURL,vcDomain,vcIPAddr,vcCountry,vcCustomer,vcNetDescr,"
                "vcMatched,vcOrg,vcName,vcHandle,vcRef) "
              " values ('{}','{}','{}','{}','{}','{}','{}','{}','{}','{}','{}');".format(
                strTableName, strCompanyURL,lstLine[0], lstLine[1], lstLine[3],strCustomer,
                strDescription,strBitMask,dictNCC["Org"],dictNCC["Name"],dictNCC["Handle"],dictNCC["Ref"] ))
    lstReturn = SQLQuery (strSQL,dbConn)
    if not ValidReturn(lstReturn):
      print ("Unexpected: {}".format(lstReturn))
      sys.exit(9)
    else:
      # print ("Inserted {} record".format(iLine),end="\r")
      if lstReturn[0] != 1:
        LogEntry("\nExpected 1 affected record, but got back {} records affected!".format(lstReturn[0]))
      print ("processed {} record".format(iLine),end="\r")
print ("")
LogEntry("Done. Processed {} records".format(iLine))

