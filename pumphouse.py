#! /opt/pumphouse/env/bin/python

import tkinter as tk
import requests
import time
import signal
import sys
import RPi.GPIO as GPIO
import datetime
import json
import sqlite3
import smbus2
import bme280
import subprocess
import queue
import threading

from tkinter import *
from levelbar import LevelBar

import board


import busio

import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

from ina219 import INA219
from ina219 import DeviceRangeError

from site_keys import location ##local secrets used throughout

# communiction protocol for sensors
i2c = busio.I2C(board.SCL, board.SDA)

# air temperature, pressure, and humidity sensor
addr = 0x77
bus = smbus2.SMBus(1)
calibration_params = bme280.load_calibration_params(bus,addr)

#A/D converter for pump power and water pressure sensing
ads = ADS.ADS1115(i2c)
ads.gain=1
adc1 = AnalogIn(ads,ADS.P0)
adc2 = AnalogIn(ads,ADS.P1)
adc3 = AnalogIn(ads,ADS.P2)
adc4 = AnalogIn(ads,ADS.P3)

# current reader for water level reading
SHUNT_OHMS = 0.1
MAX_EXPECTED_AMPS = 0.2
ina = INA219(SHUNT_OHMS, MAX_EXPECTED_AMPS, busnum=1)
ina.configure(ina.RANGE_16V)

# Digital input to motion interrupt
GPIO_MOTION = 6

# Digital output relay 1-4
GPIO_R1 = 4
GPIO_R2 = 5
GPIO_R3 = 7
GPIO_R4 = 8


## State Variables
wellPumpCurrent = 0
mainPumpCurrent = 0
mainSecondsRemaining = 0

adc1Sent = 0
adc1Sum = 0
lastAdc1 = 0

adc2Sent = 0
adc2Sum = 0
lastAdc2 = 0

adc3Sent = 0
adc3Sum = 0
lastAdc3 = 0

adc4Sent = 0
adc4Sum = 0
lastAdc4 = 0

pressureSent = 0
pressureSum = 0

humiditySent = 0
humiditySum = 0

temperatureSent = 0
temperatureSum = 0
lastTemperature = 0

levelSent = 0
levelSum = 0
lastLevel = 0

voltageSent = 0
voltageSum = 0

## Variables from the server
well_pump_on = 0
shown_well_pump_on = 0
main1_pump_on = 0
shown_main2_pump_on = 0
main2_pump_on = 0
shown_main2_pump_on = 0

## 
shown_time="00:00:00"
current_time = "00:00:00"
movements = 0
shown_movements = 0
sample_count = 0
pump_seconds_remaining=0;
last_server_contact="booting"
shown_server_contact="booting"
last_server_command = ""
shown_server_command = ""
last_status_to_server = ""
shown_last_status_to_server = ""

#def keep_window_focused(window):
#    window.focus_force()
#    window.after(100, lambda: keep_window_focused(window))

busCurrentFault = 0

waterPressureFault = 0

def get_wifi_ssid():
    try:
        ssid=subprocess.check_output(['iwgetid', '-r']).decode('utf-8').strip()
        return ssid
    except subproces.CalledProcessError:
        return "Error"
    
def on_closing():
    GPIO.output(GPIO_R1,0)
    GPIO.output(GPIO_R3,0)
    GPIO.output(GPIO_R2,0)
    GPIO.output(GPIO_R4,0)
    GPIO.cleanup()
    window.destroy()

def motion_callback(channel):
    global movements
    movements += 1

def pollADC(chanel):
    i = 5
    sum = 0.0
    while(i > 0):
        sum = sum + abs(chanel.voltage)
        i = i-1
    return sum

def poll_BME280():
    global temperatureSum, pressureSum, humiditySum, calibrationParams, addr, lastTemperature
    data = bme280.sample(bus, addr, calibration_params)
    lastTemperature = (9.0/5.0 * data.temperature) + 32
    temperatureSum += lastTemperature
    pressureSum += data.pressure
    humiditySum += data.humidity
    

