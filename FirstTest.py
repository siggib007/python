import sys
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