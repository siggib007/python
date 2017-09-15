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
strUserName = getInput("Please provide username for {0}, enter to use {1}: ".format(strDevName,DefUserName))
if strUserName == "":
	strUserName = DefUserName
# end if username is empty
strPWD = getpass.getpass(prompt="what is {0} password for {1}: ".format(strUserName,strDevName))
strCommand  = getInput("Please provide command to run on {}: ".format(strDevName))
print ("OK connecting to {0} as {1} and executing '{2}'".format(strDevName,strUserName,strCommand))
try:
	SSH = paramiko.SSHClient()
	SSH.set_missing_host_key_policy(paramiko.AutoAddPolicy())
	SSH.connect(strDevName, username=strUserName, password=strPWD, look_for_keys=False, allow_agent=False, timeout=1)
	objShell = SSH.invoke_shell()
	# time.sleep(5)
	# strOut = objShell.recv(5000)
	# objShell.send(strCommand)
	#stdin, stdout, stderr = SSH.exec_command(strCommand)
	# strOut = stdout.read()
	# strErr = stderr.read()
	# print ("show command sent")
	# print ("Raw stderr:\n{}".format(strErr))
	# print ("Raw output:\n{}".format(strOut))
	# strErr = strErr.decode("utf-8")
	# print ("decoded error: {}".format(strErr))
	# strOut = ""
	while not objShell.recv_ready():
		# print ("Not ready")
		time.sleep(1)
	# while not strOut.endswith("#"):
	# 	resp = objShell.recv(9999)
	# 	if resp == "":
	# 		break
	# 	strOut += resp.decode("ASCII")
	# # strOut = objShell.recv(5000)
	# # strOut = buff.decode("utf-8")
	# # print ("Received type: {}".format(type(strOut)))
	# print ("Command Output:\n{}".format(strOut))
	strResp = objShell.recv(999) # Clear the buffer
	objShell.send(strCommand+"\n")
	print ("show command sent")
	# time.sleep(4)
	# strOut = ""
	i = 0
	while not objShell.recv_ready():
		time.sleep(1)
		print ("Not ready")
		if i>30:
			break
		i+=1
	strResp = objShell.recv(999)
	strOut = strResp.decode("utf-8")
	# while not strOut.endswith("#"):
	# 	resp = objShell.recv(99)
	# 	# print ("REceived: {}".format(resp))
	# 	if resp == "" :
	# 		break
	# 	strOut += resp.decode("utf-8")
	print ("Command Output:\n{}".format(strOut))
	SSH.close()
except paramiko.ssh_exception.AuthenticationException as err:
	print ("Auth Exception: {0}".format(err))
except paramiko.SSHException as err:
	print ("SSH Exception: {0}".format(err))
except OSError as err:
	print ("socket Exception: {0}".format(err))
# except Exception as err:
# 	print ("{0}".format(err))