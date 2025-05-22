# Library 
from time import sleep
from machine import I2C, Pin, deepsleep, SDCard
import os 
import sys

sys.path.append('/library')
import sh1107
import sht30
from ds3231 import DS3231

# Variables
sleep_minute = 1
sleep_buffer = 15

# LED
led_pin = Pin(2, Pin.OUT)
led_pin.off()

# I2C bus lane
## I2C bus 0 (ds3231, sht30)
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
sht30_clock_adress = i2c_bus_zero.scan()
sleep(0.5)
print(sht30_clock_adress)
display_address = i2c_bus_one.scan()
sleep(0.5)
print(display_address)

if not sht30_clock_adress:
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

sleep(0.5)

## Display functions
### Display values
def display_values(date, time_now, temperature, humidity):
    display.fill(0)
    display.text(f"Date: {date}", 0, 0, 1)
    display.text(f"Time: {time_now}", 0, 8, 1)
    display.text(f"Temp: {temperature}C", 0, 16, 1)
    display.text(f"Humid: {humidity}%", 0, 24, 1)
    display.show()

### Display sleep
def display_sleep():
    display.fill(0) # black screen
    display.text("Sleeping in 15 s...", 0, 0, 1)
    display.text(f"Sleeptime: {sleep_minute} Min", 0, 8, 1)
    print("sleeping in 15s")
    print("Sleeptime:", sleep_minute)
    display.show()
    sleep(sleep_buffer)
    display.fill(0)
    display.show()
    display.sleep(True)  # Put OLED in low power mode

### Display sd card free space
def display_storage(sdcard_status):
    display.fill(0)
    display.text(f"SD: {sdcard_status} GB", 0, 0, 1)
    print(sdcard_status, "GB")
    display.show()
    
# Clock init
try:
    rtc = DS3231(i2c_bus_zero)
    sleep(1)
except Exception as e:
    print("Clock error", str(e))

##Clock functions
### Read time 
def clock_check():
    current_time = rtc.get_time()
    return current_time

### Set time 
def set_rtc_time():
    rtc.set_time((2025, 5, 18, 19, 6, 0, 3, 138))  # YY, MM, mday, hh, mm, ss, wday, yday
    print("RTC time set.")

#set_rtc_time() 

# SD card init and mount
try:
    sd = SDCard(slot=2, sck=Pin(18), mosi=Pin(23), miso=Pin(19), cs=Pin(4), freq=10_000_000) # _ = point for big numbers 
    os.mount(sd, '/sd')
    print("SD card mounted")
except Exception as e:
    print("SD Card", str(e))

sleep(1)

# CSV file setup
sd_file = 'data_one.csv'
sd_path = '/sd/' + sd_file

if sd_file not in os.listdir('/sd'):
    try:
        with open(sd_path, 'w') as f:
            f.write("Date,Time,Temperature,Humidity\n")
    except Exception as e:
        print("CSV Init", str(e))
else:
    print("CSV file present")

def sd_storage():
    try:
        statvfs = os.statvfs('/sd')
        free_space = statvfs[0] * statvfs[3]
        return round(free_space / (1024 ** 3), 2)
    except Exception as e:
        print("SD Storage", str(e))

sdcard_status = sd_storage()
display_storage(sdcard_status)
sleep(1)

# SHT30 sensor
try:
    sht = sht30.SHT30(i2c=i2c_bus_zero, i2c_address=68)
except Exception as e:
    print("SHT30", str(e))

while True:   
    for i in range(5):
        try:
            year, month, day, hour, minute, second, _, _ = clock_check()
            date = f"{year:04d}-{month:02d}-{day:02d}"
            time_now = f"{hour:02d}:{minute:02d}:{second:02d}"
            abiotic_values = sht.measure()
            temperature = round(abiotic_values[0], 1)
            humidity = round(abiotic_values[1], 1)
            
            print(f"Date:{date}\nTime:{time_now}\nTemperature:{temperature} C\nHumidty:{humidity} %")        
            display_values(date, time_now, temperature, humidity)
            
            with open(sd_path, 'a') as f:
                f.write(f"{date},{time_now},{temperature},{humidity}\n")
        except Exception as e:
            print("Loop", str(e))
        sleep(5)

    try:
        os.umount('/sd')
    except Exception as e:
        print("SD Unmount", str(e))

    display.fill(0)
    display.text("SD unmounted", 0, 0, 1)
    display.show()
    sleep(5)
    
    display_sleep()
    
    deepsleep(60 * sleep_minute * 1000)  # 1 minutes

