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
API_KEY = "32b2162f-9599-4647-8139-66e9f9528370"      
MQTT_SERVER = "@@@@@@@@"                              # MQTT server address (e.g. "127.0.0.1")
MQTT_PORT = "@@@@"                                    # MQTT server port (e.g. "1883")
USER_TOKEN = "@@@@@@@@-@@@@-@@@@-@@@@-@@@@@@@@@@@@"   # User token generated in ABRP
CAR_MODEL = "@@@@:@@:@@:@@@@:@@@@"                    # Car model (Find it on https://api.iternio.com/1/tlm/get_carmodels_list, e.g. "tesla:m3:19:bt36:none" for a Tesla Model 3 SR+ 2018-2020)
CAR_ID = "1"                                          # Car number (usually 1 if you only have a car)
DEBUG = True/False                                    # Habilitar o deshabilitar el modo de depuración
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