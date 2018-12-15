import time
import logging
import getopt
import sys
import time
import datetime
import boto3

def usage():
    pass

def parse_line(line):
    parts = line.split(',')
    if len(parts) != 4:
        raise ValueError("Wrong number of parts in that line.")
    return parts

def push_metric(parts):
   
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

def main():
    terminate = False
    debug = False
    frecuency = 60 #Number of seconds between measures

    try:
        opts, args = getopt.getopt(sys.argv[1:], "hdf:", ["help", "debug"])
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
        else:
            assert False, "Unhandled option"

    FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    if debug:
        logging.basicConfig(filename="pusher.log", format=FORMAT, level=logging.DEBUG)
    else:
        logging.basicConfig(filename="pusher.log", format=FORMAT, level=logging.WARN)

    try:
        metrics_file = open("metrics1.log","r")
    except e:
        raise e
    
    logging.debug("Metrics file was opened")

    starttime = time.time()

    while not terminate:
        timestamp = str(datetime.datetime.now())
        for i in metrics_file:
            try:
                parts = parse_line(i)
            except ValueError:
                logging.error("Wrong number of fields on line: "+str(i))
            else:
                push_metric(parts)
            time.sleep(1)
        back_to_sleep_for = (frecuency - ((time.time() - starttime)%frecuency))
        logging.debug("Sleeping for " + str(back_to_sleep_for))
        time.sleep(back_to_sleep_for)

if __name__ == "__main__":
    main()
