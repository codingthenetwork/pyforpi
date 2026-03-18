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
from gpiozero import OutputDevice

# configuring ADC
i2c = busio.I2C(board.SCL, board.SDA)
ads = ADS.ADS1115(i2c)
ads.gain = 1

def normalise(raw, low, high):
    percentage = 100 * ( (raw - low) / ( high - low) )
    percentage = max(0, min(100, percentage) )
    percentage = round(percentage, 1)

    moisture_output = percentage
    return moisture_output

states = [False, True]

components = {
    "inputs": {
        "temperature": {
            "name": "DHT22",
            "quantity": "temperature",
            "value": "Loading",
            "unit": "ºC"
        },
        "humidity": {
            "name": "DHT22",
            "quantity": "humidity",
            "value": "Loading",
            "unit": "%"
        },
        "moisture": {
            "name": "YL69 | HC38",
            "quantity": "moisture",
            "value": "Loading",
            "unit": "%"
        },
        "air_quality": {
            "quantity": "air_quality",
            "value": "Loading",
            "unit": "%"
        },
        "internal_temp": {
            "quantity": "internal_temp",
            "value": "Loading",
            "unit": "ºC"
        },
    },
    "outputs": {
      "pump": {
        "name": "pump",
        "state": states[0]
      },
      "UVlight": {
        "name": "uv_light",
        "state": states[0]
      },
      "fan": {
        "name": "fan",
        "state": states[0]
      }
    }
}

states = [False, True]

app = Flask(__name__)

# @app.route('/emergency')
def emergency(preset, value):

    preset = int(preset.replace("%",""))
    value = int(value.replace("%",""))


    if value < preset and outputs.pump.state == states[0]:
        pump.on()
        components.outputs.pump.state = states[1]
        sleep(4)
        pump.off()
        components.outputs.pump.state = states[0]
    else:
        msg = "Value did not exceed preset or pump was already on"
        # print(msg)
        pass

@app.route('/')
def home():
    return render_template("index.html", components=components)
    # return render_template("index.html")

@app.route('/get_update')
def get_update():

    global components

    # temperature
    try:
        components["inputs"]["temperature"]["value"] = adafruit_dht.DHT22(board.D24, use_pulseio=False).temperature
    except RuntimeError as e:
        print(e)

    #humidity
    try:
        components["inputs"]["humidity"]["value"] = adafruit_dht.DHT22(board.D24, use_pulseio=False).humidity
    except RuntimeError as e:
        print(e)

    #moisture
    yl69 = AnalogIn(ads, 0)

    try:
        components["inputs"]["moisture"]["value"] = normalise(yl69.value, 26500, 8500)
    except RuntimeError as e:
        print(e)
    # check moisture
    # emergency("40%", inputs["moisture"]["value"])

    #air_quality
    mq135 = AnalogIn(ads, 1)
    try:
        components["inputs"]["air_quality"]["value"] = normalise(mq135.value, 25000, 5000)
    except RuntimeError as e:
        print(e)

    #internal_temp
    output = subprocess.run(["vcgencmd", "measure_temp"], capture_output=True, text=True, check=True).stdout.strip().replace("temp=","").replace("'C","")
    try:
        components["inputs"]["internal_temp"]["value"] = output
    except RuntimeError as e:
        print(e)

    # parse all inputs
    return jsonify(components)


app.run()