def pollSensors():
    global sample_count, adc1Sum, adc2Sum, adc3Sum, adc4Sum, wellPumpCurrent, mainPumpCurrent, lastAdc4, lastAdc3, lastAdc2, lastAdc1, lastLevel, lastVoltage, ina, levelSum, voltageSum, busCurrentFault, waterPressureFault
    #pull data and add to sum
    #--> measure wellpump current
    lastAdc4 = pollADC(adc4)
    if lastAdc4 > 0.5 and wellPumpCurrent == 0:
        print("sending alert")
        sendEventToCloud("wellPumpStart")
        wellPumpCurrent=1
    if lastAdc4 < 0.1 and wellPumpCurrent == 1:
        print("sending alert")
        sendEventToCloud("wellPumpStop")        # send notification to server
        wellPumpCurrent=0
    adc4Sum += lastAdc4

    #--> measure main pump current
    lastAdc3 = pollADC(adc3)
    if lastAdc3 > 0.5 and mainPumpCurrent == 0:
        print("sending alert")
        sendEventToCloud("mainPumpStart")
        mainPumpCurrent=1
    if lastAdc3 < 0.1 and mainPumpCurrent == 1:
        print("sending alert")
        sendEventToCloud("mainPumpStop")        # send notification to server
        mainPumpCurrent=0
    adc3Sum += lastAdc3

    lastAdc1 = pollADC(adc1) # check for high water pressure and report for now
    if lastAdc1 < 13.1 and waterPressureFault == 1:
        sendEventToCloud("highWaterPressureResolved")
        waterPressureFault = 0
    if lastAdc1 > 13.3 and waterPressureFault == 0:
        sendEventToCloud("highWaterPressureFault")
        waterPressureFault = 1
    adc1Sum += lastAdc1

    lastAdc2 = pollADC(adc2)
    adc2Sum += lastAdc2

    lastVoltage = ina.voltage()
    voltageSum += lastVoltage
    try:
        lastLevel = ina.current()
        levelSum += lastLevel
        busCurrentFault = 0
    except DeviceRangeError as e:
        if busCurrentFault == 0:
            sendEventToCloud("busCurrentFault:" + e)
        busCurrentFault = 1
    
    poll_BME280()

    sample_count += 1

def generateAverages():
    global sample_count, adc1Sum, adc2Sum, adc3Sum, adc4Sum, adc1Sent, adc2Sent, adc3Sent, adc4Sent, temperatureSum, pressureSum, humiditySum, temperatureSent, pressureSent, humiditySent, voltageSent, voltageSum, levelSent, levelSum
    adc1Sent = adc1Sum / sample_count
    adc2Sent = adc2Sum / sample_count
    adc3Sent = adc3Sum / sample_count
    adc4Sent = adc4Sum / sample_count
    levelSent = levelSum / sample_count
    voltageSent = voltageSum / sample_count
    humiditySent = humiditySum / sample_count
    temperatureSent = temperatureSum / sample_count
    pressureSent = pressureSum / sample_count
    sample_count = 0
    adc1Sum = 0
    adc2Sum = 0
    adc3Sum = 0
    adc4Sum = 0
    levelSum = 0
    voltageSum = 0
    humiditySum = 0
    temperatureSum = 0
    pressureSum = 0
    
def tick():
    global shown_time, shown_movements, movements, alarm, canvas2, window, pump_seconds_remaining, last_server_contact, last_contact_id, shown_server_contact, current_time, last_server_command, shown_server_command, last_status_to_server, shown_last_status_to_server
    
    alarm = window.after(1000, tick)#assign the alarm to a variable
    current_time = datetime.datetime.now().strftime("%H:%M:%S")
    if shown_time != current_time:
        canvas2.itemconfigure(time_id,text=current_time)  #clock.configure(text=current_time)
        shown_time = current_time

    if shown_movements != movements:
        canvas2.itemconfigure(move_id,text=movements)
        shown_movements = movements

    if last_server_contact != shown_server_contact:
        canvas2.itemconfigure(last_contact_id,text=last_server_contact)
        shown_server_contact = last_server_contact

    if last_server_command != shown_server_command:
        canvas2.itemconfigure(last_command_id,text=last_server_command)
        shown_server_command = last_server_command

    if last_status_to_server != shown_last_status_to_server:
        canvas2.itemconfigure(last_status_id,text=last_status_to_server)
        shown_last_status_to_server = last_status_to_server
        
    seconds = datetime.datetime.now().strftime("%S")
    s = int(seconds)
    if(s % 5 == 0):
        pollSensors()
        
    minutes = datetime.datetime.now().strftime("%M")
    m = int(minutes)
    if(m % 5 == 0 and s == 0):  #every 5 minutes, on the 5 minute mark
        generateAverages()
        sendToCloud()
        movements = 0

    if(pump_seconds_remaining > 0):
        pump_seconds_remaining -= 1
        canvas2.itemconfigure(pump_time_id,text=pump_seconds_remaining)
        if(pump_seconds_remaining == 0):
            pump_off()
        
    return None


#def stop():
#    stop.after_cancel(alarm) #cancel alarm

    
#def pumpOn():
#    global movements, movements, secrets 
#    token = secrets['API_KEY']
#    url = secrets['SERVER']
#    data= {'token': token, 'action': 'buttonpress', 'pump': 'on'}
#    response = requests.post(url,data)
#    if response.status_code == 200:
#        canvas2.itemconfigure(stat_id,text=response.text)
#    else:
#        canvas2.itemconfigure(stat_id,text=f"Failed with status: {response.status_code}")

