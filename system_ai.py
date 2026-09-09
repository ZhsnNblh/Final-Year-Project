import time
import joblib
import pandas as pd
import requests
import serial
import spidev
from datetime import datetime

import board
import busio
import adafruit_dht
import adafruit_tsl2591
import RPi.GPIO as GPIO


# ==========================================
# CONFIGURATION
# ==========================================

SPI_BUS = 0
SPI_DEVICE = 0
SPI_SPEED_HZ = 1350000

SERIAL_PORT = "/dev/serial0"
SERIAL_BAUDRATE = 9600
SERIAL_TIMEOUT = 1

MIST_RELAY = 22

FIREBASE_URL = (
    "https://fullsystem-a0461-default-rtdb.asia-southeast1."
    "firebasedatabase.app/test.json"
)

HUMIDITY_LOW = 80
HUMIDITY_HIGH = 90


# ==========================================
# HARDWARE INITIALIZATION
# ==========================================

spi = spidev.SpiDev()
spi.open(SPI_BUS, SPI_DEVICE)
spi.max_speed_hz = SPI_SPEED_HZ

# DHT22

dht = adafruit_dht.DHT22(board.D27)

# TSL2591

i2c = busio.I2C(board.SCL, board.SDA)
while not i2c.try_lock():
    pass
i2c.unlock()
light_sensor = adafruit_tsl2591.TSL2591(i2c)

# XGBoost model

mist_model = joblib.load("mist_xgboost.pkl")
print("XGBoost mist model loaded successfully!")

# MH-Z19B

ser = serial.Serial(
    SERIAL_PORT,
    baudrate=SERIAL_BAUDRATE,
    timeout=SERIAL_TIMEOUT,
)

# GPIO relay

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(MIST_RELAY, GPIO.OUT)
GPIO.output(MIST_RELAY, GPIO.HIGH)


# ==========================================
# SENSOR FUNCTIONS
# ==========================================

def read_dht():
    try:
        temperature = dht.temperature
        humidity = dht.humidity
        return temperature, humidity

    except Exception as e:
        print("DHT Error:", e)
        return None, None


def read_co2():
    try:
        cmd = bytearray([0xFF, 0x01, 0x86] + [0x00] * 5)
        checksum = 0xFF - (sum(cmd[1:]) % 256) + 1
        cmd.append(checksum)

        ser.write(cmd)
        time.sleep(1)

        response = ser.read(9)

        if len(response) == 9:
            co2 = response[2] * 256 + response[3]
            return co2

    except Exception as e:
        print("CO2 Error:", e)

    return None


def read_light():
    try:
        return light_sensor.lux

    except Exception as e:
        print("Light Error:", e)
        return None


def read_soil():
    try:
        adc = spi.xfer2([1, (8 + 0) << 4, 0])
        value = ((adc[1] & 3) << 8) + adc[2]

        if value > 550:
            status = "DRY"
        else:
            status = "WET"

        return value, status

    except Exception as e:
        print("Soil Error:", e)
        return None, None


# ==========================================
# MIST CONTROL
# ==========================================

def control_mist_ai(temp, hum, co2):
    if None in (temp, hum, co2):
        return "UNKNOWN"

    features = pd.DataFrame([{
        "Temperature (°C)": temp,
        "Humidity (%)": hum,
        "CO2 (ppm)": co2,
    }])

    prediction = mist_model.predict(features)[0]

    if prediction == 1:
        GPIO.output(MIST_RELAY, GPIO.LOW)
        print("MIST ON (AI Prediction)")
        return "ON"

    GPIO.output(MIST_RELAY, GPIO.HIGH)
    print("MIST OFF (AI Prediction)")
    return "OFF"


# ==========================================
# FIREBASE
# ==========================================

def send_data(data):
    try:
        requests.post(
            FIREBASE_URL,
            json=data,
            timeout=5,
        )
        print("Data uploaded to Firebase")

    except Exception as e:
        print("Firebase Error:", e)


# ==========================================
# MAIN LOOP
# ==========================================

try:
    print("Mushroom Monitoring System Started")

    while True:
        # Read sensors
        temp, hum = read_dht()
        co2 = read_co2()
        light = read_light()
        soil_raw, soil_status = read_soil()

        # Control actuator
        mist_status = control_mist_ai(temp, hum, co2)

        # Time
        current_time = datetime.now()
        timestamp_str = current_time.strftime("%Y-%m-%d %H:%M:%S")
        timestamp_unix = current_time.timestamp()

        # Display
        print("\n=====================")
        print(f"Time : {timestamp_str}")
        print(f"Temp : {temp} °C")
        print(f"Hum  : {hum} %")
        print(f"CO2  : {co2} ppm")
        print(f"Light: {light} lux")
        print(f"Soil Raw : {soil_raw}")
        print(f"Soil     : {soil_status}")
        print(f"Mist : {mist_status}")
        print("=====================")

        # Upload
        if all(
            value is not None
            for value in [temp, hum, co2, light, soil_raw, soil_status]
        ):
            payload = {
                "temperature": round(temp, 2),
                "humidity": round(hum, 2),
                "co2": co2,
                "light": round(light, 2),
                "soil_raw": soil_raw,
                "soil_status": soil_status,
                "mist_prediction": mist_status,
                "timestamp_readable": timestamp_str,
                "timestamp_unix": timestamp_unix,
                "date": current_time.strftime("%Y-%m-%d"),
                "time": current_time.strftime("%H:%M:%S"),
            }
            send_data(payload)
        else:
            print("Upload skipped (invalid reading)")

        time.sleep(5)

except KeyboardInterrupt:
    print("\nProgram stopped")

finally:
    GPIO.output(MIST_RELAY, GPIO.HIGH)
    GPIO.cleanup()
    ser.close()
    print("GPIO and Sensors Closed")
