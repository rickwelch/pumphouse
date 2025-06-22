#!/opt/pumphouse/env/bin/python
import board
import busio
import time
import datetime
import RPi.GPIO as GPIO
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

i2c = busio.I2C(board.SCL, board.SDA)

ads = ADS.ADS1115(i2c)
ads.gain=8

chan1 = AnalogIn(ads,ADS.P0)
chan4 = AnalogIn(ads,ADS.P3)

try:
    while 1:
        i = 50
        sum = 0.0
        while(i > 0):
            sum = sum + abs(chan4.voltage)
            i = i-1
            
#        print(f"1: {chan1.voltage}V -- 4: {chan4.voltage}")
        print(f"Voltage: {sum} -- {sum/50}V")
        time.sleep(1)

except Exception as e:
    print(f"An error occurred: {e}")

finally:
    GPIO.cleanup()
    print("Cleanup complete!")
    
#mainloop()
