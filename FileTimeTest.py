import sys
import os
import getpass
import time
#import magic
import tkinter as tk
from tkinter import filedialog

root = tk.Tk()
root.withdraw()

print ("Welcome to my Python Test script. Your username is {3}. This is running under Python Version {0}.{1}.{2}".format(sys.version_info[0],sys.version_info[1],sys.version_info[2],getpass.getuser()))
localtime = time.localtime(time.time())
print ("Local current time :{}".format(localtime))
now = time.asctime()
print ("The time now is {}".format(now))
LongDate = time.strftime("%A %B %d, %Y")
print ("Longformat {}".format(LongDate))
ISO = time.strftime("%Y-%m-%d %H:%M:%S : ")
print ("ISO {}".format(ISO))

print ("Using the file open dialog please find the file to use")
strFilein = filedialog.askopenfilename(title = "Select file",filetypes = (("Text Files","*.txt"),("All Files","*.*")))
iLoc = strFilein.rfind(".")
iNegLoc = iLoc * -1
print ("You selected: ", strFilein)
print ("Name {0} and ext {1}".format(strFilein[:iLoc],strFilein[iLoc:]))
statinfo = os.stat(strFilein)
print ("Stat Info: {}".format(statinfo))
print ("Last Accessed: {}".format(time.asctime(time.localtime(statinfo.st_atime))))
print ("Last Modified: {}".format(time.asctime(time.localtime(statinfo.st_mtime))))
print ("Created: {}".format(time.asctime(time.localtime(statinfo.st_ctime))))
#print ("File details: {}".format(magic.form_file(strFilein)))
#sys.exit(0)
objFileIn  = open(strFilein,"r")
objFileOut = open(strFilein[:iLoc]+"-TS"+strFilein[iLoc:],"w")
strLine = objFileIn.readline()
objFileOut.write (ISO + strLine)
while strLine:
	ISO = time.strftime("%Y-%m-%d %H:%M:%S : ")
	strLine = objFileIn.readline()
	objFileOut.write (ISO + strLine)
#end while

objFileIn.close()
objFileOut.close()
now = time.asctime()
print ("Done at {} !!!".format(now))