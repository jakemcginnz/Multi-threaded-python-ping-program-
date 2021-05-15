from socket import *
import os
import sys
import struct
import time
import select
import binascii  

ICMP_ECHO_REQUEST = 8



def MyChecksum(hexlist):
    summ=0
    carry=0
    for i in range(0,len(hexlist),2):
        summ+=(hexlist[i]<< 8)  + hexlist[i+1]
        carry=summ>>16
        summ=(summ & 0xffff)  + carry
        #print(str(hex((hexlist[i]<< 8)  + hexlist[i+1]))+" "+str(hex(summ)) + "  " +str(hex(carry)) + " " + str(hex(summ^0xffff)))

    while( summ != (summ & 0xffff)):
        carry=summ>>16
        summ=summ & 0xffffffff  + carry
        #print("loop loop")

    summ^=0xffff #invert it
    return summ



def checksum(string): 
    csum = 0
    countTo = (len(string) // 2) * 2  
    count = 0

    while count < countTo:
        thisVal = ord(string[count+1]) * 256 + ord(string[count]) 
        csum = csum + thisVal 
        csum = csum & 0xffffffff  
        count = count + 2
    
    if countTo < len(string):
        csum = csum + ord(string[len(string) - 1])
        csum = csum & 0xffffffff 
    
    csum = (csum >> 16) + (csum & 0xffff)
    csum = csum + (csum >> 16)
    answer = ~csum 
    answer = answer & 0xffff 
    answer = answer >> 8 | (answer << 8 & 0xff00)
    #print(hex(answer))
    #print(hex(checksum0(string)))
    return answer
    
def receiveOnePing(mySocket, ID, timeout, destAddr):
    timeLeft = timeout
    while 1: 
        startedSelect = time.time()
        whatReady = select.select([mySocket], [], [], timeLeft)
        howLongInSelect = (time.time() - startedSelect)
        if whatReady[0] == []: # Timeout
            return "Request timed out."
    
        timeReceived = time.time() 
        recPacket, addr = mySocket.recvfrom(1024)
        rtt = 0
        #Fetch the ICMP header from the IP packet
        #Header is type (8), code (8), checksum (16), id (16), sequence (16)
        #ICMP header starts at bit 160 so recPacket[20]
        
        #type and code must be set to 0
        
        #The identifier and sequence number can be used by the client to determine which
        #echo requests are associated with the echo replies.

        #The identifier and sequence number can be used by the client to determine which
        #echo requests are associated with the echo replies.
        
        type, code, checksum, id, sequence = struct.unpack("bbHHh", recPacket[20:28])
        if (type == 0 and code == 0 and id == ID):
            #send time of packet
            send_time = struct.unpack("d", recPacket[28:])
            #Calculate round trip time
            rtt = (timeReceived - send_time[0]) * 1000
        else:
            #Error message describing what fields are not as expected
            return "Header error!\nexpexted type = 0, code = 0, id = "+ str(ID)+"\nrecieved type = "+ str(type) +", code = "+ str(code) +", id = "+ str(id) 
        
        #Confirm checksum of whole packet is 0
        header = struct.pack("bbHHh", type, code, checksum, id, sequence)
        data = struct.pack("d", send_time[0])
        myChecksum = MyChecksum ([i for i in header] + [i for i in data])
        if myChecksum == 0:
            #everything checks out
            return rtt
        else:
            return "Error! Incorrect checksum"
        timeLeft = timeLeft - howLongInSelect
        if timeLeft <= 0:
            return "Request timed out."
    
def sendOnePing(mySocket, destAddr, ID):
    # Header is type (8), code (8), checksum (16), id (16), sequence (16)
    
    myChecksum = 0
    
        # Make a dummy header with a 0 checksum
    # struct -- Interpret strings as packed binary data
    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, myChecksum, ID, 1)
    data = struct.pack("d", time.time())
    
    # Calculate the checksum on the data and the dummy header.
    #myChecksum = checksum(str(header + data))
    myChecksum = MyChecksum ([i for i in header] + [i for i in data])
    # Get the right checksum, and put in the header
    if sys.platform == 'darwin':
        # Convert 16-bit integers from host to network  byte order
        myChecksum = htons(myChecksum) & 0xffff     
    else:
        myChecksum = htons(myChecksum)
        
    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, myChecksum, ID, 1)
    packet = header + data
    
    mySocket.sendto(packet, (destAddr, 1)) # AF_INET address must be tuple, not str
    # Both LISTS and TUPLES consist of a number of objects
    # which can be referenced by their position number within the object.
    
    
def doOnePing(destAddr, timeout): 
    icmp = getprotobyname("icmp")
    # SOCK_RAW is a powerful socket type. For more details:   http://sock-raw.org/papers/sock_raw

    mySocket = socket(AF_INET, SOCK_RAW, icmp)
    
    myID = os.getpid() & 0xFFFF  # Return the current process i
    sendOnePing(mySocket, destAddr, myID)
    delay = receiveOnePing(mySocket, myID, timeout, destAddr)
    
    mySocket.close()
    return delay
    
def ping(host, timeout=1):
    # timeout=1 means: If one second goes by without a reply from the server,
    # the client assumes that either the client's ping or the server's pong is lost
    dest = gethostbyname(host)
    print("Pinging " + dest + " using Python:")
    print("")
    # Send ping requests to a server separated by approximately one second
    while 1 :
        delay = doOnePing(dest, timeout)
        print(delay)
        time.sleep(1)# one second
    return delay
ping("www.google.com")
