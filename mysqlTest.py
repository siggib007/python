#pip install pymysql
import pymysql
import sys

strServer = "10.65.46.144"
strUser = "snowImport"
strPWD = "DbBXhecXsrWELLBd5ebv3e7s"
strInitialDB = "Qualys_Portal"
strHeaders = ""

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
	global strHeaders
	try:
		# prepare a cursor object using cursor() method
		dbCursor = db.cursor()
		# Execute the SQL command
		dbCursor.execute(strSQL)
		# Capture headers
		for temp in dbCursor.description:
			strHeaders += temp[0] + ","
		if strHeaders[-1]==",":
			strHeaders = strHeaders[:-1]
		# Count rows
		iRowCount = dbCursor.rowcount
		if strSQL[:6].lower() == "select":
			dbResults = dbCursor.fetchall()
			print ("dbResults type is: {}".format(type(dbResults)))
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

strSQL = "select * from tblservicenow limit 10;"

print ("Executing: {}".format(strSQL))
db = SQLConn (strServer,strUser,strPWD,strInitialDB)
lstReturn = SQLQuery (strSQL,db)
if ValidReturn(lstReturn):
	print ("Rows affected: {}".format(lstReturn[0]))
	print (strHeaders)
	for row in lstReturn[1] :
		# print ("Row is of type {}".format(type(row)))
		print (" ".join(map(str,row)))
else:
	print ("Unexpected: {}".format(lstReturn))

# disconnect from server
db.close()