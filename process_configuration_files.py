import logging
import csv
import getopt
import sys
from jinja2 import Environment, FileSystemLoader

ENVIRONMENTS = ("master", "development")

def build_dictionary(csvdata, environment):
    first = True
    fields = []
    dic = {}

    for row in csvdata:
        if first:
            fields = row
            first = False
        else:
            if row[0] == environment:
                pairs = []
                for index in range(1,len(fields)):
                    pairs.append((fields[index],row[index]))
                for field,value in pairs:
                    dic[field]=value
                return dic
    return {}

def usage():
    print("Available args are: [-d|--debug] -f CSV_FILE -e ENVIRONMENT")
    print("-e See ENVIRONMENTS for available environments.")
    print("-f Expects a CSV formatted file.")

def main():
    debug = False
    file = ""
    environment = ""
    try:
        opts, args = getopt.getopt(sys.argv[1:], "df:e:", ["help", "debug"])
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
            file = a
        elif o in "-e":
            environment = a
            if environment not in ENVIRONMENTS:
                print(environment + " is not a valid environment. Valid environments are "+str(ENVIRONMENTS))
                sys.exit()
        else:
            print("Unhandled option")
            usage()
            sys.exit(2)

    if file == "" or environment == "":
        print("Either -f or -e parameters are missing.")
        usage()
        sys.exit(3)

    FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

    if debug:
        logging.basicConfig(filename="process_configuration_files.log", format=FORMAT, level=logging.DEBUG)
    else:
        logging.basicConfig(filename="process_configuration_files.log", format=FORMAT, level=logging.INFO)

    logging.info("Starting configuration parsing")

    with open(file, "r") as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        dictionary = build_dictionary(reader, environment)

    file_loader = FileSystemLoader('templates')
    env = Environment(loader=file_loader)
    name = file.split('.')
    template = env.get_template(name[0]+".j2")
    with open(name[0]+".conf",'w') as conf:
        conf.write(template.render(dictionary))

if __name__ == "__main__":
    main()
