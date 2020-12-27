'''
Qualys API Sample Script
Author Siggi Bjarnason Copyright 2017
Website http://www.ipcalc.us/ and http://www.icecomputing.com

Description:
This is script you can put in your specific Qualys API details and the script will save the raw response to a text as well as process it into a dict and write that to a file.

Following packages need to be installed as administrator
pip install xmltodict

'''
# Import libraries
import sys
import os
import string
import time
import xmltodict
import urllib.parse as urlparse
import subprocess as proc
import xml.parsers.expat
import platform
try:
  import tkinter as tk
  from tkinter import filedialog
  btKinterOK = True
except:
  print ("Failed to load tkinter, CLI only mode.")
  btKinterOK = False

# End imports

def getInput(strPrompt):
  if sys.version_info[0] > 2 :
    return input(strPrompt)
  else:
    print ("please upgrade to python 3")
    sys.exit(5)

strFilein = ""
sa = sys.argv
lsa = len(sys.argv)
if lsa > 1:
  strFilein = sa[1]

if strFilein == "":
  if btKinterOK:
    print ("File name to be processed is missing. Opening up a file open dialog box, please select the file you wish to process.")
    root = tk.Tk()
    root.withdraw()
    strFilein = filedialog.askopenfilename (title = "Select the WP Export file",filetypes = (("XML files","*.xml"),("all files","*.*")))
  else:
    strFilein = getInput("Please provide full path and filename for the WP Export file to be processed: ")

if strFilein == "":
  print ("No filename provided unable to continue")
  sys.exit(9)

if os.path.isfile(strFilein):
  print ("OK found {}".format(strFilein))
else:
  print ("Can't find WP export file {}".format(strFilein))
  sys.exit(4)


iLoc = strFilein.rfind(".")
strFileExt = strFilein[iLoc+1:]
strOutFile = strFilein[:iLoc] + "-fixed" + strFilein[iLoc:]

if strFileExt.lower() == "xml":
  objFileIn = open(strFilein, "r", encoding='utf-8')
else:
  print ("only able to process XML files. Unable to process {} files".format(strFileExt))
  sys.exit(5)


strXML = objFileIn.read()
try:
    dictInput = xmltodict.parse(strXML)
except xml.parsers.expat.ExpatError as err:
    print ("Expat Error: {}\n{}".format(err,strXML))
    iErrCode = "Expat Error"
    iErrText = "Expat Error: {}\n{}".format(err,strXML)

print ("File read in, here are top level keys {}".format(dictInput.keys()))
if "rss" in dictInput:
  if "channel" in dictInput["rss"]:
    if "item" in dictInput["rss"]["channel"]:
      if isinstance (dictInput["rss"]["channel"]["item"],list):
        for dictItem in dictInput["rss"]["channel"]["item"]:
          print ("{} | {} | {} ".format(dictItem["title"],dictItem["post_type"],dictItem["created"]))
      else:
        print("item is not a list, it is a {}".format(
            type(dictInput["rss"]["channel"]["item"])))
    else:
      print ("No Item list")
  else:
    print ("No channel item")
else:
  print ("No rss feed")
