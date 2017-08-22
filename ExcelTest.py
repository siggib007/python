import tkinter as tk
from tkinter import filedialog
import win32com.client as win32 #pip install pypiwin32
import os
import subprocess as proc


root = tk.Tk()
root.withdraw()
TextEditor = "subl" #sublime
#TextEditor = "notepad"
print ("Using the file open dialog please find the file to use")
strWBin = filedialog.askopenfilename(title = "Select spreadsheet",filetypes = (("Excel files","*.xlsx"),("Text Files","*.txt"),("All Files","*.*")))
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
	wsNames = wbin.Worksheets("ACL Names")
	wsVars = wbin.Worksheets("OMW-Vars")
	wsACL = wbin.Worksheets("ACL Lines")
	print ("Column header for column B is {}.".format(wsVars.Cells(1,2).Value))
	print ("Putting some BS into cell D15 of ACL Name Tab")
	wsNames.Cells(15,4).Value = "Some BS"
