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

lstHTMLElements = ["</a>", "</p>", "</ol>",
                   "</li>", "</ul>", "</span>", "</div>"]

def getInput(strPrompt):
  if sys.version_info[0] > 2 :
    return input(strPrompt)
  else:
    print ("please upgrade to python 3")
    sys.exit(5)

def IsHTML(strCheck):
  if strCheck is None:
    return False
  for strHTMLElement in lstHTMLElements:
    if strHTMLElement in strCheck:
      return True
  return False

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
iLoc = strFilein.find(".")
strOutPath = strFilein[:iLoc]
if strOutPath[-1:] != "/":
	strOutPath += "/"

if not os.path.exists(strOutPath):
  os.makedirs(strOutPath)
  print("\nPath '{0}' for the output files didn't exists, so I create it!\n".format(
      strOutPath))
else:
  print ("Path {} is OK".format(strOutPath))

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
        # print("Here are the keys in first item entry: {}".format(
        #     dictInput["rss"]["channel"]["item"][0].keys()))
        for dictItem in dictInput["rss"]["channel"]["item"]:
          strPostType = dictItem["wp:post_type"]
          strPostTitle = dictItem["title"]
          strContent = dictItem["content:encoded"]
          if strPostTitle is None:
            strPostTitle = "None"
          else:
            strPostTitle = strPostTitle.replace("?","")
            strPostTitle = strPostTitle.replace(".", "")
            strPostTitle = strPostTitle.replace("!", "")
          if strPostType == "post" or strPostType == "page":
            strItemPath = strOutPath + strPostType
            if strItemPath[-1:] != "/":
              strItemPath += "/"
            if not os.path.exists(strItemPath):
              os.makedirs(strItemPath)
              print("\nPath '{0}' for the output files didn't exists, so I create it!\n".format(
                  strItemPath))
            if IsHTML(strContent):
              strFileOut = strItemPath + strPostTitle + ".html"
              strContent = "<h1>{}</h1>\n<h2>{} by {}. Posted on {} GMT</h2>\n{}".format(
                  dictItem["title"], strPostType[0].upper()+strPostType[1:], dictItem["dc:creator"], 
                  dictItem["wp:post_date_gmt"], strContent)
            else:
              strFileOut = strItemPath + strPostTitle + ".txt"
              strContent = "{}\n{} by {}. Posted on {} GMT\n{}".format(
                  dictItem["title"], strPostType[0].upper()+strPostType[1:], dictItem["dc:creator"],
                  dictItem["wp:post_date_gmt"], strContent)
            objFileOut = open(strFileOut,"w",1)
            objFileOut.write(strContent)
            objFileOut.close()

          print("{} | {} | {} ".format(
              dictItem["title"], strPostType, dictItem["dc:creator"]))
      else:
        print("item is not a list, it is a {}".format(
            type(dictInput["rss"]["channel"]["item"])))
    else:
      print ("No Item list")
  else:
    print ("No channel item")
else:
  print ("No rss feed")
