#pip install pymysql
import pymysql
import sys

strServer = "localhost"
strUser = "test"
strPWD = "Nt3OPbI4x7WN77ZJcUg5SI58HgXpIp"
strInitialDB = "sys"

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
			dbResults = []
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

strSQL = "select * from esme.atrou051vipdest limit 5,10;"
# strSQL = "delete from esme.atrou051vipdest where tVirtual like '%smscc%'"

print ("Executing: {}".format(strSQL))
db = SQLConn (strServer,strUser,strPWD,strInitialDB)
lstReturn = SQLQuery (strSQL,db)
if isinstance(lstReturn,str):
	print (lstReturn)
else:
	print ("Rows affected: {}".format(lstReturn[0]))
	for row in lstReturn[1] :
		print (" ".join(row))

# disconnect from server
db.close()