import os
import subprocess
from argparse import ArgumentParser
from pathlib import Path

print(os.environ['HOMEPATH'])
ports = ["COM15", "COM16"]
platformio_dir = Path(os.environ["HOMEDRIVE"]) / Path(os.environ["HOMEPATH"])
platform_io_exe = platformio_dir / Path(".platformio/penv/Scripts/platformio.exe")

parser = ArgumentParser()
parser.add_argument("--upload", "-u", action="store_true")
parser.add_argument("--uploadfs", "-f", action="store_true")
parser.add_argument("--ports", "-p", nargs="+", default=ports)
args = parser.parse_args()
if not args.upload and not args.uploadfs:
    parser.print_help()
    exit(0)

ports = args.ports
if args.upload:
    for port in ports:
        print("Uploading to " + port)
        cmd = f"{platform_io_exe} run --target upload --upload-port {port}"
        subprocess.call(cmd.split(" "))
        print("Done uploading to " + port)

if args.uploadfs:
    for port in ports:
        print("Uploading filesystem to " + port)
        cmd = f"{platform_io_exe} run --target uploadfs --environment lolin_c3_mini --upload-port {port}"
        subprocess.call(cmd.split(" "))
        print("Done uploading to " + port)
