import sys
import time
from threading import Event, Thread

import serial

BAUDRATE = 115200

def print_serial_rx(port, break_event):
    while not break_event.is_set():
        while not break_event.is_set():
            try:
                ser = serial.Serial(port, BAUDRATE, timeout=0.1)
                print(f"Connected to {port}")
                break
            except serial.SerialException as excp:
                print(port, "SerialException", excp)
                time.sleep(1)
        while not break_event.is_set():
            try:
                if ser.in_waiting > 0:
                    try:
                        line = ser.readline()
                        print(port, line.decode('utf-8').rstrip())
                    except UnicodeDecodeError:
                        print(port, f"UnicodeDecodeError: {line}")
                    print(port, ser.readline().decode().rstrip())
                    # print(port, ser.readline().decode('utf-8').rstrip())
                else:
                    time.sleep(0.1)
            except serial.SerialException as excp:
                print(port, "SerialException", excp)
                break
        ser.close()

if len(sys.argv) == 1:
    print("Usage: python check_serial_ports.py COM1 COM2 ...")
    sys.exit(1)

ports = sys.argv[1:]
break_event = Event()
threads = []
for port in ports:
    th = Thread(target=print_serial_rx, args=(port, break_event))
    threads.append(th)
    th.start()

while True:
    try :
        time.sleep(1)
    except KeyboardInterrupt:
        print("KeyboardInterrupt")
        break_event.set()
        break

for th in threads:
    th.join()
