#pip install pymysql
import pymysql
import sys
import os
import tkinter as tk
from tkinter import filedialog

root = tk.Tk()
root.withdraw()

strSQLFile = filedialog.askopenfilename(title = "Select Query file",filetypes = (("Query files","*.sql"),("Text files","*.txt"),("all files","*.*")))
objFileIn  = open(strSQLFile,"r")
strSQL = objFileIn.read()
objFileIn.close()

strConf_File = "MySQLTest.ini"

if os.path.isfile(strConf_File):
	print ("Configuration File exists")
else:
	print ("Can't find configuration file {}, make sure it is the same directory as this script".format(strConf_File))
	sys.exit(4)


strLine = "  "
print ("Reading in configuration")
objINIFile = open(strConf_File,"r")
strLines = objINIFile.readlines()
objINIFile.close()

for strLine in strLines:
	strLine = strLine.strip()
	if "=" in strLine:
		strConfParts = strLine.split("=")
		if strConfParts[0] == "Server":
			strServer = strConfParts[1]
		if strConfParts[0] == "dbUser":
			strDBUser = strConfParts[1]
		if strConfParts[0] == "dbPWD":
			strDBPWD = strConfParts[1]
		if strConfParts[0] == "Database":
			strInitialDB = strConfParts[1]

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


print ("Executing: {}".format(strSQL))
db = SQLConn (strServer,strDBUser,strDBPWD,strInitialDB)
lstReturn = SQLQuery (strSQL,db)
if ValidReturn(lstReturn):
	print ("Rows affected: {}".format(lstReturn[0]))
	for row in lstReturn[1] :
		# print ("Row is of type {}".format(type(row)))
		print (" ".join(map(str,row)))
else:
	print ("Unexpected: {}".format(lstReturn))

# disconnect from server
db.close()