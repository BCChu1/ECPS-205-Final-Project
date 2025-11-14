import asyncio
import subprocess
import constants
from typing import Any

from bless import (  # type: ignore
    BlessServer,
    BlessGATTCharacteristic,
    GATTCharacteristicProperties,
    GATTAttributePermissions,
)
#setting up bluetooth via commandline in subprocess
process = subprocess.Popen( ['bluetoothctl'], stdin= subprocess.PIPE, stdout= subprocess.PIPE, stderr=subprocess.PIPE, text=True)
commands = "power on\npairable on\nadvertise on\n"
stdout, stderr = process.communicate(input=commands)

print(stdout)
print(stderr)

# # Define your service and characteristic UUIDs
# SERVICE_UUID = "7436b48e-96ed-4b8f-916d-1f1d25964635"
# CHAR_UUID = "74578b1f-1846-4759-ab5a-317cfa5ba6c9"

def read_request(characteristic: BlessGATTCharacteristic, **kwargs) -> bytearray:
    """Handle read requests"""
    print(f"Read request for {characteristic.uuid}")
    return bytearray(b"Hello from BLE Server!")

def write_request(characteristic: BlessGATTCharacteristic, value: Any, **kwargs):
    """Handle write requests"""
    print(f"Write request for {characteristic.uuid}: {value}")
    characteristic.value = value

async def run_server_with_custom_ads():
    # Custom advertisement data
    server = BlessServer(
        name=constants.BLUETOOTH_SERVER_LOCALNAME,  # This appears in the advertisement
    )
    server.read_request_func = read_request
    server.write_request_func = write_request

    await server.add_new_service(constants.SERVICE_UUID)
    char_flags = (
        GATTCharacteristicProperties.read
        | GATTCharacteristicProperties.write
        | GATTCharacteristicProperties.indicate
    )
    permissions = GATTAttributePermissions.readable | GATTAttributePermissions.writeable
    await server.add_new_characteristic(
        constants.SERVICE_UUID,
        constants.CHARACTERISTIC_UUID,
        char_flags,
        None,
        permissions
    )

    await server.start()

    print("Server advertising with custom name...")

    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        await server.stop()

if __name__ == "__main__":
    asyncio.run(run_server_with_custom_ads())