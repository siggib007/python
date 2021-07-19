'''
Security Score Card API Script. Downloads all issues for specific company filtered to a severity
Author Siggi Bjarnason Copyright 2021

Following packages need to be installed as administrator
pip install requests
pip install jason

'''
# Import libraries
import sys
import requests
import os
import time
import urllib.parse as urlparse
import json
import platform
import subprocess as proc

# End imports

#avoid insecure warning

requests.urllib3.disable_warnings()

tLastCall = 0
iTotalSleep = 0

def getInput(strPrompt):
    if sys.version_info[0] > 2 :
        return input(strPrompt)
    else:
      print("Please upgrade to Python 3")
      sys.exit()

def SendNotification(strMsg):
  LogEntry(strMsg)
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
  SendNotification("{} is exiting abnormally on {} {}".format(strScriptName,
    strScriptHost, strCause))
  objLogOut.close()
  print("objLogOut closed")
  if objFileOut is not None:
    objFileOut.close()
    print("objFileOut closed")
  else:
    print("objFileOut is not defined yet")
  sys.exit(9)

def LogEntry(strMsg,bAbort=False):
  strTimeStamp = time.strftime("%m-%d-%Y %H:%M:%S")
  objLogOut.write("{0} : {1}\n".format(strTimeStamp,strMsg))
  print(strMsg)
  if bAbort:
    SendNotification("{} on {}: {}".format (strScriptName,strScriptHost,strMsg[:99]))
    CleanExit("")

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
  # LogEntry("It's been {} seconds since last API call".format(fDelta))
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

  # LogEntry("Doing a {} to URL: \n {}\n".format(strMethod,strURL))
  try:
    if strMethod.lower() == "get":
      WebRequest = requests.get(strURL, headers=strHeader, verify=False)
      # LogEntry("get executed")
    if strMethod.lower() == "post":
      if dictPayload != "":
        WebRequest = requests.post(strURL, json= dictPayload, headers=strHeader, verify=False)
      else:
        WebRequest = requests.post(strURL, headers=strHeader, verify=False)
      # LogEntry("post executed")
  except Exception as err:
    LogEntry("Issue with API call. {}".format(err))
    CleanExit("due to issue with API, please check the logs")

  if isinstance(WebRequest,requests.models.Response)==False:
    LogEntry("response is unknown type")
    iErrCode = "ResponseErr"
    iErrText = "response is unknown type"

  # LogEntry("call resulted in status code {}".format(WebRequest.status_code))
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
    LogEntry("{} on {}: Exiting.".format (strScriptName,strScriptHost))
    objLogOut.close()
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

