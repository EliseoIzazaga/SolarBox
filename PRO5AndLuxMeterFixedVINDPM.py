#Eliseo Izazaga
import time
#this application will chart and plot the battery charging mechanism in the GEN 5 cameras through the
#serial port and matplotlib
import sys
import glob
import serial
from sqlite3 import Timestamp
from typing import Any

import numpy as np 
import time
import datetime 
from dataclasses import dataclass
from serial import Serial 
from time import sleep
import struct




GET_VOLT = '\x55!'.encode('utf-8')
READ_CALIBRATION = '\x83!'.encode('utf-8')
SET_CALIBRATION = '\x84%s%s!'.encode('utf-8')
READ_SERIAL_NUM = '\x87!'.encode('utf-8')
GET_LOGGING_COUNT = '\xf3!'.encode('utf-8')
GET_LOGGED_ENTRY = '\xf2%s!'.encode('utf-8')
ERASE_LOGGED_DATA ='\xf4!'.encode('utf-8')

class Quantum(object):
    

    def __init__(self):
        #initializes the varaibles and connects to device
        self.quantum = None
        self.offset = 0.0
        self.multiplier = 0.0 
        self.connect_to_device()


    def connect_to_device(self):
        #connect via COM serial port
        port = 'COM19'
        self.quantum = Serial(port, 115200, timeout = 0.5)
        try:
            #self.quantum.write(SET_CALIBRATION)
            #self.quantum.write(READ_CALIBRATION)
            #multiplier = self.quantum.read(5)[1:]
            #print(multiplier)
            #offset = self.quantum.read(4)
            #self.multiplier = struct.unpack('<f', multiplier)[0]
            #self.offset = struct.unpack('<f',offset)[0]
            print("Apogee instrument connected ")
        except(IOError,struct.Error) as data:
            print(data)
            self.quantum = None
        


    def get_micromoles(self):
        #converts voltage into micro moles
        voltage = self.read_voltage()
        #print(voltage)
        #print(self.offset)
        #print(self.multiplier)
        if voltage == 9999:
            #raise exception maybe
            print("crazy reading, try again")
            return
        #the following line converts volts to micromoles
        ##micromoles = (voltage - self.offset) * self.multiplier * 1000
        micromoles = (voltage * 9117.8) - 4.6363
        #print(micromoles)
        if micromoles < 0:
            micromoles = 0
        return micromoles


    def read_voltage(self):
        #this function will average 5 readings over one second of time 
        if self.quantum == None:
            try:
                self.connect_to_device()
            except IOError: 
                #exception raised 
                return
        #this stores the responses into a list to calculate average
        response_list = []
        #change to average more or less samples over the given time period
        number_to_average = 50
        #change to shorten or extend the time duration over the given time period
        number_of_seconds = 1.0    

        for i in range(number_to_average):
            try:
                self.quantum.write(GET_VOLT)
                response = self.quantum.read(5)[1:]
            except IOError as data:
                print(data)
                #something about a dummy value to know when something went wrong 
                return 9999
            else:
                if not response:
                    continue
                #if the response is not 4 bytes long, this like will raise and exception
                voltage = struct.unpack('<f', response)[0]
                response_list.append(voltage)
                sleep(number_of_seconds/number_to_average)
            if response_list:
                return sum(response_list)/len(response_list)
            return 0.0


def sanitizePMData(dirtyPMdata):
    #print("***************8 start sanitization*********************")
    #print("\n")
    #print("\n")
    #print("\n")
    #print(dirtyPMdata)
    #print("\n")
    #print("\n")
    #print("\n")

    toReturn = dirtyPMdata.split('$')

    #print("***************8 split and indexed at 1*********************")
    #print("\n")
    #print("\n")
    #print("\n")
    toReturn = str(toReturn[1])
    #print(toReturn)
    return toReturn

def sub100mV(hexIn):
    ret = int(hexIn, 16)
    ret = hex(ret)
    ret = bin(int(ret,16))
    ret = ret.split("b")
    ret = str(ret[1])
    onebit = "00000001"
    ret = bin(int(ret, 2) - int(onebit, 2))
    ret = int(ret, 2)
    ret = hex(ret)
    ret = str(ret)
    return ret

def add100mV(hexIn):
    ret = int(hexIn, 16)
    ret = hex(ret)
    ret = bin(int(ret,16))
    ret = ret.split("b")
    ret = str(ret[1])
    onebit = "00000001"
    ret = bin(int(ret, 2) + int(onebit, 2))
    ret = int(ret, 2)
    ret = hex(ret)
    ret = str(ret)
    return ret
    

def serial_ports():
    """
    Successfully tested on Windows 8.1 x64
    Windows 10 x64
    Mac OS X 10.9.x / 10.10.x / 10.11.x
    Ubuntu 14.04 / 14.10 / 15.04 / 15.10
    with both Python 2 and Python 3


         Lists serial port names

        :raises EnvironmentError:
            On unsupported or unknown platforms
        :returns:
            A list of the serial ports available on the system
    """
    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in range(256)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        # this excludes your current terminal "/dev/tty"
        ports = glob.glob('/dev/tty[A-Za-z]*')
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')
    else:
        raise EnvironmentError('Unsupported platform')

    result = []
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            result.append(port)
        except (OSError, serial.SerialException):
            pass
    return result

