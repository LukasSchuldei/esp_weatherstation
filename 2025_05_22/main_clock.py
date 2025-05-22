# Library 
from time import sleep
from machine import I2C, Pin, deepsleep
import os 
import sys

sys.path.append('/library')
import sh1107
from ds3231 import DS3231

# I2C adress
## sh1107      = 60
## ds3231      = 104

# Variables
sleep_minute = 1
sleep_buffer = 15

# I2C bus lane
## I2C bus 0 (ds3231)
try:
    i2c_bus_zero = I2C(0, scl=Pin(22), sda=Pin(21))
except Exception as e:
    print("Error init I2C bus 0 (SHT30):", str(e))

## I2C bus 1 (display)
try:
    i2c_bus_one = I2C(1, scl=Pin(26), sda=Pin(25))
except Exception as e:
    print("Error init I2C bus 1 (Display):", str(e))

## Scan I2C buses
sht30_adress = i2c_bus_zero.scan()
sleep(0.5)
print(sht30_adress)
display_address = i2c_bus_one.scan()
sleep(0.5)
print(display_address)

if not sht30_adress:
    print("I2C Bus 0", "No devices found")
if not display_address:
    print("I2C Bus 1", "No display found")

# Display init
try:
    display = sh1107.SH1107_I2C(128, 128, i2c_bus_one, address=0x3C, rotate=180) # move between four display sides
    display.sleep(False) # True in case of power saving mode (deepsleep)
    display.fill(0)
    display.text("starting...", 0, 0, 1) # any text can be used 
    display.show()
except Exception as e:
    print("Display", str(e))

## Display function
def display_values(Date, Time_now):
    display.fill(0)
    display.text(f"Date: {Date}C", 0, 0, 1)
    display.text(f"Time: {Time_now}", 0, 8, 1)
    display.show()
    
def display_sleep():
    display.fill(0) # black screen
    display.text("Sleeping in 15 s...", 0, 0, 1)
    display.text(f"Sleeptime: {sleep_minute} Min", 0, 8, 1)
    display.show()
    sleep(sleep_buffer)
    display.fill(0)
    display.show()
    display.sleep(True)  # Put OLED in low power mode
    
# Clock init
try:
    rtc = DS3231(i2c_bus_zero)
    sleep(1)
except Exception as e:
    print("Clock error", str(e))

#Clock functions

## Read time 
def clock_check():
    current_time = rtc.get_time()
    return current_time

def set_rtc_time():
    rtc.set_time((2025, 5, 18, 19, 6, 0, 3, 138))  # YY, MM, mday, hh, mm, ss, wday, yday
    print("RTC time set.")

#set_rtc_time()
    
# Log flash memory
def log_data_to_file(date, time_now, voltage, percentage):
    try:
        with open("battery_log.txt", "a") as file:
            file.write(f"{date} {time_now}, Voltage: {voltage}mV, Charge: {percentage}%\n")
    except Exception as e:
        print("Failed to write to log:", e)

# Infinity loop
while True:
    
    for i in range(5):
        
        # Get current date and time from RTC
        year, month, day, hour, minute, second, _, _ = clock_check()
        
        #character string date time 
        date = f"{year:04d}-{month:02d}-{day:02d}"
        time_now = f"{hour:02d}:{minute:02d}:{second:02d}"
        sleep(0.5)
  
        # Display values on the OLED
        print(f"Date: {date}\nTime: {time_now}")
        display_values(date, time_now)            
        sleep(10)
    
    print(f"going to deepsleep in {sleep_buffer} seconds")
    display_sleep()
    
    # deepsleep
    deepsleep(60 * sleep_minute * 1000)  # seconds*number minutes*miliseconds 
    
    
 







