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
import signal
import requests

DEVICES = []
SENSORS = []
DEVICES_FILE = "devices.conf"
MEASUREMENTS = []
METRICS_FILE = "metrics.log"
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

def store_collected_metric(parameters, timestamp, device, sensor, value):
    """
    Pushes the metric to a queue, so then they can be pulled from there.
    """
    client = boto3.client("sqs")
    url = parameters['QUEUE']['url']

    if len(MEASUREMENTS) > 0:
        logging.debug("A few measurements queuing locally :O " + str(len(MEASUREMENTS)) + " trying to push them now")
        for measure in MEASUREMENTS:
            res = __push_message(client, url, measure)
            if not res:
                MEASUREMENTS.append(measure)
    message = json.dumps({"timestamp":timestamp, "device":device, "sensor":sensor, "value":value})
    res = __push_message(client, url, message)
    if not res:
        MEASUREMENTS.append(measure)

def __push_message(client, url, message):
    """
    Function that actually pushes the message to the queue.
    """
    client.send_message(QueueUrl = url, MessageBody = message)
    return True

def term_handler(signum, frame):
    """
    Termination handler, sets TERMINATE to True and let things go back to where
    they were.
    """
    global TERMINATE
    TERMINATE = True

def openweather_get_weather(city_id, key):
    """
    This function uses https://openweathermap.org/current API to get weather
    data for the given city_id. Example
    curl "https://api.openweathermap.org/data/2.5/weather?id=2964574&units=metric&appid=LALALA"
        {"coord":{"lon":-6.27,"lat":53.34},
        "weather":[{"id":802,"main":"Clouds","description":"scattered clouds","icon":"03n"}],"base":"stations",
        "main":{"temp":5.5,"pressure":1014,"humidity":81,"temp_min":5,"temp_max":6},
        "visibility":10000,"wind":{"speed":3.1,"deg":220},"clouds":{"all":40},"dt":1549407600,
        ...}
    """
    parameters = {"id":city_id, "units":"metric", "appid":key}
    url = "https://api.openweathermap.org/data/2.5/weather"
    response = requests.get(url, params = parameters)

    if response.status_code == requests.codes.ok:
        json_data = response.json()
        logging.debug(json_data["main"])
        #json_data["main"]["temp"]
        #json_data["weather"][0]["description"]
        return json_data
    logging.warn("Call to OpenWeatherMap returned " + str(response.status_code))
    return False

def load_sensor(data):
    pass

def usage():
    pass

def main():
    global TERMINATE

    debug = False
    openweather = False
    openweather_frequency = 2 #Effectively update the data every 2 cycles
    openweather_current_temp = 0
    openweather_current_weather = "None"

    signal.signal(signal.SIGTERM, term_handler)

    configuration = configparser.ConfigParser()
    configuration.read(CONFIGURATION_FILE)
    frequency = int(configuration['COLLECTOR']['frequency'])

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
            openweathermap_key = configuration['COLLECTOR']['openweathermap-key']
            openweathermap_name = configuration['COLLECTOR']['openweathermap-name']
            openweathermap_city_id = configuration['COLLECTOR']['openweathermap-city-id']
            openweather = True
        else:
            assert False, "Unhandled option"

    FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

    if debug:
        logging.basicConfig(filename='collector.log', format=FORMAT, level=logging.DEBUG)
    else:
        logging.basicConfig(filename='collector.log', format=FORMAT, level=logging.WARN)

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

    #Colleccting weather for Dublin from OpenWeatherMap
    if openweather == True:
        logging.debug("Retrieving first weather metric from OpenWeatherMap API")
        weather = openweather_get_weather(openweathermap_city_id, openweathermap_key)
        if weather == False:
            openweather_current_temp = "100"
            openweather_current_weather = "No data :("
        else:
            openweather_current_temp = weather["main"]["temp"]
            openweather_current_weather = weather["weather"][0]["description"]
            #I should keep an eye on the length of "description" since this will go to the 16x2 LCD display

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

                if openweather and openweather_frequency == 0:
                    logging.debug("Updating data from OpenWeatherMap.")
                    openweather_frequency = 2
                    weather = openweather_get_weather(openweathermap_city_id, openweathermap_key)
                    if weather == False:
                        openweather_current_temp = "100"
                        openweather_current_weather = "No data :("
                    else:
                        openweather_current_temp = weather["main"]["temp"]
                        openweather_current_weather = weather["weather"][0]["description"]
                        #I should keep an eye on the length of "description" since this will go to the 16x2 LCD display
                        dev.write_sensor(sensor, (openweather_current_temp, openweather_current_weather))
                else:
                    openweather_frequency = openweather_frequency - 1

            else:
                logging.warn("Skipping " + dev.get_name() + " because is disabled.")
        back_to_sleep_for = (frequency - ((time.time() - starttime)%frequency))
        logging.debug("Sleeping for " + str(back_to_sleep_for))
        time.sleep(back_to_sleep_for)

    #do some house keeping
    logging.debug("Terminating... doing some house keeping and shutting down")
    return 0

if __name__ == '__main__':
    main()
