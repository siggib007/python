import sys
import getpass

def getInput(strPrompt):
    if sys.version_info[0] > 2 :
        return input(strPrompt)
    else:
        return raw_input(strPrompt)
# end getInput

sa = sys.argv
lsa = len(sys.argv)
if lsa != 2:
    print("Usage: python {} duration_in_minutes.".format(sys.argv[0]))
    print("Example: python {} 10".format(sys.argv[0]))
    sys.exit(1)

try:
    minutes = int(sa[1])
except ValueError:
    print("Invalid value {} for minutes.".format(sa[1]))
    print("Should be an integer >= 0.")
    sys.exit(1)

if minutes < 0:
    print("Invalid value {} for minutes.".format(minutes))
    print("Should be an integer >= 0.")
    sys.exit(1)

print ("Welcome to my Python Test script. Your username is {3}. This is running under Python Version {0}.{1}.{2}".format(sys.version_info[0],sys.version_info[1],sys.version_info[2],getpass.getuser()))
print ("Hello {}".format(getInput("What is your name? ")))
p = getpass.getpass(prompt="Tell me a secret ")
print ("I won't tell anyone about {}".format(p))
#print ("Your username is {}".format(getpass.getuser()))

seconds = minutes * 60

if minutes == 1:
    unit_word = " minute"
else:
    unit_word = " minutes"

strmin = str(minutes)
strsec = str(seconds)
# strout1 = "you entered " + strmin + unit_word
# strout2 = "which is " + strsec + " seconds"

# strout1 = "you entered {}".format(minutes) + unit_word
# strout2 = "which is {}".format(seconds) + " seconds"
print ("you entered " + strmin + unit_word)
print ("which is " + strsec + " seconds")

