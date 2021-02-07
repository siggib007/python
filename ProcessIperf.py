'''
iPerf processing Script.
Author Siggi Bjarnason Copyright 2021
Website https://supergeek.us

Description:
Reads in json generated by iperf and converts to csv for analysis and charting

'''
# Import libraries
import sys
import os
import string
import time
import platform
import json
try:
  import tkinter as tk
  from tkinter import filedialog
  btKinterOK = True
except:
  print ("Failed to load tkinter, CLI only mode.")
  btKinterOK = False

# End imports

def CSVClean(strText, iLimit=350):
  if strText is None:
    return ""
  else:
    strTemp = str(strText)
    strTemp = strTemp.encode("ascii", "ignore")
    strTemp = strTemp.decode("ascii", "ignore")
    strTemp = strTemp.replace(",", "")
    strTemp = strTemp.replace("\n", " ")
    strTemp = strTemp.replace("\r", " ")
    return strTemp[:iLimit]

def getInput(strPrompt):
  if sys.version_info[0] > 2:
    return input(strPrompt)
  else:
    print("please upgrade to python 3")
    sys.exit(5)

def CleanExit(strCause):
  try:
    objLogOut.close()
    objFileOut.close()
    objFileIn.close()
  except:
    pass
  sys.exit(9)

def LogEntry(strMsg, bAbort=False):
  strTimeStamp = time.strftime("%m-%d-%Y %H:%M:%S")
  objLogOut.write("{0} : {1}\n".format(strTimeStamp, strMsg))
  print(strMsg)
  if bAbort:
    CleanExit("")

