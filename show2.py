import paramiko
import sys
import time
import getpass
import os
import socket
#Ask for where the file is that has the router list
print ("MAKE SURE YOU HAVE INSTALLED PARAMIKO THROUGH PIP BEFORE RUNNING THIS SCRIPT OR IT WILL FAIL!!!!")
print ("This can be done by typing C:\Python27\Scripts> pip install paramiko")
print ("***Enter your information in the following prompts***\n")
print ("***You will need to write the full path to the router list***\n")
print ("***Make sure you adjust the full path to the router output file. This file is hardcoded, so make sure you change it in the script***\n")
print ("\n")
print ("\n")
print ("\n")
username=raw_input("Enter your username here:\t")
password = getpass.getpass()
routerlist=raw_input("Enter router list filename and full path:\t")
showcommand=raw_input("Enter the show command you would like to be sent to the routers\t")
print ("output file will be saved as router-output")

termlength = "terminal length 0"
str(routerlist)
with open(routerlist) as f:
    for line in f:
        line = line.strip()
        dssh = paramiko.SSHClient()
        dssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
		dssh.connect(line, username=username, password=password, look_for_keys=False, allow_agent=False)
		dssh.exec_command(termlength)
		print ("Term len set to 0")
		# Try to re-establish ssh connection before sending the second command.	
		dssh.connect(line, username=username, password=password, look_for_keys=False, allow_agent=False)
		stdin, stdout, stderr = dssh.exec_command(showcommand)
		print ("show command sent")
		#print shoutput
		mystring = stdout.read()
		print line
		print mystring
		#change this line to fit your machine. 
		#You will also need to create an empty file named 'router-output'
		f = open('c:\\Users\\pfarag\\router-output', 'a+')
		f.write("\n")
		f.write(line)
		f.write("\n")
		f.write(mystring)
		f.close()
	#except paramiko.AuthenticationError as error:
	#	print line + '===Bad credentials'
	#	print error
	except paramiko.SSHException:
		print line + '===Issues with ssh service'
	except socket.error:
		print line + '=== Device unreachable'