def sendToCloud():
    global last_server_contact, shown_time, current_time, last_server_command, last_status_to_server, pressureSent, temperatureSent, humiditySent, voltageSent, levelSent,adc1Sent,adc2Sent,adc3Sent,adc4Sent,secrets
    token = secrets['API_KEY']
    url = secrets['SERVER']
    now = datetime.datetime.now()
    timestamp = now.timestamp()
    d = json.dumps({'status':'update','timestamp':timestamp, 'movements': movements, 'adc1': adc1Sent, 'adc2': adc2Sent, 'adc3': adc3Sent, 'adc4': adc4Sent, 'temperature': temperatureSent, 'pressure': pressureSent, 'humidity': humiditySent, 'voltage': voltageSent, 'depth': levelSent})

    background = threading.Thread(target=transmit, args=(d,))
    background.daemon = True # should send even if main thread stops
    background.start()
    


def is_index_set(array,index):
    return 0 <= index < len(array)

def sendEventToCloud(event):
    global last_server_contact, shown_time, current_time, last_status_to_server, well_pump_on, shown_well_pump_on, main1_pump_on, shown_main1_pump_on, main2_pump_on, shown_main2_pump_on,server
  #  print("In sendEventToCloud")
    token = secrets['API_KEY']
    url = secrets['SERVER']
    now = datetime.datetime.now()
    timestamp = now.timestamp()
    d = json.dumps({'timestamp':timestamp, 'status': 'event', 'notification': event })
    background = threading.Thread(target=transmit, args=(d,))
    background.daemon = True # should send even if main thread stops
    background.start()


def sendBootToCloud():
    #don't send using transmit worker, we need initial display paramaters from the server
    token = secrets['API_KEY']
    url = secrets['SERVER']
    d = json.dumps({'notification': 'boot' })
    now = datetime.datetime.now()
    timestamp = now.timestamp()
    item = json.dumps({'timestamp':timestamp, 'status': 'event', 'notification': 'boot' })
    data= {'token': token, 'data': item}
    response = requests.post(url,data)
    if response.status_code == 200:
        print(response.text)
        sdata = json.loads(response.text)
        print(sdata)
        return sdata
    else:
        insert = json.dumps(data)
        print(insert)
        cursor.execute("INSERT INTO events ( payload ) VALUES (?)",(insert,))
        connect.commit()

def pump_timer(time):
    global pump_seconds_remaining
    pump_on();
    pump_seconds_remaining = time

def pump_button():
    pump_timer(300)
    pump_seconds_remaining = 300
    
def pump_on():
    global canvas2, pump_id
    GPIO.output(GPIO_R4,0)
    pump_id.config(text='Pump Off')
    pump_id.config(command=pump_off)
    pump_id.config(bg='red')
    pump_id.config(activebackground='red')
    
def pump_off():
    global canvas2, pump_id, pump_seconds_remaining
    GPIO.output(GPIO_R4,1)
    pump_id.config(text='Pump On')
    pump_id.config(activebackground='green')
    pump_id.config(bg='green')
    pump_id.config(command=pump_button)
    pump_seconds_remaining=0
    canvas2.itemconfigure(pump_time_id,text=pump_seconds_remaining)


    
## 
####
####
####  BACKGROUND WORKER THREAD to send data to server and repaint screen data
####
####

def transmit(data):
    global secrets, last_status_to_server, last_server_contact, current_time
    token = secrets['API_KEY']
    while True:
        url = secrets['SERVER']
        print ("initiating server contact.")
        packet = {'token': token, 'data': data}
        d = json.loads(data)
        try:
            response = requests.post(url,packet)
            if response.status_code == 200:
                print (d)
                if d['status'] == 'update' :
                    last_status_to_server = 'update'
                    print("setting last_status_to_server to update")
                  
                if d['status'] == 'event' :
                    last_status_to_server = d['notification']
                    print("setting last_status_to_server to notification")
                last_server_contact = current_time
                print("Got an 200 return code")
                print(response.text)
                sdata = json.loads(response.text)
                if "action" in sdata:
                    if sdata['action'] == 'pump_on':
                        pump_timer(int(sdata['pump_time']))
                        last_server_command = current_time + ': pump_on: ' + str((int(sdata['pump_time'])))
                        if sdata['action'] == 'pump_off':
                            pump_off()
                            last_server_command = current_time + ': pump_off'
                levelbar1.update_levels(canvas,sdata['LOC1'])
                levelbar2.update_levels(canvas,sdata['LOC2'])
                break
            else:
                # Bad return code, wtf - server error? Nothing we can do.
                print (f"Server: bad return status: {response.status_code}. Retrying...")
                
        except:
            
            # do the send, paintscreen and die on success
            print ("Send failed. Retrying...")
            time.sleep(5)
    # end loop 
