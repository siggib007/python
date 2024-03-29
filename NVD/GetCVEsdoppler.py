'''
NIST NVD Fetch CVE's API Script. Downloads all CVE's modified during a specified timeframe and updates a database.
Author Siggi Bjarnason Copyright 2021

Following packages need to be installed as administrator
pip install requests
pip install jason
pip install pyodbc
pip install pymysql


'''
# Import libraries
import sys
import requests
import os
import time
import datetime
import urllib.parse as urlparse
import json
import platform

# End imports

#avoid insecure warning

requests.urllib3.disable_warnings()

tLastCall = 0
iTotalSleep = 0
dboErr = None
dbo = None
iTotalCount = 0
iEntryID = 0
strDBType = "undef"
iRowNum = 1
iUpdateCount = 0

def SQLConn (strServer,strDBUser,strDBPWD,strInitialDB):
  global dboErr
  global dbo
  strError = ""

  try:
    # Open database connection
    if strDBType == "mssql":
      import pyodbc as dbo
      import pyodbc as dboErr
      if strDBUser == "":
        strConnect = (" DRIVER={{ODBC Driver 17 for SQL Server}};"
                      " SERVER={};"
                      " DATABASE={};"
                      " Trusted_Connection=yes;".format(strServer,strInitialDB))
        LogEntry ("Connecting to MSSQL server {} via trusted connection".format(strServer))
      else:
        strConnect = (" DRIVER={{ODBC Driver 17 for SQL Server}};"
                      " SERVER={};"
                      " DATABASE={};"
                      " UID={};"
                      " PWD={};".format(strServer,strInitialDB,strDBUser,strDBPWD))
        LogEntry ("Connecting to MSSQL server {} via username/password".format(strServer))
      return dbo.connect(strConnect)
    elif strDBType == "mysql":
      import pymysql as dbo
      from pymysql import err as dboErr
      LogEntry ("Connecting to MySQL server {}".format(strServer))
      return dbo.connect(host=strServer,user=strDBUser,password=strDBPWD,db=strInitialDB)
    else:
      strError = ("Unknown database type: {}".format(strDBType))
  except dboErr.InternalError as err:
    LogEntry ("Error: unable to connect: {}".format(err),True)
  except dboErr.OperationalError as err:
    LogEntry ("Operational Error: unable to connect: {}".format(err),True)
  except dboErr.ProgrammingError as err:
    LogEntry ("Programing Error: unable to connect: {}".format(err),True)
  if strError != "":
    LogEntry (strError,True)

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
  except dboErr.InternalError as err:
    return "Internal Error: unable to execute: {}\n{}\nLength of SQL statement {}\n".format(err,strSQL[:255],len(strSQL))
  except dboErr.ProgrammingError as err:
    return "Programing Error: unable to execute: {}\n{}\nLength of SQL statement {}\n".format(err,strSQL[:255],len(strSQL))
  except dboErr.OperationalError as err:
    return "Programing Error: unable to execute: {}\n{}\nLength of SQL statement {}\n".format(err,strSQL[:255],len(strSQL))
  except dboErr.IntegrityError as err:
    return "Integrity Error: unable to execute: {}\n{}\nLength of SQL statement {}\n".format(err,strSQL[:255],len(strSQL))
  except dboErr.DataError as err:
    return "Data Error: unable to execute: {}\n{}\nLength of SQL statement {}\n".format(err,strSQL[:255],len(strSQL))
  except dboErr.InterfaceError as err:
    return "Interface Error: unable to execute: {}\n{}\nLength of SQL statement {}\n".format(err,strSQL[:255],len(strSQL))

def ValidReturn(lsttest):
  if isinstance(lsttest,list):
    if len(lsttest) == 2:
      if isinstance(lsttest[0],int) and (isinstance(lsttest[1],tuple) or isinstance(lsttest[1],list)):
        return True
      else:
        return False
    else:
      return False
  else:
    return False

def QDate2DB(strDate):
  strTemp = strDate.replace("T"," ")
  return strTemp.replace("Z","")

def DBClean(oTemp):
  if oTemp is None:
    return ""
  if isInt(oTemp):
    return int(oTemp)
  elif isFloat(oTemp):
    return float(oTemp)
  elif isinstance(oTemp,str):
    strTemp = str(oTemp)
    strTemp = strTemp.encode("ascii", "ignore")
    strTemp = strTemp.decode("ascii", "ignore")
    strTemp = strTemp.replace("\\", "\\\\")
    strTemp = strTemp.replace("'", "\\'")
    return strTemp
  else:
    LogEntry("Can't convert and clean {}. {}".format(type(oTemp),oTemp))

def getInput(strPrompt):
    if sys.version_info[0] > 2 :
        return input(strPrompt)
    else:
      LogEntry("Please upgrade to Python 3",True)

