import time
import sys
import os

print ("This is a script to test sys.argv and stuff like that. This is running under Python Version {0}.{1}.{2}".format(sys.version_info[0],sys.version_info[1],sys.version_info[2]))
now = time.asctime()
print ("The time now is {}".format(now))

print ("sys.argv length: {}".format(len(sys.argv)))
print ("sys.argv contains: {}".format(sys.argv))
print ("file dirname: {}".format(os.path.dirname(__file__)))
print ("sys.argv[0] dirname: {}".format(os.path.dirname(sys.argv[0])))
print ("getcwd: {}".format(os.getcwd()))
print ("File:{}".format(__file__))
print ("Sys.argv[0]: {}".format(sys.argv[0]))

iLoc = sys.argv[0].rfind(".")
strConfFile = sys.argv[0][:iLoc] + ".ini"

print ("conf file: {}".format(strConfFile))