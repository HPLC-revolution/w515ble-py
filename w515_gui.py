# version 0.1.0, by Mark Tapsak
# Visit virginiaanalytical.com to purchase a pump conversion kit 

import tkinter as tk  # Import the tkinter library for creating the GUI
import threading  # Import threading to handle asynchronous BLE operations
from w515_ble_device import w515_BLEDevice  # Import the BLE device management class
from w515_experiment import run_experiment  # Import the function to run pump experiments

class w515_App:
    """
    GUI Application class for controlling the Waters 515 HPLC pump using BLE.
    
    This class provides a graphical interface for users to interact with the pump, send commands, 
    set pump rates, and execute predefined experiments.
    """

    def __init__(self, root, ble_device):
        """
        Initializes the GUI application and sets up the BLE device for communication.

        Args:
            root: The root window object for the tkinter GUI.
            ble_device (w515_BLEDevice): An instance of the BLE device management class.
        """
        self.root = root  # Store the root window object
        self.ble_device = ble_device  # Store the BLE device instance
        self.root.title("HPLC Pump Control")  # Set the window title
        self.root.geometry("660x440")  # Set the window size

        # Readout display: Time, Pressure, Current, Pump Rate
        self.readout_frame = tk.Frame(root)  # Create a frame for the readout display
        self.readout_frame.pack(pady=10)  # Add padding around the frame

        # Create a label to display the current time, pressure, current, and pump rate
        self.readout_label = tk.Label(self.readout_frame, text="Time: 0.0s  |  PSI: 0  |  Current: 0  |  Pump Rate: 0", font=("Helvetica", 14))
        self.readout_label.pack()  # Pack the label into the frame

        # Button controls for manual operations
        self.button_frame = tk.Frame(root)  # Create a frame for the button controls
        self.button_frame.pack(pady=10)  # Add padding around the frame

        # Create buttons for Run/Stop, Arrow Up, Arrow Down, Edit, and Menu operations
        self.button_run_stop = tk.Button(self.button_frame, text="Run", font=("Helvetica", 14),
                                         bg="green", fg="white", command=self.toggle_run_stop)
        self.button_run_stop.grid(row=0, column=0, padx=5)  # Place the button in the grid

        self.button_up = tk.Button(self.button_frame, text="Arrow Up", font=("Helvetica", 14),
                                   command=lambda: self.send_button_press("UP"))  # Send UP button press
        self.button_up.grid(row=0, column=1, padx=5)
        self.add_hover_effect(self.button_up)  # Add hover effect for visual feedback

        self.button_down = tk.Button(self.button_frame, text="Arrow Down", font=("Helvetica", 14),
                                     command=lambda: self.send_button_press("DOWN"))  # Send DOWN button press
        self.button_down.grid(row=0, column=2, padx=5)
        self.add_hover_effect(self.button_down)

        self.button_edit = tk.Button(self.button_frame, text="Edit", font=("Helvetica", 14),
                                     command=lambda: self.send_button_press("EDIT"))  # Send EDIT button press
        self.button_edit.grid(row=0, column=3, padx=5)
        self.add_hover_effect(self.button_edit)

        self.button_menu = tk.Button(self.button_frame, text="Menu", font=("Helvetica", 14),
                                     command=lambda: self.send_button_press("MENU"))  # Send MENU button press
        self.button_menu.grid(row=0, column=4, padx=5)
        self.add_hover_effect(self.button_menu)

        # Pump Rate Entry
        self.rate_frame = tk.Frame(root)  # Create a frame for pump rate entry
        self.rate_frame.pack(pady=20)  # Add padding around the frame

        # Create a label and entry widget for setting the pump rate
        self.rate_label = tk.Label(self.rate_frame, text="Pump Rate:", font=("Helvetica", 14))
        self.rate_label.pack(side=tk.LEFT)

        self.rate_entry = tk.Entry(self.rate_frame, font=("Helvetica", 14), width=6)
        self.rate_entry.pack(side=tk.LEFT)

        self.rate_button = tk.Button(self.rate_frame, text="Set Pump Rate", font=("Helvetica", 14),
                                     command=self.send_pump_rate)  # Set pump rate when clicked
        self.rate_button.pack(side=tk.LEFT, padx=10)
        self.add_hover_effect(self.rate_button)

        # Separator Line for visual separation between manual controls and experiment controls
        self.separator = tk.Canvas(root, height=3, bd=0, highlightthickness=0, relief='ridge')
        self.separator.pack(fill='x', padx=10, pady=10)  # Fill the width of the window
        self.separator.create_line(0, 2, 660, 2, fill="dark grey", width=6)  # Draw a bold line

        # Experiment Grid for setting up an experiment with multiple stages
        self.grid_frame = tk.Frame(root)  # Create a frame for the experiment grid
        self.grid_frame.pack(pady=20)  # Add padding around the frame

        # Initial Static Rate input widgets
        self.label_initial_rate = tk.Label(self.grid_frame, text="Initial Rate:", font=("Helvetica", 14), anchor='w')
        self.label_initial_rate.grid(row=0, column=0, padx=10, sticky='w')  # Left-aligned label
        self.entry_initial_rate = tk.Entry(self.grid_frame, font=("Helvetica", 14), width=6)
        self.entry_initial_rate.grid(row=0, column=1, padx=10)

        self.label_initial_duration = tk.Label(self.grid_frame, text="Duration (min):", font=("Helvetica", 14), anchor='w')
        self.label_initial_duration.grid(row=0, column=2, padx=10, sticky='w')  # Left-aligned label
        self.entry_initial_duration = tk.Entry(self.grid_frame, font=("Helvetica", 14), width=6)
        self.entry_initial_duration.grid(row=0, column=3, padx=10)

        # Ramp Up Stage input widgets
        self.label_ramp_up = tk.Label(self.grid_frame, text="Ramp to Rate:", font=("Helvetica", 14), anchor='w')
        self.label_ramp_up.grid(row=1, column=0, padx=10, sticky='w')  # Left-aligned label
        self.entry_ramp_up_rate = tk.Entry(self.grid_frame, font=("Helvetica", 14), width=6)
        self.entry_ramp_up_rate.grid(row=1, column=1, padx=10)

        self.label_ramp_up_duration = tk.Label(self.grid_frame, text="Duration (min):", font=("Helvetica", 14), anchor='w')
        self.label_ramp_up_duration.grid(row=1, column=2, padx=10, sticky='w')  # Left-aligned label
        self.entry_ramp_up_duration = tk.Entry(self.grid_frame, font=("Helvetica", 14), width=6)
        self.entry_ramp_up_duration.grid(row=1, column=3, padx=10)

        # Static Hold input widgets
        self.label_hold_duration = tk.Label(self.grid_frame, text="Hold (min):", font=("Helvetica", 14), anchor='w')
        self.label_hold_duration.grid(row=2, column=2, padx=10, sticky='w')  # Left-aligned label
        self.entry_hold_duration = tk.Entry(self.grid_frame, font=("Helvetica", 14), width=6)
        self.entry_hold_duration.grid(row=2, column=3, padx=10)

        # Ramp Down Stage input widgets
        self.label_ramp_down = tk.Label(self.grid_frame, text="Ramp to Rate:", font=("Helvetica", 14), anchor='w')
        self.label_ramp_down.grid(row=3, column=0, padx=10, sticky='w')  # Left-aligned label
        self.entry_ramp_down_rate = tk.Entry(self.grid_frame, font=("Helvetica", 14), width=6)
        self.entry_ramp_down_rate.grid(row=3, column=1, padx=10)

        self.label_ramp_down_duration = tk.Label(self.grid_frame, text="Duration (min):", font=("Helvetica", 14), anchor='w')
        self.label_ramp_down_duration.grid(row=3, column=2, padx=10, sticky='w')  # Left-aligned label
        self.entry_ramp_down_duration = tk.Entry(self.grid_frame, font=("Helvetica", 14), width=6)
        self.entry_ramp_down_duration.grid(row=3, column=3, padx=10)

        # Start Experiment Button to execute the experiment
        self.start_button = tk.Button(root, text="Start Experiment", font=("Helvetica", 14), command=self.start_experiment)
        self.start_button.pack(pady=20)
        self.add_hover_effect(self.start_button)

        # Start BLE tasks in a separate thread to avoid blocking the GUI
        ble_thread = threading.Thread(target=self.ble_device.run_ble_tasks, args=(self,))
        ble_thread.start()

    def toggle_run_stop(self):
        """
        Toggles the Run/Stop state of the pump when the button is clicked.
        """
        if self.button_run_stop['text'] == 'Run':
            self.send_button_press("RunStop")  # Send Run command
            self.button_run_stop.config(text='Stop', bg="red", fg="white")  # Change button to Stop
        else:
            self.send_button_press("RunStop")  # Send Stop command
            self.button_run_stop.config(text='Run', bg="green", fg="white")  # Change button to Run

    def handle_notification(self, sender, data):
        """
        Handles incoming BLE notifications and updates the GUI readout.

        Args:
            sender: The source of the notification.
            data (bytes): The data received from the BLE device.
        """
        if len(data) == 12:  # We expect 12 bytes, with the last 2 bytes being extra
            # Parse the timestamp, PSI, motor current, and pump rate from the data
            timestamp = int.from_bytes(data[0:4], byteorder='little') / 1000.0  # Convert to seconds
            psi = int.from_bytes(data[4:6], byteorder='little')
            motor_current = int.from_bytes(data[6:8], byteorder='little')
            pump_rate = int.from_bytes(data[8:10], byteorder='little')
            print(f"Parsed data - Timestamp: {timestamp:.3f} s, PSI: {psi}, Motor Current: {motor_current}, Pump Rate: {pump_rate}")

            # Update the readout label with the parsed values
            self.readout_label.config(text=f"Time: {timestamp:.3f}s | PSI: {psi} | Current: {motor_current} | Pump Rate: {pump_rate}")
        else:
            print(f"Unexpected data length: {len(data)}")  # Handle unexpected data lengths

    def send_button_press(self, button_label):
        """
        Sends a button press command to the BLE device.

        Args:
            button_label (str): The label of the button to press (e.g., "RunStop", "UP").
        """
        # Schedule the button press command to be sent in the event loop
        self.ble_device.loop.create_task(self.ble_device.send_button_press(button_label))

    def send_pump_rate(self):
        """
        Reads the pump rate from the user input and sends it to the BLE device.
        """
        try:
            pump_rate = int(self.rate_entry.get())  # Get the pump rate from the entry widget
            if 1 <= pump_rate <= 10000:
                self.ble_device.loop.create_task(self.ble_device.send_pump_rate(pump_rate))  # Send the pump rate
            else:
                print("Invalid pump rate. Please enter a number between 1 and 10000.")
        except ValueError:
            print("Please enter a valid number for the pump rate.")

    def start_experiment(self):
        """
        Collects user input from the experiment grid and starts the experiment.
        """
        try:
            # Create a list of stages for the experiment
            stages = [
                {'type': 'static', 'rate': int(self.entry_initial_rate.get()), 'duration': float(self.entry_initial_duration.get())},
                {'type': 'ramp', 'start_rate': int(self.entry_initial_rate.get()), 'end_rate': int(self.entry_ramp_up_rate.get()), 'duration': float(self.entry_ramp_up_duration.get())},
                {'type': 'static', 'rate': int(self.entry_ramp_up_rate.get()), 'duration': float(self.entry_hold_duration.get())},
                {'type': 'ramp', 'start_rate': int(self.entry_ramp_up_rate.get()), 'end_rate': int(self.entry_ramp_down_rate.get()), 'duration': float(self.entry_ramp_down_duration.get())},
            ]
            # Schedule the experiment to run in the event loop
            self.ble_device.loop.create_task(run_experiment(self.ble_device, stages))
        except ValueError:
            print("Please enter valid values for all fields.")  # Handle invalid input values

    def add_hover_effect(self, button):
        """
        Adds a hover effect to a button for better user experience.

        Args:
            button: The button widget to add the hover effect to.
        """
        # Change button background color on hover
        button.bind("<Enter>", lambda e: button.config(bg="lightblue"))
        button.bind("<Leave>", lambda e: button.config(bg="SystemButtonFace"))
