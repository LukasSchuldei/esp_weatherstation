# Library 
from time import sleep
from machine import I2C, Pin, deepsleep, SDCard
import os 
import sys

sys.path.append('/library')
import sh1107
from ds3231 import DS3231
import sht30
from DFRobot_MAX17043 import DFRobot_MAX17043

# Error handling for all hardware components 
def handle_error(source="Unknown", message="Error"):
    print(f"[{source}] {message}")
    try:
        display.fill(0)
        display.text("Error occurred!", 0, 0, 1)
        display.text(f"{source}:", 0, 16, 1)
        display.text(message[:16], 0, 32, 1)
        display.show()
    except:
        pass
    sleep(5)
    deepsleep(30 * 1000)  # sleep 30s before restart

# I2C bus lane
try:
    i2c_bus_zero = I2C(0, scl=Pin(22), sda=Pin(21))
    i2c_bus_one  = I2C(1, scl=Pin(26), sda=Pin(25))
except Exception as e:
    handle_error("I2C Init", str(e))

# Scan I2C buses
devices = i2c_bus_zero.scan()
display_address = i2c_bus_one.scan()
if not devices:
    handle_error("I2C Bus 0", "No devices found")
if not display_address:
    handle_error("I2C Bus 1", "No display found")

# SH1107 display object
try:
    display = sh1107.SH1107_I2C(128, 128, i2c_bus_one, address=0x3C, rotate=180)
    display.sleep(False)
    display.fill(0)
    display.text("starting...", 0, 0, 1)
    display.show()
except Exception as e:
    handle_error("Display", str(e))

sleep(1)

# SHT30 sensor
try:
    sht = sht30.SHT30(i2c=i2c_bus_zero, i2c_address=68)
except Exception as e:
    handle_error("SHT30", str(e))

# RTC clock

#Clock
clock_power = Pin(4, Pin.OUT)
clock_power.value(1)
sleep(0.5)

try:
    rtc = DS3231(i2c_bus_zero)
except Exception as e:
    handle_error("RTC", str(e))
    

def clock_check():
    return rtc.get_time()

def set_rtc_time():
    rtc.set_time((2025, 5, 3, 22, 23, 0, 5, 123))  # weekday: Monday=0, ..., Sunday=6
    print("RTC time set.")

def display_values(date, time_now, temperature, humidity, voltage, percentage):
    display.fill(0)
    display.text(date, 0, 0, 1)
    display.text(time_now, 0, 16, 1)
    display.text(f"Temp: {temperature}C", 0, 32, 1)
    display.text(f"Hum: {humidity}%", 0, 48, 1)
    display.text(f"Batt: {voltage}mV", 0, 64, 1)
    display.text(f"Charge: {percentage}%", 0, 80, 1)
    display.show()

def display_storage(sdcard_status):
    display.fill(0)
    display.text(f"SD: {sdcard_status} GB", 0, 0, 1)
    display.show()

# SD card init and mount
try:
    sd = SDCard(slot=2, sck=Pin(18), mosi=Pin(23), miso=Pin(19), cs=Pin(4), freq=10_000_000) # _ = point for big numbers 
    os.mount(sd, '/sd')
except Exception as e:
    handle_error("SD Card", str(e))

print("SD card mounted")
sleep(1)

# CSV setup
sd_file = 'data_one.csv'
sd_path = '/sd/' + sd_file
if sd_file not in os.listdir('/sd'):
    try:
        with open(sd_path, 'w') as f:
            f.write("Date, Time, Temperature, Humidity, Battery_V, Battery_%\n")
    except Exception as e:
        handle_error("CSV Init", str(e))
else:
    print("CSV file present")

def sd_storage():
    try:
        statvfs = os.statvfs('/sd')
        free_space = statvfs[0] * statvfs[3]
        return round(free_space / (1024 ** 3), 2)
    except Exception as e:
        handle_error("SD Storage", str(e))

sdcard_status = sd_storage()
display_storage(sdcard_status)
sleep(1)

# Battery gauge
try:
    gauge = DFRobot_MAX17043()
    rslt = gauge.begin()
except Exception as e:
    handle_error("Battery Gauge", str(e))

while True:
    for i in range(5):
        try:
            # battery
            voltage = str(round(gauge.read_voltage(), 2))
            percentage = round(gauge.read_percentage(), 2)
            
            # abiotic sht30
            values = sht.measure()
            year, month, day, hour, minute, second, _, _ = clock_check()
            date = f"{year:04d}-{month:02d}-{day:02d}"
            time_now = f"{hour:02d}:{minute:02d}:{second:02d}"
            temperature = round(values[0], 1)
            humidity = round(values[1], 1)
            display_values(date, time_now, temperature, humidity, voltage, percentage)
            with open(sd_path, 'a') as f:
                f.write(f"{date}, {time_now}, {temperature}, {humidity}, {voltage}, {percentage}\n")
        except Exception as e:
            handle_error("Loop", str(e))
        sleep(5)

    display.fill(0)
    display.text("Sleeping in 5s...", 0, 0, 1)
    display.show()
    sleep(5)
    display.fill(0)
    display.show()

    print("Going to deep sleep for 15 minutes...")

    try:
        os.umount('/sd')
    except Exception as e:
        handle_error("SD Unmount", str(e))

    display.text("SD unmounted", 0, 0, 1)
    display.show()
    sleep(5)

    display.fill(0)
    display.show()
    display.sleep(True)
    sleep(1)
    
    # clock powering off
    clock_power.value(0)
    sleep(0.5)

    deepsleep(60 * 3 * 1000)  # 3 minutes
