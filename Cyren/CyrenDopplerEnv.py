'''
Script that reads in a text file of URLs and uses Cyren's API to lookup the URL classification 
to determine relative safety of the site

Author Siggi Bjarnason Copyright 2022

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

# End imports

#avoid insecure warning

requests.urllib3.disable_warnings()

tLastCall = 0
iTotalSleep = 0
iTotalCount = 0
iEntryID = 0
iRowNum = 1
iUpdateCount = 0

def CleanExit(strCause):
  global dbConn
  if strCause != "":
    LogEntry("{} is exiting abnormally on {}: {}".format (strScriptName,strScriptHost,strCause))

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

def MakeAPICall(strURL, strHeader, strMethod, dictPayload="", strUser="", strPWD=""):

  global tLastCall
  global iTotalSleep
  global iStatusCode

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

  LogEntry("Doing a {} to URL: {}".format(strMethod,strURL))
  try:
    if strMethod.lower() == "get":
      if strUser != "":
        LogEntry("I have none blank credentials so I'm doing basic auth")
        # WebRequest = requests.get(strURL, headers=dictHeader, auth=(strUser, strPWD))
        WebRequest = requests.get(
            strURL, timeout=iTimeOut, headers=strHeader, auth=(strUser, strPWD))
      else:
        LogEntry("credentials are blank, proceeding without auth")
        WebRequest = requests.get(strURL, headers=strHeader, verify=False)
      LogEntry("get executed")
    if strMethod.lower() == "post":
      if dictPayload != "":
        LogEntry("with payload of: {}".format(dictPayload))
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
  iStatusCode = int(WebRequest.status_code)
  # if WebRequest.status_code != 200:
  #   iErrCode = WebRequest.status_code
  #   iErrText = WebRequest.text

  if iErrCode != "" :
    return "There was a problem with your request. Error {}: {}".format(iErrCode,iErrText)
  else:
    try:
      return WebRequest.json()
    except Exception as err:
      LogEntry("Issue with converting response to json. "
        "Here are the first 99 character of the response: {}".format(WebRequest.text[:99]))

def ResponseParsing(APIResponse, dictCategories):
  strReturn = ""
  if "error" in APIResponse:
    return "Error {}. {}".format(iStatusCode,APIResponse["error"])
  if "urls" in APIResponse:
      if isinstance(APIResponse["urls"], list):
        for dictURLs in APIResponse["urls"]:
          iScore = 9999
          strType = "undetermined"
          strURL = dictURLs["url"]
          strCategory = strDelim2.join (dictURLs["categoryNames"])
          for strCatItem in dictURLs["categoryNames"]:
            if strCatItem in dictCategories:
              if isInt(dictCategories[strCatItem]["Score"]):
                iTemp = int(dictCategories[strCatItem]["Score"])
                if iTemp < iScore:
                  iScore = int(dictCategories[strCatItem]["Score"])
                  strType = dictCategories[strCatItem]["Type"]
          strReturn += "{0}{4}{1}{4}{2}{4}{3}\n".format(
              strURL, strCategory, strType, iScore, strDelim)
  if "url" in APIResponse:
    dictURLs = APIResponse
    iScore = 9999
    strType = "undetermined"

    strURL = dictURLs["url"]
    strCategory = strDelim2.join(dictURLs["categoryNames"])
    for strCatItem in dictURLs["categoryNames"]:
      if strCatItem in dictCategories:
        if isInt(dictCategories[strCatItem]["Score"]):
          iTemp = int(dictCategories[strCatItem]["Score"])
          if iTemp < iScore:
            iScore = dictCategories[strCatItem]["Score"]
            strType = dictCategories[strCatItem]["Type"]
    strReturn += "{0}{4}{1}{4}{2}{4}{3}\n".format(
        strURL, strCategory, strType, iScore, strDelim)

  return strReturn

def LoadCategories(strCategories):
  dictReturn = {}
  if os.path.exists(strCategories):
    try:
      objCategories = open(strCategories, "r")
    except PermissionError:
      LogEntry("unable to open input file {} for reading, "
                "permission denied.".format(strCategories), True)
    except FileNotFoundError:
      LogEntry("unable to open input file {} for reading, "
                "File not found".format(strCategories), True)
    lstCategories = objCategories.read().splitlines()
    objCategories.close()
  else:
    LogEntry("Provided path for categories file is not valid: {}".format(strCategories))
    return dictReturn
  
  for strLine in lstCategories:
    if strLine[:8] != "Category":
      lstLineParts = strLine.split(strDelim)
      if len(lstLineParts)>2:
        dictReturn[lstLineParts[0]] = {}
        dictReturn[lstLineParts[0]]["Type"] = lstLineParts[1]
        dictReturn[lstLineParts[0]]["Score"] = lstLineParts[2]

  return dictReturn

def main():
  global strFileOut
  global objFileOut
  global objLogOut
  global strScriptName
  global strScriptHost
  global strBaseDir
  global strBaseURL
  global iMinQuiet
  global iTimeOut
  global iMinScriptQuiet
  global iGMTOffset
  global iUpdateCount
  global strDelim
  global strDelim2

  #Define few Defaults
  iTimeOut = 120 # Max time in seconds to wait for network response
  iMinQuiet = 2 # Minimum time in seconds between API calls
  iMinScriptQuiet = 0 # Minimum time in minutes the script needs to be quiet before run again
  iBatchSize = 100 # Default API Batch size
  strDelim = "!"  # Default delim character for CSV file
  strDelim2 = ";"  # Default secondary delim character for CSV file for list within the list
  
  ISO = time.strftime("-%Y-%m-%d-%H-%M-%S")
  localtime = time.localtime(time.time())
  gmt_time = time.gmtime()
  iGMTOffset = (time.mktime(localtime) - time.mktime(gmt_time))/3600
  strFileOut = None

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

  if not os.path.exists (strLogDir) :
    os.makedirs(strLogDir)
    print("\nPath '{0}' for log files didn't exists, so I create it!\n".format(strLogDir))

  strScriptName = os.path.basename(sys.argv[0])
  iLoc = strScriptName.rfind(".")
  strLogFile = strLogDir + strScriptName[:iLoc] + ISO + ".log"
  strVersion = "{0}.{1}.{2}".format(sys.version_info[0],sys.version_info[1],sys.version_info[2])
  strScriptHost = platform.node().upper()

  print("This is a script to classify URLs using Cyren's API. "
    "This is running under Python Version {}".format(strVersion))
  print("Running from: {}".format(strRealPath))
  dtNow = time.asctime()
  print("The time now is {}".format(dtNow))
  print("Logs saved to {}".format(strLogFile))
  objLogOut = open(strLogFile,"w",1)
  objFileOut = None

  #fetching secrets in doppler
  if os.getenv("APIBASEURL") != "":
    strBaseURL = os.getenv("APIBASEURL")
  else:
    CleanExit("No Base API provided")

  if strBaseURL[-1:] != "/":
    strBaseURL += "/"

  if os.getenv("BATCHSIZE") != "":
    if isInt(os.getenv("BATCHSIZE")):
      iBatchSize = int(os.getenv("BATCHSIZE"))
    else:
      LogEntry("Invalid BatchSize, setting to defaults of {}".format(iBatchSize))

  if os.getenv("TIMEOUT") != "":
    if isInt(os.getenv("TIMEOUT")):
      iTimeOut = int(os.getenv("TIMEOUT"))
    else:
      LogEntry("Invalid timeout, setting to defaults of {}".format(iTimeOut))

  if os.getenv("MINQUIET") != "":
    if isInt(os.getenv("MINQUIET")):
      iMinQuiet = int(os.getenv("MINQUIET"))
    else:
      LogEntry("Invalid MinQuiet, setting to defaults of {}".format(iMinQuiet))

  strOutDir = os.getenv("OUTDIR")
  strInfile = os.getenv("INFILE")
  strOutfile = os.getenv("OUTFILE")
  strDelim = os.getenv("DELIM")
  strDelim2 = os.getenv("DELIM2")
  dictCategories = os.getenv("CATEGORIES")

  strHeader = {
      'Content-type': 'application/json',
      'Accept': 'application/json'
      }

  strOutDir = strOutDir.replace("\\", "/")
  if strOutDir[-1:] != "/":
    strOutDir += "/"

  if not os.path.exists(strOutDir):
    os.makedirs(strOutDir)
    print(
        "\nPath '{0}' for ouput files didn't exists, so I create it!\n".format(strOutDir))

  strFileOut = strOutDir + strOutfile
  LogEntry("Output will be written to {}".format(strFileOut))

  try:
    objFileOut = open(strFileOut, "w", encoding='utf8')
  except PermissionError:
    LogEntry("unable to open output file {} for writing, "
             "permission denied.".format(strFileOut), True)
  except FileNotFoundError:
    LogEntry("unable to open output file {} for writing, "
             "Issue with the path".format(strFileOut), True)

  strRawOut = strOutDir + "RawOut.json"
  LogEntry("Raw Output will be written to {}".format(strRawOut))

  try:
    objRawOut = open(strRawOut, "w", encoding='utf8')
  except PermissionError:
    LogEntry("unable to open raw output file {} for writing, "
             "permission denied.".format(strFileOut), True)
  except FileNotFoundError:
    LogEntry("unable to open raw output file {} for writing, "
             "Issue with the path".format(strFileOut), True)


  # actual work happens here

  if strInfile == "" :
    LogEntry("No infile specified, nothing to process, exiting!",True)
  
  if os.path.exists(strInfile):
    try:
      objFileIn = open(strInfile,"r")
    except PermissionError:
      LogEntry("unable to open input file {} for reading, "
              "permission denied.".format(strInfile), True)
    except FileNotFoundError:
      LogEntry("unable to open input file {} for reading, "
              "File not found".format(strInfile), True)
    lstURL = objFileIn.read().splitlines()
  else:
    LogEntry("file {} does not exists, need a valid file to continue".format(strInfile),True)

  dictBody = {}
  iIndex = 0
  strFileHead = "URL{0}Category{0}Type{0}Score\n".format(strDelim)
  objFileOut.write(strFileHead)
  while iIndex < len(lstURL):
    if len(lstURL) == 1:
      strAPIFunc = "api/v1/free/url"
      dictBody["url"] = lstURL[0]
    else:
      strAPIFunc = "api/v1/free/urls-list"
      dictBody["urls"] = lstURL[iIndex:iIndex + iBatchSize]
    strMethod = "post"
    strURL = strBaseURL + strAPIFunc
    APIResponse = MakeAPICall(strURL, strHeader, strMethod, dictBody)
    objRawOut.write(json.dumps(APIResponse))
    objFileOut.write (ResponseParsing(APIResponse,dictCategories))
    if "error" in APIResponse:
      LogEntry ("Error {}. {}".format(iStatusCode, APIResponse["error"]),True)
    if "exp" in APIResponse:
      LogEntry("Error {}. {}".format(iStatusCode, APIResponse["exp"]), True)
    if "message" in APIResponse:
      LogEntry("Error {}. {}".format(
          iStatusCode, APIResponse["message"]), True)

    if "url" not in APIResponse and "urls" not in APIResponse:
      LogEntry("Unexpected response format and couldn't parse it. Check raw file at {} for details.".format(
          strRawOut), True)

    iIndex += iBatchSize

  # Closing thing out

  if objFileOut is not None:
    objFileOut.close()
    print("objFileOut closed")
  else:
    print("objFileOut is not defined yet")

  LogEntry("Done! Output saved to {}".format(strFileOut))
  objLogOut.close()

if __name__ == '__main__':
    main()
