I think the following should be enough as protocol to reach out to the Arduino for details, sensors, health check, etc.

# Protocol Version 2

The packets have the following format:

```
 ___B0____ ___B1___ ___B2____ ___B3____ ___B4___ _________
|         |        |         |         |        |         ...
|____|____|________|____|____|____|____|________|_________
```

## Description:

```
B0: High nible for protocol version (ie. 0001 for v1).
    Lower nible for packet type (ie. Request 0000, Response 1111)
B1: Packet ID, this field is to match packet request and responses. So technically we can have up to 255 packets in transit (not gonna happen ever xD)
B2: High nible for Operation type (ie. Read 0000, Write 0001, Ping 1111, Control 1110)
    Lower nible specifics of the operation (ie. read XXX sensor). Use 1111 to list sensors.
B3: Data format (ie. int, float represented in binary, way too many options I guess...)
B4: Total number of bytes in the packet. The smallest packet is 5 bytes (PING packet, request/response). If I moved this to B3, the smallest packet could be 4 bytes instead... (maybe one day).
B5 to B255: Potentially data
```

## Conversations:

### PING

This is a simple ping/pong message for health check, to confirm the device is responsive.

#### PING REQUEST (5 bytes)
```
0001 0000 - PACKET_ID - 1111 0000 - 0000 0000 - 0000 0101
```
#### PING RESPONSE (5 bytes)
```
0001 1111 - PACKET_ID - 1111 0000 - 0000 0000 - 0000 0101
```
### Read available devices:

This message should provide the device the chance to tell the collector what are the available sensors it can later on request. The request is pretty straight forward.
However the response can be complex.Fromat should be something like (starting in B5):

```
sensor_name\n[type|format]
```
Where:

* sensor_name is a char array, 2 or more bytes.
* "\n" byte will act as separator between sensors.
* type will be the higher nible of the first byte after "\n" and can be
  * temp = 0000
  * humidity = 0001
  * LCD Screen = 0002
  * etc
* format will be the lower nible of the first byte after "\n" and can be
  * int = 0000
  * float = 0001
  * char = 0010
  * etc

#### GET DEVICE SENSORS (5 bytes)
```
0001 0000 - PACKET_ID - 1110 1111 - 0000 0000 - 0000 0101
```

#### RESPONSE PACKET (>5 bytes)
```
0001 1111 - PACKET_ID - 1110 1111 - 0000 0000 - 0001 0011 - temp1\n0temp2\n1
```

### WRITE/UPDATE a given sensor:

This should allow the collector.py code to send write/update commands to for
example update the text showed on an LCD display.

#### WRITE MESSAGE (>5 bytes):
```
0001 0000 - PACKET_ID - 0001 0010 - 0000 0000 - 0000 0101 - hello world\ngood\nSLOT
```
SLOT is a one byte number that defines the LCD slot the text will go to.

#### RESPONSE PACKET (5 bytes):
```
0001 1111 - PACKET_ID - 0001 0010 - 0000 0000 - 0000 0101
```
