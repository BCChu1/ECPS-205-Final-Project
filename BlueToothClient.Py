import asyncio
from bleak import BleakClient, BleakScanner
from bleak.backends.characteristic import BleakGATTCharacteristic
import constants
import tkinter as tk
import threading
import logging
from datetime import datetime
logger = logging.getLogger(__name__)
import matplotlib.pyplot as plt
import collections

# Match these with your server UUIDs
SERVICE_UUID = constants.SERVICE_UUID
#CHAR_UUID = constants.CHARACTERISTIC_UUID
heartRateValue : float = 0.0
spo2Value : float = 0.0
stdValue : float = 0.0
rmssdValue : float = 0.0

update = False

bpmidx = 0
spo2idx = 0
stdidx = 0
rmssdidx = 0

bpmStamps = collections.deque(maxlen=30)
spo2Stamps = collections.deque(maxlen=30)
stdStamps = collections.deque(maxlen=30)
rmssdStamps = collections.deque(maxlen=30)

recvBPM = collections.deque(maxlen=30)
recvSPO2 = collections.deque(maxlen=30)
recvSTD = collections.deque(maxlen=30)
recvRMSSD = collections.deque(maxlen=30)

#plt.ion()
fig, ((pltBPM, pltSPO2), (pltSTD, pltRMSSD)) = plt.subplots(2, 2, figsize=(30, 10))

pltBPM.set_ylim(0, 300)
pltBPM.set_xlabel('Time Stamp (seconds)')
pltBPM.set_ylabel('Reading')
pltBPM.set_title(f"BPM")
lineBPM, = pltBPM.plot([], [])

pltSPO2.set_ylim(0, 100)
pltSPO2.set_xlabel('Time Stamp (seconds)')
pltSPO2.set_ylabel('Reading')
pltSPO2.set_title(f"SPO2")
lineSPO2, = pltSPO2.plot([], [])

pltSTD.set_ylim(0, 300)
pltSTD.set_xlabel('Time Stamp (seconds)')
pltSTD.set_ylabel('Reading')
pltSTD.set_title(f"STD")
lineSTD, = pltSTD.plot([], [])

pltRMSSD.set_ylim(0, 1000)
pltRMSSD.set_xlabel('Time Stamp (seconds)')
pltRMSSD.set_ylabel('Reading')
pltRMSSD.set_title(f"RMSSD")
lineRMSSD, = pltRMSSD.plot([], [])

