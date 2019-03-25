'''
Script to show structure of json files
Version: 3.6
Author Siggi Bjarnason Copyright 2019
Website http://www.ipcalc.us/ and http://www.icecomputing.com

'''
# Import libraries
import sys
import os
import string
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
print ("This is a script to show structure of json files. This is running under Python Version {0}.{1}.{2}".format(
	sys.version_info[0],sys.version_info[1],sys.version_info[2]))
now = time.asctime()
print ("The time now is {}".format(now))

def getInput(strPrompt):
    if sys.version_info[0] > 2 :
        return input(strPrompt)
    else:
        return raw_input(strPrompt)
# end getInput

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

with open(strJSONfile,"r") as objFilejson:
	dictFile = json.load(objFilejson)

print ("File loaded, result is a: {}".format(type(dictFile)))
if isinstance(dictFile,(list,dict)):
	for strKey in dictFile.keys():
		print ("key {} is a {} and has {} elements".format(strKey,type(dictFile[strKey]),len(dictFile[strKey])))
		if isinstance(dictFile[strKey],list):
			print ("Element {} is a list, first instance in the list has the following elements:".format(strKey))
			# print ("Element, type")
			for strElement in dictFile[strKey][0].keys():
				print ("{}, {}".format(strElement,type(dictFile[strKey][0][strElement])))
else:
	print("file did not load as a json dictionary or list, can't process")