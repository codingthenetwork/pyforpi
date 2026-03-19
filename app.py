# for dashboard
from flask import Flask, jsonify, render_template 

# for utilities
import random
import subprocess
import threading

# for sensors
import time
import board
import busio
import adafruit_dht
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
from gpiozero import OutputDevice

# set up ADC
i2c = busio.I2C(board.SCL, board.SDA)
ads = ADS.ADS1115(i2c)
ads.gain = 1

# set up pump
pump = OutputDevice(23, active_high=False, initial_value=False)
states = [0, 1] # keeping track of on and off states

# python dictionary that stores all relevant sensor data to parse into .json and send to browser
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
    },
    "pump_time":4,
    "override":False
}

# helper function to convert raw values to percentages
def normalise(raw, low, high):
    percentage = 100 * ( (raw - low) / ( high - low) )
    percentage = max(0, min(100, percentage) )
    percentage = round(percentage, 1)

    moisture_output = percentage
    return moisture_output


app = Flask(__name__)

# this function fires the pump
def fire_pump():
    print("fire_pump called") 
    if components["outputs"]["pump"]["state"] == states[0]: 
        pump.on()
        components["outputs"]["pump"]["state"] = states[1]
        time.sleep(components["pump_time"]) # wait for 4s
        pump.off()
        components["outputs"]["pump"]["state"] = states[0]

        if components["override"]:
            components["override"] = False
        else:
            pass
            
        print("pump fired")

    else:
        msg = "pump was already on"
        # print(msg)
        pass

# if humidity less than preset, fire_pump() is called
def emergency(preset, value):

    preset = float(preset.replace("%",""))
    value = float(value.replace("%",""))


    if value < preset:
        fire_pump()
        # print("Value did exceed preset")
    else:
        # print("Value did not exceed preset")
        pass

# python returns homepage at the request for '/' URL
@app.route('/')
def home():
    return render_template("index.html", components=components)

# python executes fire_pump() at the request for '/override_fire_pump' URL
@app.route('/override_fire_pump')
def override_fire_pump():
    components["override"]=True
    threading.Thread(target=fire_pump,daemon=True).start()
    # components["override"]=False
    return '', 204

# python returns emergency page at the request for '/emergency' URL
@app.route('/emergency')
def goto_emergency():
    return render_template('emergency.html', components=components)

# python reads sensor values (1) updates the python dictionary with the values (2) outputs the dictionary as a .json file (3)
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
        threading.Thread(target=emergency, args=("40%", str(components["inputs"]["moisture"]["value"])),daemon=True).start() # call emergency() in a new thread
    except RuntimeError as e:
        print(e)

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

# this function launches the web server at http://127.0.0.1:5000
app.run()
