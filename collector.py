import device
import logging
#import homemetricsutils
import json
from time import sleep
import datetime
import sys
import getopt
import time
import fcntl

DEVICES = []
SENSORS = []
DEVICES_FILE = "devices.conf"
MEASUREMENTS = []

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

def store_collected_metric(destination, timestamp, sensor, value):
    """
    This function will try to push the measure just taken (and any pending
    measures) to the intermediate store. If the measure can't be stored for many
    reason, it will be appended to MEASUREMENTS list so it can be retried later on.
    """
    try:
        fcntl.lockf(destination, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError as e:
        logging.warn("Lock couldn't be acquired -" + str(e) + "-")
        logging.warn("Measurement will be temporary stored in memory.")
        MEASUREMENTS.append([timestamp, sensor, value])
    else:
        if len(MEASUREMENTS) > 0:# Means there's pending metrics to be stored
            for measure in MEASUREMENTS:
                destination.write(measure[0], measure[1], measure[2])
            MEASUREMENTS.clear()
        destination.write(timestamp + "," + sensor + "," + value + "\n")
        destination.flush()
        fcntl.lockf(destination, fcntl.LOCK_UN)

def load_sensor(data):
    pass

def usage():
    pass

def main():
    terminate = False
    debug = False
    frecuency = 60 #Number of seconds between measures

    try:
        opts, args = getopt.getopt(sys.argv[1:], "hdf:", ["help", "debug"])
    except getopt.GetoptError as err:
        print(err)  # will print something like "option -a not recognized"
        usage()
        sys.exit(2)
    for o, a in opts:
        if o == "-v":
            verbose = True
        elif o in ("-h", "--help"):
            usage()
            sys.exit()
        elif o in ("-d", "--debug"):
            debug = True
        elif o in "-f":
            frecuency = int(a)
        else:
            assert False, "Unhandled option"

    FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

    if debug:
        logging.basicConfig(format=FORMAT, level=logging.DEBUG)
    else:
        logging.basicConfig(format=FORMAT, level=logging.WARN)

    try:
        metrics_file = open("metrics.log","a")
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

    for dev in DEVICES:
        state = dev.ping_device()
        if state:
            logging.debug("Ping to device " + dev.get_name() + " worked.")
            dev.enable()
        else:
            logging.warn("Ping to device " + dev.get_name() + " failed, so the device has been disabled.")
            dev.disable()

    starttime = time.time()

    while not terminate:
        timestamp = str(datetime.datetime.now())
        for dev in DEVICES:
            if dev.is_enabled():
                logging.debug("Reading device " + str(dev.get_name()))
                measure = dev.read_sensor(0)
                logging.debug("Sensor read: " + str(measure))
                store_collected_metric(metrics_file, timestamp, dev.get_name(), measure)
            else:
                logging.warn("Skipping " + dev.get_name() + " because is disabled.")
        back_to_sleep_for = (60 - ((time.time() - starttime)%60))
        logging.debug("Sleeping for " + str(back_to_sleep_for))
        sleep(back_to_sleep_for)
    #do some house keeping
    logging.debug("Doing some house keeping and shutting down")
    return 0

if __name__ == '__main__':
    main()