class SensorDisplay:
    def __init__(self, root : tk.Tk):
        self.root = root
        self.root.title("Heartrate Monitor")
        self.root.geometry("500x250")
    
         # Container frame
        self.container = tk.Frame(root)
        self.container.pack(fill="both", expand=True)

        self.devices = []
        self.target_device = None
        self.showConnectionScreen()

        #try auto-connecting when we first launch
        thread = threading.Thread(target=self.connectThread, daemon=True)
        thread.start()

        #create the log file for our data
        now = datetime.now()
        file_handler = logging.FileHandler(now.strftime("HeartRateMonitor_%Y%m%d_%H%M%S.log"))
        file_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        logging.basicConfig(level=logging.INFO)

    #clear all items from window
    def clearAll(self):
        for widget in self.container.winfo_children():
            widget.destroy()

    #show connecting message screen 
    def showConnectionScreen(self):
        self.clearAll()
        self.root.geometry("500x250")
        label = tk.Label(
            self.container, 
            text="Connecting...", 
            font=("Arial", 16)
        )
        label.pack(expand=True)

    #show screen with 4 values (BPM, SPO2, HRSTD, RMSSD)
    def showDataScreen(self):
        self.clearAll()
        self.root.geometry("850x200")
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

    #show screen that allows you to manually find device to pair (if auto-connect fails)
    def showDeviceSelectionScreen(self):
        self.clearAll()
        self.root.geometry("500x400")
       # Title
        title = tk.Label(
            self.container, 
            text="Select Bluetooth Device", 
            font=("Arial", 14, "bold")
        )
        title.pack(pady=15)
        
        # Frame for listbox and scrollbar
        list_frame = tk.Frame(self.container)
        list_frame.pack(pady=10, padx=20, fill="both", expand=True)
        
        # Scrollbar
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")
        
        # Listbox for devices
        self.device_listbox = tk.Listbox(
            list_frame, 
            height=8,
            yscrollcommand=scrollbar.set,
            font=("Arial", 10)
        )
        self.device_listbox.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.device_listbox.yview)
        
        # Status label
        self.status_label = tk.Label(
            self.container, 
            text="Click 'Refresh' to scan for devices", 
            font=("Arial", 9),
            fg="gray"
        )
        self.status_label.pack(pady=5)
        
        # Button frame
        button_frame = tk.Frame(self.container)
        button_frame.pack(pady=15)
        
        refresh_btn = tk.Button(
            button_frame, 
            text="🔄 Refresh", 
            command=self.startScan,
            width=12,
            font=("Arial", 10)
        )
        refresh_btn.pack(side="left", padx=5)
        
        connect_btn = tk.Button(
            button_frame, 
            text="Connect", 
            command=self.connectToSelectedDevice,
            width=12,
            font=("Arial", 10),
            bg="#4CAF50",
            fg="white"
        )
        connect_btn.pack(side="left", padx=5)
        # Auto-scan on show
        self.startScan()

    #since we are working in TKinter, in-order to do anything with asyncio(or async in general) in a synchronous way you have to:
    #create a thread
    #set up an asyncio loop in the thread
    #run w/e async method you need to run in it
    def connectThread(self, address = None):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        print("Connecting...")
        logger.info(f'Connecting to sensor {address}')
        loop.run_until_complete(self.connectToServer(address))
        loop.close()

    #update selection screen with BT devices
    def startScan(self):
        self.device_listbox.delete(0, tk.END)
        logger.info('Scanning for sensors')
        self.device_listbox.insert(tk.END, "Scanning for devices...")
        self.status_label.config(text="Scanning...", fg="blue")
        
        thread = threading.Thread(target=self.updateListBox, daemon=True)
        thread.start()
    
    #filling in the list box, (I have async methods so I need an asyncio loop to run them syncrhonously)
    def updateListBox(self):
        global update
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)     
        try:
            self.devices.clear()
            devices = loop.run_until_complete(BleakScanner.discover(timeout=5.0))
            #self.root.after(0, self.updateListBox, devices)
            if not devices:
                self.device_listbox.insert(tk.END, "No devices found")
                self.status_label.config(text="No devices found. Click Refresh to try again.", fg="orange")
                return
            # Sort devices: named devices first, then by signal strength
            devices_sorted = sorted(devices, key=lambda d: (d.name is None, -(d.rssi if hasattr(d, 'rssi') else -100)))
            self.device_listbox.delete(0, tk.END)
            for i, device in enumerate(devices_sorted):
                name = device.name or "Unknown Device"
                rssi = f" ({device.rssi} dBm)" if hasattr(device, 'rssi') else ""
                display = f"{name}{rssi}\n  {device.address}"
                self.device_listbox.insert(tk.END, display)
                self.devices.append(device.address)
            
            self.status_label.config(text=f"Found {len(devices)} device(s). Select one and click Connect.", fg="green")
        finally:
            loop.close()

    #handles button press to connect to a selected device
    def connectToSelectedDevice(self):
        selection = self.device_listbox.curselection()
        if not selection:
            return
        
        address = self.devices[selection[0]]
        self.showConnectionScreen()
        self.root.update()
        #YOU NEED THE LAMBDA HERE OR ELSE IT GETS STUCK
        thread = threading.Thread(target = lambda: self.connectThread(address), daemon=True)
        thread.start()

    #handles looking for the bluetooth server or connecting to it directly
    async def connectToServer(self, address):
        if not address:
            devices = await BleakScanner.discover(timeout=10.0)
            #await asyncio.sleep(5)
            # Find your server by name
            for device in devices:
                print(f"Found: {device.name} - {device.address}")
                if device.name == constants.BLUETOOTH_SERVER_LOCALNAME:  # Match your server name
                    logger.info(f"Found sensor: {device.name} - {device.address}")
                    logger.info('Connecting...')
                    self.target_device = device
                    break
        
            if not self.target_device:
                print("Server not found!")
                logger.info('Server not found! Prompting user...')
                self.root.after(0, self.showDeviceSelectionScreen)
                return
            
            await self.connect(self.target_device.address)
        else:
            await self.connect(address)

    #function that handles the connection and listening for data
    async def connect(self, address):
        try:
            async with BleakClient(address, timeout=10) as client:
                print(f"Connected: {client.is_connected}")
                await asyncio.sleep(3)          #small delay after to allow for some stability (if this is not here, causes exceptions when reading characteristic)
                # List services
                # for service in client.services:
                #     print(f"Service: {service.uuid}")
                #     for char in service.characteristics:
                #         print(f"  Characteristic: {char.uuid}")

                try:
                    print("Starting monitoring sensor...")
                    if client.is_connected:
                        logger.info('Connected')
                        for char in constants.CHARACTERISTIC_LIST:
                            await client.start_notify(char, notification_handler)
                        self.root.after(0, self.showDataScreen)
                    else:
                        logger.info('Connection failed')
                    while client.is_connected:
        #                await client.connect()
                        #if client.is_connected:
                            # Read data from characteristic
                            #value = await client.read_gatt_char(CHAR_UUID)
                            #print(f"Read value: {value.decode()}")
                            # for char in constants.CHARACTERISTIC_LIST:
                            #     await client.start_notify(char, notification_handler)
                        self.root.after(0, self.updateValues)       #update UI
                        await asyncio.sleep(1)
                
                except KeyboardInterrupt:
                    # Stop the sensor after keyboard interrupt
                    print('Stop monitoring!')
                finally:
                    for char in constants.CHARACTERISTIC_LIST:
                        await client.stop_notify(char)
                    await client.disconnect()
        except Exception as e:
            print(e)
            self.root.after(0, self.showDeviceSelectionScreen)
    def updateValues(self):
        """Update the sensor reading"""
        global heartRateValue, spo2Value, stdValue, rmssdValue
        try:
            #while True:
                # Update the display
            self.bpmVal_label.config(text=f"{heartRateValue}")
            self.spo2Val_label.config(text=f"{spo2Value}")
            self.hrstdVal_label.config(text=f"{stdValue}")
            self.rmssdVal_label.config(text=f"{rmssdValue}")
            #await asyncio.sleep(1)      #may need some adjusting in the future, currently server sends about 1/sec
                #  # Update timestamp
                # current_time = time.strftime("%H:%M:%S")
                # self.time_label.config(text=f"Last updated: {current_time}")
            
        except Exception as e:
            self.bpmVal_label.config(text="ERROR")
            print(f"Error reading sensor: {e}")

        if (update):
            fig.canvas.draw_idle()
            fig.canvas.flush_events()
            plt.pause(0.01)
        
        # # Schedule next update (1000ms = 1 second)
        # self.root.after(1000, self.update_sensor)

