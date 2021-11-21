import paho.mqtt.client as mqtt
import requests
import sys
import datetime
import calendar
import config as conf
from time import sleep


state = ""
data = {
    "utc": 0,
    "soc": 0,
    "power": 0,
    "speed": 0,
    "lat": 0,
    "lon": 0,
    "elevation": 0,
    "is_charging": 0,
    "is_dcfc": 0,
    "is_parked": 0,
    "ext_temp": 0,
    "car_model": conf.CAR_MODEL,
    "voltage": 0,
    "current": 0,
    "kwh_charged": 0,
    "heading": 0,
    "odometer": 0
}
change_state = False
RESTART = 15


def on_connect(client, userdata, flags, rc):
    if conf.DEBUG:
        print("Connected to the TeslaMate MQTT")

    client.subscribe("teslamate/cars/" + str(conf.CAR_ID) + "/latitude")
    client.subscribe("teslamate/cars/" + str(conf.CAR_ID) + "/longitude")
    client.subscribe("teslamate/cars/" + str(conf.CAR_ID) + "/elevation")
    client.subscribe("teslamate/cars/" + str(conf.CAR_ID) + "/speed")
    client.subscribe("teslamate/cars/" + str(conf.CAR_ID) + "/power")
    client.subscribe("teslamate/cars/" + str(conf.CAR_ID) + "/heading")
    client.subscribe("teslamate/cars/" + str(conf.CAR_ID) + "/outside_temp")
    client.subscribe("teslamate/cars/" + str(conf.CAR_ID) + "/odometer")
    client.subscribe("teslamate/cars/" + str(conf.CAR_ID) + "/charger_actual_current")
    client.subscribe("teslamate/cars/" + str(conf.CAR_ID) + "/charger_voltage")
    client.subscribe("teslamate/cars/" + str(conf.CAR_ID) + "/state")
    client.subscribe("teslamate/cars/" + str(conf.CAR_ID) + "/battery_level")
    client.subscribe("teslamate/cars/" + str(conf.CAR_ID) + "/charge_energy_added")


def on_disconnect(client, userdata, rc=0):
    if conf.DEBUG:
        print ("Disconnected: result code " + str(rc))

    client.loop_stop()
    sleep(RESTART)
    createMQTTConnection()


def on_message(client, userdata, message):
    global data
    global change_state
    global state

    channel = ""
    try:
        payload = str(message.payload.decode("utf-8"))
        topic = str(message.topic).split('/')[3]

        if topic == "latitude":
            data["lat"] = float(payload)
        elif topic == "longitude":
            data["lon"] = float(payload)
        elif topic == "elevation":
            data["elevation"] = int(payload)
        elif topic == "speed":
            data["speed"] = int(payload)
        elif topic == "power":
            data["power"] = float(payload)
        elif topic == "heading":
            data["heading"] = int(payload)
        elif topic == "outside_temp":
            data["ext_temp"] = float(payload)
        elif topic == "odometer":
            data["odometer"] = float(payload)
        elif topic == "charger_actual_current":
            data["current"] = int(payload)
        elif topic == "charger_voltage":
            data["voltage"] = int(payload)
        elif topic == "state":
            if state != payload:
                state = payload
                change_state = True

            if payload == "driving":
                data["is_parked"] = 0
                data["is_charging"] = 0
                data["is_dcfc"] = 0
            elif payload == "charging":
                data["is_parked"] = 1
                data["is_charging"] = 1
                data["is_dcfc"] = 0
            elif payload == "supercharging":
                data["is_parked"] = 1
                data["is_charging"] = 1
                data["is_dcfc"] = 1
            else:
                data["is_parked"] = 1
                data["is_charging"] = 0
                data["is_dcfc"] = 0
        elif topic == "battery_level":
            data["soc"] = int(payload)
        elif topic == "charge_energy_added":
            data["kwh_charged"] = float(payload)

        if conf.DEBUG:
            print(topic + ": " + payload)

    except:
        print("Exception on_message(): ", sys.exc_info()[0], message.topic, message.payload)


def updateABRP():
    try:
        if state != "charging" and state != "supercharging":
            if "is_dcfc" in data: del data["is_dcfc"]
            if "voltage" in data: del data["voltage"]
            if "current" in data: del data["current"]
            if "kwh_charged" in data: del data["kwh_charged"]

        current_datetime = datetime.datetime.utcnow()
        current_timetuple = current_datetime.utctimetuple()
        data["utc"] = calendar.timegm(current_timetuple)

        url = "https://api.iternio.com/1/tlm/send?token=" + conf.USER_TOKEN
        headers = {"Authorization": "APIKEY " + conf.API_KEY}
        body = {"tlm": data}
        response = requests.post(url, headers=headers, json=body)
        if conf.DEBUG:
            print(data)
            print(response.text)
    except:
        print("Exception updateABRP(): ", sys.exc_info()[0])
        print(data)


def createMQTTConnection():
    global state
    state = ""

    client = mqtt.Client("teslamate-ABRP")
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
    global change_state

    createMQTTConnection()

    i = -1
    while True:
        i += 1
        sleep(5)

        if change_state:
            if conf.DEBUG:
                print("Changed state: " + state)
            change_state = False
            updateABRP()
        else:
            if state == "charging":
                if i % 6 == 0:
                    if conf.DEBUG:
                        print("Charging, updating every 30s")
                    updateABRP()
            elif state == "driving":
                if conf.DEBUG:
                    print("Driving, updating every 5s")
                updateABRP()
            elif state == "parked" or state == "online":
                if i % 300 == 0:
                    if conf.DEBUG:
                        print("Online, updating every 25min")
                    updateABRP()

        if i > 300:
            i = 0


if __name__ == '__main__':
    main()