def SendNotification(strMsg):
  if not bNotifyEnabled:
    return "notifications not enabled"
  dictNotify = {}
  dictNotify["token"] = dictConfig["NotifyToken"]
  dictNotify["channel"] = dictConfig["NotifyChannel"]
  dictNotify["text"]=strMsg[:199]
  strNotifyParams = urlparse.urlencode(dictNotify)
  strURL = dictConfig["NotificationURL"] + "?" + strNotifyParams
  bStatus = False
  try:
    WebRequest = requests.get(strURL,timeout=iTimeOut)
  except Exception as err:
    LogEntry("Issue with sending notifications. {}".format(err))
  if isinstance(WebRequest,requests.models.Response)==False:
    LogEntry("response is unknown type")
  else:
    dictResponse = json.loads(WebRequest.text)
    if isinstance(dictResponse,dict):
      if "ok" in dictResponse:
        bStatus = dictResponse["ok"]
        LogEntry("Successfully sent slack notification\n{} ".format(strMsg))
    if not bStatus or WebRequest.status_code != 200:
      LogEntry("Problme: Status Code:[] API Response OK={}")
      LogEntry(WebRequest.text)

def CleanExit(strCause):
  global dbConn
  if strCause != "":
    LogEntry("{} is exiting abnormally on {}: {}".format (strScriptName,strScriptHost,strCause))
  SendNotification("{} is exiting abnormally on {} {}".format(strScriptName,
    strScriptHost, strCause))
  if dbConn !="":
    if iEntryID > 0:
      strdbNow = time.strftime("%Y-%m-%d %H:%M:%S")
      strSQL = ("update tblScriptExecuteList set dtStopTime='{}', bComplete=0, "
        " iRowsUpdated={} where iExecuteID = {} ;".format(strdbNow, iTotalCount,iEntryID))
      lstReturn = SQLQuery (strSQL,dbConn)
      LogEntry("tblScriptExecuteList for entry #{} updated. {} records updated".format(
          iEntryID, lstReturn[1]))
    dbConn.close()
    dbConn = ""
    LogEntry("dbconn closed")

  objLogOut.close()
  print("objLogOut closed")
  if objFileOut is not None:
    objFileOut.close()
    print("objFileOut closed")
  else:
    print("objFileOut is not defined yet")
  sys.exit(9)

def LogEntry(strMsg,bAbort=False):
  strTemp = ""
  strDBMsg = DBClean(strMsg[:9990])
  if dbConn !="":
    strSQL = "INSERT INTO tblLogs (vcScriptName, vcLogEntry) VALUES ('{}','{}');".format(strScriptName,strDBMsg)
    lstReturn = SQLQuery (strSQL,dbConn)
    if not ValidReturn(lstReturn):
      strTemp = ("\n Unexpected issue inserting log entry to the database: {}\n{}".format(lstReturn,strSQL))
    elif lstReturn[0] != 1:
      strTemp = ("   Records affected {}, expected 1 record affected when inserting log entry to the database".format(len(lstReturn[1])))
  else:
    strTemp = ". Database connection not established"
  strMsg += strTemp
  strTimeStamp = time.strftime("%m-%d-%Y %H:%M:%S")
  objLogOut.write("{0} : {1}\n".format(strTimeStamp,strMsg))
  print(strMsg)
  if bAbort:
    SendNotification("{} on {}: {}".format (strScriptName,strScriptHost,strMsg[:99]))
    CleanExit("")

def isFloat(fValue):
  if isinstance(fValue, (float, int, str)):
    try:
      fTemp = float(fValue)
    except ValueError:
      fTemp = "NULL"
  else:
    fTemp = "NULL"
  return fTemp != "NULL"

def isInt(CheckValue):
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

def ConvertFloat(fValue):
  if isinstance(fValue,(float,int,str)):
    try:
      fTemp = float(fValue)
    except ValueError:
      fTemp = "NULL"
  else:
    fTemp = "NULL"
  return fTemp

def formatUnixDate(iDate):
  structTime = time.localtime(iDate)
  return time.strftime(strFormat,structTime)

def TitleCase(strConvert):
  strTemp = strConvert.replace("_", " ")
  return strTemp.title()

def MakeAPICall(strURL, strHeader, strMethod,  dictPayload=""):

  global tLastCall
  global iTotalSleep

  fTemp = time.time()
  fDelta = fTemp - tLastCall
  LogEntry("It's been {} seconds since last API call".format(fDelta))
  if fDelta > iMinQuiet:
    tLastCall = time.time()
  else:
    iDelta = int(fDelta)
    iAddWait = iMinQuiet - iDelta
    LogEntry ("It has been less than {} seconds since last API call, "
      "waiting {} seconds".format(iMinQuiet,iAddWait))
    iTotalSleep += iAddWait
    time.sleep(iAddWait)
  iErrCode = ""
  iErrText = ""

  LogEntry("Doing a {} to URL: \n {}\n".format(strMethod,strURL))
  try:
    if strMethod.lower() == "get":
      WebRequest = requests.get(strURL, headers=strHeader, verify=False)
      LogEntry("get executed")
    if strMethod.lower() == "post":
      if dictPayload != "":
        WebRequest = requests.post(strURL, json= dictPayload, headers=strHeader, verify=False)
      else:
        WebRequest = requests.post(strURL, headers=strHeader, verify=False)
      LogEntry("post executed")
  except Exception as err:
    LogEntry("Issue with API call. {}".format(err))
    CleanExit("due to issue with API, please check the logs")

  if isinstance(WebRequest,requests.models.Response)==False:
    LogEntry("response is unknown type")
    iErrCode = "ResponseErr"
    iErrText = "response is unknown type"

  LogEntry("call resulted in status code {}".format(WebRequest.status_code))
  if WebRequest.status_code != 200:
    # LogEntry(WebRequest.text)
    iErrCode = WebRequest.status_code
    iErrText = WebRequest.text

  if iErrCode != "" or WebRequest.status_code !=200:
    return "There was a problem with your request. Error {}: {}".format(iErrCode,iErrText)
  else:
    try:
      return WebRequest.json()
    except Exception as err:
      LogEntry("Issue with converting response to json. "
        "Here are the first 99 character of the response: {}".format(WebRequest.text[:99]))

