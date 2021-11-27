# TeslaMate to A Better Routeplanner (ABRP)

[![](https://img.shields.io/badge/Donate-PayPal-ff69b4.svg)](https://www.paypal.com/donate?hosted_button_id=9H6B9CRBL6V4E)

Sync your Tesla data between [Teslamate](https://docs.teslamate.org/) and [ABRP](https://abetterrouteplanner.com/).  

### Extra info

* Fork of [letienne/teslamate-abrp](https://github.com/letienne/teslamate-abrp).
* Modified following the documentation of:
  * [Iternio Telemetry API](https://documenter.getpostman.com/view/7396339/SWTK5a8w#fdb20525-51da-4195-8138-54deabe907d5)
  * [Open Vehicles](https://docs.openvehicles.com/en/latest/plugin/abrp/README.html)


## Requirements

* Python 2.7+
* Install dependencies of Python included in requirements.txt

## Instructions

1. Install all dependencies of Python
~~~
pip install -r requirements.txt
~~~
2. Create the `config.py` file
3. Configure the variables of your MQTT of Teslamate and ABRP inside `config.py` file
~~~
API_KEY = "@@@@@@@@-@@@@-@@@@-@@@@-@@@@@@@@@@@@"
MQTT_SERVER = "127.0.0.1"
MQTT_PORT = "1883"
USER_TOKEN = "@@@@@@@@-@@@@-@@@@-@@@@-@@@@@@@@@@@@"
CAR_MODEL = "@@@@:@@:@@:@@@@:@@@@"
CAR_ID = "1"
DEBUG = True/False
~~~
4. Run the script
* Run on command line (ideal for testing)
~~~
python ./teslamate2abrp.py
~~~
* Run in the background
~~~
nohup python ./teslamate2abrp.py &
~~~