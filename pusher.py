import time
import loggin

METRICS_FILE = "metrics.log"

def usage():
    pass

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

    while not terminate:
        pass
        try:
             meitrics_file = open(METRICS_FILE, "w")
        except OSError as e:
            logging.debug("Wasn't able to open the metrics file: " + str(e))
        else:

        back_to_sleep_for = (frecuency - ((time.time() - starttime)%frecuency))
        logging.debug("Sleeping for " + str(back_to_sleep_for))
        sleep(back_to_sleep_for)

if "__name__" == "__main__":
    main()
