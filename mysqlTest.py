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

strDescr = "My test descr"
iNeighborID = 8
# strSQL = "select * from esme.atrou051vipdest limit 25;"
#strSQL = "delete from esme.atrou051vipdest where Virtual like '%smscd%'"
strSQL = "update networks.tblneighbors set vcDescription = '{}' where iNeighborID = {}".format(strDescr,iNeighborID)

print ("Executing: {}".format(strSQL))
db = SQLConn (strServer,strUser,strPWD,strInitialDB)
lstReturn = SQLQuery (strSQL,db)
if ValidReturn(lstReturn):
	print ("Rows affected: {}".format(lstReturn[0]))
	if lstReturn[0] == 1:
		print ("{}".format(lstReturn[1][0][0]))
	else:
		for row in lstReturn[1] :
			print (" ".join(map(str,row)))
else:
	print ("Unexpected: {}".format(lstReturn))

# disconnect from server
db.close()