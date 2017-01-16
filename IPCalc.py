import sys
SysArgs = sys.argv
iSysArgLen = len(sys.argv)
strMask = ""
iBitMask = ""


def BitMask2Dec(iBitMask):
	#Convert bitmask to Decimal
	iBitLeft = 32 - iBitMask
	strBinMask=("1"*iBitMask) + ("0"*iBitLeft)
	return int(strBinMask,2)


def DotDecGen (iDecValue):
	#Convert decimal to hex
	HexMask = hex(iDecValue)
	# print ("Hex: " + HexMask)

	#Convert Hex to dot dec
	strTemp = str(int(HexMask[2:4],16)) + "." + str(int(HexMask[4:6],16)) + "." 
	strTemp = strTemp + str(int(HexMask[6:8],16)) + "." + str(int(HexMask[8:10],16))
	return strTemp


def ValidateIP(strToCheck):
	Quads = strToCheck.split(".")
	if len(Quads) != 4:
		return False

	for Q in Quads:
		try:
			iQuad = int(Q)
		except ValueError:
			return False

		if iQuad > 255 or iQuad < 0:
			return False

	return True


def DotDec2Int (strValue):
	strHex = ""
	if ValidateIP(strValue) == False:
		return 0

	Quads = strValue.split(".")
	for Q in Quads:
		QuadHex = hex(int(Q))
		strwp = "00"+ QuadHex[2:]
		strHex = strHex + strwp[-2:]

	return int(strHex,16)

def ValidateMask(strToCheck):
	if ValidateIP(strToCheck) == False:
		return 0

	x=0
	iDecValue = DotDec2Int(strToCheck)
	strBinary = bin(iDecValue)
	cBit = strBinary[2]
	bFound = False
	for c in strBinary[2:]:
		x=x+1
		if cBit != c:
			iBitMask = str(x-1)
			print ("bit: " + iBitMask)
			if bFound:
				return 0
			else:
				cBit=c
				bFound = True

	return iBitMask


if iSysArgLen < 2:
    print("Usage: python {} IPAddress mask".format(sys.argv[0]))
    print("Example1: python {} 218.55.213.55/27".format(sys.argv[0]))
    print("Example1: python {} 218.55.213.55 255.255.255.224".format(sys.argv[0]))
    sys.exit(1)

strIPAddress = SysArgs[1]

if iSysArgLen > 2:
	strMask = SysArgs[2]

print ("You provdide IP address of " + strIPAddress + " " + strMask)

if strMask != "":
	print ("The mask you provided is in dotted decimal notation")

if "/" in strIPAddress:
	print ("you provided the mask as a bit mask")
	IPAddrParts = strIPAddress.split("/")
	strIPAddress=IPAddrParts[0]
	iBitMask=int(IPAddrParts[1])
	strMask = DotDecGen(BitMask2Dec(iBitMask))


iBitMask = ValidateMask(strMask)
print ("IPAddr: " + strIPAddress )
print ("str mask: " + strMask)
print ("bit Mask: " + str(iBitMask))

if ValidateIP(strIPAddress):
	print ("The IP you provided is valid")
else:
	print (strIPAddress + " is not a valid IP!")

if iBitMask:
	print ("The mask you provided is valid")
else:
	print (strMask + " is not a valid mask!")
