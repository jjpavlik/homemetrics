import serial

class Interface:
    """
    Generic Interface Class
    """

    def __init__(self, access = "dummy", interface = "dummy"):
        self.access = access
        self.interface = Interface

class SerialUSB(Interface):
    """
    Specification for SerialUSB interface
    """

    def __init__(self, access = "/dev/ttyACM0"):
        super().__init__(access, interface = "SerialUSB")
        #help(serial.Serial.__init__), looks like the default parameters are good, maybe we should set the timeout?
        self.real_interfae = serial.Serial(self.access, timeout = 2, writeTimeout = 2)

    def send_message(self, message):
        self.real_interfae.write(message)

    def receive_message(self):
        aux = self.real_interfae.read(-1)
        
    def receive_message_bytes(self, size):
        aux = self.real_interfae.read(size)

    def _send_byte(self, byte):
        pass

    def _receive_byte(self):
        pass

class Dummy(Interface):
    def __init__(self, access = "dummy"):
        pass
