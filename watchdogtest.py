import argparse
import datetime
import sys
import threading
import time
import serial
import serial.tools.list_ports
import pyudev
import json

import discoverboards
import hubcontrol
import targetscripts
import config

SERIAL_RATE = 115200
PORT_DELAY = 3

done = threading.Event()
stop_event = threading.Event()
context = pyudev.Context()


class WatchdogParser(argparse.ArgumentParser):
    def __init__(self, standalone=False):
        super().__init__(
            description="Run watchdog test on devices in the hub")
        self.standalone = standalone
        self.add_argument(
            '-d', '--discover',
            action='store_true',
            help="discover connected devices before testing",
            dest='discover')
        self.add_argument(
            '-s', '--serial-number',
            type=str,
            help="specify serial number of the hub controller discovery",
            metavar="SERIAL",
            dest='serial')

    def error(self, message):
        if not self.standalone:
            raise Exception(message)
        self.print_usage(sys.stderr)
        self.exit(2, f"Error: {message[0].upper() + message[1:] if message else ''}.\n")

    def parse(self, arg_ns=None):
        return self.parse_args(namespace=arg_ns)


def watchdog_search(ser):
    if ser is None:
        print("Serial connection is not established.")
        stop_event.set()
    while not stop_event.is_set() and ser.is_open:
        try:
            reading = ser.readline()
            reading = reading.decode('utf-8', errors="ignore")
            print("    " + reading, end='')
            if "Reset reason: Watchdog" in reading:
                done.set()
                print(f"Watchdog found!")
                break
        except serial.serialutil.SerialException:
            stop_event.set()
            print("Serial exception occurred. Reading from serial failed.")


def watchdog_test(board_name, board_serial):
    ports = serial.tools.list_ports.comports()
    ser = None
    device_serial = None
    for port in ports:
        if 'ttyACM' in port.device:
            device = pyudev.Devices.from_device_file(context, port.device)
            device_serial = device.get('ID_SERIAL_SHORT')
            if device_serial == board_serial:
                ser = serial.Serial(port.device, SERIAL_RATE)

    done.clear()
    stop_event.clear()

    print(f"Found device serial: {device_serial}")
    print(f"Target board serial: {board_serial}")
    if device_serial == board_serial:
        target_name = targetscripts.create_target_name(board_name, "boot")
        targetscripts.full_create_target(target_name, board_name, "boot", print_output=False)
        targetscripts.load_image(target_name, print_output=False)
        target_name = targetscripts.create_target_name(board_name, "watchdog")
        targetscripts.full_create_target(target_name, board_name, "watchdog", print_output=False)
        targetscripts.load_image(target_name, print_output=False)
        print("Watchdog test started.")
        t = threading.Thread(target=watchdog_search, args=(ser, ), daemon=False)
        t.start()
        timeout = 60
        start_time = time.time()
        while time.time() < start_time + timeout:
            if not t.is_alive() or done.is_set():
                break
            time.sleep(0.2)
        if done.is_set():
            stop_event.set()
            print("Watchdog test passed.")
        elif stop_event.is_set():
            print("Watchdog test failed.")
        elif not t.is_alive():
            print("Thread no longer exists.\n"
                  "Watchdog test failed.")
        else:
            stop_event.set()
            print("Thread have reached timeout.\n"
                  "Watchdog test failed.")
    else:
        print("Different serial numbers. Connection abandoned.")

    return done.is_set()


def watchdogs_hub(device_map_location=f"{config.PYTHON_PATH}jsons/", discovered=False):
    if discovered:
        with open(f"{device_map_location}device_map_discover.json", "r") as f:
            device_map = json.load(f)
    else:
        with open(f"{device_map_location}device_map.json", "r") as f:
            device_map = json.load(f)
    ports = device_map["Ports"]
    hub_serial = device_map["Hub serial"]
    hub_controller = hubcontrol.HubController()
    hub_controller.serial = hub_serial
    hub_controller.find_hub()
    hub_controller.set_power('a', False)
    time.sleep(PORT_DELAY)

    print(f"Testing hub {hub_serial}")
    board_pass = []
    for port in ports:
        print(f"\nTesting port {port['Port']}")
        board_name = port["Name"]
        board_serial = port['Serial_number']
        number = port["Port"]
        hub_controller.set_power(number, True)
        time.sleep(PORT_DELAY)

        test_start = time.perf_counter()
        test_pass = watchdog_test(board_name, board_serial)
        test_end = time.perf_counter()
        test_time = (test_end - test_start)
        board_pass.append({
            "Port": number,
            "Board name": board_name,
            "Board serial": board_serial,
            "Test passed": test_pass,
            "Test time [s]": test_time,
        })
        print(f"Test time: {test_time:.4} seconds.")
        hub_controller.set_power(number, False)
        time.sleep(PORT_DELAY)

    watchdog_test_result = {
        "Hub serial": hub_serial,
        "Watchdog tests": board_pass
    }
    now = (datetime.datetime.now())
    result_file = f"{device_map_location}watchdog_test_{now.strftime('%Y-%m-%d_%H-%M')}.json"
    with open(result_file, "w") as f:
        json.dump(watchdog_test_result, f, indent=2)
    return result_file


def run(standalone=False, h_serial=None):
    program_start = time.perf_counter()
    print("Watchdog tests for hub started.\n")
    parser = WatchdogParser(standalone=standalone)
    if standalone:
        args = parser.parse()
        hub_serial = args.serial
        discovered = args.discover
    else:
        hub_serial = h_serial
        discovered = False

    if discovered:
        try:
            discoverboards.run(h_serial=hub_serial)
        except Exception as e:
            parser.error(str(e))
    program_discover = time.perf_counter()
    result_file = watchdogs_hub(discovered=discovered)
    program_end = time.perf_counter()

    print("\nWatchdog tests for hub ended.")
    if discovered:
        program_time = program_discover - program_start
        print(f"Discover time:  {program_time:.4f} seconds")
    program_time = program_end - program_discover
    print(f"Watchdogs test time:  {program_time:.4f} seconds")
    program_time = program_end - program_start
    print(f"Program time:  {program_time:.4f} seconds")

    return result_file


def main():
    run(standalone=True)


if __name__ == "__main__":
    main()
