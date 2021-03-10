'''
Script to import Bitsight exports and process for customer details
Author Siggi Bjarnason Copyright 2021
Website https://supergeek.us/ 

Following packages need to be installed as administrator
pip install pymysql

'''
# Import libraries
import sys
import os
import string
import time
import pymysql
import csv
import socket

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

# Initialize stuff
iLoc = sys.argv[0].rfind(".")
strCSVName = ""
strConf_File = sys.argv[0][:iLoc] + ".ini"
localtime = time.localtime(time.time())

#Start doing stuff
print ("This is a script to import export files from Bitsight. "
        " This is running under Python Version {0}.{1}.{2}".format(
            sys.version_info[0],sys.version_info[1],sys.version_info[2]))
now = time.asctime()
print ("The time now is {}".format(now))

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
    if strVarName == "FieldDelim":
      strDelim = strValue
    if strVarName == "CSVFileName":
      strCSVName = strValue
    if strVarName == "DateTimeFormat":
      strDTFormat = strValue

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

dbConn = SQLConn (strServer,strDBUser,strDBPWD,strInitialDB)
LogEntry("Starting the import of {} into database on {}".format(strCSVName,strServer))
LogEntry("Date Time format set to: {}".format(strDTFormat))
LogEntry ("Truncating exiting table")
strSQL = "delete from tblbitsightvulns;"
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
    if lstLine[0][:10] == "Disclaimer" or lstLine[0][:11] == "*IP address":
      continue 
    lstFindingParts = lstLine[1].split(":")
    if ValidateIP(lstFindingParts[0]):
      strIPAddress = lstFindingParts[0]
    else:
      try:
        strDNS = socket.gethostbyname(lstFindingParts[0])
      except Exception as err:
        strDNS = err
      strIPAddress = strDNS
    
    lstValues = []
    lstCustomer = []
    lstDescr = []
    if strIPAddress[0] != "[":
      dictIPInfo = IPCalc(strIPAddress)
      strSQL = ("SELECT vcCustomer,vcDescription,iBitMask FROM tbl_ipam"
                " WHERE iNetID <= {0} AND iBroadcast >= {0} "
                " ORDER BY iHostCount;".format(dictIPInfo["DecIP"]))
      lstReturn = SQLQuery (strSQL,dbConn)
      if not ValidReturn(lstReturn):
        print ("Unexpected: {}".format(lstReturn))
        sys.exit(9)
      else:
        for dbRow in lstSubnets[1]:
          strCustomer = dbRow[0]
          strDescription = dbRow[1]
          iBitMask = int(dbRow[2])
          if iBitMask > 22:
            if strCustomer != "":
              lstCustomer.append(strCustomer)
            if strDescription != "":
              lstDescr.append(strDescription)
          if iBitMask = 32:
            break
    strCustomer = ";".join(lstCustomer)
    strDescription = ";".join(lstDescr)

    iLine += 1
    for strCSV in lstLine:
      lstValues.append(DBClean(strCSV))
    lstValues.append( "'{}'".format(strIPAddress))
    lstValues.append( "'{}'".format(strCustomer))
    lstValues.append( "'{}'".format(strDescription))
    strSQL = ("insert into tblbitsightvulns (vcRiskVector,vcFindingID,dtFirstSeen," 
              "dtLastSeen,vcGrade,vcImpactRVG,iLifeTime,vcSeverity,vcDetails,iSrcPort,"
              "iDstPort,vcPort,vcSrvType,vcSrvVer,vcRefresh,vcIPAddr,vcCustomer,vcNetDescr) "
              " values ({});".format(",".join(lstValues)))
    lstReturn = SQLQuery (strSQL,dbConn)
    if not ValidReturn(lstReturn):
      print ("Unexpected: {}".format(lstReturn))
      sys.exit(9)
    else:
      print ("Inserted {} record".format(lstReturn[0]),end="\r")
LogEntry("Done. Processed {} records".format(iLine))

