import time
import logging
import getopt
import sys
import time
import datetime
import boto3
import json

METRICS_FILE = "metrics.log"
LAST_DATAPOINT_FILE = "pusher_last_datapoint.log"
LAST_DATAPOINT = ""

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

def push_metric(parts):
    """
    Pushes a given metric to CW, that's pretty much it.
    """
    logging.debug("Pushing metric: " + str(parts))
    client = boto3.client("cloudwatch")

    namespace = "homemetrics"
    metric_name = parts[1] + "-" + parts[2]
    timestamp = parts[0]
    dimensions = [{"Name":"Device","Value":parts[1]},{"Name":"Sensor","Value":parts[2]}]
    value = float(parts[3])
    counts = 1
    metric_data = [{"MetricName":metric_name, "Timestamp":timestamp, "Value":value, "Dimensions":dimensions}]

    response = client.put_metric_data(Namespace = namespace, MetricData = metric_data)
    logging.debug(response)

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
    Picks up the offset to use in metrics.log
    """
    pass

def main():
    terminate = False
    debug = True
    resume = True
    frecuency = 60 #Number of seconds between measures
    global METRICS_FILE

    try:
        opts, args = getopt.getopt(sys.argv[1:], "hdf:m:", ["help", "debug"])
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
            frecuency = int(a)
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
    try:
        metrics_file = open(METRICS_FILE,"r")
    except e:
        raise e
    
    logging.debug("Metrics file was opened")

 #   try:
 #       open(LAST_DATAPOINT_FILE,"r")
 #   except:

    starttime = time.time()

    while not terminate:
        timestamp = str(datetime.datetime.now())
        for i in metrics_file:
            try:
                parts = parse_metric_line(i)
            except ValueError:
                logging.error("Wrong number of fields on line: "+str(i))
            else:
                push_metric(parts)
                save_last_datapoint(i.rstrip())
            time.sleep(1)

        back_to_sleep_for = (frecuency - ((time.time() - starttime)%frecuency))
        logging.debug("Sleeping for " + str(back_to_sleep_for))
        time.sleep(back_to_sleep_for)

        if terminate:
            pass
            #Do some housekeeping and finish

if __name__ == "__main__":
    main()
