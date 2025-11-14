import asyncio
from bleak import BleakClient, BleakScanner
from bleak.backends.characteristic import BleakGATTCharacteristic
import constants

# Match these with your server UUIDs
SERVICE_UUID = constants.SERVICE_UUID
CHAR_UUID = constants.CHARACTERISTIC_UUID

def notification_handler(characteristic: BleakGATTCharacteristic, data: bytearray):
    """Simple notification handler which prints the data received."""
    print(f"%s: %r", characteristic.description, data)

async def run_client():
    print("Scanning for BLE devices...")
    
    # Scan for devices
    devices = await BleakScanner.discover(timeout=10.0)
    await asyncio.sleep(5)
    
    # Find your server by name
    target_device = None
    for device in devices:
        print(f"Found: {device.name} - {device.address}")
        if device.name == constants.BLUETOOTH_SERVER_LOCALNAME:  # Match your server name
            target_device = device
            break
    
    if not target_device:
        print("Server not found!")
        return
    
    print(f"\nConnecting to {target_device.name} ({target_device.address})...")
    
    # Connect to the device
    async with BleakClient(target_device.address, timeout=10) as client:
        print(f"Connected: {client.is_connected}")
        await asyncio.sleep(10)          #small delay after to allow for some stability (if this is not here, causes exceptions when reading characteristic)
         # List services
        # for service in client.services:
        #     print(f"Service: {service.uuid}")
        #     for char in service.characteristics:
        #         print(f"  Characteristic: {char.uuid}")

        try:
            print("Starting monitoring sensor...")

            while True:
#                await client.connect()
                if client.is_connected:
                    # Read data from characteristic
                    #value = await client.read_gatt_char(CHAR_UUID)
                    #print(f"Read value: {value.decode()}")
                    await client.start_notify(CHAR_UUID, notification_handler)
        
            # Write data to characteristic
            #data_to_send = b"Hello from client!"
            #await client.write_gatt_char(CHAR_UUID, data_to_send)
            #print(f"Wrote: {data_to_send.decode()}")
        
            # Read back to verify
            #value = await client.read_gatt_char(CHAR_UUID)
            #print(f"Read after write: {value}")
        except KeyboardInterrupt:
            # Stop the sensor after keyboard interrupt
            print('Stop monitoring!')
        finally:
            await client.stop_notify(CHAR_UUID)
            await client.disconnect()

if __name__ == "__main__":
    asyncio.run(run_client())