def processConf(strConf_File):

  LogEntry("Looking for configuration file: {}".format(strConf_File))
  if os.path.isfile(strConf_File):
    LogEntry("Configuration File exists")
  else:
    LogEntry("Can't find configuration file {}, make sure it is the same directory "
      "as this script and named the same with ini extension".format(strConf_File))
    LogEntry("{} on {}: Exiting.".format (strScriptName,strScriptHost),True)

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

def CPEParsing(lstCPEMatch, strCVEID):
  for dictCPE in lstCPEMatch:
        if "vulnerable" in dictCPE:
          bVuln = DBClean(dictCPE["vulnerable"])
        else:
          bVuln = "n/a"
        if "cpe23Uri" in dictCPE:
          strCPEuri = DBClean(dictCPE["cpe23Uri"])
        else:
          strCPEuri = "n/a"
        if "versionEndExcluding" in dictCPE:
          strVerEnd = DBClean(dictCPE["versionEndExcluding"])
        else:
          strVerEnd = "n/a"
        if "versionStartIncluding" in dictCPE:
          strVerStart = DBClean(
              dictCPE["versionStartIncluding"])
        else:
          strVerStart = "n/a"
        # print("  -- {} {} Version incl {} - {} ".format(bVuln, strCPEuri, strVerStart, strVerEnd))
        strCPEuri = strCPEuri.replace("\:","\;")
        lstCPEuri = strCPEuri.split(":")
        del lstCPEuri[0]
        del lstCPEuri[0]
        while len(lstCPEuri) > 11:
          del lstCPEuri[len(lstCPEuri)-1]
        lstCPEClean = []
        for strCPEitem in lstCPEuri:
          if strCPEitem == "*":
            lstCPEClean.append("any")
          elif strCPEitem == "-":
            lstCPEClean.append("n/a")
          elif strCPEitem == "a":
            lstCPEClean.append("Application")
          elif strCPEitem == "o":
            lstCPEClean.append("OS")
          elif strCPEitem == "h":
            lstCPEClean.append("Hardware")
          else:
            lstCPEClean.append(strCPEitem)

        strCPEClean = "', '".join(lstCPEClean)
        strdbNow = time.strftime("%Y-%m-%d %H:%M:%S")
        strSQL = ("INSERT INTO tblCPE (vcCVEid, bVulnerable, vcCPEurl, vcVerStart, vcVerStop, dtLastTouched, "
                  "vcType, vcVendor, vcProduct, vcVersion, vcUpdate, vcEdition, vcLanguage, vcSWEdition, "
                  "vcTargetSW, vcTargetHW, vcOther) VALUES ('{}', '{}', '{}', '{}', '{}', '{}','{}');").format(
            strCVEID, bVuln, strCPEuri, strVerStart, strVerEnd, strdbNow, strCPEClean)
        lstReturn = SQLQuery(strSQL, dbConn)
        if not ValidReturn(lstReturn):
          LogEntry("Unexpected: {}".format(lstReturn))
          CleanExit(
              "due to unexpected SQL return, please check the logs")

