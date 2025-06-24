import tkinter as tk
import requests
import time
import signal
import sys
import RPi.GPIO as GPIO
import datetime
import json
import sqlite3

from tkinter import *

showed_time="00:00:00"
movements = 0
showed_movements = 0
sample_count = 0
pump_seconds_remaining=0;

GPIO_MOTION = 6
GPIO_R1 = 4
GPIO_R2 = 5
GPIO_R3 = 7
GPIO_R4 = 8


def on_closing():
    GPIO.output(GPIO_R1,0)
    GPIO.output(GPIO_R3,0)
    GPIO.output(GPIO_R2,0)
    GPIO.output(GPIO_R4,0)
    GPIO.cleanup()

    
def pump_on(pump):
    global canvas2, pump_id
    GPIO.output(pump,0)
    #pump_id.config(text='Pump Off')
    #pump_id.config(command=pump_off)
    #pump_id.config(bg='red')
    #pump_id.config(activebackground='red')
    
def pump_off(pump):
    global canvas2, pump_id, pump_seconds_remaining
    GPIO.output(pump,1)
    #pump_id.config(text='Pump On')
    #pump_id.config(activebackground='green')
    #pump_id.config(bg='green')
    #pump_id.config(command=pump_button)
    #pump_seconds_remaining=0

        
GPIO.setmode(GPIO.BCM)
GPIO.setup(GPIO_R1, GPIO.OUT)
GPIO.setup(GPIO_R2, GPIO.OUT)
GPIO.setup(GPIO_R3, GPIO.OUT)
GPIO.setup(GPIO_R4, GPIO.OUT)
GPIO.output(GPIO_R1,1)
GPIO.output(GPIO_R3,1)
GPIO.output(GPIO_R2,1)
GPIO.output(GPIO_R4,1)

try:
    while 1:
        pump_on(GPIO_R1);
        time.sleep(2)
        pump_off(GPIO_R1);
        pump_on(GPIO_R2);
        time.sleep(2)
        pump_off(GPIO_R2);
        pump_on(GPIO_R3);
        time.sleep(2)
        pump_off(GPIO_R3);
        pump_on(GPIO_R4);
        time.sleep(2)
        pump_off(GPIO_R4);
except Exception as e:
    print(f"An error occurred: {e}")

finally:
    GPIO.cleanup()
    print("Cleanup complete!")
    
window.mainloop()