def openSerialPort(COMDEVICENUMBER):
    """This function opens a new port and returns it in the main body of the application"""
    #encodedComPort = str(COMDEVICENUMBER)
    newport = serial.Serial(port=COMDEVICENUMBER, baudrate=115200, parity="N", stopbits=1, bytesize=8, timeout=0.1)
    print("Opened " + newport.portstr)
    return newport

def utilityBatteryFunction(targetCam):  #will return pm 05 data in a comma delimited list, the list will become string then written to the file, 
    #targetCam.flush()
    #print("command sent: " + "pm 05")
    data = targetCam.read(500)
    #print(data)
    stringData = str(data)
    #print(stringData)
    while(stringData.find('$') == -1):
        #print("in first loop")
        data = targetCam.read_until('\n') #reads until new line 
        #print(data)
        stringData = str(data)
        #print(stringData)
    if(stringData.find('$') != -1): #when dollar sign is found prints good data and returns ot
        #print("good Data")
        #print(stringData)
        return stringData          #returns good data as a string for later processing. 
    
def sendCMDToEFR(targetCam, commandIn):
    #print("sendCMDtoEFR "+ commandIn)
    targetCam.reset_input_buffer()
    targetCam.reset_output_buffer()
    time.sleep(0.1)
    targetCam.write('\r'.encode('ASCII'))
    targetCam.reset_input_buffer()
    targetCam.reset_output_buffer()
    time.sleep(0.1)
    targetCam.write('\r'.encode('ASCII'))
    targetCam.reset_input_buffer()
    targetCam.reset_output_buffer()
    time.sleep(0.1)
    targetCam.write('\r'.encode('ASCII'))
    targetCam.reset_input_buffer()
    targetCam.reset_output_buffer()
    #targetCam.flush()
    
    targetCam.write(commandIn.encode('utf-8'))
    time.sleep(0.3)
    targetCam.write('\r'.encode('ASCII'))
    targetCam.reset_input_buffer()
    targetCam.reset_output_buffer()
    #print(commandIn)
    #print(targetCam.readline())

def configBQregValues(targetCam, regValuesIn):
    #print("********************SENDING REG VALUES****************")
    sendCMDToEFR(targetCam, regValuesIn)
    dataOut = targetCam.read(62)
    dataOut = str(dataOut)
    #print(dataOut)
    while(dataOut.find('Su') == -1):
        sendCMDToEFR(targetCam, regValuesIn)
        dataOut = targetCam.read(60)
        dataOut = str(dataOut)
        #print(dataOut)

def readBQregValues(targetCam, regValuesIn):
    #print("**************8 READING REG VALUES***************")
    sendCMDToEFR(targetCam, regValuesIn)
    dataOut = targetCam.read(62)
    dataOut = str(dataOut)
    #print(dataOut)
    while(dataOut.find('data') == -1):
        sendCMDToEFR(targetCam, regValuesIn)
        dataOut = targetCam.read(60)
        dataOut = str(dataOut)
        #print(dataOut)
    dataOut = dataOut.split("data:")
    #print(dataOut[1])
    dataOut = dataOut[1]
    #print(dataOut)
    dataOut = str(dataOut)
    dataOut = dataOut.split('\\r')
    #print(dataOut[0])
    return str(dataOut[0])