#end transmit() background worker

####
####
####  MAIN THREAD
####
####
GPIO.setmode(GPIO.BCM)
GPIO.setup(GPIO_R1, GPIO.OUT)
GPIO.setup(GPIO_R2, GPIO.OUT)
GPIO.setup(GPIO_R3, GPIO.OUT)
GPIO.setup(GPIO_R4, GPIO.OUT)
GPIO.output(GPIO_R1,1)
GPIO.output(GPIO_R3,1)
GPIO.output(GPIO_R2,1)
GPIO.output(GPIO_R4,1)

GPIO.setup(GPIO_MOTION, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.add_event_detect(GPIO_MOTION, GPIO.RISING, callback=motion_callback, bouncetime=100)
    

wifi = get_wifi_ssid()
print(f"WiFi: {wifi}")

# do we have keys for this site?
if wifi in location:
    secrets = json.loads(location[wifi])
    print ("it's working")
else: # load defaults
    secrets = json.loads(location['default'])
    print ("no workie")

#print(location[wifi])

db = str(secrets['DATABASE_FULLPATH'])
print(db)

connect = sqlite3.connect(db)
#connect = sqlite3.connect("/opt/pumphouse/DB/data.db")
cursor = connect.cursor()


#sys.exit()

data = sendBootToCloud()

#### SET UP DISPLAY WINDOW

window = tk.Tk()
window.title(secrets['SITE'])

# Create a canvas widget
canvas = tk.Canvas(window, width=140, height=500, bg="white")
canvas.pack(side="left")

canvas3 = tk.Canvas(window, width=140, height=500, bg="white")
canvas3.pack(side="left")

canvas2 = tk.Canvas(window, width=410, height=500, bg="#c1d9db")
canvas2.pack(side="left")


#print(data)
#sys.exit()
#level,low,high,maximum,minimum
#json = json.loads(data)

#print(json)
#print(data)

#sys.exit()
#print(data['LOC1'])

levelbar1 = LevelBar(canvas, data['LOC1'])
#print(data['LOC2'])
levelbar2 = LevelBar(canvas3, data['LOC2'])
#
#canvas2.create_text(30,30,text="Time:", font=("Arial",15))
time_id = canvas2.create_text(190, 20, text="00:00:00", font=("Arial",20))

canvas2.create_text(50,300, text="Movement: ")
move_id = canvas2.create_text(100, 300, text="0")

canvas2.create_text(70, 75, text='Last Server Update:')
last_contact_id = canvas2.create_text(180, 75, font='Arial 15 bold', text=last_server_contact)

canvas2.create_text(45, 100, text='Sent Status:')
last_status_id = canvas2.create_text(180, 100, text=last_status_to_server)

canvas2.create_text(60, 120, text='Server Command:')
last_command_id = canvas2.create_text(200, 120, font='Arial', text=last_server_command)

canvas2.create_text(45, 150, text='WiFi:')
canvas2.create_text(100,150, text=wifi)


#canvas2.create_text(45, 150, text='2->4 Pump:')
#if data['LOC2']['mainpump'] == 1:
#    main2_id = canvas2.create_text(100, 150, fill='green', text='ON')
#else:
#    main2_id = canvas2.create_text(100, 150, fill='red', text='OFF')
#shown_main2_pump_on = data['LOC2']['mainpump']
#main2_pump_on = shown_main2_pump_on

#canvas2.create_text(45, 170, text='1->2 Pump:')
#if data['LOC1']['mainpump'] == 1:
#    main1_id = canvas2.create_text(100, 170, fill='green', text='ON')
#else:
#    main1_id = canvas2.create_text(100, 170, fill='red', text='OFF')
#shown_main1_pump_on = data['LOC2']['mainpump']
#main1_pump_on = shown_main1_pump_on

#canvas2.create_text(45, 190, text='Well Pump:')
#if data['LOC1']['wellpump'] == 1:
#    well1_id = canvas2.create_text(100, 190, fill='green', text='ON')
#else:
#    well1_id = canvas2.create_text(100, 190, fill='red', text='OFF')
#shown_well_pump_on = data['LOC2']['mainpump']
#well_pump_on = shown_well_pump_on

pump_id = Button(canvas2, width=6,  height=2, text="Pump On", bg="green", activebackground='green',  bd=10, command=pump_on)
pump_id.place(x=10, y=400)
pump_time_id = canvas2.create_text(60, 480, fill='green', font='Times 20 bold', text="00")

window.protocol("WM_DELETE_WINDOW", on_closing)

#keep_window_focused(window)

tick()

window.mainloop()
