import asyncio
import subprocess
import constants
import time
import random
from typing import Any
from max30102.heartrate_monitor import HeartRateMonitor
import numpy as np

from bless import (  # type: ignore
    BlessServer,
    BlessGATTCharacteristic,
    GATTCharacteristicProperties,
    GATTAttributePermissions,
)

#reset bluetooth via commandline in subprocess
commands = [['sudo', 'rfkill', "unblock", "bluetooth"],
            ['sudo', 'service', "bluetooth", "restart"]]

for cmd in commands:
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(result.stdout)
    print(result.stderr)
time.sleep(1)

#setting up bluetooth via commandline in subprocess
#turn off bt security
commands = [['sudo', 'btmgmt', "power", "on"],
            ['sudo', 'btmgmt', "sc", "off"],
            ['sudo', 'btmgmt', "le", "on"],
            ['sudo', 'btmgmt', "ssp", "off"],
            ['sudo', 'btmgmt', "bondable", "on"],
            ['sudo', 'btmgmt', "pairable", "on"],
            ['sudo', 'btmgmt', "connectable", "on"]]

for cmd in commands:
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(result.stdout)
    print(result.stderr)

# # Define your service and characteristic UUIDs
# SERVICE_UUID = "7436b48e-96ed-4b8f-916d-1f1d25964635"
# CHAR_UUID = "74578b1f-1846-4759-ab5a-317cfa5ba6c9"

def calculateSTD(lst : list[int]) -> float:
    return np.std(lst)

def calculateRMSSD(lst : list[int]) -> float:
    if len(lst) == 0:
        return 0
    time_between_heartbeats = [60000/bpm if bpm > 0 else 0 for bpm in lst]       #BPM * 1min/60 seconds = BPS, invert to get seconds between each beat, convert to milliseconds
    successive_differences = np.diff(time_between_heartbeats)   #successive differences
    mean_squared_differences = np.mean(successive_differences ** 2) #mean square of succ. diff.
    return np.sqrt(mean_squared_differences)
    
def read_request(characteristic: BlessGATTCharacteristic, **kwargs) -> bytearray:
    """Handle read requests"""
    print(f"Read request for {characteristic.uuid}")
    return characteristic.value

def write_request(characteristic: BlessGATTCharacteristic, value: Any, **kwargs):
    """Handle write requests"""
    print(f"Write request for {characteristic.uuid}: {value}")
    characteristic.value = value

def update_characteristic(server : BlessServer, char : str, newValue, valueName : str):
    print(f"Updating {valueName} value to: {newValue:.2f}")
    server.get_characteristic(char).value = bytearray(f"{newValue:.2f}", 'utf-8')
    server.update_value(constants.SERVICE_UUID, char)

async def run_server_with_custom_ads():
    # Custom advertisement data
    server = BlessServer(
        name=constants.BLUETOOTH_SERVER_LOCALNAME,  # This appears in the advertisement
        connectable=True,
        bondable=True,             # allows pairing
        security_level="low"       # no passcode confirmation
    )
    server.read_request_func = read_request
    server.write_request_func = write_request

    await server.add_new_service(constants.SERVICE_UUID)
    char_flags = (
        GATTCharacteristicProperties.read
        | GATTCharacteristicProperties.write
        | GATTCharacteristicProperties.indicate
    )
    permissions = GATTAttributePermissions.readable
    for characteristic in constants.CHARACTERISTIC_LIST:
        await server.add_new_characteristic(
            constants.SERVICE_UUID,
            characteristic,
            char_flags,
            None,
            permissions
        )

    await server.start()

    print("Server advertising with custom name...")

    #change print_raw and print_result to enable or disable printing of raw and processed data
    hrm = HeartRateMonitor(print_raw=False, print_result=False)
    # Initialize the HeartRateMonitor object
    # Set print_raw to True to avoid printing raw data
    # Set print_result to True to print the calculated results
    BPM_Samples = []
    try:
        print("Starting heart rate sensor...")
        # Start the heart rate sensor
        hrm.start_sensor()
        while True:
            # Update the characteristic value with the current BPM
            BPM = hrm.bpm
            SPO2 = hrm.sp02
            BPM_Samples.append(BPM)
            STD = calculateSTD(BPM_Samples)
            RMSSD = calculateRMSSD(BPM_Samples)

            # print(f"Updating BPM value to: {BPM:.2f}")
            # server.get_characteristic(constants.CHARACTERISTIC_UUID).value = bytearray(f"{BPM:.2f}", 'utf-8')
            # server.update_value(constants.SERVICE_UUID, constants.CHARACTERISTIC_UUID)
            update_characteristic(server, constants.BPM_CHARACTERISTIC_UUID, BPM, "BPM")
            update_characteristic(server, constants.SPO2_CHARACTERTISTIC_UUID, SPO2, "SPO2")
            update_characteristic(server, constants.HRSTD_CHARACTERISTIC_UUID, STD, "HRSTD")
            update_characteristic(server, constants.RMSSD_CHARACTERISTIC_UUID, RMSSD, "RMSSD")

            await asyncio.sleep(1)
    except KeyboardInterrupt:
        # Stop the sensor after keyboard interrupt
        # Print a message indicating the sensor has stopped
        print('sensor stopped!')
        hrm.stop_sensor()
        await server.stop()

if __name__ == "__main__":
    asyncio.run(run_server_with_custom_ads())
