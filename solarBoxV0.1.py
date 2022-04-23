# by Eliseo Izazaga
# This is for solar data collection and will use two 
# joulescopes with the numpy library and will run 
# in parallel with the other model
#64.74 magic num


from sqlite3 import Timestamp
import joulescope 
import numpy as np 
import time
import datetime 
from dataclasses import dataclass
from serial import Serial 
from time import sleep
import struct

#300 is about 10 mins
#14400 would be about 3.5 hours 
#98744 would be about 24 hours 
testDuration = 2000000

durationPerReading = 30 #has to be a double, the joulescope takes a reading to compute the mean of the data
#collected 

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
        port = 'COM16'
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
        number_to_average = durationPerReading
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

def main():
    print("executing main application ")
    luxMeter = Quantum()

    deviceList = joulescope.scan(config='auto') #the joulscope library will look for the connected joulescopes and
    #return the found devices in a list as its own object

    #print(deviceList)

    #print(deviceList[0].device_serial_number)

    JS1 = deviceList[1]
    JS2 = deviceList[1]

    if deviceList[0].device_serial_number == '003248':
        JS1 = deviceList[0]
        JS2 = deviceList[1]
    else:
        JS1 = deviceList[1]
        JS2 = deviceList[0]
    #JS1.stop()
    #JS2.stop()
    #JS1.start()
    #JS2.start()

    print(JS1.device_serial_number)
    print(JS2.device_serial_number)

    header = "Time,Voltage, Current in Amps, umols,"
    MainHeader = "Time, Arlo Panel Voltage, Arlo Panel Current in Amps, Photonics Panel Voltage, Photonics Current in Amps, umols, "

    mainLog = open("SolarBoxlog.txt", "a")
    js1Log = open("JS1Log.txt" , "a")
    js2Log = open("JS2Log.txt" , "a")
    #micromoles = luxMeter.get_micromoles()#first 2 readings are bad readings. 
    #micromoles = luxMeter.get_micromoles()#issue resolved 4/23/22

    mainLog.write(header +"\n")

    js1Log.write(JS1.device_serial_number)
    js1Log.write("\n")

    js2Log.write(JS2.device_serial_number)
    js2Log.write("\n")

    js1Log.write(header + "\n")
    js2Log.write(header + "\n")

    mainLog.close
    js1Log.close
    js2Log.close

    print("Arlo,                                        Photonics,                        umols")
    OverallTime = testDuration
    while OverallTime != 0:
        #print("Recording Now")

        #take in lux reading, formula lux = micromoles * 54, record number converted before and after
        micromoles = luxMeter.get_micromoles()
        #lux = micromoles * 64.74
        #lux = micromoles * 615045 - 1196
        #lux = micromoles 
        js1Log = open("JS1Log.txt" , "a")
        js2Log = open("JS2Log.txt" , "a")
        mainLog = open("SolarBoxlog.txt", "a")
        with JS1: #this built in keyword opens the device and once it gets to the end of the "scope"
            # the device closes. 
            #print("Reading JS1")
            incomingDataStreamJS1 = JS1.read(duration=durationPerReading, contiguous_duration=None, out_format=None)
            #print("Read JS1")
        js1Current, js1Voltage = np.mean(incomingDataStreamJS1, axis=0, dtype=np.float64)

        with JS2:
            #print("Reading JS2")
            incomingDataStreamJS2 = JS2.read(duration=durationPerReading, contiguous_duration=None, out_format=None)
            #print("Read JS2")
        js2Current, js2Voltage = np.mean(incomingDataStreamJS2, axis=0, dtype=np.float64)


        timeStamp = time.time()
        timeStamp = datetime.datetime.fromtimestamp(timeStamp).strftime('%Y-%m-%d %H:%M:%S')
        timeStamp = str(timeStamp + ",")

        micromoles = str(micromoles)
        lux        = str(lux)
        js1Current = str(js1Current)
        js1Voltage = str(js1Voltage)
        js2Current = str(js2Current)
        js2Voltage = str(js2Voltage)

        if js1Current != "nan" and js2Current !="nan":

            js1Log.writelines(timeStamp + js1Voltage + "," + js1Current + "," +  micromoles + "\n")
            js2Log.writelines(timeStamp + js2Voltage + "," + js2Current + "," + micromoles + "\n")
            mainLog.writelines(timeStamp + js1Voltage + "," + js1Current + ","+ js2Voltage + "," + js2Current + "," + micromoles + "\n")
            print()
            print(js1Voltage +" , " + js1Current + " | " + js2Voltage +" , " + js2Current +"      |      "+ micromoles +str(OverallTime))
            #print(js2Voltage +" , " + js2Current)
            print("Counter at: " + str(OverallTime))

        OverallTime = OverallTime - 1
        js1Log.close
        js2Log.close
        #print(overallTime)

    js1Log.close
    js2Log.close




if __name__=="__main__":
    main()

