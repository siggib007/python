import tkinter as tk
from tkinter import filedialog
import win32com.client as win32 #pip install pypiwin32
import win32gui, win32console, win32con, ctypes
import os
import subprocess as proc
import sys

xlSrcExternal = 0 #External data source
xlSrcModel = 4 #PowerPivot Model
xlSrcQuery = 3 #Query
xlSrcRange = 1 #Range
xlSrcXml = 2 #XML
xlGuess = 0 # Excel determines whether there is a header, and where it is, if there is one.
xlNo = 2 # Default. The entire range should be sorted.
xlYes = 1 # The entire range should not be sorted.

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
strWBin = strWBin.replace("/","\\")
print ("You selected: " + strWBin)
print ("File extention is:{}".format(strWBin[-4:]))
if strWBin[-4:] != "xlsx" :
	strCmdLine = "{0} \"{1}\"".format(TextEditor,strWBin)
	print ("Command line is:" + strCmdLine)
	#os.system(strCmdLine) #depreciated method
	proc.call(strCmdLine) #Blocking call
	#proc.Popen(strCmdLine) #Non blocking call
else:
	user32 = ctypes.WinDLL('user32', use_last_error=True)
	user32.LockSetForegroundWindow(1)
	app = win32.gencache.EnsureDispatch('Excel.Application')
	win32gui.SetWindowPos(win32console.GetConsoleWindow(), win32con.HWND_TOP, 0, 0, 0, 0, win32con.SWP_NOSIZE | win32con.SWP_NOMOVE)
	app.Visible = True
	wbin = app.Workbooks.Open (strWBin,0,True)
	iSheetCount = wbin.Worksheets.Count
	wbin.Sheets.Add()
	wsTest = wbin.ActiveSheet
	wsTest.Name = "Testing"
	# print ("clearing all cells")
	# wsTest.Range(Cells.Address).Clear()
	print ("Putting some BS into cell D15 of new testing sheet")
	wsTest.Cells(15,4).Value = "Some BS"
	wsTest.ListObjects.Add(xlSrcRange, wsTest.Range(wsTest.Cells(1,1),wsTest.Cells(25,6)),"",xlYes,"","TableStyleLight1").Name = "Siggib"

	print ("That workbook has {0} sheets".format(iSheetCount))
	for i in range(1,iSheetCount+1):
		strTemp = wbin.Worksheets(i).Name
		print ("Sheet #{0} is called {1}".format(i,strTemp))
		dictSheets[strTemp]=i
	# end for loop
	if "Unsecured Debt" in dictSheets:
		print ("Found Unsecured Debt, erasing it")
		wsDebt = wbin.Worksheets("Unsecured Debt")
		wsDebt.Cells.Clear()
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

	# wbin.SaveAs("c:\\temp\\exceltest.xlsx")
