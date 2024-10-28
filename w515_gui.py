# version 0.1.1, by Mark Tapsak
# Visit mtapsak@hotmail.com to purchase a pump conversion kit 

import asyncio
import tkinter as tk
from tkinter import filedialog
import csv
from bleak import BleakClient, BleakError
import threading

# UUIDs for BLE characteristics
BLE_PUMP_CHARACTERISTIC_UUID =      "000055A5-0000-1000-8000-00805F9B34FB"  # pump data notifications
MEAS_INTERVAL_CHARACTERISTIC_UUID = "000055A6-0000-1000-8000-00805F9B34FB"  # setting measurement interval
BUTTON_PRESS_CHARACTERISTIC_UUID =  "000055A8-0000-1000-8000-00805F9B34FB"  # simulating a button press
PUMP_RATE_CHARACTERISTIC_UUID =     "000055A9-0000-1000-8000-00805F9B34FB"  # setting pump rate

# Dictionary to store incoming data for logging purposes
data_records = {
    "Timestamp": [],
    "PSI": [],
    "MotorCurrent": [],
    "PumpRate": []
}

class w515_app:
    """
    BLE device interface class that handles all BLE communication and controls
    """
    def __init__(self, address):
        self.address = address  # BLE device MAC address
        self.client = BleakClient(address)  # Bleak client instance for BLE communication
        self.loop = asyncio.new_event_loop()  # New event loop for asynchronous BLE tasks
        asyncio.set_event_loop(self.loop)  # Set the created event loop as the current loop

    async def connect(self):
        """
        Connect to the BLE device and perform service discovery.
        """
        print(f"Attempting to connect to {self.address}...")
        try:
            await self.client.connect()  # Attempt to connect to the device
            print("Connected to device:", self.address)
            await self.client.get_services()  # Perform service discovery after connection
            print("Service discovery completed.")
        except BleakError as e:
            print(f"Failed to connect to device: {e}")

    async def start_notify(self, callback):
        """
        Subscribe to notifications from a specific characteristic (pump data).
        """
        print(f"Subscribing to notifications from characteristic {BLE_PUMP_CHARACTERISTIC_UUID}")
        try:
            await self.client.start_notify(BLE_PUMP_CHARACTERISTIC_UUID, callback)  # Subscribe to notifications
            print("Subscription to 55A5 successful.")
        except BleakError as e:
            print(f"Failed to start notification: {e}")

    async def send_button_press(self, mux1_channel, mux2_channel):
        """
        Send a button press command to the device by writing to a characteristic.
        """
        command = bytearray([mux1_channel, mux2_channel])  # Convert channel selection into byte array
        print(f"Sending button press command: {command.hex()} to characteristic {BUTTON_PRESS_CHARACTERISTIC_UUID}")
        try:
            await self.client.write_gatt_char(BUTTON_PRESS_CHARACTERISTIC_UUID, command)  # Send command to characteristic
            print("Button press command sent")
        except (BleakError, OSError) as e:
            print(f"Failed to send button press command: {e}")

    async def send_pump_rate(self, pump_rate):
        """
        Send a pump rate command to the device by writing to a characteristic.
        """
        pump_rate_bytes = pump_rate.to_bytes(2, byteorder='little')  # Convert pump rate to 2-byte little-endian
        print(f"Sending pump rate: {pump_rate} ({pump_rate_bytes.hex()}) to characteristic {PUMP_RATE_CHARACTERISTIC_UUID}")
        try:
            await self.client.write_gatt_char(PUMP_RATE_CHARACTERISTIC_UUID, pump_rate_bytes)  # Send pump rate to characteristic
            print("Pump rate sent")
        except (BleakError, OSError) as e:
            print(f"Failed to send pump rate: {e}")

    async def send_measurement_interval(self, interval):
        """
        Send a measurement interval command to the device by writing to a characteristic.
        """
        interval_bytes = interval.to_bytes(2, byteorder='little')  # Convert interval to 2-byte little-endian
        print(f"Sending measurement interval: {interval} ({interval_bytes.hex()}) to characteristic {MEAS_INTERVAL_CHARACTERISTIC_UUID}")
        try:
            await self.client.write_gatt_char(MEAS_INTERVAL_CHARACTERISTIC_UUID, interval_bytes)  # Send interval to characteristic
            print("Measurement interval sent")
        except (BleakError, OSError) as e:
            print(f"Failed to send measurement interval: {e}")

    async def execute_ramp(self, start_rate, end_rate, duration):
        """
        Execute a ramping pump rate over a specified duration.
        """
        update_interval = 2.0  # Interval in seconds between each rate update
        num_steps = int((duration * 60) / update_interval)  # Calculate number of steps based on duration
        rate_increment = (end_rate - start_rate) / num_steps  # Calculate rate increment per step
        current_rate = start_rate

        # Incrementally adjust the pump rate
        for _ in range(num_steps):
            await self.send_pump_rate(int(current_rate))  # Send current rate to device
            current_rate += rate_increment  # Increment rate
            await asyncio.sleep(update_interval)  # Wait for the next update

        # Ensure the final rate is sent
        await self.send_pump_rate(int(end_rate))

    async def execute_static(self, rate, duration):
        """
        Set a static pump rate for a specified duration.
        """
        await self.send_pump_rate(rate)  # Send the desired pump rate to the device
        await asyncio.sleep(duration * 60)  # Wait for the duration in seconds

    async def run_experiment(self, stages):
        """
        Run an experiment consisting of multiple stages (static or ramp).
        """
        for stage in stages:
            if stage['type'] == 'static':
                await self.execute_static(stage['rate'], stage['duration'])
            elif stage['type'] == 'ramp':
                await self.execute_ramp(stage['start_rate'], stage['end_rate'], stage['duration'])

    async def disconnect(self):
        """
        Disconnect from the BLE device.
        """
        print(f"Disconnecting from device at {self.address}")
        try:
            await self.client.disconnect()
            print("Disconnected from device:", self.address)
        except BleakError as e:
            print(f"Failed to disconnect from device: {e}")

    def run_ble_tasks(self, app):
        """
        Run BLE tasks in a continuous loop to maintain connection and handle notifications.
        """
        asyncio.set_event_loop(self.loop)  # Set the event loop for BLE operations
        while True:
            try:
                self.loop.run_until_complete(self.connect())  # Connect to the device
                self.loop.run_until_complete(self.start_notify(app.handle_notification))  # Start notifications
                while self.client.is_connected:
                    self.loop.run_until_complete(asyncio.sleep(1))  # Keep the connection alive
            except BleakError as e:
                print(f"Error during BLE operation: {e}. Reconnecting...")
            except Exception as e:
                print(f"Unexpected error: {e}. Reconnecting...")
            self.loop.run_until_complete(self.disconnect())  # Disconnect and retry after an error
            self.loop.run_until_complete(asyncio.sleep(5))  # Wait before retrying connection