def main():
  global strFileOut
  global objFileOut
  global objLogOut
  global strScriptName
  global strScriptHost
  global tLastCall
  global iTotalSleep
  global strBaseDir
  global strBaseURL
  global dictConfig
  global strFormat
  global bNotifyEnabled
  global iMinQuiet
  global iTimeOut

  #Define few Defaults
  iTimeOut = 120 # Max time in seconds to wait for network response
  iMinQuiet = 2 # Minimum time in seconds between API calls
  iSecSleep = 60 # Time to wait between check if ready
  iTargetImprovement = 10 # What is the target score improvement
  strOrigionalFormat = "markdown"
  strConvert2 = "docx"


  ISO = time.strftime("-%Y-%m-%d-%H-%M-%S")

  dictParams = {}
  
  strFormat = "%Y-%m-%dT%H:%M:%S"
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
  dictPayload = {}
  strScriptHost = platform.node().upper()

  print("This is a script to download results of a Tenable workbench query via API. "
    "This is running under Python Version {}".format(strVersion))
  print("Running from: {}".format(strRealPath))
  dtNow = time.asctime()
  print("The time now is {}".format(dtNow))
  print("Logs saved to {}".format(strLogFile))
  objLogOut = open(strLogFile,"w",1)
  objFileOut = None

  dictConfig = processConf(strConf_File)

  if "AccessKey" in dictConfig:
    strHeader={
      'Content-type':'application/json',
      'authorization': 'Token ' + dictConfig["AccessKey"]}
  else:
    LogEntry("API Keys not provided, exiting.",True)

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

  if "CompanyURL" in dictConfig:
    strCompanyURL = dictConfig["CompanyURL"]
  else:
    CleanExit("Company URL is required but not provided, sorry have to bail")

  if "CompanyName" in dictConfig:
    strName = dictConfig["CompanyName"]
  else:
    strName = ""

  if "TargetImprove" in dictConfig:
    if isInt(dictConfig["TargetImprove"]):
      iTargetImprovement = int(dictConfig["TargetImprove"])
    else:
      LogEntry("Invalid TargetImprove, setting to defaults of {}".format(iTargetImprovement))

  if "OutDir" in dictConfig:
    strOutDir = dictConfig["OutDir"]

  strOutDir = strOutDir.replace("\\", "/")

  if strOutDir[-1:] != "/":
    strOutDir += "/"
  if not os.path.exists(strOutDir):
    os.makedirs(strOutDir)
    print("\nPath '{0}' for output files didn't exists, so I create it!\n".format(
        strOutDir))
  strFileOut = strOutDir + strCompanyURL + "-ImprovementPlan.md"
  strFileConv = strOutDir + strCompanyURL + "-ImprovementPlan." + strConvert2
  LogEntry("Output will be written to {}".format(strFileOut))

  try:
    objFileOut = open(strFileOut, "w", encoding='utf8')
  except PermissionError:
    LogEntry("unable to open output file {} for writing, "
             "permission denied.".format(strFileOut), True)

  dictIssueDet = {}
  strMethod = "get"
  strAPIFunction = "companies/{CompanyURL}".format(CompanyURL=strCompanyURL)
  # strParams = urlparse.urlencode(dictParams)
  strURL = strBaseURL + strAPIFunction 
  LogEntry("Submitting query request\n {} {}\n Payload{}".format(
      strMethod, strURL, dictPayload))
  APIResponse = MakeAPICall(strURL, strHeader, strMethod, dictPayload)
  if strName == "":
    if "name" in APIResponse:
      strName = APIResponse["name"]
    else:
      strName = "unknown"
  if "score" in APIResponse:
    if isInt(APIResponse["score"]):
      iScore = int(APIResponse["score"])
    else:
      CleanExit("Could not retrieve a valid current score, can't proceed")
  else:
    CleanExit("No score in API response, can't proceed")

  iTargetScore = iScore + iTargetImprovement
  objFileOut.write(
      "![Advania Logo](https://advania.is/library/Template/logo_o.png)\n")
  objFileOut.write("# Improvement plan to increase the security score of {} by {} points.\n\n".format(
            strName,iTargetImprovement))
  objFileOut.write(
      "## Summary Action Plan to bring the score from {} to {}\n\n".format(iScore, iTargetScore))
  strAPIFunction = "companies/{CompanyURL}/score-plans/by-target/{TargetScore}".format(
                    CompanyURL=strCompanyURL,TargetScore=iTargetScore)
  # strParams = urlparse.urlencode(dictParams)
  strURL = strBaseURL + strAPIFunction 
  LogEntry("Submitting query request\n {} {}\n Payload{}".format(
      strMethod, strURL, dictPayload))
  APIResponse = MakeAPICall(strURL, strHeader, strMethod, dictPayload)
  if "entries" in APIResponse:
    if isinstance(APIResponse["entries"],list):
      iListCount = len(APIResponse["entries"])
      LogEntry("Entries is a list with {} entries ".format(iListCount))
      objFileOut.write("***This plan contains {} types of issues to be addressed.***\n".format(iListCount))
      objFileOut.write("|Factor | Title | severity | Remediations|\n")
      objFileOut.write("|------|--------|----------|-------------|\n")
      for dictEntry in APIResponse["entries"]:
        LogEntry("Factor: {} Issue Type: {} Severity: {} Remediation count: {}".format(
            dictEntry["factor"], dictEntry["title"], dictEntry["severity"], dictEntry["remediations"]))
        objFileOut.write("|{} | {} | {} | {}|\n".format(
            TitleCase(dictEntry["factor"]), dictEntry["title"], dictEntry["severity"],dictEntry["remediations"]))
        dictIssueDet[dictEntry["issue_type"]] = dictEntry["title"]
    else:
      LogEntry("Entries is not a list, it is: {}".format(
          type(APIResponse["entries"])))
  else:
    LogEntry("Entries does not exists in API Response. {} ".format(APIResponse))


  for strKey in dictIssueDet.keys():
    strAPIFunction = "companies/{CompanyURL}/issues/{IssueType}".format(
                      CompanyURL=strCompanyURL,IssueType=strKey)
    # strParams = urlparse.urlencode(dictParams)
    strURL = strBaseURL + strAPIFunction 

    LogEntry("Getting detail for {} via {}".format(dictIssueDet[strKey],strURL))
    objFileOut.write("\n## Details for {}\n\n".format(dictIssueDet[strKey]))
    APIResponse = MakeAPICall(strURL,strHeader,strMethod,dictPayload)
    if "entries" in APIResponse:
      if isinstance(APIResponse["entries"], list):
        lstKeys = APIResponse["entries"][0].keys()
        strKeys = TitleCase ("|".join(lstKeys))

        objFileOut.write("|"+strKeys+"|\n|")
        for strTemp in lstKeys:
          objFileOut.write("----|")
        objFileOut.write("\n")
        LogEntry(strKeys)
        iListCount = len(APIResponse["entries"])
        LogEntry("Entries is a list with {} entries ".format(iListCount))
        for dictIssue in APIResponse["entries"]:
          lstLine = []
          for strItem in dictIssue.keys():
            if isinstance(dictIssue[strItem], str):
              strTemp = dictIssue[strItem].replace(",",";")
              lstLine.append(strTemp)
            elif isinstance(dictIssue[strItem],int):
              lstLine.append(str(dictIssue[strItem]))
            else:
              lstLine.append(str(type(dictIssue[strItem])))
          strLine = "|".join(lstLine)
          objFileOut.write("|"+strLine +"|\n")
        objFileOut.write("\n\n")
      else:
        LogEntry("Entries is not a list, it is: {}".format(
            type(APIResponse["entries"])))
    else:
      LogEntry("Entries does not exists in API Response. {} ".format(APIResponse))

  objFileOut.close()

  # strCmdLine = "pandoc {} -f {} -t {} -o {}".format(
  #     strFileOut, strOrigionalFormat, strConvert2, strFileConv)
  # LogEntry ("executing {}".format(strCmdLine))
  # proc.Popen(strCmdLine)

  LogEntry("Done! Output savet to {}".format(strFileOut))
  objLogOut.close()



if __name__ == '__main__':
    main()