if __name__ == '__main__':
    TESTCAM1 = openSerialPort("COM10")
    TESTCAM2 = openSerialPort("COM14")
    print("Starting Main Application: ")
    luxMeter = Quantum()
    mainLogGEN5 = open("VINDMP SOLAR TEST WITH GEN5 PANEL v2 fixed VINDPM.txt", "a")
    mainLogVENDOR = open("VINDMP SOLAR TEST WITH VENDOR PANEL v2 fixed VINDPM.txt", "a")
    mainHeader = "Time,BAT_TYPE,CHG_TYPE,PM_ST,SYS_ST,VOLT,TEMP,PERC,BAT_CURR,INPUT_CURR,VBUS,INPUT_VOLT,VBATT,CHG_VOLT,CHG_CURR,CHG_STATUS,OP_STATUS,JEITA_VOLT,JEITA_CURR,IMAX,TrueRemQ,micromoles,HEX READ FROM REG0D,HEX SENT TO REG0D/VINDPM, \n" # needs to be replaced with proper header
    mainLogGEN5.write(mainHeader)
    mainLogVENDOR.write(mainHeader) 
    #micromoles = luxMeter.get_micromoles()
    #micromoles = f"{micromoles:4f}"

    sendCMDToEFR(TESTCAM1, "pm 05")
    sendCMDToEFR(TESTCAM2, "pm 05")
    time.sleep(3)

    pmDataCam1 = utilityBatteryFunction(TESTCAM1)
    pmDataCam2 = utilityBatteryFunction(TESTCAM2)
    #print(pmData)
    pmDataCam1 = sanitizePMData(pmDataCam1)
    pmDataCam2 = sanitizePMData(pmDataCam2)
    #print(pmData)
    #tempPMData = str(pmDataCam1).split(",") #needs just IBAT
    #print(tempPMData)
    #IBATTold = int(tempPMData[7])
    #VBUSold = int(tempPMData[9])
    #print("vbus old pos 9 " +str(VBUSold))
    #powerold = IBATTold * VBUSold
    #print(powerold)
    VINDPM = "0xa0"
    timeStamp = time.time()
    timeStamp = datetime.datetime.fromtimestamp(timeStamp).strftime('%Y-%m-%d %H:%M:%S')
    timeStamp = str(timeStamp + ",")
    micromoles = luxMeter.get_micromoles()
    micromoles = f"{micromoles:4f}"
    reg0D = readBQregValues(TESTCAM1, "rbq 0x0d")
    #powerNew = powerold #power new not yet set
    mainLogGEN5.write(timeStamp + pmDataCam1+ "," + str(micromoles)+ "," + reg0D + "," + VINDPM + "," +  "\n")
    mainLogVENDOR.write(timeStamp + pmDataCam2+ "," + str(micromoles)+ "," + reg0D + "," + VINDPM + "," + "\n")
    configBQregValues(TESTCAM1, "wbq 0x0d "+VINDPM)
    mainLogGEN5.close()
    mainLogVENDOR.close()
    while(True):
        #print("inside true statement")
        mainLogGEN5 = open("VINDMP SOLAR TEST WITH GEN5 PANEL v2 fixed VINDPM.txt", "a")
        mainLogVENDOR = open("VINDMP SOLAR TEST WITH VENDOR PANEL v2 fixed VINDPM.txt", "a")
        counter = 0
        while(counter <= 10):
            micromoles = luxMeter.get_micromoles()
            micromoles = f"{micromoles:4f}"
            print(micromoles)
            time.sleep(1)
            counter = counter  + 1
        #time.sleep(10)
        pmDataCam1 = utilityBatteryFunction(TESTCAM1)
        pmDataCam2 = utilityBatteryFunction(TESTCAM2)
        #print(pmData)
        pmDataCam1 = sanitizePMData(pmDataCam1)
        pmDataCam2 = sanitizePMData(pmDataCam2)
        #print(pmData)
        #tempPMdataNew = str(pmData).split(",") #needs just IBAT
        #print(IBATTnew)
        #IBATTnew = int(tempPMdataNew[7])
        #VBUSnew = int(tempPMdataNew[9])
        #powerNew = IBATTnew * IBATTnew
        #print("Calculated newpower: "+str(powerNew))
        timeStamp = time.time()
        timeStamp = datetime.datetime.fromtimestamp(timeStamp).strftime('%Y-%m-%d %H:%M:%S')
        timeStamp = str(timeStamp + ",")
        micromoles = luxMeter.get_micromoles()
        micromoles = f"{micromoles:4f}"
        #print(micromoles)
        #reg0D 
        reg0Dcam1 = readBQregValues(TESTCAM1, "rbq 0x0d")
        reg0Dcam2 = readBQregValues(TESTCAM2, "rbq 0x0d")
        mainLogGEN5.write(timeStamp + pmDataCam1+ "," + str(micromoles)+ "," + reg0Dcam1 + "," + VINDPM + "," +  "\n")
        mainLogVENDOR.write(timeStamp + pmDataCam2+ "," + str(micromoles)+ "," + reg0Dcam2 + "," + VINDPM + "," + "\n")
        mainLogGEN5.close()
        mainLogVENDOR.close()



        #if(powerNew >= powerold and IBATTnew > 0):
        #    VINDPM = add100mV(VINDPM)
        #    print("incremented "+VINDPM)
        #    configBQregValues(TESTCAM1, "wbq 0x0d "+VINDPM)
        #    powerold = powerNew
        #    mainLog.write(VINDPM + "," +str(powerold)+ "\n")
        #else:
        #    VINDPM = sub100mV(VINDPM)
        #    print("decremented "+VINDPM)
        #    configBQregValues(TESTCAM1, "wbq 0x0d "+VINDPM)
        #    powerold = powerNew
        #    mainLog.write(VINDPM + ","+str(powerold)+ "\n")
        mainLogGEN5.close()
        mainLogVENDOR.close()


    
    
    #listofSerPorts = serial_ports()
    #print(listofSerPorts)
    #testCommand = 'pm'.encode('utf-8') + '\r'.encode('ascii')
    #TESTCAM1.write(testCommand)
    #print(TESTCAM1.read(100))
    #TESTCAM1.reset_input_buffer()
    #TESTCAM1.reset_output_buffer()
    #getBatteryData(TESTCAM1)
    #sendCMDToEFR(TESTCAM1, "wbq 0x0d 0xa2")
    #sendCMDToEFR(TESTCAM1, "wbq 0x0d 0xa2")
    #sendCMDToEFR(TESTCAM1, "wbq 0x0d 0xa2")
    #configBQregValues(TESTCAM1, "wbq 0x0d 0xa3")
    #sendCMDToEFR(TESTCAM1, "pm 05")