import time
import logging
import getopt
import sys
import time
import datetime
import boto3
import json
import re
import configparser 

METRICS_FILE = "metrics.log"
LAST_DATAPOINT_FILE = "pusher_last_datapoint.log"
LAST_DATAPOINT = ""
CONFIGURATION_FILE = "general.conf"

def usage():
    pass

def parse_metric_line(line):
    """
    Just splits the line into the expected 4 fields, otherwise raises ValueError.
    Some more field validation should be done here as well according to the fields.
    """
    parts = line.split(',')
    if len(parts) != 4:
        raise ValueError("Wrong number of parts in that line.")
    return parts

def push_metric(message, configuration):
    """
    Pushes a given metric to CW, that's pretty much it.
    """
    parts = json.loads(message)
    logging.debug("Pushing metric: " + str(parts))
    client = boto3.client("cloudwatch")

    namespace = configuration['PUSHER']['metric-namespace']

    metric_name = parts['device'] + "-" + parts['sensor']
    timestamp = parts['timestamp']
    dimensions = [{"Name":"Device","Value":parts['device']},{"Name":"Sensor","Value":parts['sensor']}]
    value = float(parts['value'])
    counts = 1
    metric_data = [{"MetricName":metric_name, "Timestamp":timestamp, "Value":value, "Dimensions":dimensions}]

    response = client.put_metric_data(Namespace = namespace, MetricData = metric_data)
    logging.debug(response)

    return True

def save_last_datapoint(last_datapoint):
    """
    Stores in LAST_DATAPOINT_FILE the offset witin metrics.log for the next datapoint in order to know where to start next time.
    When pusher.py starts this value should be picked up and used to seek the next metric to be pushed.
    """
    logging.debug("Storing " + last_datapoint + " in " + LAST_DATAPOINT_FILE)
    with open(LAST_DATAPOINT_FILE,"w") as f:
        f.truncate()
        json.dump({"last-datapoint":last_datapoint, "timestamp":time.time()},f)

def read_last_datapoint():
    """
    Picks the lastest pushed datapoint
    """
    try:
        f = open(LAST_DATAPOINT_FILE,"r")
    except e:
        raise e
    else:
        last_datapoint = json.load(f)
    return last_datapoint

def get_available_messages(parameters):
    """
    Pull the messages from the queue if any
    """
    client = boto3.client("sqs")
    url = parameters['QUEUE']['url']
    messages = client.receive_message(QueueUrl = url, MaxNumberOfMessages = 10, WaitTimeSeconds = 2)
    return messages

def acknowledge_message(message, parameters):
    """
    ACKs the message so the queue service can get rid of it
    """
    client = boto3.client("sqs")
    url = parameters['QUEUE']['url']

    client.delete_message(QueueUrl = url, ReceiptHandle = message['ReceiptHandle'])

def main():
    terminate = False
    debug = True
    resume = True
    use_queue = False
    global METRICS_FILE

    configuration = configparser.ConfigParser()
    configuration.read(CONFIGURATION_FILE)
    frequency = int(configuration['PUSHER']['frequency'])

    try:
        opts, args = getopt.getopt(sys.argv[1:], "hdf:m:q", ["help", "debug"])
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
            frequency = int(a)
        elif o in "-q":
            use_queue = True
        elif o in "-m":
             METRICS_FILE = str(a)
        else:
            print("Unhandled option")
            usage()
            sys.exit(2)

    FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    if debug:
        logging.basicConfig(filename="pusher.log", format=FORMAT, level=logging.DEBUG)
    else:
        logging.basicConfig(filename="pusher.log", format=FORMAT, level=logging.WARN)

    starttime = time.time()
    while not terminate:
        timestamp = str(datetime.datetime.now())
        messages = get_available_messages(configuration)
        if 'Messages' in messages.keys():
            for i in messages['Messages']:
                res = push_metric(i['Body'], configuration)
                if res:
                    acknowledge_message(i, configuration)
        back_to_sleep_for = (frequency - ((time.time() - starttime)%frequency))
        logging.debug("Sleeping for " + str(back_to_sleep_for))
        time.sleep(back_to_sleep_for)

        if terminate:
            pass
            #Do some housekeeping and finish

if __name__ == "__main__":
    main()
