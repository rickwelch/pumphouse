#!/opt/pumphouse/env/bin/python
from ina219 import INA219
from ina219 import DeviceRangeError

SHUNT_OHMS = 0.1
MAX_EXPECTED_AMPS = 0.2

def read():
    ina = INA219(SHUNT_OHMS, MAX_EXPECTED_AMPS, busnum=1)
    ina.configure(ina.RANGE_16V)
    print("Bus Voltage: %.3f V" % ina.voltage())
    try:
        print("Bus Current: %.3f mA" % ina.current())
    except DeviceRangeError as e:
        print(e)


if __name__ == "__main__":
    read()
