'''
IP Calculator
Author Siggi Bjarnason Copyright 2017
Website http://www.ipcalc.us/ and http://www.icecomputing.com

Description:
This is a command line IP address subnet calculator for IPv4
Execute the script and pass in an ip address as a parameter
Any of these three formats are valid
IPCalc.py 218.55.213.56/27
IPCalc.py 218.55.213.56 255.255.255.224
IPCalc.py 218.55.213.56 0.0.0.31

The script will output
- mask in other two formats
- host count
- Subnet IP
- broadcast IP

Following packages need to be installed as administrator
pip install requests
pip install jason

'''

# Import libraries
import sys
import requests
import json
# End imports

# Function section

# Function BinMask2Dec
# Convert bitmask to Decimal
# Takes in an integer from 1 to 32 as mask reprisenting number of bits in the subnet
# converts that to a decimal number that can be converted lated to a dotted decimal
def BitMask2Dec(iBitMask):
	if iBitMask < 0 or iBitMask > 32:
		return 0
	# end if
	iBitLeft = 32 - iBitMask
	strBinMask=("1"*iBitMask) + ("0"*iBitLeft)
	return int(strBinMask,2)
# End Function

# Function DotDecGen
# Takes a decimal value and converts it to a dotted decimal string
# Number has to be greater than 0 and 32 bits.
def DotDecGen (iDecValue):
	if iDecValue < 1 or iDecValue > 4294967295:
		return "Invalid"
	# end if

	# Convert decimal to hex
	HexValue = hex(iDecValue)

	#Ensure the results is 8 hex digits long.
	#IP's lower than 16.0.0.0 have trailing 0's that get trimmed off by hex function
	HexValue = "0"*8+HexValue[2:]
	HexValue = "0x"+HexValue[-8:]
	# Convert Hex to dot dec
	strTemp = str(int(HexValue[2:4],16)) + "." + str(int(HexValue[4:6],16)) + "."
	strTemp = strTemp + str(int(HexValue[6:8],16)) + "." + str(int(HexValue[8:10],16))
	return strTemp
# End Function


# Function ValidateIP
# Takes in a string and validates that it follows standard IP address format
# Should be four parts with period deliniation
# Each nubmer should be a number from 0 to 255.
def ValidateIP(strToCheck):
	Quads = strToCheck.split(".")
	if len(Quads) != 4:
		return False
	# end if

	for Q in Quads:
		try:
			iQuad = int(Q)
		except ValueError:
			return False
		# end try

		if iQuad > 255 or iQuad < 0:
			return False
		# end if

	return True
# end function

# Function DotDec2Int
# Takes in a string like an IP address or a mask
# returns decimal integer representation of that string
def DotDec2Int (strValue):
	strHex = ""
	if ValidateIP(strValue) == False:
		return 0
	# end if

	Quads = strValue.split(".")
	for Q in Quads:
		QuadHex = hex(int(Q))
		strwp = "00"+ QuadHex[2:]
		strHex = strHex + strwp[-2:]
	# next

	return int(strHex,16)
# end function

# Function ValidMask
# Takes in a string containing a dotted decimal mask
# validates that it is valid, by checking if it follows normal IP format
# and that bits are all sequential, such as 111111100000 not 1100111110001111, etc
def ValidMask(strToCheck):
	iNumBits=0
	if ValidateIP(strToCheck) == False:
		return 0
	# end if

	iDecValue = DotDec2Int(strToCheck)
	strBinary = bin(iDecValue)

	strTemp = "0"*32 + strBinary[2:]
	strBinary = strTemp[-32:]
	cBit = strBinary[0]
	bFound = False
	x=0
	for c in strBinary:
		x=x+1
		if cBit != c:
			iNumBits = x-1
			if bFound:
				return 0
			else:
				cBit=c
				bFound = True
			# end if
		# end if
	# next
	if iNumBits==0:
		iNumBits = x
	# end if
	return iNumBits
# end function

