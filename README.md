#pumphouse - python files to remotely manage each pumphouse. Monitor water levels and pump current, movement within the building, air temperature and humidity, and report that to a remote server every 15 minutes. 

Install new version of 16-bit Raspian onto Raspberry Pi 4 or 5 and install python and sqlite3
Make sure the I2C bus is enabled on your pi using the

     Preferences-> Raspberry Pi Configuration -> Interfaces

screen. 

To install this code
* mkdir /opt/foo
* chown pi:pi /opt/foo ( or your login user name )
* cd /opt/foo
* git clone git@github.com:rickwelch/pumphouse.git
* sudo mv /opt/foo/pumphouse /opt
* sudo rm foo
* cd /opt/pumphouse

#set up python virtual environment

* python3 -m venv env
* source env/bin/activate
* pip install requests
* pip install RPi.GPIO
* pip install smbus2
* pip install adafruit-circuitpython-bme280
* pip install bme280
* pip install adafruit-circuitpython-ads1x15
* pip install adafruit-circuitpython-ina219
* pip install RPi.bme280
* pip install rpi-lgpio

If you want this automatically started at boot copy ./loginuser/.config/autostart/pumphouse.desktop to the user that is automaticsally logged in when the pi boots. Usually pi but I generally change it.

I also add a "New Item" in Preferences -> Main Menu Editor:
  Name: Pumphouse Controller
  Command: /opt/pumphouse/pumphouse.py