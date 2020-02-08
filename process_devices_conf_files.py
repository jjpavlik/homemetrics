from jinja2 import Environment, FileSystemLoader

DEVICES = [
    {
    "type":"arduino",
    "name":"arduino-living",
    "access":"/dev/ttyACM0",
    "interface":"serialUSB",
    "location":"living-room"
    },
    {
    "type":"dummy",
    "name":"dummy",
    "access":"dummy",
    "interface":"dummy",
    "location":"dummy"
    }
]

def main():

    with open("devices.conf",'w') as conf:
        file_loader = FileSystemLoader('templates')
        env = Environment(loader=file_loader)
        template = env.get_template("devices.j2")
        conf.write(template.render(devices=DEVICES))

if __name__ == "__main__":
    main()