class App:
    """
    Tkinter GUI class that manages user interface and interactions with the BLE device.
    """
    def __init__(self, root, ble_device):
        self.root = root  # Tkinter root window
        self.ble_device = ble_device  # Instance of the BLE device handler
        self.root.title("HPLC Pump Control")  # Set window title
        self.root.geometry("620x500")  # Set window size

        # Readout display for real-time data
        self.readout_frame = tk.Frame(root)
        self.readout_frame.pack(pady=10)

        self.readout_label = tk.Label(self.readout_frame, text="Time: 0.0s  |  PSI: 0  |  Current: 0  |  Pump Rate: 0", font=("Helvetica", 14))
        self.readout_label.pack()
        
        # Separator Line
        self.separator = tk.Canvas(root, height=3, bd=0, highlightthickness=0, relief='ridge')
        self.separator.pack(fill='x', padx=10, pady=10)
        self.separator.create_line(0, 2, 660, 2, fill="dark grey", width=3)
        
        # Button controls for pump operation
        self.button_frame = tk.Frame(root)
        self.button_frame.pack(pady=10)

        self.button_run_stop = tk.Button(self.button_frame, text="Run", font=("Helvetica", 14),
                                         bg="green", fg="white", command=self.toggle_run_stop)
        self.button_run_stop.grid(row=0, column=0, padx=5)

        self.button_up = tk.Button(self.button_frame, text="Arrow Up", font=("Helvetica", 12),
                                   command=lambda: self.send_button_press(1, 0))
        self.button_up.grid(row=0, column=1, padx=5)
        self.add_hover_effect(self.button_up)

        self.button_down = tk.Button(self.button_frame, text="Arrow Down", font=("Helvetica", 12),
                                     command=lambda: self.send_button_press(1, 1))
        self.button_down.grid(row=0, column=2, padx=5)
        self.add_hover_effect(self.button_down)

        self.button_edit = tk.Button(self.button_frame, text="Edit", font=("Helvetica", 12),
                                     command=lambda: self.send_button_press(2, 1))
        self.button_edit.grid(row=0, column=3, padx=5)
        self.add_hover_effect(self.button_edit)

        self.button_menu = tk.Button(self.button_frame, text="Menu", font=("Helvetica", 12),
                                     command=lambda: self.send_button_press(2, 0))
        self.button_menu.grid(row=0, column=4, padx=5)
        self.add_hover_effect(self.button_menu)

        # Pump Rate Entry
        self.rate_frame = tk.Frame(root)
        self.rate_frame.pack(pady=20)

        self.rate_label = tk.Label(self.rate_frame, text="Pump Rate (uL):", font=("Helvetica", 12))
        self.rate_label.pack(side=tk.LEFT)

        self.rate_entry = tk.Entry(self.rate_frame, font=("Helvetica", 12), width=6)
        self.rate_entry.pack(side=tk.LEFT)

        self.rate_button = tk.Button(self.rate_frame, text="Set Pump Rate (uL)", font=("Helvetica", 12),
                                     command=self.send_pump_rate)
        self.rate_button.pack(side=tk.LEFT, padx=10)
        self.add_hover_effect(self.rate_button)

        # Time Interval Entry
        self.interval_frame = tk.Frame(root)
        self.interval_frame.pack(pady=20)

        self.interval_label = tk.Label(self.interval_frame, text="Measurement Interval (ms):", font=("Helvetica", 12))
        self.interval_label.pack(side=tk.LEFT)

        self.interval_entry = tk.Entry(self.interval_frame, font=("Helvetica", 12), width=6)
        self.interval_entry.pack(side=tk.LEFT)

        self.interval_button = tk.Button(self.interval_frame, text="Set Interval (ms)", font=("Helvetica", 12),
                                         command=self.send_measurement_interval)
        self.interval_button.pack(side=tk.LEFT, padx=10)
        self.add_hover_effect(self.interval_button)

        # Separator Line
        self.separator = tk.Canvas(root, height=3, bd=0, highlightthickness=0, relief='ridge')
        self.separator.pack(fill='x', padx=10, pady=10)
        self.separator.create_line(0, 2, 660, 2, fill="dark grey", width=3)

        # Experiment Grid for configuring experiment parameters
        self.grid_frame = tk.Frame(root)
        self.grid_frame.pack(pady=20)

        # Initial Static Rate
        self.label_initial_rate = tk.Label(self.grid_frame, text="Initial Rate:", font=("Helvetica", 12), anchor='w')
        self.label_initial_rate.grid(row=0, column=0, padx=10, sticky='w')
        self.entry_initial_rate = tk.Entry(self.grid_frame, font=("Helvetica", 12), width=6)
        self.entry_initial_rate.grid(row=0, column=1, padx=10)
        self.label_initial_duration = tk.Label(self.grid_frame, text="Duration (min):", font=("Helvetica", 12), anchor='w')
        self.label_initial_duration.grid(row=0, column=2, padx=10, sticky='w')
        self.entry_initial_duration = tk.Entry(self.grid_frame, font=("Helvetica", 12), width=6)
        self.entry_initial_duration.grid(row=0, column=3, padx=10)

        # Ramp Up Stage
        self.label_ramp_up = tk.Label(self.grid_frame, text="Ramp to Rate:", font=("Helvetica", 12), anchor='w')
        self.label_ramp_up.grid(row=1, column=0, padx=10, sticky='w')
        self.entry_ramp_up_rate = tk.Entry(self.grid_frame, font=("Helvetica", 12), width=6)
        self.entry_ramp_up_rate.grid(row=1, column=1, padx=10)
        self.label_ramp_up_duration = tk.Label(self.grid_frame, text="Duration (min):", font=("Helvetica", 12), anchor='w')
        self.label_ramp_up_duration.grid(row=1, column=2, padx=10, sticky='w')
        self.entry_ramp_up_duration = tk.Entry(self.grid_frame, font=("Helvetica", 12), width=6)
        self.entry_ramp_up_duration.grid(row=1, column=3, padx=10)

        # Static Hold
        self.label_hold_duration = tk.Label(self.grid_frame, text="Hold (min):", font=("Helvetica", 12), anchor='w')
        self.label_hold_duration.grid(row=2, column=2, padx=10, sticky='w')
        self.entry_hold_duration = tk.Entry(self.grid_frame, font=("Helvetica", 12), width=6)
        self.entry_hold_duration.grid(row=2, column=3, padx=10)

        # Ramp Down Stage
        self.label_ramp_down = tk.Label(self.grid_frame, text="Ramp to Rate:", font=("Helvetica", 12), anchor='w')
        self.label_ramp_down.grid(row=3, column=0, padx=10, sticky='w')
        self.entry_ramp_down_rate = tk.Entry(self.grid_frame, font=("Helvetica", 12), width=6)
        self.entry_ramp_down_rate.grid(row=3, column=1, padx=10)
        self.label_ramp_down_duration = tk.Label(self.grid_frame, text="Duration (min):", font=("Helvetica", 12), anchor='w')
        self.label_ramp_down_duration.grid(row=3, column=2, padx=10, sticky='w')
        self.entry_ramp_down_duration = tk.Entry(self.grid_frame, font=("Helvetica", 12), width=6)
        self.entry_ramp_down_duration.grid(row=3, column=3, padx=10)

        # Frame for Experiment and Save Buttons
        self.button_frame_experiment = tk.Frame(root)
        self.button_frame_experiment.pack(pady=20)

        # Start Experiment Button
        self.start_button = tk.Button(self.button_frame_experiment, text="Start Experiment Stages", font=("Helvetica", 12), command=self.start_experiment)
        self.start_button.pack(side=tk.LEFT, padx=10)
        self.add_hover_effect(self.start_button)

        # Save to CSV Button
        self.save_button = tk.Button(self.button_frame_experiment, text="Save pump data to CSV", font=("Helvetica", 12), command=self.save_to_csv)
        self.save_button.pack(side=tk.LEFT, padx=10)
        self.add_hover_effect(self.save_button)

        # Start BLE tasks in a separate thread (daemon)
        ble_thread = threading.Thread(target=self.ble_device.run_ble_tasks, args=(self,), daemon=True)
        ble_thread.start()

    def toggle_run_stop(self):
        """
        Toggle between 'Run' and 'Stop' for pump control.
        """
        if self.button_run_stop['text'] == 'Run':
            self.send_button_press(0, 0)  # Run action
            self.button_run_stop.config(text='Stop', bg="red", fg="white")
        else:
            self.send_button_press(0, 0)  # Stop action
            self.button_run_stop.config(text='Run', bg="green", fg="white")

    def handle_notification(self, sender, data):
        """
        Handle notifications received from the BLE device, parse and display data.
        """
        if len(data) == 12:  # Expect 12 bytes; last 2 bytes might be extra
            timestamp = int.from_bytes(data[0:4], byteorder='little') / 1000.0  # Convert to seconds
            psi = int.from_bytes(data[4:6], byteorder='little')
            motor_current = int.from_bytes(data[6:8], byteorder='little')
            pump_rate = int.from_bytes(data[8:10], byteorder='little')
            print(f"Parsed data - Timestamp: {timestamp:.3f} s, PSI: {psi}, Motor Current: {motor_current}, Pump Rate: {pump_rate}")

            # Update the readout label in the GUI
            self.readout_label.config(text=f"Time: {timestamp:.3f}s | PSI: {psi} | Current: {motor_current} | Pump Rate: {pump_rate}")

            # Store parsed data in the dictionary
            data_records["Timestamp"].append(timestamp)
            data_records["PSI"].append(psi)
            data_records["MotorCurrent"].append(motor_current)
            data_records["PumpRate"].append(pump_rate)
        else:
            print(f"Unexpected data length: {len(data)}")

    def send_button_press(self, mux1_channel, mux2_channel):
        """
        Send a button press signal to the BLE device.
        """
        self.ble_device.loop.create_task(self.ble_device.send_button_press(mux1_channel, mux2_channel))

    def send_pump_rate(self):
        """
        Validate and send a pump rate to the BLE device.
        """
        try:
            pump_rate = int(self.rate_entry.get())
            if 1 <= pump_rate <= 10000:
                self.ble_device.loop.create_task(self.ble_device.send_pump_rate(pump_rate))
            else:
                print("Invalid pump rate. Please enter a number between 1 and 10000.")
        except ValueError:
            print("Please enter a valid number for the pump rate.")

    def send_measurement_interval(self):
        """
        Validate and send a measurement interval to the BLE device.
        """
        try:
            interval = int(self.interval_entry.get())
            if 1 <= interval <= 16000:  # Range from 1 to 16000 milliseconds
                asyncio.run_coroutine_threadsafe(
                    self.ble_device.send_measurement_interval(interval), 
                    self.ble_device.loop
                )
                print(f"Measurement interval set to {interval} ms.")
            else:
                print("Invalid interval. Please enter a number between 1 and 16000.")
        except ValueError:
            print("Please enter a valid number for the interval.")

    def save_to_csv(self):
        """
        Save collected data to a CSV file.
        """
        # Open a file dialog to choose file name and location
        file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if file_path:
            with open(file_path, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                # Write the header
                writer.writerow(data_records.keys())
                # Write the data
                rows = zip(*data_records.values())
                writer.writerows(rows)
            print(f"Data saved to {file_path}")

    def start_experiment(self):
        """
        Start the experiment based on user-defined parameters.
        """
        try:
            # Create a list of stages based on user inputs
            stages = [
                {'type': 'static', 'rate': int(self.entry_initial_rate.get()), 'duration': float(self.entry_initial_duration.get())},
                {'type': 'ramp', 'start_rate': int(self.entry_initial_rate.get()), 'end_rate': int(self.entry_ramp_up_rate.get()), 'duration': float(self.entry_ramp_up_duration.get())},
                {'type': 'static', 'rate': int(self.entry_ramp_up_rate.get()), 'duration': float(self.entry_hold_duration.get())},
                {'type': 'ramp', 'start_rate': int(self.entry_ramp_up_rate.get()), 'end_rate': int(self.entry_ramp_down_rate.get()), 'duration': float(self.entry_ramp_down_duration.get())},
            ]
            # Start the experiment by scheduling it in the event loop
            self.ble_device.loop.create_task(self.ble_device.run_experiment(stages))
        except ValueError:
            print("Please enter valid values for all fields.")

    def add_hover_effect(self, button):
        """
        Add a hover effect to a button to change its background color.
        """
        button.bind("<Enter>", lambda e: button.config(bg="lightblue"))
        button.bind("<Leave>", lambda e: button.config(bg="SystemButtonFace"))

def start_tkinter_app():
    """
    Initialize and start the Tkinter application.
    """
    root = tk.Tk()
    mac_address = "C3:04:D7:5E:6F:E4"  # Update this to your pump's MAC address
    ble_device = w515_app(mac_address)
    app = App(root, ble_device)
    root.mainloop()

# Run Tkinter app in the main thread
start_tkinter_app()
