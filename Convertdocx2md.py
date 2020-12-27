'''
This is the reverse of Convertmd2doc, this script takes a docx file,
converts it to markdown and splits up in it's origional files.
Takes the index file generated by the other script as input.
Paths require linux convention with /, windows convention of \\ will bomb.
Requires pandocs installed from https://pandoc.org/installing.html.
Read pandocs document regarding possible values for strOrigionalFormat and strConvert2
This script was written for python 3 and tested under Python Version 3.6.5
Author Siggi Bjarnason Copyright 2019
Website https://www.supergeek.us/

'''
import sys
import os
import time
import subprocess as proc

# Defining stuff
strFilein = "D:/OneDrive/Documents/infosechelp/Book/OnlineSafetyIndex.txt"
strOutPath = "C:/temp/"
strOutFile = "C:/temp/testOnlineSafety.md"
strConvertedFileName = "D:/OneDrive/Documents/infosechelp/Book/testOnlineSafety.docx"
strOrigionalFormat = "docx"
strConvert2 = "markdown"

strCmdLine = "pandoc {} -f {} -t {} -o {}".format(strConvertedFileName,strOrigionalFormat,strConvert2,strOutFile)
print ("executing {}".format(strCmdLine))
proc.Popen(strCmdLine)

lstStr2Delete = []
lstStr2Delete.append("{frontmatter}")
lstStr2Delete.append("{book: true, sample: true}")
lstStr2Delete.append("{mainmatter}")
lstStr2Delete.append("{book: true, sample: false}")
lstStr2Delete.append("{backmatter}")

dictReplacements = {}
dictReplacements["](C:/book/source/manuscript/resources/"] = "]("


# Doing stuff

print ("This is a script to combine bunch of files into a single markdown file, then convert it to docx."
	"\n This is running under Python Version {0}.{1}.{2}".format(
	sys.version_info[0],sys.version_info[1],sys.version_info[2]))
now = time.asctime()
print ("The time now is {}".format(now))

if os.path.isfile(strFilein) :
	print ("Found input file, good to go")
else:
	print ("could not find input file. Please validate the strFilein variable. exiting")
	sys.exit()

if not os.path.exists (strOutPath) :
  os.makedirs(strOutPath)
  print ("\nPath '{0}' for the output files didn't exists, so I create it!\n".format(strOutPath))

if strOutPath[-1:] != "/":
	strOutPath += "/"