# Function MaskType
# Takes is a string with a subnet mask and determines if it is:
# - standard dotted decimal format
# - inverse dotted decimal format
# - neither, aka invalid mask format
def MaskType (strToCheck):
	if ValidMask(strToCheck)==False:
		return "Invalid Mask"
	# end if

	Quads = strToCheck.split(".")
	if int(Quads[0]) == int(Quads[3]):
		if int(Quads[0]) ==255:
			return "dotDec"
		else:
			return "inv"
		# end if
	# end if

	if int(Quads[0]) > int(Quads[3]):
		return "dotDec"
	else:
		return "inv"
	# end if
# End Function

# Function SubnetCompare
# Takes in three integers, two are int represenation of IP addresses, one is int of a mask
def SubnetCompare (iIP1,iIP2,iMask):
	iSubnet1 = iIP1 | iMask
	iSubnet2 = iIP2 | iMask
	return iSubnet1==iSubnet2
# End function

# Function ConvertMask
# Switches between dotted decimal and inverse dotted decimal
def ConvertMask (strToCheck):
	if ValidMask(strToCheck)==False:
		return "Invalid Mask"
	# end if
	strTemp = ""
	Quads = strToCheck.split(".")
	for Q in Quads:
		if strTemp =="":
			strTemp = str(255-int(Q))
		else:
			strTemp = strTemp + "." + str(255-int(Q))
		# End if
	#next
	return strTemp
# End function

# Function IPCalc
# This function takes in a string of IP address and does the actual final colculation
def IPCalc (strIPAddress):
	strIPAddress=strIPAddress.strip()
	dictIPInfo={}
	if " " in strIPAddress:
		IPAddrParts = strIPAddress.split(" ")
		strMask = IPAddrParts[1]
	# end if

	if "/" in strIPAddress:
		IPAddrParts = strIPAddress.split("/")
		try:
			iBitMask=int(IPAddrParts[1])
		except ValueError:
			iBitMask=0
	# end if

	# end try
	strIPAddress=IPAddrParts[0]

	strMask = DotDecGen(BitMask2Dec(iBitMask))
	if strMask != "Invalid":
		dictIPInfo['Maskmsg'] = "You provided the mask as a bit mask"
	else:
		dictIPInfo['MaskErr'] = str(iBitMask) + " is an invalid bit mask, changing to /32"
		iBitMask=32
		strMask = DotDecGen(BitMask2Dec(iBitMask))
	# end if


	iBitMask = ValidMask(strMask)
	if iBitMask==0:
		dictIPInfo['MaskErr'] = strMask + " is an invalid mask, changing to host only"
		iBitMask=32
		strMask = DotDecGen(BitMask2Dec(iBitMask))
	# end if

	strMask2 = ConvertMask(strMask)
	strType = MaskType(strMask)
	if strType =="dotDec":
		dictIPInfo['Mask'] = strMask
		dictIPInfo['InvMask'] = strMask2
	elif strType == "inv":
		dictIPInfo['Mask'] = strMask2
		dictIPInfo['InvMask'] = strMask
	# end if

	if ValidateIP(strIPAddress):
		dictIPInfo['IPAddr'] = strIPAddress
		dictIPInfo['BitMask'] = str(iBitMask)
		iHostcount = 2**(32 - iBitMask)
		dictIPInfo['Hostcount'] = iHostcount

		# End If iHoustcount
		iDecIPAddr = DotDec2Int(strIPAddress)
		iDecSubID = iDecIPAddr-(iDecIPAddr%iHostcount)
		iDecBroad = iDecSubID + iHostcount - 1
		dictIPInfo['Subnet'] = DotDecGen(iDecSubID)
		dictIPInfo['Broadcast'] = DotDecGen(iDecBroad)

		#execute Whois Query against ARIN.
		strURL="http://whois.arin.net/rest/ip/"+strIPAddress
		strHeader={'Accept': 'application/json'}
		try:
			WebRequest = requests.get(strURL, headers=strHeader)
		except:
			pass
		# end try
		if isinstance(WebRequest,requests.models.Response)==False:
			return dictIPInfo
		# end if

		jsonWebResult = json.loads(WebRequest.text)
		dictIPInfo['Org'] = jsonWebResult['net']['orgRef']['@name']
		dictIPInfo['Handle'] = jsonWebResult['net']['orgRef']['@handle']
		if isinstance(jsonWebResult['net']['netBlocks']['netBlock'],dict):
			dictIPInfo['StartIP'] = jsonWebResult['net']['netBlocks']['netBlock']['startAddress']['$']
			dictIPInfo['EndIP']   = jsonWebResult['net']['netBlocks']['netBlock']['endAddress']['$']
			dictIPInfo['CIDR']    = jsonWebResult['net']['netBlocks']['netBlock']['cidrLength']['$']
			dictIPInfo['Type']    = jsonWebResult['net']['netBlocks']['netBlock']['type']['$']
		else:
			dictIPInfo['StartIP'] = jsonWebResult['net']['netBlocks']['netBlock'][0]['startAddress']['$']
			dictIPInfo['EndIP']   = jsonWebResult['net']['netBlocks']['netBlock'][0]['endAddress']['$']
			dictIPInfo['CIDR']    = jsonWebResult['net']['netBlocks']['netBlock'][0]['cidrLength']['$']
			dictIPInfo['Type']    = jsonWebResult['net']['netBlocks']['netBlock'][0]['type']['$']
		# End if
		dictIPInfo['Ref'] = jsonWebResult['net']['ref']['$']
		dictIPInfo['Name'] = jsonWebResult['net']['name']['$']
	else:
		dictIPInfo['IPError'] = strIPAddress + " is not a valid IP!"
	# End if
	return dictIPInfo
