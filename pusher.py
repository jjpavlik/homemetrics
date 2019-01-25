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

CONFIGURATION_FILE = "general.conf"

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

    response = client.put_metric_data(Namespace = namespace, MetricData = metric_data)
    logging.debug(response)

    return True


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
    global METRICS_FILE

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