def ResponseParsing(APIResponse):
  global iUpdateCount

  if "result" in APIResponse:
    if "CVE_Items" in APIResponse["result"]:
      if isinstance(APIResponse["result"]["CVE_Items"], list):
        for dictCVEItem in APIResponse["result"]["CVE_Items"]:
          strDescr = "n/a"
          strCVEID = "unknown"
          strProbType = "n/a"
          fExploitableScore = -1.5
          fImpactScore = -1.5
          fCVSSv3 = -1.5
          strVector = "none"
          strPubDate = "n/a"
          strModDate = "n/a"
          if "cve" in dictCVEItem:
            if "CVE_data_meta" in dictCVEItem["cve"]:
              if "ID" in dictCVEItem["cve"]["CVE_data_meta"]:
                strCVEID = DBClean(dictCVEItem["cve"]["CVE_data_meta"]["ID"])
              else:
                LogEntry("Entry {} is without ID field.".format(dictCVEItem))
            else:
              LogEntry(
                "Entry {} is without CVE_data_meta tree.".format(dictCVEItem))
            if "description" in dictCVEItem["cve"]:
              if "description_data" in dictCVEItem["cve"]["description"]:
                if isinstance(dictCVEItem["cve"]["description"]["description_data"], list):
                  # LogEntry("CVE {} description_data is a list with {} elements. Fetching just first one".format(strCVEID,
                     # len(dictCVEItem["cve"]["description"]["description_data"])))
                  if "value" in dictCVEItem["cve"]["description"]["description_data"][0]:
                    strDescr = DBClean(
                      dictCVEItem["cve"]["description"]["description_data"][0]["value"])
                  else:
                    LogEntry(
                      "CVE {} has no description data value in first row.".format(strCVEID))
                elif isinstance(dictCVEItem["cve"]["description"]["description_data"], dict):
                  # LogEntry(
                  #     "CVE {} description_data is a dict. Fetching just first one".format(strCVEID))
                  if "value" in dictCVEItem["cve"]["description"]["description_data"]:
                    strDescr = DBClean(
                      dictCVEItem["cve"]["description"]["description_data"]["value"])
                  else:
                    LogEntry(
                        "CVE {} has no description data value.".format(strCVEID))
                else:
                  LogEntry("CVE {} description data is an unknown datatype {}".format(
                      strCVEID, type(dictCVEItem["cve"]["description"]["description_data"])))
              else:
                LogEntry(
                    "CVE {} has no description_data tree.".format(strCVEID))
            else:
              LogEntry("CVE {} has no description tree".format(strCVEID))
            if "problemtype" in dictCVEItem["cve"]:
              if "problemtype_data" in dictCVEItem["cve"]["problemtype"]:
                if "description" in dictCVEItem["cve"]["problemtype"]["problemtype_data"][0]:
                  if len(dictCVEItem["cve"]["problemtype"]["problemtype_data"][0]["description"]) > 0:
                    strProbType = DBClean(
                      dictCVEItem["cve"]["problemtype"]["problemtype_data"][0]["description"][0]["value"])
                  else:
                    strProbType = "not present"
                    LogEntry(
                        "Problem type description for CVE {} not present".format(strCVEID))
                else:
                  LogEntry(
                    "Problem type description for CVE {} not present".format(strCVEID))
              else:
                LogEntry(
                    "Problem type data for CVE {} not present".format(strCVEID))
            else:
              LogEntry(
                  "Problem type tree for CVE {} not present".format(strCVEID))
          else:
            LogEntry("Entry {} is without cve tree.".format(dictCVEItem))
          if "impact" in dictCVEItem:
            if "baseMetricV3" in dictCVEItem["impact"]:
              if "exploitabilityScore" in dictCVEItem["impact"]["baseMetricV3"]:
                fExploitableScore = DBClean(
                  dictCVEItem["impact"]["baseMetricV3"]["exploitabilityScore"])
              else:
                LogEntry("CVE {} has no Exploitablility Score".format(strCVEID))
              if "impactScore" in dictCVEItem["impact"]["baseMetricV3"]:
                fImpactScore = DBClean(
                  dictCVEItem["impact"]["baseMetricV3"]["impactScore"])
              else:
                LogEntry("CVE {} has no impact Score".format(strCVEID))
              if "cvssV3" in dictCVEItem["impact"]["baseMetricV3"]:
                if "baseScore" in dictCVEItem["impact"]["baseMetricV3"]["cvssV3"]:
                  fCVSSv3 = DBClean(
                    dictCVEItem["impact"]["baseMetricV3"]["cvssV3"]["baseScore"])
                else:
                  LogEntry("CVE {} has no base Score".format(strCVEID))
                if "vectorString" in dictCVEItem["impact"]["baseMetricV3"]["cvssV3"]:
                  strVector = DBClean(
                    dictCVEItem["impact"]["baseMetricV3"]["cvssV3"]["vectorString"])
                else:
                  LogEntry("CVE {} has no vector string".format(strCVEID))
              else:
                LogEntry("CVE {} has no cvss3 tree".format(strCVEID))
            else:
              LogEntry("CVE {} has no Base v3 metric".format(strCVEID))
          else:
            LogEntry("CVE {} has no impact tree".format(strCVEID))
          if "publishedDate" in dictCVEItem:
            strPubDate = QDate2DB(DBClean(dictCVEItem["publishedDate"]))
          else:
            LogEntry("CVE {} has no published date".format(strCVEID))
          if "lastModifiedDate" in dictCVEItem:
            strModDate = QDate2DB(DBClean(dictCVEItem["lastModifiedDate"]))
          else:
            LogEntry("CVE {} has no mod date".format(strCVEID))
          print("{} {}. Impact: {} Exploitable {} CVSSv3: {} Vector: {} Pub: {} Mod: {} Descr Len: {}".format(
              strCVEID, strProbType, fImpactScore, fExploitableScore, fCVSSv3, strVector, strPubDate, strModDate, len(strDescr)))
          strdbNow = time.strftime("%Y-%m-%d %H:%M:%S")
          strSQL = "select * from tblNVD where vcCVEid = '{}'".format(strCVEID)
          lstReturn = SQLQuery(strSQL, dbConn)
          if not ValidReturn(lstReturn):
            LogEntry("Unexpected: {}".format(lstReturn))
            sys.exit(9)
          elif len(lstReturn[1]) == 0:
            LogEntry("Adding CVE {}".format(strCVEID))
            strSQL = ("INSERT INTO tblNVD (vcCVEid, vcCWEid, fImpactScore, fExploitScore, fCVSSv3, vcVector, dtPubDate, dtModDate, strDescr, dtLastTouched) "
                      " VALUES ('{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}');").format(strCVEID, strProbType, fImpactScore,
                                                fExploitableScore, fCVSSv3, strVector, strPubDate, strModDate, strDescr, strdbNow)
          elif len(lstReturn[1]) == 1:
            LogEntry("Updating CVE {}".format(strCVEID))
            strSQL = ("UPDATE tblNVD SET vcCWEid = '{}', fImpactScore = '{}', fExploitScore = '{}', fCVSSv3 = '{}', vcVector = '{}', dtPubDate = '{}', "
                      " dtModDate = '{}', strDescr = '{}', dtLastTouched = '{}' WHERE vcCVEid = '{}' ;").format(strProbType, fImpactScore, fExploitableScore, fCVSSv3,
                      strVector, strPubDate, strModDate, strDescr, strdbNow, strCVEID)
          else:
            LogEntry("Something is horrible wrong, there are {} entries for CVE {}".format(
                len(lstReturn[1]), strCVEID), True)
          lstReturn = SQLQuery(strSQL, dbConn)
          if not ValidReturn(lstReturn):
            LogEntry("Unexpected: {}".format(lstReturn))
            LogEntry(strSQL)
            CleanExit("due to unexpected SQL return, please check the logs")
          elif lstReturn[0] != 1:
            LogEntry("Records affected {}, expected 1 record affected when updating tblVulnDetails".format(
                len(lstReturn[1])))

          iUpdateCount += 1

          if "configurations" in dictCVEItem:
            if "nodes" in dictCVEItem["configurations"]:
              if isinstance(dictCVEItem["configurations"]["nodes"], list):
                strSQL = "delete from tblCPE where vcCVEid = '{}';".format(
                    strCVEID)
                lstReturn = SQLQuery(strSQL, dbConn)
                if not ValidReturn(lstReturn):
                  LogEntry("Unexpected: {}".format(lstReturn))
                  CleanExit(
                    "due to unexpected SQL return, please check the logs")
                else:
                  LogEntry(
                    "Deleted {} CVE to CPE mappings".format(lstReturn[0]))
                for dictNodes in dictCVEItem["configurations"]["nodes"]:
                  if "cpe_match" in dictNodes:
                    if isinstance(dictNodes["cpe_match"], list):
                      CPEParsing(dictNodes["cpe_match"],strCVEID)
                    else:
                      LogEntry("CPE Match for {} is a {} not a list as expected.".format(
                          strCVEID, type(dictCVEItem["configuration"]["nodes"]["cpe_match"])))
                  else:
                    LogEntry(
                      "There is no CPE match branch for {}".format(strCVEID))
              else:
                LogEntry("Configuration nodes for {} is a {} not a list as expected.".format(
                  strCVEID, type(dictCVEItem["configuration"]["nodes"])))
            else:
              LogEntry("There is configuration node branch in {}".format(strCVEID))
          else:
            LogEntry("There is no configuration branch for {}".format(strCVEID))
      else:
        LogEntry("CVE_Items is a {} not a list".format(
            type(APIResponse["result"]["CVE_Items"])))
    else:
      LogEntry("No CVE_items tree in response")
  else:
    LogEntry("no results tree in response")

