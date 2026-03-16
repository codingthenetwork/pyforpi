# for dashboard
from flask import Flask, jsonify, render_template
import random
import subprocess

# for sensors
import time
import board
import busio
import adafruit_dht
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

i2c = busio.I2C(board.SCL, board.SDA)
ads = ADS.ADS1115(i2c)
ads.gain = 1

def moist_lvl(raw):
    dry_limit = 26500
    wet_limit = 8500

    percentage = 100 * ( (raw - dry_limit) / ( wet_limit - dry_limit) )
    percentage = max(0, min(100, percentage) )
    percentage = round(percentage, 1)

    moisture_output = percentage
    return moisture_output

def normalise(raw, low, high):
    percentage = 100 * ( (raw - low) / ( high - low) )
    percentage = max(0, min(100, percentage) )
    percentage = round(percentage, 1)

    moisture_output = percentage
    return moisture_output

def air_quality(raw):
    clean_limit = 5000
    danger_limit = 25000

    percentage = 100 * ( (raw - clean_limit) / ( danger_limit - clean_limit) )
    percentage = max(0, min(100, percentage) )
    percentage = round(percentage, 1)

    aq_output = 100 - percentage
    return aq_output

    # if percentage > 90:
    #   aq_output = "Immediate Danger"
    # elif percentage > 60:
    #   aq_output = "Low Danger"
    # elif percentage > 40:
    #   aq_output = "Satisfactory"
    # else:
    #   aq_output = "All good"

inputs = {
    "temperature": {
        "sensor": "None",
        "name": "DHT22",
        "quantity": "temperature",
        "value": "Loading",
        "unit": "ºC"
    },
    "humidity": {
        "sensor": "None",
        "name": "DHT22",
        "quantity": "humidity",
        "value": "Loading",
        "unit": "%"
    },
    "moisture": {
        "sensor": "None",
        "name": "YL69 | HC38",
        "quantity": "moisture",
        "value": "Loading",
        "unit": "%"
    },
    "air_quality": {
        "sensor": "None",
        "quantity": "air_quality",
        "value": "Loading",
        "unit": "%"
    },
    "internal_temp": {
        "sensor": "None",
        "quantity": "internal_temp",
        "value": "Loading",
        "unit": "ºC"
    },
}

options = ["on", "off"]

outputs = {
  "waterpump": {
    "name": "water_pump",
    "state": options[0]
  },
  "UVlight": {
    "name": "uv_light",
    "state": options[0]
  },
  "fan": {
    "name": "fan",
    "state": options[0]
  }
}

app = Flask(__name__)

@app.route('/')
def home():
    return render_template("index.html", inputs=inputs, outputs=outputs)
    # return render_template("index.html")

@app.route('/get_update')
def get_update():

    global inputs

    # temperature
    try:
        # inputs["temperature"]["sensor"] = adafruit_dht.DHT22(board.D4, use_pulseio=False)
        inputs["temperature"]["value"] = adafruit_dht.DHT22(board.D24, use_pulseio=False).temperature
    except RuntimeError as e:
        # inputs["temperature"]["value"] = f"Error {e}"
        pass

    #humidity
    try:
        # inputs["humidity"]["sensor"] = adafruit_dht.DHT22(board.D4, use_pulseio=False)
        inputs["humidity"]["value"] = adafruit_dht.DHT22(board.D24, use_pulseio=False).humidity
    except RuntimeError as e:
        # inputs["humidity"]["value"] = f"Error {e}"
        pass

    #moisture
    try:
        yl69 = AnalogIn(ads, 0)

        inputs["moisture"]["value"] = normalise(yl69.value, 26500, 8500)
    except RuntimeError as e:
        inputs["moisture"]["value"] = f"Error {e}"
        pass

    #air_quality
    try:
        mq135 = AnalogIn(ads, 1)

        inputs["air_quality"]["value"] = normalise(mq135.value, 5000, 25000)
    except RuntimeError as e:
        inputs["air_quality"]["value"] = f"Error {e}"
        pass

    #internal_temp
    try:
        result = subprocess.run(["vcgencmd", "measure_temp"], capture_output=True, text=True, check=True).stdout.strip()
        output = result.replace("temp=","").replace("'C","")

        inputs["internal_temp"]["value"] = output
    except RuntimeError as e:
        inputs["internal_temp"]["value"] = f"Error {e}"
        pass

    return jsonify(inputs)


app.run()
