
# w515ble-py

## Overview

`w515ble-py` is a Python package designed to provide seamless control over a Waters 515 HPLC pump using proprietary hardware developed by Virginia Analytical. The pump modification gives users control over key functions of the HPLC pump such as continuous monitoring of the pump back pressure, control of its pump rates, and front panel button functions using Bluetooth Low Energy (BLE). This effectively converts a manual pump into a fully programmable gradient HPLC pump. This package offers a robust and user-friendly interface to interact wirelessly with the Virginia Analytical pump controller, allowing users to send button press commands, adjust pump rates, and set up complex experiments involving the combination of rate ramps and static pump rates. The package also includes a graphical user interface (GUI) for easy real-time control and monitoring.

## Features

**BLE Communication**: Establish and maintain a BLE connection with a converted Waters 515 pump.
**Button Press Commands**: Send predefined button press commands like "RUN/STOP", "UP ARROW", "DOWN ARROW", "EDIT", and "MENU".
**Pump Rate Control**: Adjust the pump rate directly from your Python script or via the GUI.
**Experiment Setup**: Define and execute complex experiments with multiple stages, including ramp-up and ramp-down of pump rates and constant pump rates.
**Graphical User Interface (GUI)**: Provides real-time monitoring of pump parameters and easy control of the pump.

# Installation
You can install `w515ble-py` using pip:

```bash
pip install w515ble-py

# Getting Started
Importing the Package
First, you need to import the necessary components from the package:
from w515_ble_device import w515_BLEDevice
from w515_experiment import run_experiment, create_experiment
from w515_gui import w515_App

# Connecting to the Pump
You need to know the MAC address of your Virginia Analytical module installed in your Waters 515 pump. This came with the packing materials of the pump or the DIY kit. Replace "C3:04:D7:5E:6F:E4" with your pump's MAC address.

ble_device = w515_BLEDevice("C3:04:D7:5E:6F:E4")

Running the GUI
To launch the graphical user interface run the following script:
import tkinter as tk
def start_tkinter_app():
    root = tk.Tk()
    app = w515_App(root, ble_device)
    root.mainloop()

if __name__ == "__main__":
    start_tkinter_app()

Using the BLE Device Programmatically
Sending Button Press Commands
You can send predefined button press commands to the pump:
await ble_device.send_button_press("RunStop")  # Starts or stops the pump
await ble_device.send_button_press("UP")       # Simulates an "UP" button press
await ble_device.send_button_press("DOWN")     # Simulates a "DOWN" button press
await ble_device.send_button_press("EDIT")     # Simulates an "EDIT" button press
await ble_device.send_button_press("MENU")     # Simulates a "MENU" button press
Note that the series of button presses can be programmed to emulate any function of the pump, just like if one were to be pressing the buttons manually.

Adjusting the Pump Rate
You can set the pump rate in either  L/min or mL/min, for example:
await ble_device.send_pump_rate(1.5, unit="mL/min")  # Sets pump rate to 1.5 mL/min
await ble_device.send_pump_rate(500, unit=" L/min")  # Sets pump rate to 500  L/min

Setting Up Experiments
Creating an Experiment
You can define an experiment with an initial rate, ramp-up, hold, and ramp-down stages, for example:
stages = create_experiment(
    initial_rate=500,         # Initial rate in  L/min
    ramp_up_rate=1000,        # Ramp up to this rate in  L/min
    ramp_up_duration=10,      # Duration of the ramp-up in minutes
    hold_duration=10,         # Duration of the hold in minutes
    ramp_down_rate=500,       # Ramp down to this rate in  L/min
    ramp_down_duration=10     # Duration of the ramp-down in minutes
)

Running the Experiment
Once the experiment stages are defined, you can execute it as follows:

       await run_experiment(ble_device, stages)

Full Example
Here is a full example of setting up the BLE device, launching the GUI, and running an experiment programmatically:
import tkinter as tk
from w515_ble_device import w515_BLEDevice
from w515_gui import w515_App
from w515_experiment import create_experiment, run_experiment

# Initialize BLE Device
ble_device = w515_BLEDevice("C3:04:D7:5E:6F:E4")

# Start the GUI
def start_tkinter_app():
    root = tk.Tk()
    app = w515_App(root, ble_device)
    root.mainloop()

# Run the GUI in the main thread
if __name__ == "__main__":
    start_tkinter_app()

    # Example of running an experiment programmatically
    stages = create_experiment(
        initial_rate=500,
        ramp_up_rate=1000,
        ramp_up_duration=10,
        hold_duration=10,
        ramp_down_rate=500,
        ramp_down_duration=10
    )

    asyncio.run(run_experiment(ble_device, stages))

Customizing the GUI
You can easily modify the GUI layout by editing w515_gui.py. For instance, you can change button labels, adjust the size of input fields, or rearrange the layout to suit your needs.

Error Handling
The package includes basic error handling, such as checking for valid pump rates and button labels. If you pass an invalid value, the package will raise a ValueError with a descriptive error message.

License
This project is licensed under the MIT License - see the LICENSE file for details.

Contributing
Contributions are welcome! If you have suggestions for improving this package or have found a bug, please open an issue or submit a pull request.

Acknowledgments
* This package was developed by Mark Tapsak at Virginia Analytical for controlling the Waters 515 HPLC pumps via BLE. I proprietary module must be installed into your pump to utilize this python package. Contact mtapsak@hotmail.com for questions regarding the purchase of fully operational converted pumps, or to purchase the conversion kit and modify a pump yourself. Additional videos and details, along with more example scripts can be found at virginiaanalytical.com. This software is offered free of charge in hopes that the broader HPLC community will benefit. It is designed to be user-friendly and extendable for a variety of analytical applications.

## Trademark Acknowledgment and Disclaimer

Waters and 515 are registered trademarks or trademarks of Waters Corporation in the United States and other countries. This software package, `w515ble-py`, is an independent project and is not affiliated with, endorsed by, or connected to Waters Corporation in any way.

The use of the Waters 515 name and trademark is solely for reference purposes to describe the functionality of this software in relation to Waters 515 HPLC pumps. All other product and company names are trademarks or registered trademarks of their respective holders.

The modification of electrical components within an HPLC pump should be performed by qualified persons.


### Summary

**Overview**: The README starts with a brief overview of the package and its features.
**Installation and Usage**: Provides clear instructions on how to install the package, set up BLE communication, and use the GUI and experiment features.
**Examples**: Includes code examples that demonstrate how to use the package.
**Customization and Error Handling**: Briefly discusses how users can customize the GUI and the basic error handling provided.
**License and Contributing**: Includes standard sections for licensing and contributions.



