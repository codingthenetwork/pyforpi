# for dashboard
from flask import Flask, jsonify, render_template
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

# configuring ADC
i2c = busio.I2C(board.SCL, board.SDA)
ads = ADS.ADS1115(i2c)
ads.gain = 1

# configuring pump
pump = OutputDevice(23, active_high=False, initial_value=False)

states = [0, 1]

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

def normalise(raw, low, high):
    percentage = 100 * ( (raw - low) / ( high - low) )
    percentage = max(0, min(100, percentage) )
    percentage = round(percentage, 1)

    moisture_output = percentage
    return moisture_output


app = Flask(__name__)

def fire_pump():
    print("fire_pump called")
    if components["outputs"]["pump"]["state"] == states[0]:
        # components["override"] = True
        pump.on()
        components["outputs"]["pump"]["state"] = states[1]
        time.sleep(components["pump_time"])
        pump.off()
        components["outputs"]["pump"]["state"] = states[0]

        if components["override"]:
            components["override"] = False
        else:
            pass

        # components["override"] = False
        print("pump fired")

    else:
        msg = "pump was already on"
        # print(msg)
        pass

def emergency(preset, value):

    preset = float(preset.replace("%",""))
    value = float(value.replace("%",""))


    if value < preset:
        fire_pump()
        # print("Value did exceed preset")
    else:
        # print("Value did not exceed preset")
        pass

@app.route('/')
def home():
    return render_template("index.html", components=components)
    # return render_template("index.html")

# @app.route('/get_update_fake')
# def get_update_fake():

#     global components

#     # temperature
#     try:
#         components["inputs"]["temperature"]["value"] = random.choice([61,67])
#     except RuntimeError as e:
#         print(e)

#     #humidity
#     try:
#         components["inputs"]["humidity"]["value"] = random.choice([61,67])
#     except RuntimeError as e:
#         print(e)

#     #moisture
#     # yl69 = AnalogIn(ads, 0)

#     try:
#         components["inputs"]["moisture"]["value"] = random.choice([61,67,64,63,55,57,67])
#         # emergency("40%", str(components["inputs"]["moisture"]["value"]))
#         threading.Thread(target=emergency, args=("40", str(components["inputs"]["moisture"]["value"])),daemon=True).start()
#     except RuntimeError as e:
#         print(e)
#     # check moisture

#     #air_quality
#     # mq135 = AnalogIn(ads, 1)
#     try:
#         components["inputs"]["air_quality"]["value"] = random.choice([61,67])
#     except RuntimeError as e:
#         print(e)

#     #internal_temp
#     try:
#         components["inputs"]["internal_temp"]["value"] = random.choice([61,67])
#     except RuntimeError as e:
#         print(e)

#     # parse all inputs
#     return jsonify(components)

@app.route('/override_fire_pump')
def override_fire_pump():
    components["override"]=True
    threading.Thread(target=fire_pump,daemon=True).start()
    # components["override"]=False
    return '', 204

@app.route('/emergency')
def goto_emergency():
    return render_template('emergency.html', components=components)


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
        threading.Thread(target=emergency, args=("40%", str(components["inputs"]["moisture"]["value"])),daemon=True).start()
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


app.run()
