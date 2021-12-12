import paho.mqtt.client as mqtt
import requests
import sys
from datetime import datetime
import calendar
import config as conf
from time import sleep
import logging
import logging.handlers

objTLM = {
    "utc": 0,
    "soc": 0,
    "power": 0,
    "speed": 0,
    "lat": 0,
    "lon": 0,
    "is_charging": False,
    "is_dcfc": True,
    "is_parked": False,
    "heading": 0,
    "elevation": 0,
    "ext_temp": 0,
    "voltage": 0,
    "current": 0,
    "odometer": 0,
    "est_battery_range": 0,
    "car_model": conf.CAR_MODEL
}
previousState = ""
currentState = ""
RESTART = 15
logger = logging.getLogger()


def setupLogging():
    if conf.DEBUG:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
    handler = logging.handlers.RotatingFileHandler('teslamate2abrp.log', maxBytes=10000000, backupCount=5)
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(funcName)s:%(lineno)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)


def on_connect(client, userdata, flags, rc):
    if conf.DEBUG:
        logger.info("Connected to the TeslaMate MQTT")

    client.subscribe("teslamate/cars/" + str(conf.CAR_ID) + "/#")


def on_disconnect(client, userdata, rc=0):
    if conf.DEBUG:
        logger.debug("Disconnected: result code " + str(rc))

    client.loop_stop()
    sleep(RESTART)
    createMQTTConnection()


def on_message(client, userdata, message):
    global objTLM
    global currentState

    try:
        topic = str(message.topic).split('/')[3]
        payload = str(message.payload.decode("utf-8"))

        if topic == "usable_battery_level":
            objTLM["soc"] = int(payload)
        elif topic == "latitude":
            objTLM["lat"] = float(payload)
        elif topic == "longitude":
            objTLM["lon"] = float(payload)
        elif topic == "elevation":
            objTLM["elevation"] = int(payload)
        elif topic == "speed":
            objTLM["speed"] = int(payload)
        elif topic == "power":
            objTLM["power"] = float(payload)
        elif topic == "heading":
            objTLM["heading"] = int(payload)
        elif topic == "outside_temp":
            objTLM["ext_temp"] = float(payload)
        elif topic == "odometer":
            objTLM["odometer"] = float(payload)
        elif topic == "charger_actual_current":
            objTLM["current"] = int(payload)
        elif topic == "charger_voltage":
            objTLM["voltage"] = int(payload)
        elif topic == "state":
            currentState = payload
            if payload == "driving":
                objTLM["is_parked"] = False
                objTLM["is_charging"] = False
                objTLM["is_dcfc"] = False
            elif payload == "charging":
                objTLM["is_parked"] = True
                objTLM["is_charging"] = True
                objTLM["is_dcfc"] = True
            else:
                objTLM["is_parked"] = True
                objTLM["is_charging"] = False
                objTLM["is_dcfc"] = False
        elif topic == "charge_energy_added":
            objTLM["kwh_charged"] = float(payload)
        elif topic == "est_battery_range_km":
            objTLM["est_battery_range"] = float(payload)
        elif topic == "charger_power":
            if int(payload) > 0:
                objTLM["is_charging"] = True
        elif topic == "shift_state":
            if payload == "P" or payload == "N":
                objTLM["is_parked"] = True
            elif payload == "D" or payload == "R":
                objTLM["is_parked"] = False

    except (ValueError, Exception):
        logger.error("Exception on_message(): ", sys.exc_info()[0], message.topic, message.payload)


def sendToABRP():
    global objTLM
    try:
        if currentState != "charging":
            if "kwh_charged" in objTLM:
                del objTLM["kwh_charged"]

        d = datetime.utcnow()
        objTLM["utc"] = calendar.timegm(d.utctimetuple())

        url = "https://api.iternio.com/1/tlm/send?token=" + conf.USER_TOKEN
        headers = {"Authorization": "APIKEY " + conf.API_KEY}
        body = {"tlm": objTLM}
        response = requests.post(url, headers=headers, json=body)
        if conf.DEBUG:
            logger.debug(objTLM)
            logger.debug(response.text)
    except (ValueError, Exception):
        logger.error("Exception sendToABRP(): ", sys.exc_info()[0])
        logger.error(objTLM)


def createMQTTConnection():
    global currentState
    currentState = ""

    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect

    try:
        if conf.DEBUG:
            logger.info("Trying to connect to the MQTT")

        client.connect(str(conf.MQTT_SERVER), int(conf.MQTT_PORT), 30)
        client.loop_start()

    except (ValueError, Exception):
        if conf.DEBUG:
            logger.error("Error trying to connect to the MQTT")
        sleep(RESTART)
        createMQTTConnection()


def main():
    global previousState
    setupLogging()
    createMQTTConnection()
    i = -1

    while True:
        i += 1
        sleep(5)

        if previousState != currentState:
            if conf.DEBUG:
                logger.debug("New state: " + currentState)
            previousState = currentState
            i = 300

        if currentState == "charging":
            if i % 2 == 0:
                if conf.DEBUG:
                    logger.debug("Charging")
                sendToABRP()
        elif currentState == "driving":
            if conf.DEBUG:
                logger.debug("Driving")
            sendToABRP()
        elif currentState == "parked" or currentState == "online":
            if i % 30 == 0:
                if conf.DEBUG:
                    logger.debug("Online / Parked")
                sendToABRP()

        if i > 30:
            i = -1


if __name__ == '__main__':
    main()
