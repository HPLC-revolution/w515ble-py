# version 0.1.0, by Mark Tapsak
# Visit virginiaanalytical.com to purchase a pump conversion kit

import asyncio  # Import the asyncio library to handle asynchronous operations
from bleak import BleakClient, BleakError  # Import Bleak for Bluetooth Low Energy (BLE) communication

# Define UUIDs for the BLE characteristics. These UUIDs are used to identify specific BLE characteristics 
# related to the Waters 515 HPLC pump, such as pump control and button press.
BLE_PUMP_CHARACTERISTIC_UUID =     "000055A5-0000-1000-8000-00805F9B34FB"
BUTTON_PRESS_CHARACTERISTIC_UUID = "000055A8-0000-1000-8000-00805F9B34FB"
PUMP_RATE_CHARACTERISTIC_UUID =    "000055A9-0000-1000-8000-00805F9B34FB"

# Button Mappings for different button functionalities. This dictionary provides a mapping of human-readable
# button labels to their corresponding multiplexer channels (mux1_channel, mux2_channel) for the pump.
BUTTON_MAPPING = {
    "RunStop": (0, 0),
    "UP":      (1, 0),
    "DOWN":    (1, 1),
    "EDIT":    (2, 1),
    "MENU":    (2, 0)
}

def convert_pump_rate(rate, unit="µL/min"):
    """
    Converts the pump rate between units (µL/min and mL/min).

    Args:
        rate (float): The pump rate to be converted.
        unit (str): The unit of the pump rate, either 'µL/min' or 'mL/min'.

    Returns:
        int: The pump rate converted to µL/min.

    Raises:
        ValueError: If an invalid unit is provided.
    """
    # Convert rate to µL/min if the unit is 'mL/min'
    if unit == "mL/min":
        return int(rate * 1000)  # Convert from mL/min to µL/min
    # Return the rate as is if the unit is already 'µL/min'
    elif unit == "µL/min":
        return int(rate)
    else:
        # Raise an error if the unit is not recognized
        raise ValueError(f"Invalid unit '{unit}'. Please specify either 'mL/min' or 'µL/min'.")

class w515_BLEDevice:
    """
    Class to manage BLE communication with the Waters 515 HPLC pump.

    This class provides methods to connect to the BLE device, send button press commands,
    set pump rates, and handle notifications from the pump.
    """

    def __init__(self, address):
        """
        Initializes the BLEDevice with the BLE address of the pump.

        Args:
            address (str): The BLE address of the pump device.
        """
        self.address = address  # Store the BLE address
        self.client = BleakClient(address)  # Initialize the BLE client with the given address
        self.loop = asyncio.new_event_loop()  # Create a new asyncio event loop for BLE operations

    async def connect(self):
        """
        Connects to the BLE device at the specified address and performs service discovery.

        Raises:
            BleakError: If there is an error while connecting to the device.
        """
        print(f"Attempting to connect to {self.address}...")
        try:
            await self.client.connect()  # Attempt to connect to the BLE device
            print("Connected to device:", self.address)
            await self.client.get_services()  # Perform service discovery to enumerate the characteristics
            print("Service discovery completed.")
        except BleakError as e:
            # Print an error message if the connection fails
            print(f"Failed to connect to device: {e}")

    async def start_notify(self, callback):
        """
        Subscribes to notifications from a specific BLE characteristic and sets a callback function
        to handle incoming notifications.

        Args:
            callback (function): The function to call when a notification is received.

        Raises:
            BleakError: If there is an error starting notifications.
        """
        print(f"Subscribing to notifications from characteristic {BLE_PUMP_CHARACTERISTIC_UUID}")
        try:
            # Start receiving notifications and call the provided callback function
            await self.client.start_notify(BLE_PUMP_CHARACTERISTIC_UUID, callback)
            print("Subscription to 55A5 successful.")
        except BleakError as e:
            # Print an error message if starting notifications fails
            print(f"Failed to start notification: {e}")

    async def send_button_press(self, button_label):
        """
        Sends a button press command to the BLE device based on the provided button label.

        Args:
            button_label (str): A label representing the button to press (e.g., "RunStop", "UP").

        Raises:
            ValueError: If the button label is not recognized.

        Raises:
            BleakError or OSError: If there is an error sending the command to the BLE device.
        """
        # Validate that the button label is known; raise an error if not
        if button_label not in BUTTON_MAPPING:
            raise ValueError(f"Unknown button label '{button_label}'. Valid labels are: {list(BUTTON_MAPPING.keys())}")

        # Retrieve the multiplexer channels corresponding to the button label
        mux1_channel, mux2_channel = BUTTON_MAPPING[button_label]
        # Convert the channel values to a byte array
        command = bytearray([mux1_channel, mux2_channel])
        print(f"Sending button press command: {button_label} ({command.hex()}) to characteristic {BUTTON_PRESS_CHARACTERISTIC_UUID}")
        try:
            # Send the button press command to the BLE device
            await self.client.write_gatt_char(BUTTON_PRESS_CHARACTERISTIC_UUID, command)
            print(f"{button_label} button press command sent")
        except (BleakError, OSError) as e:
            # Print an error message if sending the command fails
            print(f"Failed to send button press command: {e}")

    async def send_pump_rate(self, pump_rate, unit="µL/min"):
        """
        Sends a pump rate command to the BLE device after converting it to µL/min.

        Args:
            pump_rate (float): The desired pump rate.
            unit (str): The unit of the pump rate, either 'mL/min' or 'µL/min'.

        Raises:
            ValueError: If an invalid unit is provided.
            BleakError or OSError: If there is an error sending the command to the BLE device.
        """
        # Convert the pump rate to µL/min
        rate_in_µL = convert_pump_rate(pump_rate, unit)
        # Convert the rate to bytes in little-endian format
        pump_rate_bytes = rate_in_µL.to_bytes(2, byteorder='little')
        print(f"Sending pump rate: {pump_rate} {unit} ({pump_rate_bytes.hex()}) to characteristic {PUMP_RATE_CHARACTERISTIC_UUID}")
        try:
            # Send the pump rate command to the BLE device
            await self.client.write_gatt_char(PUMP_RATE_CHARACTERISTIC_UUID, pump_rate_bytes)
            print("Pump rate sent")
        except (BleakError, OSError) as e:
            # Print an error message if sending the command fails
            print(f"Failed to send pump rate: {e}")

    async def disconnect(self):
        """
        Disconnects from the BLE device.

        Raises:
            BleakError: If there is an error disconnecting from the device.
        """
        print(f"Disconnecting from device at {self.address}")
        try:
            await self.client.disconnect()  # Attempt to disconnect from the BLE device
            print("Disconnected from device:", self.address)
        except BleakError as e:
            # Print an error message if disconnecting fails
            print(f"Failed to disconnect from device: {e}")

    def run_ble_tasks(self, app):
        """
        Runs BLE tasks for connecting, starting notifications, and handling disconnection.

        Args:
            app: An instance of an application class that contains a callback for handling notifications.
        """
        # Connect to the BLE device and start notifications
        self.loop.run_until_complete(self.connect())
        self.loop.run_until_complete(self.start_notify(app.handle_notification))
        # Continuously check the connection and attempt reconnection if needed
        while True:
            if not self.client.is_connected:
                print("Disconnected, attempting to reconnect...")
                self.loop.run_until_complete(self.connect())
                self.loop.run_until_complete(self.start_notify(app.handle_notification))
            # Sleep for a short interval before checking the connection again
            self.loop.run_until_complete(asyncio.sleep(1))