def ExecuteStats(dbConn):
  global iEntryID
  global dtLastExecute
  global dtStartTime
  
  strSQL = ("select dtStartTime from tblScriptExecuteList where iExecuteID = "
      " (select max(iExecuteID) from tblScriptExecuteList where vcScriptName = '{}')").format(strScriptName)
  lstReturn = SQLQuery (strSQL,dbConn)
  if not ValidReturn(lstReturn):
    LogEntry ("Unexpected: {}".format(lstReturn))
    CleanExit("due to unexpected SQL return, please check the logs")
  elif len(lstReturn[1]) == 0:
    dtLastExecute = None
  elif len(lstReturn[1]) == 1:
    dtLastExecute = lstReturn[1][0][0]
    LogEntry("Script was last executed on {}".format(dtLastExecute))
  else:
    LogEntry ("Looking for last execution date, fetched {} rows, expected 1 record affected".format(len(lstReturn[1])))
    LogEntry (strSQL,True)
    dtLastExecute = -10

  if strDBType == "mysql":
    strSQL = ("select TIMESTAMPDIFF(MINUTE,max(dtTimestamp),now()) as timediff "
              " from tblLogs where vcLogEntry not like '%last executed on%' and vcLogEntry not like 'Database connected%' and vcScriptName = '{}';".format(strScriptName))
  elif strDBType == "mssql":
    strSQL = ("select datediff(MINUTE,max(dtTimestamp),GETDATE()) as timediff "
              " from tblLogs where vcLogEntry not like '%last executed on%%' and vcLogEntry not like 'Database connected%' and vcScriptName = '{}';".format(strScriptName))
  else:
    LogEntry ("Unknown database type {}".format(strDBType),True)

  lstReturn = SQLQuery (strSQL,dbConn)
  if not ValidReturn(lstReturn):
    LogEntry ("Unexpected: {}".format(lstReturn))
    CleanExit("due to unexpected SQL return, please check the logs")
  elif len(lstReturn[1]) != 1:
    LogEntry ("While looking for quiet time fetched {}, rows expected 1 record affected".format(len(lstReturn[1])))
    iQuietMin = iMinScriptQuiet
  else:
    if isInt(lstReturn[1][0][0]):
      iQuietMin = int(lstReturn[1][0][0])
    else:
      LogEntry ("This is the first time this script is run in this environment, "
        " setting last scan time to {} minutes to work around quiet time logic".format(iMinScriptQuiet))
      iQuietMin = iMinScriptQuiet

  if iQuietMin < iMinScriptQuiet :
    LogEntry ("It has been {1} minutes since last log entry. Either the script is already running or it's been less that {0} min since it last run. "
      " Please wait until after {0} minutes since last run. Exiting".format(iMinScriptQuiet,iQuietMin),True)
  else:
    LogEntry("{} Database connection established. It's been {} minutes since last log entry.".format(strDBType, iQuietMin))

  strdbNow = time.strftime("%Y-%m-%d %H:%M:%S")
  strSQL = ("INSERT INTO tblScriptExecuteList (vcScriptName,dtStartTime,iGMTOffset) "
            " VALUES('{}','{}',{});".format(strScriptName,strdbNow,iGMTOffset))
  lstReturn = SQLQuery (strSQL,dbConn)
  if not ValidReturn(lstReturn):
    LogEntry ("Unexpected: {}".format(lstReturn))
    CleanExit("due to unexpected SQL return, please check the logs")
  elif lstReturn[0] != 1:
    LogEntry ("Records affected {}, expected 1 record affected when inserting int tblScriptExecuteList".format(len(lstReturn[1])))

  strSQL = ("select iExecuteID,dtStartTime from tblScriptExecuteList where iExecuteID in "
    " (select max(iExecuteID) from tblScriptExecuteList where vcScriptName = '{}');".format(strScriptName))
  lstReturn = SQLQuery (strSQL,dbConn)
  if not ValidReturn(lstReturn):
    LogEntry ("Unexpected: {}".format(lstReturn))
    CleanExit("due to unexpected SQL return, please check the logs")
  elif len(lstReturn[1]) != 1:
    LogEntry ("Records affected {}, expected 1 record affected when finding iEntryID".format(len(lstReturn[1])))
    iEntryID = -10
    dtStartTime = strdbNow
  else:
    iEntryID = lstReturn[1][0][0]
    dtStartTime = lstReturn[1][0][1]

  LogEntry("Recorded start entry, ID {}".format(iEntryID))

