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
import signal
from botocore.exceptions import ClientError
from os import path

CONFIGURATION_FILE = "general.conf"
TERMINATE = False

def usage():
    pass

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

    try:
        response = client.put_metric_data(Namespace = namespace, MetricData = metric_data)
    except ClientError as e:
        logging.error("Some ClientError: " + e.response['Error']['Code'])
        return False
    except Exception as e:
        logging.error(e)
        return False

    logging.debug(response)
    return True

def get_available_messages(parameters):
    """
    Pull the messages from the queue if any
    """
    client = boto3.client("sqs")
    url = parameters['QUEUE']['url']
    messages = {}
    try:
        messages = client.receive_message(QueueUrl = url, MaxNumberOfMessages = 10, WaitTimeSeconds = 2)
    except ClientError as e:
        logging.error("Some ClientError: " + e.response['Error']['Code'])
    except Exception as e:
        logging.error(e)
    return messages

def acknowledge_message(message, parameters):
    """
    ACKs the message so the queue service can get rid of it
    """
    client = boto3.client("sqs")
    url = parameters['QUEUE']['url']

    try:
        client.delete_message(QueueUrl = url, ReceiptHandle = message['ReceiptHandle'])
    except ClientError as e:
        logging.error("Some ClientError: " + e.response['Error']['Code'])
    except Exception as e:
        logging.error(e)

def is_message_valid(message):
    """
    Some message field validation in order not to crash the pusher and to make
    sure we are getting good data from the sensors.
    """
    parts = json.loads(message)
    try:
        float(parts['value'])
    except ValueError as e:
        logging.warn(e)
        return False
    return True

def term_handler(signum, frame):
    """
    Just sets TERMINATE to True and goes back to where things were
    """
    global TERMINATE
    TERMINATE = True

def main():
    debug = False
    global METRICS_FILE
    global TERMINATE

    signal.signal(signal.SIGTERM, term_handler)

    configuration = configparser.ConfigParser()
    configuration.read(CONFIGURATION_FILE)
    frequency = int(configuration['PUSHER']['frequency'])

    try:
        opts, args = getopt.getopt(sys.argv[1:], "hdf:", ["help", "debug"])
    except getopt.GetoptError as err:
        print(err)  # will print something like "option -a not recognized"
        usage()
        sys.exit(2)
    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
            sys.exit()
        elif o in ("-d", "--debug"):
            debug = True
        elif o in "-f":
            frequency = int(a)
        else:
            print("Unhandled option")
            usage()
            sys.exit(2)

    FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

    if debug:
        logging.basicConfig(filename="pusher.log", format=FORMAT, level=logging.DEBUG)
    else:
        logging.basicConfig(filename="pusher.log", format=FORMAT, level=logging.INFO)

    logging.info("Starting pusher.py")
    starttime = time.time()
    while not TERMINATE:
        timestamp = str(datetime.datetime.now())
        messages = get_available_messages(configuration)
        if 'Messages' in messages.keys():
            for i in messages['Messages']:
                # In theory any message that hasn't been acked will be retried once and then moved to the deadletter queue.
                if is_message_valid(i['Body']):
                    res = push_metric(i['Body'], configuration)
                    if res:
                        acknowledge_message(i, configuration)
                    else:
                        logging.warn("For some reason message " + str(i) + " wasn't pushed correctly to CW.")

        if path.exists("debug"):
            if not debug: #If debug file was just created, enable DEBUG
                logging.basicConfig(level=logging.DEBUG)
                logging.info("DEBUG logging ENABLED")
        else:
            if debug: #If debug file was just deleted disable it (regardless of --debug start)
                logging.basicConfig(level=logging.INFO)
                logging.info("DEBUG logging DISABLED (back to INFO)")

        back_to_sleep_for = (frequency - ((time.time() - starttime)%frequency))
        logging.debug("Sleeping for " + str(back_to_sleep_for))
        time.sleep(back_to_sleep_for)

    logging.info("Terminating... doing some housekeeping now.")

if __name__ == "__main__":
    main()
