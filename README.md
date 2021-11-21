# TeslaMate to A Better Routeplanner (ABRP)

[![](https://img.shields.io/badge/Donate-PayPal-ff69b4.svg)](https://www.paypal.com/donate?hosted_button_id=9H6B9CRBL6V4E)

Sync your Tesla data between Teslamate and ABRP

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
DEBUG = True
~~~
4. Run the script
~~~
python ./teslamateMqttToABRP.py
~~~
