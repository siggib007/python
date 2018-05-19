#pip install pyodbc
import pyodbc
import sys

strServer = "localhost"
strInitialDB = "Qualys_Portal"
strSQL = "select * from tblNetBlocks;"

def SQLConn (strServer,strInitialDB):
	try:
		# Open database connection
		return pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER='+strServer+';DATABASE='+strInitialDB+';Trusted_Connection=yes;')
	except pyodbc.InternalError as err:
		print ("Error: unable to connect: {}".format(err))
		sys.exit(5)
	except pyodbc.OperationalError as err:
		print ("Operational Error: unable to connect: {}".format(err))
		sys.exit(5)
	except pyodbc.ProgrammingError as err:
		print ("Programing Error: unable to connect: {}".format(err))
		sys.exit(5)
	# except Exception as err:
	# 	print ("Unknown Error: unable to connect: {}".format(err))
	# 	sys.exit(5)

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
		if strSQL[:6].lower() == "select":
			dbResults = dbCursor.fetchall()
			print ("dbResults type is: {}".format(type(dbResults)))
		else:
			db.commit()
			dbResults = ()
		iRowCount = dbCursor.rowcount
		return [iRowCount,dbResults]
	except pyodbc.InternalError as err:
		if strSQL[:6].lower() != "select":
			db.rollback()
		return "Internal Error: unable to execute: {}".format(err)
	except pyodbc.ProgrammingError as err:
		if strSQL[:6].lower() != "select":
			db.rollback()
		return "Programing Error: unable to execute: {}".format(err)
	except pyodbc.OperationalError as err:
		if strSQL[:6].lower() != "select":
			db.rollback()
		return "Programing Error: unable to execute: {}".format(err)
	except pyodbc.IntegrityError as err:
		if strSQL[:6].lower() != "select":
			db.rollback()
		return "Integrity Error: unable to execute: {}".format(err)
	# except Exception as err:
	# 	return "Unknown Error: unable to execute: {}".format(err)

def ValidReturn(lsttest):
	if isinstance(lsttest,list):
		if len(lsttest) == 2:
			if isinstance(lsttest[0],int) and isinstance(lsttest[1],list):
				return True
			else:
				return False
		else:
			return False
	else:
		return False

strHeaders = ""
print ("Executing: {}".format(strSQL))
db = SQLConn (strServer,strInitialDB)
lstReturn = SQLQuery (strSQL,db)
if ValidReturn(lstReturn):
	print ("Rows affected: {}".format(lstReturn[0]))
	print ("Result set size: {}".format(len(lstReturn[1])))
	print (strHeaders)
	for row in lstReturn[1] :
		# print ("Row is of type {}".format(type(row)))
		print (" ".join(map(str,row)))
else:
	print ("Unexpected: {} \n{}".format(lstReturn,strSQL))

# disconnect from server
db.close()