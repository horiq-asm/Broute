#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

import sys
import serial
import time
import datetime

rbfile = "/home/pi/test/b-route.idpwd"
rb = open(rbfile, "r")
rbid  = rb.readline().strip().replace('\n','').upper()
rbpwd = rb.readline().strip().replace('\n','').upper()
rb.close()

#print( rbid )
#print( rbpwd )
#exit(0)

#
time.sleep(10)
#
serialPortDev = '/dev/ttyUSB0'

#
ser = serial.Serial(serialPortDev, 115200)

#
ser.write("SKVER\r\n")
ser.readline()
ser.readline()

#
ser.write("SKSETPWD C " + rbpwd + "\r\n")
ser.readline()
ser.readline()

#
ser.write("SKSETRBID " + rbid + "\r\n")
ser.readline()
ser.readline()

scanDuration = 4;   #sample 6
scanRes = {} #

#
while not scanRes.has_key("Channel") :
    #
    # about 10Sec. wait
    ser.write("SKSCAN 2 FFFFFFFF " + str(scanDuration) + "\r\n")

    #
    scanEnd = False
    while not scanEnd :
        line = ser.readline()
#        print(line, end="")

        if line.startswith("EVENT 22") :
            #
            scanEnd = True
        elif line.startswith("  ") :
            #
            #
            #  Channel:39
            #  Channel Page:09
            #  Pan ID:FFFF
            #  Addr:FFFFFFFFFFFFFFFF
            #  LQI:A7
            #  PairID:FFFFFFFF
            cols = line.strip().split(':')
            scanRes[cols[0]] = cols[1]
    scanDuration+=1

    if 7 < scanDuration and not scanRes.has_key("Channel"):
        # max 14, over 7 muda
#        print("Scan retory over time")
        sys.exit()  #### END ####

#
ser.write("SKSREG S2 " + scanRes["Channel"] + "\r\n")
ser.readline()
ser.readline()

#
ser.write("SKSREG S3 " + scanRes["Pan ID"] + "\r\n")
ser.readline()
ser.readline()
# MAC address (64bit)toIPV6 link local address convert
# (BP35A1)
ser.write("SKLL64 " + scanRes["Addr"] + "\r\n")
ser.readline()
ipv6Addr = ser.readline().strip()
#print(ipv6Addr)

# PANA connect start
ser.write("SKJOIN " + ipv6Addr + "\r\n");
ser.readline()
ser.readline()

# PANA connected
bConnected = False
while not bConnected :
    line = ser.readline()
#    print(line, end="")
    if line.startswith("EVENT 24") :
#        print("PANA connect error")
        pinrt("0")
        print("999")
        sys.exit()  #### END ####
    elif line.startswith("EVENT 25") :
        # connect succeed
        bConnected = True

#
ser.timeout = 2

#
# (ECHONET-Lite_Ver.1.12_02.pdf p.4-16)
ser.readline()

# ECHONET Lite Flame create
#
# CHONET-Lite_Ver.1.12_02.pdf (EL)
# Appendix_H.pdf (AppH)
echonetLiteFrame = ""
echonetLiteFrame += "\x10\x81"      # EHD (EL p.3-2)
echonetLiteFrame += "\x00\x01"      # TID (EL p.3-3)
echonetLiteFrame += "\x05\xFF\x01"  # SEOJ (EL p.3-3 AppH p.3-408)
echonetLiteFrame += "\x02\x88\x01"  # DEOJ (EL p.3-3 AppH p.3-274)

echonetLiteFrame += "\x62"          # ESV(62:) (EL p.3-5)
echonetLiteFrame += "\x03"          # OPC(1)(EL p.3-7)
echonetLiteFrame += "\xE7"          # EPC(EL p.3-7 AppH p.3-275)
echonetLiteFrame += "\x00"          # PDC(EL p.3-9)
echonetLiteFrame += "\xE0"          # EPC(EL p.3-7 AppH p.3-275)
echonetLiteFrame += "\x00"          # PDC(EL p.3-9)
echonetLiteFrame += "\xE3"          # EPC(EL p.3-7 AppH p.3-275)
echonetLiteFrame += "\x00"          # PDC(EL p.3-9)
command = "SKSENDTO 1 {0} 0E1A 1 {1:04X} {2}".format(ipv6Addr, len(echonetLiteFrame), echonetLiteFrame)

E0 = 0
E7 = 0
E3 = 0
#d = datetime.datetime.today()
#loop = 5 - (d.minute % 5)
loop = 1

while loop:

#    d = datetime.datetime.today()
#    time.sleep(60-d.second)
    loop -= 1

    #Send command
    ser.write(command)
#    print("SKSENDTO")

    lop2 = 5
    while lop2 :
        line = ser.readline()
#       print(line, end="")

        if line.startswith("ERXUDP") :
            cols = line.strip().split(' ')
            res = cols[8]   # UDP recieve data
            #tid = res[4:4+4];
            seoj = res[8:8+6]
            deoj = res[14:14+6]
            ESV = res[20:20+2]
            OPC = res[22:22+2]

            if deoj == "05FF01" and seoj == "028801" and ESV == "72" and OPC == "03" :
                EPC = res[24:24+2]
                if EPC == "E7" :
                    hexPower = res[28:28+8]
                    intPower = int(hexPower, 16)
                    E7 = intPower
#                    print(u"{0}".format(intPower))
                    EPC = res[36:36+2]
                    if EPC == "E0" :
                        hexPower = res[40:40+8]
                        intPower = int(hexPower, 16)
                        if E0 < intPower :
                            E0 = intPower
#                        print(u"{0}".format(intPower))
                        EPC = res[48:48+2]
                        if EPC == "E3" :
                            hexPowerSel = res[52:52+8]
                            intPowerSel = int(hexPowerSel, 16)
                            if E3 < intPowerSel :
                                E3 = intPowerSel
#                            print(u"{0}".format(intPowerSel))
                            lop2 = 0

ser.close()
if  E7 > 16777216 :
    intPowerSel = 4294967296 - E7
    E7 = 0
else :
    intPowerSel = 0
print( "BRT"+cols[1]+" ", end="")
print( "{0} {1} {2} {3}".format(E0,E7,E3,intPowerSel))
