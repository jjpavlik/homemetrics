import serial
import interfaces
import logging

PROTOCOL = 16 # 0001 ____
RESPONSE = 15 # ____ 1111
REQUEST = 0 # ____ 0000

#Higher nible B2
READ = 0  # 0000 ____
WRITE = 16 # 0001 ____
PING = 240 # 1111 0000
CONTROL = 224 #1110 ____
ERROR 192 # 1100 ____
#Lower nible B2 defines the sensor ...
GET_SENSORS = 15 #____ 1111



class Device():
    """
    Generic device Class
    """

    def __init__(self, device = "dummy", name = "dummy", access = "dummy", interface = "dummy", location = "dummy"):
        self.device_type = device
        self.device_name = name
        self.access = access
        self.interface = interface
        self.location = location
        self.message_id = 0
        self.available_sensors = []
        self.enabled = False

    def get_location(self):
        return self.location

    def get_name(self):
        return self.device_name

    def get_sensors_list(self):
        return self.available_sensors

    def add_sensor(self, sensor):
        self.available_sensors.append(sensor)

    def is_enabled(self):
        return self.enabled

    def disable(self):
        self.enabled = False

    def enable(self):
        self.enabled = True

class Arduino(Device):
    """
    Specification of Device for Arduino devices
    """

    def __init__(self,device = "dummy", name = "dummy", access = "dummy", interface = "dummy", location = "dummy"):
        super().__init__(device, name, access, interface, location)
        if self.interface == "serialUSB":
            self.comm = interfaces.SerialUSB(access)
        else:
            raise ValueError("Unknown interface: " + self.interface)
        self.buffer_size = 256

    def read_sensor(self, sensor_id):
        """
        Reading a given sensor from the device
        """
        message_id = self._get_message_id()
        message = bytearray([PROTOCOL|REQUEST]) #B0
        message.append(message_id)              #B1
        message.append(READ)                    #B2
        message.append(sensor_id)			#B3
        message.append(5)			#B4

        logging.debug("Message ID " + str(message_id))
        logging.debug("Sending:" + str(message))
        self._send_message(message)
        received_message = self._receive_message()
        logging.debug("Received: " + str(received_message))
        return self._parse_sensor_read(received_message)

    def write_sensor(self, sensor_id, data):
        """
        This function is meant to be able to update sensor information or send
        data for example to update the LCD.
        """
        message_id = self._get_message_id()
        message = bytearray([PROTOCOL | REQUEST]) #B0
        message.append(message_id)              #B1
        message.append(WRITE | 2)                    #B2
        message.append(sensor_id)			#B3 is actually the data format, so this is just a placeholder here.

        logging.debug("About to write to sensor " + self.available_sensors[sensor_id]['name'] + " type " + str(self.available_sensors[sensor_id]['type']))
        logging.debug("Data to be written: " + str(data))
        if self.available_sensors[sensor_id]['type'] == 32: #Sensor is actually a LCD display
            temp = str(data[0])
            description = data[1]
            slot = data[2]
            message.append(5 + len(temp) + 1 + len(description) + 1 + 1) #B4 SIZE
            #Copy the letters one by one on the message payload.
            aux = list(temp)
            for i in aux:
                message.append(ord(i))
            message.append(ord('\n'))
            aux = list(description)
            for i in aux:
                message.append(ord(i))
            message.append(ord('\n'))
            message.append(ord(str(slot)) - 48)#Terrible workaround
        else:
            message.append(5) #B4

        #Send the message
        logging.debug("Message ID " + str(message_id))
        logging.debug("Sending:" + str(message))
        self._send_message(message)
        received_message = self._receive_message()
        logging.debug("Received message " + str(received_message))
        if received_message[2] == ERROR:
            return False
        return True

    def _good_response(sent_id, received_id):
        """
        See wether the returned packet is an actual response of the one previously sent
        Initially just check that the packet returned ID matches
        """
        if sent_id == received_id:
            return True
        return False

    def get_sensor_name(self, id):
        return self.available_sensors[id]['name']

    def identify_device_sensors(self):
        """
        Ideally, this would send a message to the Arduino asking for the available sensors.
        Then parse the sensors and keep them in available_sensors[]
        """
        message_id = self._get_message_id()
        message = bytearray([PROTOCOL|REQUEST]) #B0
        message.append(message_id)              #B1
        message.append(CONTROL|GET_SENSORS)                    #B2
        message.append(0)			#B3
        message.append(5)			#B4

        logging.debug("Message ID " + str(message_id))
        logging.debug("Sending: " + str(message))
        self._send_message(message)
        # Now wait for the response
        received_message = self._receive_message()
        logging.debug("Received: " + str(received_message))
        message_length = len(received_message)
        self._parse_discovered_sensors(received_message)
        return True

    def _parse_sensor_read(self, message):
        """
        Pull the sensor read out of the message_id
        """
        message_length = len(message)
        data = message[5:message_length]
        value = data.decode('ascii')
        return value

    def _parse_discovered_sensors(self, message):
        """
        Parse the sensors provided by the device. Remember format is:
        sensor_name\n[type|format]
        """
        message_length = len(message)
        index = 5
        start = index
        while index < message_length:
            index = index + 1
            if message[index] == 10: #'\n'
                index = index + 1
                name = message[start:index-1]
                sensor = {'name':name.decode('ascii'), 'type':message[index] & 240, 'format': message[index] & 15}
                logging.debug("Sensor discovered: " + str(sensor))
                self.add_sensor(sensor)
                index = index + 1
                start = index

    def read_details(self):
        pass

    def _get_message_id(self):
        """
        Simple wrapper function to make sure the message_id doesn't go beyond the byte frontier.
        """
        if self.message_id == 255:
            self.message_id = 0
        else:
            self.message_id = self.message_id + 1
        return self.message_id

    def ping_device(self):
        """
        Kind of health check function. Sends a PING type packet and waits for the corresponding response.
        """
        message_id = self._get_message_id()
        message = bytearray([PROTOCOL|REQUEST]) #B0
        message.append(message_id)              #B1
        message.append(PING)                    #B2
        message.append(0)			#B3
        message.append(5)			#B4

        logging.debug("Message ID " + str(message_id))
        logging.debug("Sending:" + str(message))
        self._send_message(message)
        # PING Response packet should be 5 bytes long see Arduino_porotocol_draft.txt
        received_message = self._receive_message()
        logging.debug("Received: " + str(received_message))
        message_length = len(received_message)
        if(message_length != 5):
            if message_length == 0:
                logging.warn("PING to " + self.get_name() + " Timed out")
            else:
                logging.error("Looks like " + self.get_name() + " returned a malformed message: " + str(received_message))
            return False
        # Check for RESPONSE and _get_message_id
        if received_message[0] == PROTOCOL|RESPONSE and received_message[2] == PING:
            return True
        return False

    def _send_message(self, message):
        self.comm.send_message(message)

    def _receive_message(self):
        received_message = self.comm.receive_message()
        if received_message[2] == ERROR:
            logging.error("Response to message ID "+ str(received_message[1]) +" returned error code " + str(receive_message[3]))
        return message

class Dummy(Device):
    """
    Specification of Device called Dummy just to have a testing device for the logic
    """

    def __init__(self, device = "dummy", access = "dummy", interface = "dummy", location = "dummy"):
        super().__init__("dummy", "dummy", "dummy", "dummy")
        self.real_interface = "dummy"
        self.name = self.get_name()
        self.location = "Dummy location"

    def get_details(self):
        return "Dummy details"

    def get_name(self):
        return "Dummy Device"
