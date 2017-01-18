import sys
import re

vname = raw_input("Enter the vlan name:\t")
vnum = raw_input("Enter the vlan number:\t")
#bits = raw_input("Enter the number of bits without the leading /:\t")
subnet= raw_input("Enter the IPv4 of the subnet in the format of x.x.x.x/xx.:\t")
switch1= raw_input("What is the first switch you will be updating?")
switch2= raw_input("What is the second switch you will be updating?")
#network = int(raw_input("Enter the network address for the 4th octet:\t"))
last=re.split(r'(\.|/)', subnet)
hsrp=1+int(last[6])
sw1_ip=2+int(last[6])
sw2_ip=3+int(last[6])
full_hsrp_ip=last[0]+last[1]+last[2]+last[3]+last[4]+last[5]+str(hsrp)+last[7]+last[8]
full_sw1_ip=last[0]+last[1]+last[2]+last[3]+last[4]+last[5]+str(sw1_ip)+last[7]+last[8]
full_sw2_ip=last[0]+last[1]+last[2]+last[3]+last[4]+last[5]+str(sw2_ip)+last[7]+last[8]
# uncomment to make sure math is being done to variables correctly
#print last
#ip=last[0]+last[1]+last[2]+last[3]+last[4]+last[5]+last[6]+last[7]+last[8]
#print ip
#print ("The last octet is %s") %last[6]
#print ("hsrp is %s") %hsrp
#print ("1st ip is %s") %sw1_ip
#print ("2nd ip is %s") %sw2_ip

if int(vnum) % 2 == 0:
	print ("VLAN is even")
	hsrpprio01=100
	hsrpprio02=105
else:
	print ("Vlan is odd")
	hsrpprio01=105
	hsrpprio02=100
### Print Different MOP Sections
### Precheck section below:
print ("Precheck/Baseline for %s and %s") % (switch1, switch2)

print ("NOTE: The same commands will be used for both switches.")

print ("!")
print ("term length 0")
print ("!")
print ("sh vlan brief | include ^%s") %vnum
print ("! ")
print ("! *** Verify above VLAN(s) are not in use (no output expected) ***")
print ("!")
print ("show interface port-channel 1 switchport | include 'VLANs Allowed'")
print ("! ")
print ("! *** Verify VLAN(s) %s is not listed ***") %vnum
print ("! ")
print ("show ip interface brief | include Vlan%s") %vnum
print ("!  ")
print ("! *** Verify above interface(s) are not listed (no output expected) ***")
print ("! ")
print ("show interface status | include <ENTER YOUR ACCESS PORTS HERE!!!>")
print ("! ")
print ("! *** Verify above interface(s) are connected and in Cable_Testing state *** ")
print ("!")
print ("show run interface <ENTER YOUR ACCESS PORTS HERE!!!>")
print ("!")
print ("! *** Capture the pre-change output ***")
print ("!")

###Configuratyion for router 02 in the pair
print ("**************%s configuration*******") %switch2
print("!")
print("term length 0")
print("!")
print ("conf t")
print("!")
print("vlan %s") %vnum
print ("	%s") % vname
print("!")
#Need to capture port channel info above and you can adjust this below
#For now hard coding port channel 1
print("interface port-channel1")
print("  switchport trunk allowed vlan add %s") %vnum
print("!")
print ("interface Vlan%s") %vnum
print("  no shutdown")
print("    mtu 9216")
print("    description %s") %vname
print("  ip address %s") % full_sw2_ip
print("  no ip redirect")
print("  hsrp version 2")
print("  hsrp %s") %vnum
print("    preempt ")
print("    priority %s") %hsrpprio02
print("    ip %s") % full_hsrp_ip
print("    track 1 ")
print("    track 101 decrement 50 ")
print("!")

print("exit")
print("!")
print("end")
print("!")
print("copy run start")
print("!")

###Configuratyion for router 01 in the pair

print ("**************%s configuration*******") %switch1
print("!")
print("term length 0")
print("!")
print ("conf t")
print("!")
print("vlan %s") %vnum
print ("	%s") % vname
print("!")


#Need to capture port channel info above and you can adjust this below
#For now hard coding port channel 1
print("interface port-channel1")
print("  switchport trunk allowed vlan add %s") %vnum
print("!")
print ("interface Vlan%s") %vnum
print("  no shutdown")
print("    mtu 9216")
print("    description %s") %vname
print("  ip address %s") % full_sw1_ip
print("  no ip redirect")
print("  hsrp version 2")
print("  hsrp %s") %vnum
print("    preempt ")
print("    priority %s") %hsrpprio01
print("    ip %s") % full_hsrp_ip
print("    track 1 ")
print("    track 101 decrement 50 ")
print("!")

print("exit")
print("!")
print("end")
print("!")
print("copy run start")
print("!")

### Postcheck section below:
print ("Precheck/Baseline for %s and %s") % (switch1, switch2)

print ("NOTE: The same commands will be used for both switches.")

print ("!")
print ("term length 0")
print ("!")
print ("sh vlan brief | include ^%s") %vnum
print ("! ")
print ("! *** Verify above VLAN(s) are not in use (no output expected) ***")
print ("!")
print ("show interface port-channel 1 switchport | include 'VLANs Allowed'")
print ("! ")
print ("! *** Verify VLAN(s) %s is not listed ***") %vnum
print ("! ")
print ("show ip interface brief | include Vlan%s") %vnum
print ("!  ")
print ("! *** Verify above interface(s) are not listed (no output expected) ***")
print ("! ")
print ("show interface status | include <ENTER YOUR ACCESS PORTS HERE!!!>")
print ("! ")
print ("! *** Verify above interface(s) are connected and in Cable_Testing state *** ")
print ("!")
print ("show run interface <ENTER YOUR ACCESS PORTS HERE!!!>")
print ("!")
print ("! *** Capture the pre-change output ***")
print ("!")
print("! *** Verify above interface has VLAN %s applied  *** ") % vnum
print("! *** Verify that storm-control broadcast & multicast level is 4.00 ***")
print("! *** Verify that storm-control action is trap ***")
print("! *** Verify that spanning-tree port type is edge and bpduguard enabled ***")
print("!")
