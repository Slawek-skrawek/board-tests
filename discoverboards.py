import time
import json
import argparse
import sys
from serial.tools import list_ports
from pathlib import Path

import hubcontrol
import config

NUM_PORTS = 7
PORT_DELAY = 3


class DiscoverParser(argparse.ArgumentParser):
    def __init__(self, standalone=False):
        super().__init__(
            description="Discover devices in the hub")
        self.standalone = standalone
        self.add_argument(
            '-s', '--serial-number',
            type=str,
            help="specify serial number of the hub controller",
            metavar="SERIAL",
            dest='serial')

    def error(self, message):
        if not self.standalone:
            raise Exception(message)
        self.print_usage(sys.stderr)
        self.exit(2, f"Error: {message[0].upper() + message[1:] if message else ''}.\n")

    def parse(self, arg_ns=None):
        return self.parse_args(namespace=arg_ns)


def load_device_list(filename=f"{config.PYTHON_PATH}jsons/device_list.json"):
    try:
        with open(filename, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print("Could not find device_list.json")
        return {}


def identify_device(serial_number, device_list,
                    unknown_devices_file=f"{config.PYTHON_PATH}jsons/unknown_devices"):
    device_name = device_list.get(serial_number, {"name": "unknown_device"})
    if device_name["name"] == "unknown_device":
        output_file = Path(unknown_devices_file)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, "a") as f:
            print(f"Unknown device with serial number: {serial_number}", file=f)
    return device_name


def snapshot_devices():
    snapshot = {}
    ports = list_ports.comports()
    for port in ports:
        if port.serial_number is not None:
            snapshot[port.serial_number] = {
                "name": port.name,
                "vendor_id": f"{port.vid:04x}",
                "product_id": f"{port.pid:04x}",
                "manufacturer": port.manufacturer,
                "product": port.product,
            }
    return snapshot


def detect_new_device(before, after):
    # Return any serial number(s) present in after but not in before
    return {s: after[s] for s in after if s not in before}


def probe_port(port, hubcontroller=hubcontrol.HubController()):
    print(f"\nProbing port {port}")
    before = snapshot_devices()

    hubcontroller.set_power(port, True)
    time.sleep(PORT_DELAY)
    after = snapshot_devices()

    new_devices = detect_new_device(before, after)
    if not new_devices:
        print("No new device found.")
    else:
        for serial, info in new_devices.items():
            print(f"Detected new device:")
            print(f"  Serial      : {serial}")
            print(f"  Vendor ID   : {info['vendor_id']}")
            print(f"  Product ID  : {info['product_id']}")
            print(f"  Manufacturer: {info['manufacturer']}")
            print(f"  Product     : {info['product']}")
    hubcontroller.set_power(port, False)
    return new_devices


def map_ports(hubcontroller=hubcontrol.HubController()):
    hubcontroller.set_power('a', False)
    device_list = load_device_list()

    results = {}
    for port in range(1, NUM_PORTS + 1):
        new_dev = probe_port(port, hubcontroller)
        if new_dev:
            results[port] = new_dev

    print("\n--- Port Mapping Result ---")
    ports_list = []
    for port, devs in results.items():
        for serial, info in devs.items():
            identified_device = identify_device(serial, device_list)
            name = identified_device["name"]
            ports_list.append({
                'Port': port,
                'Serial_number': serial,
                'Name': name
            })
            print(f"Port {port}: {serial} - {name}")
    return {
        "Hub serial": hubcontroller.serial,
        "Ports": ports_list
    }


def run(device_map_location=f"{config.PYTHON_PATH}jsons/",
        standalone=False, h_serial=None):
    parser = DiscoverParser(standalone=standalone)
    if standalone:
        args = parser.parse()
        hub_serial = args.serial
    else:
        hub_serial = h_serial

    hubcontroller = hubcontrol.HubController()
    hubcontroller.serial = hub_serial
    try:
        hubcontroller.find_hub()
    except Exception as e:
        parser.error(str(e))
    device_map = map_ports(hubcontroller)

    output_file = Path(f"{device_map_location}device_map_discover.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w") as f:
        json.dump(device_map, f, indent=2)


def main():
    run(standalone=True)


if __name__ == "__main__":
    main()
