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
currentState = ""
hasChangedState = False
RESTART = 15


def on_connect(client, userdata, flags, rc):
    if conf.DEBUG:
        print("Connected to the TeslaMate MQTT")

    client.subscribe("teslamate/cars/" + str(conf.CAR_ID) + "/usable_battery_level")
    client.subscribe("teslamate/cars/" + str(conf.CAR_ID) + "/power")
    client.subscribe("teslamate/cars/" + str(conf.CAR_ID) + "/speed")
    client.subscribe("teslamate/cars/" + str(conf.CAR_ID) + "/latitude")
    client.subscribe("teslamate/cars/" + str(conf.CAR_ID) + "/longitude")
    client.subscribe("teslamate/cars/" + str(conf.CAR_ID) + "/state")
    client.subscribe("teslamate/cars/" + str(conf.CAR_ID) + "/heading")
    client.subscribe("teslamate/cars/" + str(conf.CAR_ID) + "/elevation")
    client.subscribe("teslamate/cars/" + str(conf.CAR_ID) + "/outside_temp")
    client.subscribe("teslamate/cars/" + str(conf.CAR_ID) + "/charger_voltage")
    client.subscribe("teslamate/cars/" + str(conf.CAR_ID) + "/charger_actual_current")
    client.subscribe("teslamate/cars/" + str(conf.CAR_ID) + "/odometer")
    client.subscribe("teslamate/cars/" + str(conf.CAR_ID) + "/rated_battery_range_km")
    client.subscribe("teslamate/cars/" + str(conf.CAR_ID) + "/charge_energy_added")


def on_disconnect(client, userdata, rc=0):
    if conf.DEBUG:
        print ("Disconnected: result code " + str(rc))

    client.loop_stop()
    sleep(RESTART)
    createMQTTConnection()


def on_message(client, userdata, message):
    global objTLM
    global hasChangedState
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
            if currentState != payload:
                currentState = payload
                hasChangedState = True
            if payload == "driving":
                objTLM["is_parked"] = 0
                objTLM["is_charging"] = 0
                objTLM["is_dcfc"] = 0
            elif payload == "charging" or payload == "supercharging":
                objTLM["is_parked"] = 1
                objTLM["is_charging"] = 1
                objTLM["is_dcfc"] = 0
                if payload == "supercharging":
                    objTLM["is_dcfc"] = 1
            else:
                objTLM["is_parked"] = 1
                objTLM["is_charging"] = 0
                objTLM["is_dcfc"] = 0
        elif topic == "charge_energy_added":
            objTLM["kwh_charged"] = float(payload)
        elif topic == "rated_battery_range_km":
            objTLM["est_battery_range"] = float(payload)

        if conf.DEBUG:
            print(topic + ": " + payload)

    except:
        print("Exception on_message(): ", sys.exc_info()[0], message.topic, message.payload)


def sendToABRP():
    try:
        if currentState != "charging" and currentState != "supercharging":
            # if "voltage" in objTLM:
            #     del objTLM["voltage"]
            # if "current" in objTLM:
            #     del objTLM["current"]
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
    except:
        print("Exception sendToABRP(): ", sys.exc_info()[0])
        print(objTLM)


def createMQTTConnection():
    global currentState
    currentState = ""

    client = mqtt.Client("teslamate2abrp")
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect

    try:
        if conf.DEBUG:
            print("Trying to connect to the MQTT")

        client.connect(str(conf.MQTT_SERVER), int(conf.MQTT_PORT), 30)
        client.loop_start()

    except:
        if conf.DEBUG:
            print("Error trying to connect to the MQTT")
        sleep(RESTART)
        createMQTTConnection()


def main():
    global hasChangedState
    createMQTTConnection()
    i = -1

    while True:
        i += 1
        sleep(5)

        if hasChangedState:
            if conf.DEBUG:
                print("New state: " + currentState)
            hasChangedState = False
            sendToABRP()

        else:
            if currentState == "charging" or currentState == "supercharging":
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
                        print("Online or parked")
                    sendToABRP()

        if i > 300:
            i = 0


if __name__ == '__main__':
    main()