# end function
# End function section

# Main section of the script
SysArgs = sys.argv
iSysArgLen = len(sys.argv)
strMask = ""
iBitMask = ""

if iSysArgLen < 2:
    print("Usage: python {} IPAddress mask".format(sys.argv[0]))
    print("Example1: python {} 218.55.213.55/27".format(sys.argv[0]))
    print("Example1: python {} 218.55.213.55 255.255.255.224".format(sys.argv[0]))
    sys.exit(1)
# End If

strIPAddress = SysArgs[1]

if iSysArgLen > 2:
	strMask = SysArgs[2]
# End If

print ("You provided IP address of " + strIPAddress + " " + strMask)

if strMask != "":
	strType = MaskType(strMask)
	if strType =="dotDec":
		print ("The mask provided is a normal dotted decimal mask")
	elif strType == "inv":
		print ("You provided an inverse mask")
	# else:
	# 	print(strMask + " is not a valid mask")
# end if

IP_Result = IPCalc (strIPAddress + " " + strMask)
if "IPError" in IP_Result:
	print(IP_Result['IPError'])
else:
	if "MaskErr" in IP_Result:
		print (IP_Result['MaskErr'])
	# end if
	if "Maskmsg" in IP_Result:
		print (IP_Result['Maskmsg'])
	# end if
	print ("IP Addr: " + strIPAddress)
	print ("Bit Mask: " + IP_Result['BitMask'])
	print ("Mask: " + IP_Result['Mask'])
	print ("Inverse Mask: " + IP_Result['InvMask'])
	iHostcount = IP_Result['Hostcount']
	if iHostcount == 1:
		print ("Host only")
	if iHostcount == 2:
		print ("only subnet and broadcast")
	if iHostcount > 2:
		print ("Host count: " + str(iHostcount-2))

	print ("Subnet IP: " + IP_Result['Subnet'])
	print ("Broadcast IP: " + IP_Result['Broadcast'])

	strType = IP_Result['Type']
	if strType=="RV" or strType=="AP" or strType=="AF":
		print ("Assigned by " + strOrg)
	else:
		strOrgURL = "  https://whois.arin.net/rest/org/"+IP_Result['Handle']
		strOrg = IP_Result['Org']
		if strType == "IU":
			strOrg = IP_Result['Name']
			strOrgURL = ""
		#end if
		strStart = IP_Result['StartIP']
		strEnd = IP_Result['EndIP']
		strCIDR = IP_Result['CIDR']
		strRef = IP_Result['Ref']
		print ("Information from ARIN")
		print ("Org: "+strOrg+strOrgURL  )
		print ("Netblock: " + strStart +"/"+strCIDR+"("+strStart+"-"+strEnd+")")
		print (strRef)
		print ("Type:" + strType)
	# end if
#end if