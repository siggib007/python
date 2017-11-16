#pip install pymysql
import pymysql
import sys
import os
import time
import tkinter as tk
from tkinter import filedialog, messagebox

def SQLConn (strServer,strUser,strPWD,strInitialDB):
	try:
		# Open database connection
		return pymysql.connect(strServer,strUser,strPWD,strInitialDB)
	except pymysql.err.InternalError as err:
		print ("Error: unable to connect: {}".format(err))
		sys.exit(5)
	except pymysql.err.OperationalError as err:
		print ("Operational Error: unable to connect: {}".format(err))
		sys.exit(5)
	except pymysql.err.ProgrammingError as err:
		print ("Programing Error: unable to connect: {}".format(err))
		sys.exit(5)

def SQLQuery (strSQL,db):
	try:
		# prepare a cursor object using cursor() method
		dbCursor = db.cursor()
		# Execute the SQL command
		dbCursor.execute(strSQL)
		# Count rows
		iRowCount = dbCursor.rowcount
		if strSQL[:6].lower() == "select":
			dbResults = dbCursor.fetchall()
		else:
			db.commit()
			dbResults = ()
		return [iRowCount,dbResults]
	except pymysql.err.InternalError as err:
		if strSQL[:6].lower() != "select":
			db.rollback()
		return "Internal Error: unable to execute: {}".format(err)
	except pymysql.err.ProgrammingError as err:
		if strSQL[:6].lower() != "select":
			db.rollback()
		return "Programing Error: unable to execute: {}".format(err)
	except pymysql.err.OperationalError as err:
		if strSQL[:6].lower() != "select":
			db.rollback()
		return "Programing Error: unable to execute: {}".format(err)
	except pymysql.err.IntegrityError as err:
		if strSQL[:6].lower() != "select":
			db.rollback()
		return "Integrity Error: unable to execute: {}".format(err)

def ValidReturn(lsttest):
	if isinstance(lsttest,list):
		if len(lsttest) == 2:
			if isinstance(lsttest[0],int) and isinstance(lsttest[1],tuple):
				return True
			else:
				return False
		else:
			return False
	else:
		return False

def isInt (CheckValue):
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

if os.path.isfile("Routes.txt"):
	print ("Configuration File exists")
else:
	print ("Can't find configuration file Routes.txt, make sure it is the same directory as this script")
	sys.exit(4)

print ("Reading in configuration")
objINIFile = open("Routes.txt","r")
strLines = objINIFile.readlines()
objINIFile.close()

for strLine in strLines:
	strLine = strLine.strip()
	if "=" in strLine:
		strConfParts = strLine.split("=")
		if strConfParts[0] == "Server":
			strServer = strConfParts[1]
		if strConfParts[0] == "Database":
			strInitialDB = strConfParts[1]
		if strConfParts[0] == "dbUser":
			strDBUser = strConfParts[1]
		if strConfParts[0] == "dbPWD":
			strDBPWD = strConfParts[1]

print ("This is an update script. This is running under Python Version {0}.{1}.{2}".format(sys.version_info[0],sys.version_info[1],sys.version_info[2]))
now = time.asctime()
print ("The time now is {}".format(now))
print ("This script will read in a CSV file and query the router audit database to see if any are missing and insert as nessisary,\n")
input ("Press enter to bring up a file open dialog so you may choose the source csv file")

root = tk.Tk()
root.withdraw()
strCSVin = filedialog.askopenfilename(title = "Select CSV file from HPNA",filetypes = (("CSV files","*.csv"),("Text Files","*.txt"),("All Files","*.*")))
if strCSVin =="":
	print ("You cancelled so I'm exiting")
	sys.exit(2)
#end if no file
strCSVin = strCSVin.replace("/","\\")
print ("You selected: " + strCSVin)
print ("File extention is:{}!".format(strCSVin[-3:]))
if strCSVin[-3:].lower() != "csv" :
	print ("I was expecting a text input file with csv extension. Don't know what do to except exit")
	sys.exit(2)
#end if xlsx

if os.path.isfile(strCSVin):
	objINIFile = open(strCSVin,"r")
	strLines = objINIFile.readlines()
	objINIFile.close()
else:
	print ("Can't find the file you just select, not sure what happened, exiting!")
	sys.exit(8)

print ("That file has {} lines.".format(len(strLines)))
print ("and contains {} comma seperated values".format(strLines[0].count(",")+1))
if strLines[0].count(",") < 3 :
	print ("insufficient number of comma seperated values, need at least 4")
	sys.exit(1)
if len(strLines) > 5:
	print ("Here is a preview of that file:")
	print (strLines[0].strip())
	print (strLines[1].strip())
	print (strLines[2].strip())
	print (strLines[3].strip())
	print (strLines[4].strip())
	strInput = input ("\n ...Press enter to continue, anything to abort:")
	if strInput != "":
		print ("Got it, exiting.")
		sys.exit(0)
else:
	print ("File seems way to short, it should be more than five lines as there are couple of hundred applicable routers in the network.")
	sys.exit(4)

dbConn = SQLConn (strServer,strDBUser,strDBPWD,strInitialDB)

for strLine in strLines:
	strLine = strLine.strip()
	strLineParts = strLine.split(",")
	if strLineParts[0] != "Host Name":
		# print ("router:{}, site:{}".format(strLineParts[0],strLineParts[0][3:6]))
		strSQL = ("SELECT iRouterID,vcHostName FROM networks.tblrouterlist"
			" where vcHostName = '{}';".format(strLineParts[0]))
		lstRouters = SQLQuery (strSQL,dbConn)
		if not ValidReturn(lstRouters):
			print ("Unexpected: {}".format(lstRouters))
			sys.exit(8)
		elif lstRouters[0] == 1:
			print ("{} already in database".format(strLineParts[0]))
		# else:
		# 	print ("Fetched {} rows".format(lstRouters[0]))

		if lstRouters[0] == 0 and len(strLineParts) > 3 :
			strSQL = ("INSERT INTO networks.tblrouterlist (vcHostName,vcDeviceIP,vcDeviceVendor,vcDeviceModel,vcSiteCode)"
						"VALUES ('{0}','{1}','{2}','{3}','{4}');".format(strLineParts[0],strLineParts[1],strLineParts[2],strLineParts[3],strLineParts[0][3:6]))
			lstReturn = SQLQuery (strSQL,dbConn)
			if not ValidReturn(lstReturn):
				print ("Unexpected: {}".format(lstReturn))
				bAbort = True
				break
			elif lstReturn[0] != 1:
				print ("Records affected {}, expected 1 record affected".format(lstReturn[0]))
			else:
				print ("Inserted {}".format(strLineParts[0]))