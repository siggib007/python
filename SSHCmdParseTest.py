import getpass
import time
import sys
import paramiko #pip install paramiko

def getInput(strPrompt):
    if sys.version_info[0] > 2 :
        return input(strPrompt)
    else:
        return raw_input(strPrompt)
# end getInput
DefUserName = getpass.getuser()
print ("This is a SSH connect testing script. Your username is {3}. This is running under Python Version {0}.{1}.{2}".format(sys.version_info[0],sys.version_info[1],sys.version_info[2],DefUserName))
now = time.asctime()
print ("The time now is {}".format(now))
strDevName  = getInput("Please provide hostname you wish to connect to: ")
# strDevName = "brcwsc31"
strUserName = getInput("Please provide username for {0}, enter to use {1}: ".format(strDevName,DefUserName))
if strUserName == "":
	strUserName = DefUserName
# end if username is empty
strPWD = getpass.getpass(prompt="what is {0} password for {1}: ".format(strUserName,strDevName))
strCmd  = getInput("Please provide command to run on {}: ".format(strDevName))
# strCmd = "show bgp vrf INTERNET ipv6 unicast summary"
print ("OK connecting to {0} as {1} and executing '{2}'".format(strDevName,strUserName,strCmd))
try:
	SSH = paramiko.SSHClient()
	SSH.set_missing_host_key_policy(paramiko.AutoAddPolicy())
	SSH.connect(strDevName, username=strUserName, password=strPWD, look_for_keys=False, allow_agent=False)
	stdin, stdout, stderr = SSH.exec_command(strCmd)
	print ("sent {0} to {1}".format(strCmd,strDevName))
	strOut = stdout.read()
	SSH.close()
	strOut = strOut.decode("utf-8")
	print ("Command Output:\n{}".format(strOut))
	SSH.close()
except paramiko.ssh_exception.AuthenticationException as err:
	print ("Auth Exception: {0}".format(err))
	sys.exit(5)
except paramiko.SSHException as err:
	print ("SSH Exception: {0}".format(err))
except OSError as err:
	print ("socket Exception: {0}".format(err))
except Exception as err:
	print ("Unknown error: {0}".format(err))
print ("Here is the breakdown of that output:")
strOutputLines = strOut.splitlines()
i=0
for strLine in strOutputLines:
	print ("{} {}".format(i,strLine))
	i+=1
	strTokens = strLine.split()
	itokencount = len(strTokens)
	print ("There are {} tokens on this line".format(itokencount))
	for token in strTokens:
		print ("   - {}".format(token))