import tkinter as tk
from tkinter import filedialog
import win32com.client as win32 #pip install pypiwin32
import os
import subprocess as proc
import sys


root = tk.Tk()
root.withdraw()
dictSheets={}
TextEditor = "subl" #sublime
#TextEditor = "notepad"
print ("Using the file open dialog please find the file to use")
strWBin = filedialog.askopenfilename(title = "Select spreadsheet",filetypes = (("Excel files","*.xlsx"),("Text Files","*.txt"),("All Files","*.*")))
if strWBin =="":
	print ("no file selected, exiting")
	sys.exit(2)
#end if no file
print ("You selected: " + strWBin)
print ("File extention is:{}".format(strWBin[-4:]))
if strWBin[-4:] != "xlsx" :
	strCmdLine = "{0} \"{1}\"".format(TextEditor,strWBin)
	print ("Command line is:" + strCmdLine)
	#os.system(strCmdLine) #depreciated method
	proc.call(strCmdLine) #Blocking call
	#proc.Popen(strCmdLine) #Non blocking call
else:
	app = win32.gencache.EnsureDispatch('Excel.Application')
	app.Visible = True
	wbin = app.Workbooks.Open (strWBin,0,True)
	iSheetCount = wbin.Worksheets.Count
	wbin.Sheets.Add()
	wbin.Worksheets(1).Name = "Testing"
	wsTest = wbin.Worksheets("Testing")
	print ("Putting some BS into cell D15 of new testing sheet")
	wsTest.Cells(15,4).Value = "Some BS"
	print ("That workbook has {0} sheets".format(iSheetCount))
	for i in range(1,iSheetCount+1):
		strTemp = wbin.Worksheets(i).Name
		print ("Sheet #{0} is called {1}".format(i,strTemp))
		dictSheets[strTemp]=i
	# end for loop
	if "ACL Names" in dictSheets:
		print ("ACL Names is good!")
		wsNames = wbin.Worksheets("ACL Names")
	if "OMW-Vars" in dictSheets:
		print ("OMW-Vars is good!")
		wsVars = wbin.Worksheets("OMW-Vars")
		print ("Column header for column B in sheet OMW-Vars is {}.".format(wsVars.Cells(1,2).Value))
	if "ACL Names" in dictSheets:
		print ("ACL Lines is good!")
		wsACL = wbin.Worksheets("ACL Lines")

	wbin.SaveAs("c:\\temp\\exceltest.xlsx")
