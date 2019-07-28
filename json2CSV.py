'''
Script to convert json file to CSV
Version: 3.6
Author Siggi Bjarnason Copyright 2019
Website http://www.ipcalc.us/ and http://www.icecomputing.com

'''
# Import libraries
import sys
import os
import time
import json

try:
	import tkinter as tk
	from tkinter import filedialog
	btKinterOK = True
except:
	print ("Failed to load tkinter, CLI only mode.")
	btKinterOK = False
# End imports

# Initialize stuff
strJSONfile = ""


#Start doing stuff
print ("This is a script to convert json file to a CSV file. This is running under Python Version {0}.{1}.{2}".format(
	sys.version_info[0],sys.version_info[1],sys.version_info[2]))
now = time.asctime()
print ("The time now is {}".format(now))

def getInput(strPrompt):
	if sys.version_info[0] > 2 :
		return input(strPrompt)
	else:
		return raw_input(strPrompt)
# end getInput

def ConvertJson2CSV(Itm2Bconverted):
	strLine = ""
	lstHeaders = []
	if isinstance(Itm2Bconverted,dict):
		for strKey in Itm2Bconverted.keys():
			if isinstance(Itm2Bconverted[strKey],(list)):
				print ("{} is a {} and has {} elements".format(strKey,type(Itm2Bconverted[strKey]),
					len(Itm2Bconverted[strKey])))
				# print ("second element of the list is a {}".format(type(Itm2Bconverted[strKey][1])))
				for outitem in Itm2Bconverted[strKey]:
					for InnerItem in outitem.keys():
						if InnerItem not in lstHeaders:
							lstHeaders.append(InnerItem)
				for strHeadKey in lstHeaders:
					strLine += strHeadKey + ","
				strLine = strLine[:-1]
				# print ("Header:\n{}".format(strLine))
				objFileOut.write ("\n{}\n{}\n".format(strKey,strLine))
				for dictItem in Itm2Bconverted[strKey]:
					strLine = ""
					for strHeadKey in lstHeaders:
						if strHeadKey in dictItem:
							if isinstance(dictItem[strHeadKey],dict):
								strLine += "dictionary with {} items,".format(len(dictItem[strHeadKey]))
							elif isinstance(dictItem[strHeadKey],list):
								strLine += "list with {} items,".format(len(dictItem[strHeadKey]))
							else:
								strLine += str(dictItem[strHeadKey]) +","
						else:
							strLine += ","
					strLine = strLine[:-1]
					# print (strLine)
					objFileOut.write(strLine + "\n")
			else:
				print ("{} is a {}".format(strKey,type(Itm2Bconverted[strKey])))
	elif isinstance(Itm2Bconverted,list):
		print ("item is a list and has {} elements".format(len(Itm2Bconverted)))
		for itm in Itm2Bconverted:
			print ("{} is a {}".format(itm,type(itm)))

def Analyze(dictInspect,strPrefix):
	if isinstance(dictInspect,dict):
		print ("{} is a dict".format(strPrefix))
		for strKey in dictInspect.keys():
			print ("analyzing key:{}".format(strKey))
			if isinstance(dictInspect[strKey],(dict,list)):
				print ("{}{} is a {} and has {} elements".format(strPrefix, strKey,type(dictInspect[strKey]),
					len(dictInspect[strKey])))
				Analyze(dictInspect[strKey],strPrefix+strKey+"/")
			else:
				print ("{}{} is a {}".format(strPrefix, strKey,type(dictInspect[strKey])))
	elif isinstance(dictInspect,list):
		print ("{} Element is a list and has {} elements".format(strPrefix, len(dictInspect)))
		if len(dictInspect) > 0:
			if isinstance(dictInspect[0],dict):
				print ("{} first instance in the list is a dictionary and has the following elements:".format(strPrefix))
				for strKey in dictInspect[0]:
					print ("{}{} is a {}".format(strPrefix, strKey,type(dictInspect[0][strKey])))
					if isinstance(dictInspect[0][strKey],(dict,list)):
						Analyze(dictInspect[0][strKey],strPrefix+strKey+"/")
			else:
				print ("{} first instance in the list is a {}".format(strPrefix, type(dictInspect[0])))
		else:
			print ("List has no elements, moving on.")
	else:
		print("{} dictInspect not a list or a dictionary".format(strPrefix))

sa = sys.argv

lsa = len(sys.argv)
if lsa > 1:
	strJSONfile = sa[1]

if strJSONfile == "":
	if btKinterOK:
		print ("File name to be imported is missing. Opening up a file open dialog box, please select the file you wish to import.")
		root = tk.Tk()
		root.withdraw()
		strJSONfile = filedialog.askopenfilename(title = "Select the json file",filetypes = (("json files","*.json"),("Text files","*.txt"),("all files","*.*")))
	else:
		strJSONfile = getInput("Please provide full path and filename for the json file to be imported: ")

if strJSONfile == "":
	print ("No filename provided unable to continue")
	sys.exit()

if os.path.isfile(strJSONfile):
	print ("OK found {}".format(strJSONfile))
else:
	print ("Can't find json file {}".format(strJSONfile))
	sys.exit(4)

iLoc = strJSONfile.rfind(".")
strOutFile = strJSONfile[:iLoc] + ".csv"

print ("writing output to {}".format(strOutFile))

objFileOut = open(strOutFile,"w")

with open(strJSONfile,"r") as objFilejson:
	dictFile = json.load(objFilejson)

print ("File loaded, result is a: {}".format(type(dictFile)))
if isinstance(dictFile,(list,dict)):
	# Analyze(dictFile,"/")
	ConvertJson2CSV(dictFile)
else:
	print("file did not load as a json dictionary or list, can't process")

print ("All Done :-D")