def main():
  global strFileOut
  global objFileOut
  global objLogOut
  global strScriptName
  global strScriptHost
  global strBaseDir
  global strBaseURL
  global dictConfig
  global strFormat
  global bNotifyEnabled
  global iMinQuiet
  global iTimeOut
  global iMinScriptQuiet
  global iGMTOffset
  global strDBType
  global dbConn
  global iUpdateCount
  global strNVDDateFormat

  #Define few Defaults
  iTimeOut = 120 # Max time in seconds to wait for network response
  iMinQuiet = 2 # Minimum time in seconds between API calls
  iMinScriptQuiet = 0 # Minimum time in minutes the script needs to be quiet before run again
  iSecSleep = 60 # Time to wait between check if ready
  iLastDays = 1  # Default number of days in the past. ex Last 1 day.
  iBatchSize = 10 # Default API Batch size
  iStartIndex = 0 # Initial start value
  dbConn = ""
  
  ISO = time.strftime("-%Y-%m-%d-%H-%M-%S")
  localtime = time.localtime(time.time())
  gmt_time = time.gmtime()
  iGMTOffset = (time.mktime(localtime) - time.mktime(gmt_time))/3600
  strFormat = "%Y-%m-%d %H:%M:%S"
  strNVDDateFormat = "%Y-%m-%dT%H:%M:%S:000 Z"
  strFileOut = None
  bNotifyEnabled = False

  strBaseDir = os.path.dirname(sys.argv[0])
  strRealPath = os.path.realpath(sys.argv[0])
  strRealPath = strRealPath.replace("\\","/")
  if strBaseDir == "":
    iLoc = strRealPath.rfind("/")
    strBaseDir = strRealPath[:iLoc]
  if strBaseDir[-1:] != "/":
    strBaseDir += "/"
  strLogDir  = strBaseDir + "Logs/"
  if strLogDir[-1:] != "/":
    strLogDir += "/"

  iLoc = sys.argv[0].rfind(".")
  strConf_File = sys.argv[0][:iLoc] + ".ini"

  if not os.path.exists (strLogDir) :
    os.makedirs(strLogDir)
    print("\nPath '{0}' for log files didn't exists, so I create it!\n".format(strLogDir))

  strScriptName = os.path.basename(sys.argv[0])
  iLoc = strScriptName.rfind(".")
  strLogFile = strLogDir + strScriptName[:iLoc] + ISO + ".log"
  strVersion = "{0}.{1}.{2}".format(sys.version_info[0],sys.version_info[1],sys.version_info[2])
  strScriptHost = platform.node().upper()

  print("This is a script to download CVE's from NIST's NVD via API. "
    "This is running under Python Version {}".format(strVersion))
  print("Running from: {}".format(strRealPath))
  dtNow = time.asctime()
  print("The time now is {}".format(dtNow))
  print("Logs saved to {}".format(strLogFile))
  objLogOut = open(strLogFile,"w",1)
  objFileOut = None

  dictConfig = processConf(strConf_File)

  if "NotifyToken" in dictConfig and "NotifyChannel" in dictConfig and "NotificationURL" in dictConfig:
    bNotifyEnabled = True
  else:
    bNotifyEnabled = False
    LogEntry("Missing configuration items for Slack notifications, "
      "turning slack notifications off")

  if "APIBaseURL" in dictConfig:
    strBaseURL = dictConfig["APIBaseURL"]
  else:
    CleanExit("No Base API provided")
  if strBaseURL[-1:] != "/":
    strBaseURL += "/"

  if "NotifyEnabled" in dictConfig:
    if dictConfig["NotifyEnabled"].lower() == "yes" \
      or dictConfig["NotifyEnabled"].lower() == "true":
      bNotifyEnabled = True
    else:
      bNotifyEnabled = False

  if "DateTimeFormat" in dictConfig:
    strFormat = dictConfig["DateTimeFormat"]

  if "NDVTimeFormat" in dictConfig:
    strNVDDateFormat = dictConfig["NDVTimeFormat"]

  if "BatchSize" in dictConfig:
    if isInt(dictConfig["BatchSize"]):
      iBatchSize = int(dictConfig["BatchSize"])
    else:
      LogEntry("Invalid BatchSize, setting to defaults of {}".format(iBatchSize))

  if "TimeOut" in dictConfig:
    if isInt(dictConfig["TimeOut"]):
      iTimeOut = int(dictConfig["TimeOut"])
    else:
      LogEntry("Invalid timeout, setting to defaults of {}".format(iTimeOut))

  if "SecondsBeetweenChecks" in dictConfig:
    if isInt(dictConfig["SecondsBeetweenChecks"]):
      iSecSleep = int(dictConfig["SecondsBeetweenChecks"])
    else:
      LogEntry("Invalid sleep time, setting to defaults of {}".format(iSecSleep))

  if "MinQuiet" in dictConfig:
    if isInt(dictConfig["MinQuiet"]):
      iMinQuiet = int(dictConfig["MinQuiet"])
    else:
      LogEntry("Invalid MinQuiet, setting to defaults of {}".format(iMinQuiet))

  if "MinQuietTime" in dictConfig:
    if isInt(dictConfig["MinQuietTime"]):
      iMinScriptQuiet = int(dictConfig["MinQuietTime"])
    else:
      LogEntry("Invalid MinQuiet, setting to defaults of {}".format(iMinScriptQuiet))

  if "LastDays" in dictConfig:
    if isInt(dictConfig["LastDays"]):
      iLastDays = int(dictConfig["LastDays"])
    else:
      LogEntry("Invalid Last Days, setting to defaults of {}".format(iLastDays))

  if "FetchType" in dictConfig:
    strFetchType = dictConfig["FetchType"].lower()
  else:
    strFetchType = "undef"

  if "OutDir" in dictConfig:
    strOutDir = dictConfig["OutDir"]
  else:
    strOutDir = ""

  strAPIKey = os.getenv("ACCESSKEY")
  strServer = os.getenv("SERVER")
  strDBUser = os.getenv("DBUSER")
  strDBPWD = os.getenv("DBPWD")
  strInitialDB = os.getenv("INITIALDB")
  strDBType = os.getenv("DBTYPE")

  
  strOutDir = strOutDir.replace("\\", "/")
  if strOutDir[-1:] != "/":
    strOutDir += "/"

  if not os.path.exists(strOutDir):
    os.makedirs(strOutDir)
    print(
        "\nPath '{0}' for ouput files didn't exists, so I create it!\n".format(strOutDir))

  strFileOut = strOutDir + "apigetcves.json"
  LogEntry("Output will be written to {}".format(strFileOut))

  try:
    objFileOut = open(strFileOut, "w", encoding='utf8')
  except PermissionError:
    LogEntry("unable to open output file {} for writing, "
             "permission denied.".format(strFileOut), True)
  except FileNotFoundError:
    LogEntry("unable to open output file {} for writing, "
             "Issue with the path".format(strFileOut), True)

  dbConn = SQLConn (strServer,strDBUser,strDBPWD,strInitialDB)
  LogEntry("Database connected, entering execute stats")
  ExecuteStats(dbConn)

  # actual work happens here

  oStart = ""

  strSQL = (
      "select max(dtStartTime) from tblScriptExecuteList where vcScriptName = '{}' and iExecuteID < {}".format(strScriptName, iEntryID))
  lstReturn = SQLQuery (strSQL,dbConn)
  if not ValidReturn(lstReturn):
    LogEntry ("Unexpected: {}".format(lstReturn))
    CleanExit("due to unexpected SQL return, please check the logs")
  elif len(lstReturn[1]) == 0:
    oStart = None
  elif len(lstReturn[1]) == 1:
    oStart = lstReturn[1][0][0]
    LogEntry("start time set to {}".format(oStart))
  else:
    LogEntry ("Looking for last query date, fetched {} rows, expected 1 record affected".format(len(lstReturn[1])))
    LogEntry (strSQL,True)
    oStart = -10

  dtEnd = time.strftime(strNVDDateFormat)
  if strFetchType == "update":
    dtStart = oStart.strftime(strNVDDateFormat) 
    LogEntry("Fetch Type is Update, fetching CVE's updated between {} and {}".format(dtStart,dtEnd))
  elif strFetchType == "last":
    oStart = datetime.timedelta(days=-iLastDays)+datetime.datetime.now()
    dtStart = oStart.strftime(strNVDDateFormat) 
    LogEntry("Fetch Type is last {} days, fetching CVE's updated between {} and {}".format(iLastDays, dtStart, dtEnd))
  elif strFetchType == "full":
    LogEntry("Fetch Type is Full, no date filter")
  else:
    CleanExit("Fetchtype {}, not recognized".format(strFetchType))

  iResultCount = 1
  while iStartIndex < iResultCount:
    strMethod = "get"
    dictParams = {}
    dictParams["apiKey"] = strAPIKey
    dictParams["startIndex"] = iStartIndex
    dictParams["resultsPerPage"] = iBatchSize
    if strFetchType != "full":
      dictParams["modStartDate"] = dtStart
      dictParams["modEndDate"] = dtEnd
    strQueryParam = urlparse.urlencode(dictParams)
    strURL = strBaseURL + "?" + strQueryParam
    APIResponse = MakeAPICall(strURL,"",strMethod)
    objFileOut.write(json.dumps(APIResponse))
    if "totalResults" in APIResponse:
      iResultCount = int(APIResponse["totalResults"])
    else:
      LogEntry("No result count in response")
      iResultCount = -15

    LogEntry("There are {} results in the query".format(iResultCount))

    ResponseParsing(APIResponse)
    iStartIndex += iBatchSize
    LogEntry("Batch complete. Next batch start={} Total: {}".format(iStartIndex,iResultCount))
    strdbNow = time.strftime("%Y-%m-%d %H:%M:%S")
    LogEntry("Updating progress in tblScriptExecuteList #{}".format(iEntryID))
    strSQL = ("update tblScriptExecuteList set dtStopTime='{}' , bComplete=0, "
              " iRowsUpdated={} where iExecuteID = {} ;".format(strdbNow, iUpdateCount, iEntryID))
    lstReturn = SQLQuery(strSQL, dbConn)
    if not ValidReturn(lstReturn):
      LogEntry("Unexpected: {}".format(lstReturn))

  # Closing thing out
  LogEntry("Doing validation checks")


  strSQL = "select count(*) from tblNVD where dtLastTouched > '{}';".format(dtStartTime)
  lstReturn = SQLQuery(strSQL, dbConn)
  if not ValidReturn(lstReturn):
    LogEntry("Unexpected: {}".format(lstReturn))
    CleanExit("due to unexpected SQL return, please check the logs")
  else:
    iCountVulnChange = lstReturn[1][0][0]

  LogEntry("VALIDATE: Total Number of vulnerabitlities downloaded {}; "
          " Total number of vulnerabitlities updated in the database {}".format(iUpdateCount, iCountVulnChange))
  if iUpdateCount != iCountVulnChange:
    LogEntry("VALIDATE: KB validation failed")
    SendNotification("{} has completed processing on {}, and validation checks failed".format(
        strScriptName, strScriptHost))
  else:
    LogEntry("VALIDATE: KB validation successful")
    SendNotification("{} has completed processing on {}, validation checks are good. "
                    " Processed {} vulnerabitlities.".format(strScriptName, strScriptHost, iUpdateCount))
  strdbNow = time.strftime("%Y-%m-%d %H:%M:%S")
  LogEntry("Updating completion entry #{}".format(iEntryID))
  strSQL = ("update tblScriptExecuteList set dtStopTime='{}' , bComplete=1, "
          " iRowsUpdated={} where iExecuteID = {} ;".format(strdbNow,iUpdateCount,iEntryID))
  lstReturn = SQLQuery (strSQL,dbConn)
  if not ValidReturn(lstReturn):
    LogEntry ("Unexpected: {}".format(lstReturn))

  if objFileOut is not None:
    objFileOut.close()
    print("objFileOut closed")
  else:
    print("objFileOut is not defined yet")

  LogEntry("Done! Output saved to {}".format(strFileOut))
  objLogOut.close()

if __name__ == '__main__':
    main()
