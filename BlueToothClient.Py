import asyncio
from bleak import BleakClient, BleakScanner
from bleak.backends.characteristic import BleakGATTCharacteristic
import constants
import tkinter as tk

# Match these with your server UUIDs
SERVICE_UUID = constants.SERVICE_UUID
#CHAR_UUID = constants.CHARACTERISTIC_UUID
heartRateValue : float = 0.0
spo2Value : float = 0.0
stdValue : float = 0.0
rmssdValue : float = 0.0


class SensorDisplay:
    def __init__(self, root):
        self.root = root
        self.root.title("Heartrate Monitor")
        self.root.geometry("870x250")
        
        # General Frame for all the stats
        self.stats_frame = tk.Frame(root)
        self.stats_frame.pack(side="top", fill="x", padx=20, pady=10, anchor="n")

        # Create frame/labels for BPM (Beats Per Minute)
        self.bpm_frame = tk.Frame(self.stats_frame)
        self.bpm_frame.pack(side="left", padx=15)

        self.bpm_label = tk.Label(
            self.bpm_frame,
            text="BPM",
            font=("Arial", 16, "bold")
        )
        self.bpm_label.pack()
        self.bpmSubtitle_label = tk.Label(
            self.bpm_frame,
            text="(Beats Per Minute)",
            font=("Arial", 8, "bold")
        )
        self.bpmSubtitle_label.pack()

        self.bpmVal_label = tk.Label(
            self.bpm_frame,
            text="--", 
            font=("Arial", 40, "bold"),
            fg="blue"
        )
        self.bpmVal_label.pack()
        
        self.bpm_unit_label = tk.Label(
            self.bpm_frame, 
            text="BPM", 
            font=("Arial", 14)
        )
        self.bpm_unit_label.pack()

        # Create frame/labels for IPM (Impulses Per Minute)
        self.spo2_frame = tk.Frame(self.stats_frame)
        self.spo2_frame.pack(side="left", padx=15)

        self.spo2_label = tk.Label(
            self.spo2_frame,
            text="SpO2",
            font=("Arial", 16, "bold")
        )
        self.spo2_label.pack()
        self.spo2Subtitle_label = tk.Label(
            self.spo2_frame,
            text="(SpO2)",
            font=("Arial", 8, "bold")
        )
        self.spo2Subtitle_label.pack()

        self.spo2Val_label = tk.Label(
            self.spo2_frame, 
            text="--", 
            font=("Arial", 40, "bold"),
            fg="blue"
        )
        self.spo2Val_label.pack()
        
        self.spo2_unit_label = tk.Label(
            self.spo2_frame, 
            text="%", 
            font=("Arial", 14)
        )
        self.spo2_unit_label.pack()

        # Create frame/labels for HRSTD (Heart Rate Standard Deviation)
        self.hrstd_frame = tk.Frame(self.stats_frame)
        self.hrstd_frame.pack(side="left", padx=15)

        self.hrstd_label = tk.Label(
            self.hrstd_frame, 
            text="HRSTD",
            font=("Arial", 16, "bold")
        )
        self.hrstd_label.pack()
        self.hrstdSubtitle_label = tk.Label(
            self.hrstd_frame,
            text="(Heart Rate Standard Deviation)",
            font=("Arial", 8, "bold")
        )
        self.hrstdSubtitle_label.pack()
        

        self.hrstdVal_label = tk.Label(
            self.hrstd_frame, 
            text="--", 
            font=("Arial", 40, "bold"),
            fg="blue"
        )
        self.hrstdVal_label.pack()
        
        self.hrstd_unit_label = tk.Label(
            self.hrstd_frame, 
            text="HRSTD", 
            font=("Arial", 14)
        )
        self.hrstd_unit_label.pack()
        
        # Create frame/labels for RMSSD (Root Mean Square of the Successive Differences)
        self.rmssd_frame = tk.Frame(self.stats_frame)
        self.rmssd_frame.pack(side="left", padx=15)

        self.rmssd_label = tk.Label(
            self.rmssd_frame,
            text="RMSSD",
            font=("Arial", 16, "bold")
        )
        self.rmssd_label.pack()
        self.rmssdSubtitle_label = tk.Label(
            self.rmssd_frame,
            text="(Root Mean Square of the Successive Differences)",
            font=("Arial", 8, "bold")
        )
        self.rmssdSubtitle_label.pack()

        self.rmssdVal_label = tk.Label(
            self.rmssd_frame, 
            text="--", 
            font=("Arial", 40, "bold"),
            fg="blue"
        )
        self.rmssdVal_label.pack()
        
        self.rmssd_unit_label = tk.Label(
            self.rmssd_frame, 
            text="RMSSD", 
            font=("Arial", 14)
        )
        self.rmssd_unit_label.pack()
        
        # # Create timestamp label
        # self.time_label = tk.Label(
        #     root, 
        #     text="Last updated: --", 
        #     font=("Arial", 10)
        # )
        # self.time_label.pack(pady=10)
        
    def read_sensor(self):
        global heartRateValue, spo2Value, stdValue, rmssdValue
        return heartRateValue, spo2Value, stdValue, rmssdValue
    
    async def update_sensor(self):
        """Update the sensor reading"""
        try:
            while True:
                # Read sensor value
                hr, spo, std, rmssd = self.read_sensor()
            
                # Update the display
                self.bpmVal_label.config(text=f"{hr}")
                self.spo2Val_label.config(text=f"{spo}")
                self.hrstdVal_label.config(text=f"{std}")
                self.rmssdVal_label.config(text=f"{rmssd}")
                await asyncio.sleep(1)      #may need some adjusting in the future, currently server sends about 1/sec
                #  # Update timestamp
                # current_time = time.strftime("%H:%M:%S")
                # self.time_label.config(text=f"Last updated: {current_time}")
            
        except Exception as e:
            self.bpmVal_label.config(text="ERROR")
            print(f"Error reading sensor: {e}")
        
        # # Schedule next update (1000ms = 1 second)
        # self.root.after(1000, self.update_sensor)

root = tk.Tk()
app = SensorDisplay(root)

async def update_UI(root, interval = 0.05):
    while True:
        root.update()
        await asyncio.sleep(interval)

def notification_handler(characteristic: BleakGATTCharacteristic, data: bytearray):
    global heartRateValue, spo2Value, stdValue, rmssdValue
    if characteristic.uuid == constants.BPM_CHARACTERISTIC_UUID:
        heartRateValue = float(data)
        print(f"BPM   : %f", heartRateValue)
    elif characteristic.uuid == constants.SPO2_CHARACTERTISTIC_UUID:
        spo2Value = float(data)
        print(f"SPO2  : %f", spo2Value)
    elif characteristic.uuid == constants.HRSTD_CHARACTERISTIC_UUID:
        stdValue = float(data)
        print(f"HRSTD : %f", stdValue)
    elif characteristic.uuid == constants.RMSSD_CHARACTERISTIC_UUID:
        rmssdValue = float(data)
        print(f"RMSSD : %f", rmssdValue)
    else:
        print(f"UNKNOWN CHARACTERISTIC {characteristic}")

async def run_client():
    global root, app
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
                    for char in constants.CHARACTERISTIC_LIST:
                        await client.start_notify(char, notification_handler)
                    await asyncio.gather(update_UI(root), app.update_sensor())
        
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
            for char in constants.CHARACTERISTIC_LIST:
                await client.stop_notify(char)
            await client.disconnect()

if __name__ == "__main__":
    asyncio.run(run_client())
