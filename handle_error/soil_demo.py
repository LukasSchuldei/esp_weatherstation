from time import sleep
from machine import I2C, Pin, deepsleep, SDCard
import os 
import sys

sys.path.append('/library')
from soil_moisture import SoilSensor

# Initialize sensor
soil_sensor = SoilSensor(pin=36, air_val=3549, water_val=385)

# Air and full water calibration 
#soil_sensor.calibrate()

# Read data
soil_data = soil_sensor.read()
print(soil_data)

while True:
    for i in range(10):
        try:
            soil = soil_sensor.read_list()
            level_one = soil[0]
            raw_one = soil[1]
            percentage_one = soil[2]
            voltage_one = soil[3]
            
            print(f"Reading {i+1}, Level: {level_one}, Raw ADC: {raw_one}, Moisture: {percentage_one} %, Voltage: {voltage_one} V")
            
        except Exception as e:
            print("Reading error", str(e))
            
        sleep(2)
        
    sleep(20)

        
        


