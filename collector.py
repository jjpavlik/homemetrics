import device
import logging
import json
import datetime
import sys
import getopt
import time
import fcntl
import configparser
import boto3
from botocore.exceptions import ClientError
import signal
import requests

DEVICES = []
SENSORS = []
DEVICES_FILE = "devices.conf"
MEASUREMENTS = []
CONFIGURATION_FILE = "general.conf"
TERMINATE = False

def load_device(dev):
    '''
    Load the devices read from DEVICES_FILE
    '''
    logging.debug("Loading device "+str(device))
    device_name = dev['device-name']
    device_type = dev['device-type']
    device_access = dev['access']
    device_interface = dev['interface']
    device_location = dev['location']
    aux = device.Arduino(device = device_type, name = device_name, access = device_access, interface = device_interface, location = device_location)
    logging.debug("Loading device "+str(device))
    return aux

def update_temperature_table(room, temperature, timestamp):
    """
    Function in charge of updating the temperature item on the dynamodb table.
    This is later on read by Lambda as part of an Alexa skill for example.
    Maybe this should go in pusher.py... but in fairness pusher.py could be
    processing data out of order (due to SQS) and since I only want the most
    recent temperature available I push it directly from here.
    """
    client = boto3.resource("dynamodb")

    try:
        table = client.Table("temperatures")
        table.update_item(
            Key={'room':room},
            UpdateExpression='SET temperature=:val1, sensorTimestamp=:val2',
            ExpressionAttributeValues={':val1':temperature, ':val2':timestamp}
            )
    except Exception as e:
        logging.error(e)
        return False
    logging.debug("Stored temperature "+str(temperature)+" for room "+str(room)+" timestamp "+str(timestamp))
    return True

def store_collected_metric(parameters, timestamp, device, sensor, value):
    """
    Pushes the metric to a queue, so then they can be pulled from there.
    """
    client = boto3.client("sqs")
    url = parameters['QUEUE']['url']

    if len(MEASUREMENTS) > 0:
        logging.info("A few measurements queuing locally :O " + str(len(MEASUREMENTS)) + " trying to push them now")
        for measure in MEASUREMENTS:
            res = __push_message(client, url, measure)
            if not res:
                logging.info("Appending measure to push later (n attemp)")
                MEASUREMENTS.append(measure)
    message = json.dumps({"timestamp":timestamp, "device":device, "sensor":sensor, "value":value})
    res = __push_message(client, url, message)
    if not res:
        logging.info("Appending measure to push later (first attemp)")
        MEASUREMENTS.append(measure)

def __push_message(client, url, message):
    """
    Function that actually pushes the message to the queue.
    """
    try:
        client.send_message(QueueUrl = url, MessageBody = message)
    except ClientError as e:
        logging.error("Some ClientError: " + e.response['Error']['Code'])
        return False
    except Exception as e:
        logging.error(e)
        return False
    return True

def term_handler(signum, frame):
    """
    Termination handler, sets TERMINATE to True and let things go back to where
    they were.
    """
    global TERMINATE
    TERMINATE = True

def load_sensor(data):
    pass

def usage():
    pass

def main():
    global TERMINATE

    debug = False

    signal.signal(signal.SIGTERM, term_handler)

    configuration = configparser.ConfigParser()
    configuration.read(CONFIGURATION_FILE)
    frequency = int(configuration['COLLECTOR']['frequency'])

    FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(filename='collector.log', format=FORMAT, level=logging.DEBUG)

    try:
        opts, args = getopt.getopt(sys.argv[1:], "hdf:", ["help", "debug", "openweather"])
    except getopt.GetoptError as err:
        print(err)  # will print something like "option -a not recognized"
        usage()
        sys.exit(2)
    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
            sys.exit()
        elif o in ("-d", "--debug"):
            debug = True
        elif o in "-f":
            frequency = int(a)
        elif o in ("--openweather"):
            import openweather
            try:
                ow = Openweather(
                    configuration['COLLECTOR']['openweathermap-key'],
                    configuration['COLLECTOR']['openweathermap-name'],
                    configuration['COLLECTOR']['openweathermap-city-id'])
                openweather_enabled = True
            except Exception as e:
                logging.warn("OpenWeather has been disabled :(... due to " + str(e))
                openweather_enabled = False
        else:
            assert False, "Unhandled option"

    if not debug:
        logging.basicConfig(filename='collector.log', format=FORMAT, level=logging.INFO)

    logging.info("Loading " + DEVICES_FILE)
    with open(DEVICES_FILE) as f:
        aux_devices = json.load(f)

    for device in aux_devices:
        if device['device-type'] == "arduino":
            DEVICES.append(load_device(device))
        elif device['device-type'] == "sensor":
            SENSORS.append(load_sensor(device))
    logging.info("All devices loaded")
    time.sleep(5)
    ####
    for dev in DEVICES:
        logging.info("Identifying devices for " + dev.get_name())
        dev.identify_device_sensors()
    time.sleep(5)

    for dev in DEVICES:
        state = dev.ping_device()
        if state:
            logging.debug("Ping to device " + dev.get_name() + " worked.")
            dev.enable()
        else:
            logging.warn("Ping to device " + dev.get_name() + " failed, so the device has been disabled.")
            dev.disable()

    starttime = time.time()

    while not TERMINATE:
        timestamp = str(datetime.datetime.now())
        for dev in DEVICES:
            if dev.is_enabled():
                logging.debug("Reading device " + str(dev.get_name()))
                sensor = 0 # Hardcoded sensor 1 (temp1)
                measure = dev.read_sensor(sensor)
                logging.debug("Sensor read: " + str(measure))
                store_collected_metric(configuration, timestamp, dev.get_name(), dev.get_sensor_name(sensor), measure)
                update_temperature_table("livingroom", measure, timestamp)

                if openweather_enabled:
                    sensor = 2
                    logging.debug("Retrieving data from OpenWeatherMap.")
                    weather = ow.get_weather()
                    temperature = ow.get_temperature()
                    if len(weather) > 16:#I should keep an eye on the length of "description" since this will go to the 16x2 LCD display
                            weather = weather[:16]
                    dev.write_sensor(sensor, (temperature, weather))
            else:
                logging.warn("Skipping " + dev.get_name() + " because is disabled.")
        back_to_sleep_for = (frequency - ((time.time() - starttime)%frequency))
        logging.debug("Sleeping for " + str(back_to_sleep_for))
        time.sleep(back_to_sleep_for)

    #do some house keeping
    logging.info("Terminating... doing some house keeping and shutting down")
    return 0

if __name__ == '__main__':
    main()
