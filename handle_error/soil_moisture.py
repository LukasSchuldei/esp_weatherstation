"""
Minimal Soil Moisture Sensor Library

FORMULAS USED:
==============

1. RAW ADC TO VOLTAGE CONVERSION:
   voltage = (raw_value / 4095) * 3.3
   - Converts 12-bit ADC reading (0-4095) to actual voltage (0-3.3V)
   - 4095 = max ADC value (2^12 - 1)
   - 3.3 = ESP32 ADC reference voltage

2. MOISTURE PERCENTAGE CALCULATION:
   percentage = ((air_val - raw_value) / (air_val - water_val)) * 100
   - Inverted scale: lower raw values = higher moisture
   - air_val = calibrated dry reading (high value)
   - water_val = calibrated wet reading (low value)
   - Result: 0% (dry) to 100% (wet)

3. LEVEL THRESHOLD CALCULATION:
   intervals = (air_val - water_val) // 3
   dry_threshold = air_val - intervals
   wet_threshold = water_val + intervals
   - Divides sensor range into 3 equal parts
   - Uses integer division (//) to avoid floating point

4. LEVEL CLASSIFICATION (DFRobot Logic):
   if raw > dry_threshold:     → "Dry"
   elif raw > wet_threshold:   → "Wet" 
   else:                       → "Very Wet"
   - Exclusive lower bounds (>) following DFRobot specification
   - Higher raw values = drier conditions

5. VALUE CONSTRAINING:
   if raw > air_val: raw = air_val
   elif raw < water_val: raw = water_val
   - Keeps readings within calibrated range
   - Prevents percentage values outside 0-100%

EXAMPLE WITH TYPICAL VALUES:
===========================
air_val = 3550 (dry) = 2.862V
water_val = 321 (wet) = 0.259V
intervals = (3550-321)//3 = 1076
dry_threshold = 3550-1076 = 2474
wet_threshold = 321+1076 = 1397

Ranges:
- Very Wet: 0-1397 (0.000V-1.127V)
- Wet: 1398-2474 (1.128V-1.996V)  
- Dry: 2475-4095 (1.997V-3.300V)
"""
from machine import Pin, ADC

class SoilSensor:
    def __init__(self, pin=36, air_val=3550, water_val=321):
        self.air_val = air_val
        self.water_val = water_val
        self.adc = ADC(Pin(pin))
        self.adc.atten(ADC.ATTN_11DB)
        self.adc.width(ADC.WIDTH_12BIT)
    
    def read(self):
        raw = self.adc.read()
        
        # Constrain value
        if raw > self.air_val:
            raw = self.air_val
        elif raw < self.water_val:
            raw = self.water_val
        
        # Calculate percentage
        percentage = ((self.air_val - raw) / (self.air_val - self.water_val)) * 100
        
        # Get level (DFRobot exact specification)
        # DFRobot: Dry: (air, threshold], Wet: (threshold, threshold], Very Wet: (threshold, water]
        intervals = (self.air_val - self.water_val) // 3
        
        # Calculate thresholds
        dry_threshold = self.air_val - intervals      # 3550 - 1076 = 2474
        wet_threshold = self.water_val + intervals    # 321 + 1076 = 1397
        
        # DFRobot's boundary logic: exclusive lower, inclusive upper
        if raw > dry_threshold:          # > 2474 = Dry
            level = "Dry"
        elif raw > wet_threshold:        # > 1397 (but <= 2474) = Wet
            level = "Wet"
        else:                           # <= 1397 = Very Wet
            level = "Very Wet"
        
        return {
            'raw': raw,
            'voltage': round((raw / 4095) * 3.3, 3),
            'percentage': round(percentage, 1),
            'level': level
        }
    
    def read_list(self):
        """
        Return readings as ordered list instead of dictionary
        
        Returns:
            list: [level, raw, percentage, voltage]
            - level (str): Moisture level category
            - raw (int): Raw ADC reading (0-4095)
            - percentage (float): Moisture percentage (0.0-100.0)
            - voltage (float): Sensor voltage (0.000-3.300V)
        """
        data = self.read()  # Get dictionary first
        return [
            data['level'],
            data['raw'], 
            data['percentage'],
            data['voltage']
        ]
    
    def calibrate(self):
        from time import sleep
        
        print("=== Calibration ===")
        print("1. Keep sensor in air, press Enter...")
        input()
        
        air_readings = []
        for i in range(5):
            reading = self.adc.read()
            air_readings.append(reading)
            voltage = round((reading / 4095) * 3.3, 3)
            print(f"Air {i+1}: {reading} (raw) = {voltage}V")
            sleep(1)
        
        air_avg = sum(air_readings) // len(air_readings)
        air_voltage = round((air_avg / 4095) * 3.3, 3)
        print(f"Air average: {air_avg} (raw) = {air_voltage}V")
        
        print("\n2. Put sensor in water, press Enter...")
        input()
        
        water_readings = []
        for i in range(5):
            reading = self.adc.read()
            water_readings.append(reading)
            voltage = round((reading / 4095) * 3.3, 3)
            print(f"Water {i+1}: {reading} (raw) = {voltage}V")
            sleep(1)
        
        water_avg = sum(water_readings) // len(water_readings)
        water_voltage = round((water_avg / 4095) * 3.3, 3)
        print(f"Water average: {water_avg} (raw) = {water_voltage}V")
        
        print(f"\nResults:")
        print(f"Air: {air_avg} raw = {air_voltage}V")
        print(f"Water: {water_avg} raw = {water_voltage}V")
        print(f"Voltage range: {round(air_voltage - water_voltage, 3)}V")
        print(f"\nCode: air_val={air_avg}, water_val={water_avg}")
        
        self.air_val = air_avg
        self.water_val = water_avg
        
        return air_avg, water_avg