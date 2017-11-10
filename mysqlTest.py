#pip install pymysql
import pymysql
import sys

try:
# Open database connection
	db = pymysql.connect("localhost","test","Nt3OPbI4x7WN77ZJcUg5SI58HgXpIp","sys" )
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
      print ("{0} {1} {2} {3} {4} {5} ".format(row[0],row[1],row[2],row[3],row[4],row[5]))
except pymysql.err.InternalError as err:
   print ("Internal Error: unable to fetch data: {}".format(err))
except pymysql.err.ProgrammingError as err:
   print ("Programing Error: unable to fetch data: {}".format(err))
except pymysql.err.OperationalError as err:
   print ("Programing Error: unable to fetch data: {}".format(err))

# disconnect from server
db.close()