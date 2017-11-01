import time
import sys
import getpass

print ("Welcome to my Python Test script. Your username is {3}. This is running under Python Version {0}.{1}.{2}".format(sys.version_info[0],sys.version_info[1],sys.version_info[2],getpass.getuser()))

localtime = time.localtime(time.time())
gmt_time = time.gmtime()
iGMT_offset = localtime.tm_gmtoff
localgtmdiff = time.mktime(localtime) - time.mktime(gmt_time)
print ("Local current time :{}".format(localtime))
print ("GTM current time :{}".format(gmt_time))
print ("Local time diff from GTM: {}".format(localgtmdiff))
# print ("Last night :{}".format(lastnight))
# print ("\n month:{}\n ".format(localtime[1]))
# print ("\n isdst:{}\n ".format(localtime[8]))
print ("\n zone:{}\n ".format(localtime.tm_gmtoff))

now = time.asctime()
print ("The time now is {}".format(now))
LongDate = time.strftime("%A %B %d, %Y %Z %z")
print ("Longformat {}".format(LongDate))
ISO = time.strftime("%Y-%m-%d %H:%M:%S : ")
print ("ISO {}".format(ISO))
shortDate = time.strftime("%Y-%m-%d",time.localtime(time.time()-86400)) + " 22:00"
print ("last night 10pm: {}".format(shortDate))
print ("last night tuple: {}".format(time.strptime(shortDate,"%Y-%m-%d %H:%M")))
lastnightgmt = time.localtime(time.mktime(time.strptime(shortDate,"%Y-%m-%d %H:%M"))-iGMT_offset)
print ("last night gmt: {}".format(lastnightgmt))
strQualysTime = time.strftime("%Y-%m-%dT%H:%M:%SZ",lastnightgmt)
print ("Qualys Time: {}".format(strQualysTime))