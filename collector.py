import device
import logging
#import homemetricsutils
import json
from time import sleep

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

def load_sensor(data):
    pass

def loop():
    terminate = False
    while not terminate:
        for i in DEVICES:
            state = i.ping_device()
            if state:
                logging.debug("Ping to device "+i.get_name()+" worked")
            else:
                logging.warn("Ping to device "+i.get_name()+" failed")
        sleep(5)
    #do some house keeping
    logging.debug("Doing some house keeping and shutting down")

def main():
    FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(format=FORMAT, level=logging.DEBUG)

    logging.info("Loading " + DEVICES_FILE)
    with open(DEVICES_FILE) as f:
        aux_devices = json.load(f)

    for device in aux_devices:
        if device['device-type'] == "arduino":
            DEVICES.append(load_device(device))
        elif device['device-type'] == "sensor":
            SENSORS.append(load_sensor(device))
    logging.info("All devices loaded")
    return 0
#    return loop()

if __name__ == '__main__':
    main()
