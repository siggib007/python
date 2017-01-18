#Python version used 2.7.11
#
# Check if all prerequisites libraries were installed - paramiko and win32 are not standard libraries
# and have to be downloaded from the Internet
import sys
import paramiko
import time
import getpass
import re
import socket
import win32com.client as win32


ssh = paramiko.SSHClient()

# Function to disable paging
def disable_paging(remote_shell):
#    '''Disable paging on a Cisco router'''
    remote_shell.send("terminal length 0\n")
    time.sleep(1)
# Clear the buffer on screen
    output = remote_shell.recv(1000)
    return output

# Getting credentials for remote login on devices
username = getpass.getuser()
password = "" # <------- you should put your password here or replace it with raw_input function to prompt user enter it from CLI!!!!!


# Addressing SSH host_key inconvenience

ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

# Reading the file with list of markets that are in the scope
# 3 char format like - WSC; every market = line !!!!!!! 
def read_market_file():
    file = open("", "r")# <------- you should put your path to file here or replace it with raw_input function to prompt user enter it from CLI!!!!!
    content = file.readlines()
    file.close()
    return content

# Finding ACL entry with specific word stored in scope variable and returning sequence number
def find_entries(scope):
    remote_shell.send('show access-lists ipv4 OMW-ABF-IN | i %s\r\n' % scope)
    time.sleep(1)
    cli_output = re.sub("\x08", "", remote_shell.recv(5000)).splitlines()
    try:
        result = cli_output[3].strip()
        entry_pointer = re.search('^[0-9].*', result)
        if entry_pointer:
            entry = [y for y in (x.strip() for x in entry_pointer.group(0).split(" ")) if y][0]
            print entry
        else:
            entry = None
    except IndexError:
        entry = None
        pass
    return entry

# Finding all ACL entries with nexthop (ABF rule) configured and storing all nex-hops in a list
# All list entries then checked for same nexthop configured and nexthop get populated into excell spreadsheet
# with red background if nexthops configured are not consistent among all ABF entries and with green if all good
def find_nexthop(current_line):
    remote_shell.send('show access-lists ipv4 OMW-ABF-IN | i nexthop1.ipv4.[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$\r\n' )
    time.sleep(1)
    nexthop_list = []
    cli_output = re.sub("\x08", "", remote_shell.recv(5000)).splitlines()
    for i in cli_output:
        nexthop_line = re.search('.*nexthop1.*', i)
        if nexthop_line:
            nexthop = [y for y in (x.strip() for x in nexthop_line.group(0).split(" ")) if y][-1]
            nexthop_list.append(nexthop)
    trigger = 0
    for i in range (2,len(nexthop_list)):
        if nexthop_list[i-1] != nexthop_list[i]:
            trigger = 1
    if nexthop_list[1]:
        ws.Cells(current_line,12).Value = nexthop_list[1]
    if trigger == 0:
        ws.Cells(current_line,12).Interior.ColorIndex = 4
    else:
        ws.Cells(current_line,12).Interior.ColorIndex = 3


# Checking if 9 entries, before the entry we previously found,  are not used
# populating results into excell and marking sequence numbers that are not used with green
# and those that used with red
def check_seq(seq_num,current_line):
    current_row = 3
    for i in range (int(seq_num)-9, int(seq_num)):
        current_seq = find_entries(i)
        if current_seq == None:
            ws.Cells(current_line,current_row).Value = i
            ws.Cells(current_line,current_row).Interior.ColorIndex = 4
        else:
            ws.Cells(current_line,current_row).Value = i
            ws.Cells(current_line,current_row).Interior.ColorIndex = 3
        current_row += 1

# Initializing excell application, creating new workbook,spreadsheet, and naming last
# Returns them as variables.
def invoke_excel():
    excel = win32.gencache.EnsureDispatch('Excel.Application')
    excel.Visible = True
    wb = excel.Workbooks.Add()
    ws = wb.Worksheets('Sheet1')
    ws.Name = 'Entries check'
    return wb,ws,excel

# !!!!
# Main body starts
#

# Calling invoke_excel function
wb,ws,excel = invoke_excel()

#setting initial value of variable used for tracking curent line while filling excell script
current_line = 2

# Formating Excell spreadsheet
ws.Cells(1,1).Value = "hostname"
ws.Cells(1,2).Value = "GGC entry seq num"
ws.Cells(1,3).Value = "seq0"
ws.Cells(1,4).Value = "seq1"
ws.Cells(1,5).Value = "seq2"
ws.Cells(1,6).Value = "seq3"
ws.Cells(1,5).Value = "seq4"
ws.Cells(1,6).Value = "seq5"
ws.Cells(1,7).Value = "seq6"
ws.Cells(1,8).Value = "seq7"
ws.Cells(1,9).Value = "seq8"
ws.Cells(1,10).Value = "seq9"
ws.Cells(1,11).Value = "seq10"
ws.Cells(1,12).Value = "nexthop"
ws.Cells(1,12).ColumnWidth = 17
ws.Cells(1,12).Font.Bold = True
ws.Cells(1,1).Font.Bold = True
ws.Cells(1,1).ColumnWidth = 12
ws.Cells(1,2).Font.Bold = True
ws.Cells(1,2).ColumnWidth = 17


# Calling read_market_file function - gives us list of markets
markets = read_market_file()

#For each market we found in markets file try to connect to ARG21/22/23/24
# and run functions that were defined previuosly
for i in markets:
    market = re.sub("\n", "", i)
    arg_num = 1
    while arg_num < 5:
        ARG = "ARG%s2%d" % (market,arg_num)
        print '\n'
        print ARG
        ws.Cells(current_line,1).Value = ARG
        print "Following seq number used for Google description:"
        try:
            ssh.connect(ARG, username=username, password=password)
            time.sleep(1)
            remote_shell = ssh.invoke_shell()
            time.sleep(1)
            print ("SSH session established")
            # Turn off paging
            disable_paging(remote_shell)
            scope = "Google"   # <------ YOU can change word you want to use to search thru ACL here or use function raw_input to prompt user enter it from CLI !!!!!!
            # Call function find_entries to find sequence number with de
            seq_num = find_entries(scope)
            ws.Cells(current_line,2).Value = seq_num
            if seq_num != None:
                # Call functions check_seq and find_nexthop if function find_entries returned sequence number value 
                check_seq(seq_num,current_line)
                find_nexthop(current_line)
            ssh.close()
            current_line += 1
        except (socket.error, paramiko.AuthenticationException):
            status = 'fail'
            print ('Connection problem')
            pass
        arg_num += 1


sys.exit("operation completed")
    
