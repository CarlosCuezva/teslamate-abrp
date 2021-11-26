import paho.mqtt.client as mqtt
import requests
import sys
from datetime import datetime
import calendar
import config as conf
from time import sleep

objTLM = {
    "utc": 0,
    "soc": 0,
    "power": 0,
    "speed": 0,
    "lat": 0,
    "lon": 0,
    "is_charging": 0,
    "is_dcfc": 0,
    "is_parked": 0,
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


def on_connect(client, userdata, flags, rc):
    if conf.DEBUG:
        print("Connected to the TeslaMate MQTT")

    client.subscribe("teslamate/cars/" + str(conf.CAR_ID) + "/#")


def on_disconnect(client, userdata, rc=0):
    if conf.DEBUG:
        print("Disconnected: result code " + str(rc))

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
            if objTLM["is_charging"] == 1 and int(payload) < -22:
                objTLM["is_dcfc"] = 1
        elif topic == "heading":
            objTLM["heading"] = int(payload)
        elif topic == "outside_temp":
            objTLM["ext_temp"] = float(payload)
        elif topic == "odometer":
            objTLM["odometer"] = float(payload)
        elif topic == "charger_actual_current":
            if int(payload) > 0:
                objTLM["current"] = int(payload)
        elif topic == "charger_voltage":
            if objTLM["is_charging"] == 1:
                objTLM["voltage"] = int(payload)
        elif topic == "state":
            currentState = payload
            if payload == "driving":
                objTLM["is_parked"] = 0
                objTLM["is_charging"] = 0
                objTLM["is_dcfc"] = 0
            elif payload == "charging":
                objTLM["is_parked"] = 1
                objTLM["is_charging"] = 1
                objTLM["is_dcfc"] = 0
            else:
                objTLM["is_parked"] = 1
                objTLM["is_charging"] = 0
                objTLM["is_dcfc"] = 0
        elif topic == "charge_energy_added":
            objTLM["kwh_charged"] = float(payload)
        elif topic == "est_battery_range_km":
            objTLM["est_battery_range"] = float(payload)
        elif topic == "charger_power":
            if int(payload) > 0:
                objTLM["is_charging"] = 1
                if int(payload) > 22:
                    objTLM["is_dcfc"] = 1
        elif topic == "shift_state":
            if payload == "P" or payload == "N":
                objTLM["is_parked"] = "1"
            elif payload == "D" or payload == "R":
                objTLM["is_parked"] = "0"

        if conf.DEBUG:
            print(topic + ": " + payload)

    except (ValueError, Exception):
        print("Exception on_message(): ", sys.exc_info()[0], message.topic, message.payload)


def sendToABRP():
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
            print(objTLM)
            print(response.text)
    except (ValueError, Exception):
        print("Exception sendToABRP(): ", sys.exc_info()[0])
        print(objTLM)


def createMQTTConnection():
    global currentState
    currentState = ""

    client = mqtt.Client("teslamate-abrp")
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect

    try:
        if conf.DEBUG:
            print("Trying to connect to the MQTT")

        client.connect(str(conf.MQTT_SERVER), int(conf.MQTT_PORT), 30)
        client.loop_start()

    except (ValueError, Exception):
        if conf.DEBUG:
            print("Error trying to connect to the MQTT")
        sleep(RESTART)
        createMQTTConnection()


def main():
    global previousState
    createMQTTConnection()
    i = -1

    while True:
        i += 1
        sleep(5)

        if currentState == "charging":
            if i % 2 == 0:
                if conf.DEBUG:
                    print("Charging")
                sendToABRP()
        elif currentState == "driving":
            if conf.DEBUG:
                print("Driving")
            sendToABRP()
        elif currentState == "parked" or currentState == "online":
            if i % 300 == 0:
                if conf.DEBUG:
                    print("Online / Parked")
                sendToABRP()

        if i > 300:
            i = 0


if __name__ == '__main__':
    main()
