import device
import logging
#import homemetricsutils
import json
from time import sleep
import datetime
import sys

DEVICES = []
SENSORS = []
DEVICES_FILE = "devices.conf"

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

def store_collected_metric(sensor, value):
    pass

def load_sensor(data):
    pass

def main():
    terminate = False
    FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(format=FORMAT, level=logging.DEBUG)

    try:
        metrics_file = open("metrics.log","w")
    except:
        print("Unexpected error:", sys.exc_info()[0])
        raise

    logging.info("Loading " + DEVICES_FILE)
    with open(DEVICES_FILE) as f:
        aux_devices = json.load(f)

    for device in aux_devices:
        if device['device-type'] == "arduino":
            DEVICES.append(load_device(device))
        elif device['device-type'] == "sensor":
            SENSORS.append(load_sensor(device))
    logging.info("All devices loaded")
    sleep(5)
    ####
    for dev in DEVICES:
        logging.info("Identifying devices for " + dev.get_name())
        dev.identify_device_sensors()
    sleep(5)
    while not terminate:
        for dev in DEVICES:
            state = dev.ping_device()
            if state:
                logging.debug("Ping to device " + dev.get_name() + " worked")
                logging.debug("Reading sensor 0")
                measure = dev.read_sensor(0)
                logging.debug("Sensor read: " + str(measure))
                ts = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
                metrics_file.write(ts + "," + measure)
            else:
                logging.warn("Ping to device " + dev.get_name() + " failed")
        sleep(2)
    #do some house keeping
    logging.debug("Doing some house keeping and shutting down")
    return 0
#    return loop()

if __name__ == '__main__':
    main()
