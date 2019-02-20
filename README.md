# homemetrics

Little home project to collect metrics from my house and eventually take actions on them. Kind of an IoT project in really really early stages as of now.

## Architecture

Right now the things look like in the picture below.
![Architecture](https://raw.githubusercontent.com/jjpavlik/homemetrics/master/architecture.png)

The Arduino is connected to the Raspberry over a USB serial connection.

### collector.py

This is the piece of code in charge of querying the Arduino for the sensors measurements. Once it gets the data from the Arduino it pushes the measurement to the SQS queue.

### pusher.py

Ironically (now that I think of), this piece of code pulls the messages from the SQS queue and then pushes it into CW.

### arduino.ino

Is the code that runs on the Arduino, this is extremely ugly to be honest.

### install.sh

Simple bash script that "installs" puller.py and collector.py under /opt/homemetrics, and also adds two systemd Units to handle these two as services.

### collector.sh

Script used by collecctor.service so systemd can start collector.py as a service

### pusher.sh

Script used by pusher.service so systemd can start pusher.py as a service
