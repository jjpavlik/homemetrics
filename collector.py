import device
import logging
#import homemetricsutils
import json
from time import sleep
import datetime
import sys
import getopt

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
        #timestamp = str(datetime.datetime.now()).split('.')[0]
        timestamp = str(datetime.datetime.now())
        for dev in DEVICES:
            if dev.is_enabled():
                logging.debug("Reading sensor " + str(dev.get_name()))
                measure = dev.read_sensor(0)
                logging.debug("Sensor read: " + str(measure))
                metrics_file.write(timestamp + "," + measure + "\n")
                metrics_file.flush()
            else:
                logging.warn("Ping to device " + dev.get_name() + " failed")
        sleep(60 - ((time.time() - starttime)%60))
    #do some house keeping
    logging.debug("Doing some house keeping and shutting down")
    return 0

if __name__ == '__main__':
    main()
