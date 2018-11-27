import serial
import interfaces
import logging

PROTOCOL = 16 # 0001 ____
RESPONSE = 0 # ____ 0000
REQUEST = 15 # ____ 1111

READ = 0  # 0000 ____
WRITE = 1 # 0001 ____
PING = 240 # 1111 0000
#Lower nible defines the sensor ...



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

    def get_location(self):
        return self.location

    def get_name(self):
        return self.device_name

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
        self.sensors = []
        self.buffer_size = 260

    def read_sensor(self, sensor):
        pass

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

        self._send_message(message)
        # PING Response packet should be 3 bytes long see Arduino_porotocol_draft.txt
        received_message = self._receive_message()
        if(len(received_message) != 3):
            print(received_message)
            return False
        # Check for RESPONSE and _get_message_id
        if received_message[0] == PROTOCOL|RESPONSE and received_message[1] == PING:
            return True
        return False

    def _send_message(self, message):
        self.comm.send_message(message)

    def _receive_message(self):
        return self.comm.receive_message()

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