def notification_handler(characteristic: BleakGATTCharacteristic, data: bytearray):
    global heartRateValue, spo2Value, stdValue, rmssdValue, recvBPM, recvSPO2, recvSTD, recvRMSSD, bpmStamps, spo2Stamps, stdStamps, rmssdStamps, fig, pltBPM, pltSPO2, pltSTD, pltRMSSD, bpmidx, spo2idx, stdidx, rmssdidx, update
    if characteristic.uuid == constants.BPM_CHARACTERISTIC_UUID:
        heartRateValue = float(data)
        logger.info(f'Recieved heart rate of {heartRateValue} bpm')
        print(f"BPM   :{heartRateValue}")

        if (len(bpmStamps) >= 30):
           bpmStamps.popleft()
           recvBPM.popleft()
        recvBPM.append(heartRateValue)
        bpmStamps.append(bpmidx)

        if (len(bpmStamps) > 0):
            minT = min(bpmStamps)
            maxT = max(bpmStamps)
        else:
            minT = 0
            maxT = 1 

        pltBPM.set_xlim(minT, maxT)
        pltBPM.set_xticks(range(minT, maxT))
        lineBPM.set_data(bpmStamps, recvBPM)
        bpmidx += 1
        update = True

    elif characteristic.uuid == constants.SPO2_CHARACTERTISTIC_UUID:
        spo2Value = float(data)
        logger.info(f'Recieved blood oxygen of {spo2Value} sp02')
        print(f"SPO2  :{spo2Value}")

        if (len(spo2Stamps) >= 30):
           spo2Stamps.popleft()
           recvSPO2.popleft()
        recvSPO2.append(spo2Value)
        spo2Stamps.append(spo2idx)

        if (len(spo2Stamps) > 0):
            minT = min(spo2Stamps)
            maxT = max(spo2Stamps)
        else:
            minT = 0
            maxT = 1

        pltSPO2.set_xlim(minT, maxT)
        pltSPO2.set_xticks(range(minT, maxT))
        lineSPO2.set_data(spo2Stamps, recvSPO2)
        spo2idx += 1
        update = True

    elif characteristic.uuid == constants.HRSTD_CHARACTERISTIC_UUID:
        stdValue = float(data)
        logger.info(f'Recieved heart rate standard deviation of {stdValue} hrstd')
        print(f"HRSTD :{stdValue}")

        if (len(stdStamps) >= 30):
           stdStamps.popleft()
           recvSTD.popleft()
        recvSTD.append(stdValue)
        stdStamps.append(stdidx)

        if (len(stdStamps) > 0):
            minT = min(stdStamps)
            maxT = max(stdStamps)
        else:
            minT = 0
            maxT = 1

        pltSTD.set_xlim(minT, maxT)
        pltSTD.set_xticks(range(minT, maxT))
        lineSTD.set_data(stdStamps, recvSTD)
        stdidx += 1
        update = True

    elif characteristic.uuid == constants.RMSSD_CHARACTERISTIC_UUID:
        rmssdValue = float(data)
        logger.info(f'Recieved heart rate root mean squared standard deviation of {rmssdValue} rmssd')
        print(f"RMSSD :{rmssdValue}")

        if (len(rmssdStamps) >= 30):
           rmssdStamps.popleft()
           recvRMSSD.popleft()
        recvRMSSD.append(rmssdValue)
        rmssdStamps.append(rmssdidx)

        if (len(rmssdStamps) > 0):
            minT = min(rmssdStamps)
            maxT = max(rmssdStamps)
        else:
            minT = 0
            maxT = 1

        pltRMSSD.set_xlim(minT, maxT)
        pltRMSSD.set_xticks(range(minT, maxT))
        lineRMSSD.set_data(rmssdStamps, recvRMSSD)
        rmssdidx += 1
        update = True

    else:
        logger.info(f'Recieved unknown/invalid characteristic {characteristic}')
        print(f"UNKNOWN CHARACTERISTIC {characteristic}")
        update = False

if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = SensorDisplay(root)

        root.mainloop()
        while(1):
            if (update):
                fig.canvas.draw_idle()
                fig.canvas.flush_events()
                plt.pause(1)

    except KeyboardInterrupt:
        logger.info('Recieved keyboard interrupt, stopping client.')
        for handler in logger.handlers:
            if isinstance(handler, logging.FileHandler):
                handler.flush()
                handler.close()
                logger.removeHandler(handler)
