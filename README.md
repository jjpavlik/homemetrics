# homemetrics

Little home project to collect metrics from my house and eventually take actions on them. Kind of an IoT project in really really early stages as of now.

## Architecture

Right now the things look like in the picture below.
![Architecture](https://raw.githubusercontent.com/jjpavlik/homemetrics/master/architecture.png)

The Arduino is connected to the Raspberry over a USB serial connection.

### collector.py

This is the piece of code in charge of querying the Arduino for the sensors measurements. Once it gets the data from the Arduino it pushes the measurement to the SQS queue. Also uses OpenWeather API to get weather details and update the LCD Screen hooked to the Arduino.

### pusher.py

Ironically (now that I think of), this piece of code pulls the messages from the SQS queue and then pushes them into CW.

### arduino.ino

Is the code that runs on the Arduino, this is extremely ugly to be honest.

#### Uploading code to Arduino from the Pi

```
pi@raspberrypi:~ $ cd arduino-1.8.7/
pi@raspberrypi:~/arduino-1.8.7 $ ls
arduino          arduino-linux-setup.sh  hardware    java  libraries  revisions.txt  tools-builder
arduino-builder  examples                install.sh  lib   reference  tools          uninstall.sh
pi@raspberrypi:~/arduino-1.8.7 $ ./arduino --board arduino:avr:uno --port /dev/ttyACM0 --upload /opt/homemetrics/arduino.ino
Picked up JAVA_TOOL_OPTIONS:
Loading configuration...
Initialising packages...
Preparing boards...
Verifying...
Sketch uses 6154 bytes (19%) of program storage space. Maximum is 32256 bytes.
Global variables use 481 bytes (23%) of dynamic memory, leaving 1567 bytes for local variables. Maximum is 2048 bytes.
Uploading...
pi@raspberrypi:~/arduino-1.8.7 $
```

### install.sh

Simple bash script that "installs" puller.py and collector.py under /opt/homemetrics, and also adds two systemd Service Units to handle these two as services.

### collector.sh

Script used by collector.service so systemd can start/stop collector.py as a service

### pusher.sh

Script used by pusher.service so systemd can start/stop pusher.py as a service
