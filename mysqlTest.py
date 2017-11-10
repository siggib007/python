#pip install pymysql
import pymysql
import sys
strServer = "localhost"
strUser = "test"
strPWD = "Nt3OPbI4x7WN77ZJcUg5SI58HgXpIp"
strInitialDB = "sys"
try:
# Open database connection
	db = pymysql.connect(strServer,strUser,strPWD,strInitialDB)
except pymysql.err.InternalError as err:
   print ("Error: unable to connect: {}".format(err))
   sys.exit(5)
except pymysql.err.OperationalError as err:
   print ("Operational Error: unable to connect: {}".format(err))
   sys.exit(5)
except pymysql.err.ProgrammingError as err:
   print ("Programing Error: unable to connect: {}".format(err))
   sys.exit(5)

# prepare a cursor object using cursor() method
dbCursor = db.cursor()

strSQL = "select * from esme.atrou051vipdest limit 5,10;"
print ("executing: {}".format(strSQL))
try:
   # Execute the SQL command
   dbCursor.execute(strSQL)
   # Count rows
   iRowCount = dbCursor.rowcount
   print ("There are {} rows in the response.".format(iRowCount))
   # Fetch all the rows in a list of lists.
   dbResults = dbCursor.fetchall()
   for row in dbResults:
      # Now print fetched result
      print (" ".join(row))
except pymysql.err.InternalError as err:
   print ("Internal Error: unable to fetch data: {}".format(err))
except pymysql.err.ProgrammingError as err:
   print ("Programing Error: unable to fetch data: {}".format(err))
except pymysql.err.OperationalError as err:
   print ("Programing Error: unable to fetch data: {}".format(err))

# disconnect from server
db.close()