# version 0.1.0, by Mark Tapsak
# visit virginiaanalytical.com to purchase a pump converstion kit 

import tkinter as tk
from w515_ble_device import w515_BLEDevice
from w515_gui import w515_App

def start_tkinter_app():
    root = tk.Tk()
    mac_address = "C3:04:D7:5E:6F:E4"  # Updated with the correct MAC address
    ble_device = w515_BLEDevice(mac_address)
    app = w515_App(root, ble_device)
    root.mainloop()

# Run Tkinter app in the main thread
if __name__ == "__main__":
    start_tkinter_app()