def main():
  global objLogOut
  global objFileOut
  global objFileIn

  ISO = time.strftime("-%Y-%m-%d-%H-%M-%S")

  strBaseDir = os.path.dirname(sys.argv[0])
  strBaseDir = strBaseDir.replace("\\", "/")
  strRealPath = os.path.realpath(sys.argv[0])
  strRealPath = strRealPath.replace("\\", "/")
  if strBaseDir == "":
    iLoc = strRealPath.rfind("/")
    strBaseDir = strRealPath[:iLoc]
  if strBaseDir[-1:] != "/":
    strBaseDir += "/"
  strLogDir = strBaseDir + "Logs/"
  if strLogDir[-1:] != "/":
    strLogDir += "/"

  iLoc = sys.argv[0].rfind(".")

  if not os.path.exists(strLogDir):
    os.makedirs(strLogDir)
    print(
        "\nPath '{0}' for log files didn't exists, so I create it!\n".format(strLogDir))

  strScriptName = os.path.basename(sys.argv[0])
  iLoc = strScriptName.rfind(".")
  strLogFile = strLogDir + strScriptName[:iLoc] + ISO + ".log"
  objLogOut = open(strLogFile, "w", 1)

  strVersion = "{0}.{1}.{2}".format(
      sys.version_info[0], sys.version_info[1], sys.version_info[2])

  LogEntry ("This is a script process json file from iperf and generate a csv file "
          " that is easier to analyze and chart. "
          "This is running under Python Version {}".format(strVersion))
  LogEntry ("Running from: {}".format(strRealPath))
  dtNow = time.asctime()
  LogEntry ("The time now is {}".format(dtNow))
  LogEntry ("Logs saved to {}".format(strLogFile))

  strFilein = "C:/Users/siggi/OneDrive/iperf/iperf.json"
  sa = sys.argv
  lsa = len(sys.argv)
  if lsa > 1:
    strFilein = sa[1]

  if strFilein == "":
    if btKinterOK:
      LogEntry ("File name to be processed is missing. Opening up a file open dialog box, "
              " please select the file you wish to process.")
      root = tk.Tk()
      root.withdraw()
      strFilein = filedialog.askopenfilename(title="Select the iperf json file", filetypes=(
          ("json files", "*.json"), ("all files", "*.*")))
    else:
      strFilein = getInput(
          "Please provide full path and filename for the WP Export file to be processed: ")

  if strFilein == "":
    LogEntry ("No filename provided unable to continue",True)

  if os.path.isfile(strFilein):
    LogEntry ("OK found {}".format(strFilein))
  else:
    LogEntry ("Can't find iperf json file {}".format(strFilein),True)

  iLoc = strFilein.rfind(".")
  strFileExt = strFilein[iLoc+1:]
  iLoc = strFilein.find(".")
  strOutFile = strFilein[:iLoc] + ".csv"

  LogEntry ("CSV results will be written to {}".format(strOutFile))
  try:
    objFileOut = open(strOutFile, "w")
  except PermissionError:
    LogEntry("unable to open output file {} for writing, "
             "permission denied.".format(strOutFile),True)
  except Exception as err:
    LogEntry("Unexpected error while attempting to open {} for writing. Error Details: {}".format(
        strOutFile, err), True)
  LogEntry("Output file {} created".format(strOutFile))
  objFileOut.write(
      "Sys Info,Version,Remote Host,Remote Port,Text Time Stamp,Excel Time Stamp,"
      "Host CPU,Remote CPU,Sent Mbps,Rcvd Mbps\n")

  if strFileExt.lower() == "json":
    try:
      objFileIn = open(strFilein, "r")
    except Exception as err:
      LogEntry("Unexpected error while opening input file {}. Error details {}".format(strFilein,err))
  else:
    LogEntry(
        "only able to process json files. Unable to process {} files".format(strFileExt),True)

  LogEntry ("Input file {} opened and ready for reading.".format(strFilein))
  strJson = objFileIn.read()
  strJson = "[" + strJson + "]"
  strJson = strJson.replace("}\n{", "},\n{")

  lstInput = []
  strRemoteHost = ""
  strTimeStamp = ""
  iExcelTime = 0
  strSysInfo = ""
  strRemotePort = ""
  iSumSentbps = ""
  iSumRcvdbps = ""
  iHostCPU = ""
  iRemoteCPU = ""

  try:
      lstInput = json.loads(strJson)
  except Exception as err:
      LogEntry("json Error: {}\n".format(err),True)

  LogEntry ("top level is {} with {} entries.".format(type(lstInput),len(lstInput)))
  iInstance = 0
  for dictPerf in lstInput:
    if "error" in dictPerf:
      LogEntry ("Entry {}: {}".format (iInstance, dictPerf["error"]))
      objFileOut.write("{}\n".format(dictPerf["error"]))
    else:
      if "start" in dictPerf:
        if "version" in dictPerf["start"]:
          strVersion = CSVClean (dictPerf["start"]["version"])
        else:
          strVersion = "unknown version"
        if "system_info" in dictPerf["start"]:
          strSysInfo = CSVClean (dictPerf["start"]["system_info"],30)
        else:
          strSysInfo = "no system info"
        if "connecting_to" in dictPerf["start"]:
          if "host" in dictPerf["start"]["connecting_to"]:
            strRemoteHost = CSVClean (dictPerf["start"]["connecting_to"]["host"])
          else:
            strRemoteHost = "unknown remote host"
          if "port" in dictPerf["start"]["connecting_to"]:
            strRemotePort = CSVClean (dictPerf["start"]["connecting_to"]["port"])
          else:
            strRemotePort = "unknown remote port"
        else:
          strRemoteHost = "no connecting to branch"
          strRemotePort = "no connecting to branch"
        if "timestamp" in dictPerf["start"]:
          if "time" in dictPerf["start"]["timestamp"]:
            strTimeStamp = CSVClean (dictPerf["start"]["timestamp"]["time"])
          else:
            strTimeStamp = "no time in timestamp"
          if "timesecs" in dictPerf["start"]["timestamp"]:
            iExcelTime = int(dictPerf["start"]["timestamp"]["timesecs"])
            iExcelTime = iExcelTime/86400+25569
          else:
            iExcelTime = "no time in timestamp"
        else:
          strTimeStamp = "no timestamp branch"
      if "end" in dictPerf:
        if "sum_sent" in dictPerf["end"]:
          if "bits_per_second" in dictPerf["end"]["sum_sent"]:
            iSumSentbps = dictPerf["end"]["sum_sent"]["bits_per_second"]
          else:
            iSumSentbps = -5
        else:
          iSumSentbps = -6
        if "sum_received" in dictPerf["end"]:
          if "bits_per_second" in dictPerf["end"]["sum_received"]:
            iSumRcvdbps = dictPerf["end"]["sum_received"]["bits_per_second"]
          else:
            iSumRcvdbps = -5
        else:
          iSumRcvdbps = -6

        if "cpu_utilization_percent" in dictPerf["end"]:
          if "host_total" in dictPerf["end"]["cpu_utilization_percent"]:
            iHostCPU = dictPerf["end"]["cpu_utilization_percent"]["host_total"]
          else:
            iHostCPU = -5
        else:
          iHostCPU = -6
        if "cpu_utilization_percent" in dictPerf["end"]:
          if "remote_total" in dictPerf["end"]["cpu_utilization_percent"]:
            iRemoteCPU = dictPerf["end"]["cpu_utilization_percent"]["remote_total"]
          else:
            iRemoteCPU = -5
        else:
          iRemoteCPU = -6

      LogEntry("processed entry to {} on {}".format(
          strRemoteHost, strTimeStamp))
      objFileOut.write("{},{},{},{},{},{},{},{},{},{}\n".format(
          strSysInfo, strVersion, strRemoteHost, strRemotePort, strTimeStamp,
          iExcelTime, iHostCPU,iRemoteCPU,iSumSentbps/1e6,iSumRcvdbps/1e6))

    iInstance += 1
  LogEntry("Done")
  objFileIn.close()
  objFileOut.close()
  objLogOut.close()

if __name__ == '__main__':
  main()
