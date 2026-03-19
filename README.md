# PyForPi
## Logic
1. `app.py`
  2. starts a local web server
  3. reads values from sensors
  4. assigns all the values to a python dictionary
  5. converts the dictionary to a `.json` file and sends it to browser
6. browser (`templates/index.html`)
  7. uses `fetch()` to receive the `.json` file
  8. uses `forEach()` to assign values from the `.json` file to `<span>` tags in the html

## Sensors

| Sensor                  | Quantity             | Remarks                            |
| ----------------------- | -------------------- | ---------------------------------- |
| MQ-135                  | Air Quality          | Uses analogue-to-digital converter |
| YL69 \| HC38            | Soil Moisture        | Uses analogue-to-digital converter |
| DHT22                   | Ambient Temperature  | Outputs digital values             |
| DHT22                   | Humidity             | Outputs digital values             |
| Internal Thermal Sensor | Internal Temperature | Read using a shell command         |
