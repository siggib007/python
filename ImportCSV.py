'''
Script to import CSV files
Author Siggi Bjarnason Copyright 2017
Website http://www.ipcalc.us/ and http://www.icecomputing.com

Following packages need to be installed as administrator
pip install requests
pip install xmltodict
pip install pymysql

'''
# Import libraries
import sys
import requests
import os
import string
import time
import pymysql
# End imports


strConf_File = "QSAppliance.ini"

strInitialDB = "Qualys_Portal"
strTableName = "tblservicenow"
bTruncateTable = True   # Truncate the table prior to insert
bConvertBool = True     # Convert strings true/false into 1 and 0 for insert into database boolean field.
strDelim = ","          # what is the field seperate in the input file
iStatusFreq = 1000      # How frequently to print out how many rows have been imported


sa = sys.argv

lsa = len(sys.argv)
if lsa > 1:
	strCSVName = sa[1]
else:
	strCSVName = input("Please provide full path and filename for the CSV file to be imported: ")

if strCSVName =="":
	print ("No filename provided unable to continue")
	sys.exit()

if os.path.isfile(strCSVName):
	print ("OK found {}".format(strCSVName))
else:
	print ("Can't find CSV file {}".format(strCSVName))
	sys.exit(4)

print ("This is a script to import csv files. This is running under Python Version {0}.{1}.{2}".format(sys.version_info[0],sys.version_info[1],sys.version_info[2]))
now = time.asctime()
print ("The time now is {}".format(now))

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
		if strConfParts[0] == "APIBaseURL":
			strBaseURL = strConfParts[1]
		if strConfParts[0] == "APIRequestHeader":
			strHeadReq = strConfParts[1]
		if strConfParts[0] == "QUserID":
			strUserName = strConfParts[1]
		if strConfParts[0] == "QUserPWD":
			strPWD = strConfParts[1]
		if strConfParts[0] == "Server":
			strServer = strConfParts[1]
		if strConfParts[0] == "dbUser":
			strDBUser = strConfParts[1]
		if strConfParts[0] == "dbPWD":
			strDBPWD = strConfParts[1]

def SQLConn (strServer,strDBUser,strDBPWD,strInitialDB):
	try:
		# Open database connection
		return pymysql.connect(strServer,strDBUser,strDBPWD,strInitialDB)
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
		if strSQL[:6].lower() == "select" or strSQL[:4].lower() == "call" or strSQL[:4].lower() == "show" or strSQL[:8].lower() == "describe":
			dbResults = dbCursor.fetchall()
		else:
			db.commit()
			dbResults = ()
		return [iRowCount,dbResults]
	except pymysql.err.InternalError as err:
		if strSQL[:6].lower() != "select":
			db.rollback()
		return "Internal Error: unable to execute: {}\n{}".format(err,strSQL)
	except pymysql.err.ProgrammingError as err:
		if strSQL[:6].lower() != "select":
			db.rollback()
		return "Programing Error: unable to execute: {}\n{}".format(err,strSQL)
	except pymysql.err.OperationalError as err:
		if strSQL[:6].lower() != "select":
			db.rollback()
		return "Programing Error: unable to execute: {}\n{}".format(err,strSQL)
	except pymysql.err.IntegrityError as err:
		if strSQL[:6].lower() != "select":
			db.rollback()
		return "Integrity Error: unable to execute: {}\n{}".format(err,strSQL)
	except Exception as err:
		if strSQL[:6].lower() != "select":
			db.rollback()
		return "unknown Error: unable to execute: {}\n{}".format(err,strSQL)

def DBConvertEUdt (strDate):
	return time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(time.mktime(time.strptime(strDate,"%d-%m-%Y %H:%M:%S"))))

def DBConvertUSdt (strDate):
	return time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(time.mktime(time.strptime(strDate,"%m/%d/%Y %H:%M:%S"))))

def DBClean(strText):
	if strText.strip() == "":
		return "NULL"
	else:
		strTemp = strText.encode("ascii","ignore")
		strTemp = strTemp.decode("ascii","ignore")
		strTemp = strTemp.replace("\\","\\\\")
		strTemp = strTemp.replace("'","\\'")
		if strTemp.count(":") == 2 and strTemp.count("-") == 2 and strTemp.count(" ") == 1:
			strTemp = DBConvertEUdt(strTemp)
		if bConvertBool:
			if strTemp.lower() == "false":
				strTemp = "0"
			if strTemp.lower() == "true":
				strTemp = "1"
		return "'" + strTemp + "'"

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

x=0
lstFields = []
dbConn = SQLConn (strServer,strDBUser,strDBPWD,strInitialDB)
objFileIn  = open(strCSVName,"r")
strLine = objFileIn.readline()
strLine = strLine.replace("\"","")
strLine = strLine.replace("\\","\\\\")
strLine = strLine.replace("'","\\'")
strLineParts = strLine[:-1].split(strDelim)
print ("CSV Headers: {}".format(strLine))
strSQL = "show columns from {};".format(strTableName)
lstReturn = SQLQuery (strSQL,dbConn)
if not ValidReturn(lstReturn):
	print ("Unexpected: {}".format(lstReturn))
	sys.exit(9)
else:
	if lstReturn[0] > 0:
		print ("CSV Header: <> Database Field")
		for FieldName in lstReturn[1]:
			print ("{} <> {}".format(strLineParts[x],FieldName[0]))
			x += 1
			lstFields.append(FieldName[0])

if len(lstFields)>0:
	iFieldCount = len(lstFields)
	if bTruncateTable:
		strSQL = "delete from {};".format(strTableName)
		lstReturn = SQLQuery (strSQL,dbConn)
		if not ValidReturn(lstReturn):
			print ("Unexpected: {}".format(lstReturn))
			sys.exit(9)
		else:
			print ("Deleted {} old records".format(lstReturn[0]))
else:
	print ("{} has no fields, aborting.".format(strTableName))
	sys.exit()

iLineNum = 2
while strLine:
	x=0
	strLine = objFileIn.readline()
	strLine = strLine.replace("\"","")
	strLine = strLine.replace("\\","\\\\")
	strLine = strLine.replace("'","\\'")
	strLineParts = strLine[:-1].split(strDelim)
	if len(strLineParts) > 0 and strLine.strip() != "" :
		strSQL = "insert into {} (".format(strTableName)
		for Field in lstFields :
			strSQL += Field + ","
		strSQL = strSQL[:-1] + ") values ("
		for csvValue in strLineParts:
			strSQL +=  DBClean(csvValue) + ","
			x += 1
			if x > iFieldCount-1:
				break
		if len(strLineParts) > len(lstFields):
			print("Line {} {} has {} values, expecting {}. Dropping extra values".format(iLineNum,strLineParts[0],len(strLineParts),iFieldCount))
		if len(strLineParts) < len(lstFields):
			print("Line {} {} has {} values, expecting {}. Padding missing".format(iLineNum,strLineParts[0],len(strLineParts),iFieldCount))
			for i in list(range(x,iFieldCount)):
				strSQL += "NULL,"
		strSQL = strSQL[:-1]+");"
		lstReturn = SQLQuery (strSQL,dbConn)
		if not ValidReturn(lstReturn):
			print ("Line {} Unexpected return: {}".format(iLineNum, lstReturn))
			sys.exit(9)
		else:
			if lstReturn[0] != 1:
				print ("{} row inserted, line {}".format(lstReturn[0],iLineNum))
			iLineNum += 1
		if iLineNum%iStatusFreq == 0:
			print ("Imported {} records...".format(iLineNum))
print ("{} records imported. Except as noted above all records imported successfully".format(iLineNum-1))