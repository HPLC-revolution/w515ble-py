# version 0.1.0, by Mark Tapsak
# Visit virginiaanalytical.com to purchase a pump conversion kit

import asyncio  # Importing asyncio to handle asynchronous tasks

def validate_stage(stage):
    """
    Validates an experimental stage dictionary to ensure it has valid values for 'duration', 'rate', 'start_rate', 
    and 'end_rate'. Raises ValueError if any of the conditions are not met.

    Args:
        stage (dict): A dictionary representing a stage of an experiment with keys like 'duration', 'rate', 
                      'start_rate', 'end_rate'.

    Raises:
        ValueError: If 'duration' is non-positive, or 'rate', 'start_rate', or 'end_rate' are out of valid range.
    """
    # Check if 'duration' is specified and ensure it is a positive number
    if 'duration' in stage and stage['duration'] <= 0:
        raise ValueError(f"Duration must be a positive number. Received: {stage['duration']}")

    # Check if 'rate' is within the valid range (1 to 10000 µL/min)
    if 'rate' in stage and (stage['rate'] < 1 or stage['rate'] > 10000):
        raise ValueError(f"Rate must be between 1 and 10000 µL/min. Received: {stage['rate']}")

    # Check if both 'start_rate' and 'end_rate' are provided and within the valid range
    if 'start_rate' in stage and 'end_rate' in stage:
        if stage['start_rate'] < 1 or stage['end_rate'] < 1:
            raise ValueError(f"Rates must be between 1 and 10000 µL/min. Received start_rate: {stage['start_rate']}, end_rate: {stage['end_rate']}")

async def execute_ramp(ble_device, start_rate, end_rate, duration):
    """
    Executes a ramp experiment where the pump rate is gradually increased or decreased from start_rate to end_rate 
    over the specified duration.

    Args:
        ble_device: An instance of BLEDevice that handles communication with the pump.
        start_rate (int): The starting pump rate in µL/min.
        end_rate (int): The ending pump rate in µL/min.
        duration (float): Duration of the ramp in minutes.
    """
    update_interval = 3.0  # Interval in seconds between updates to the pump rate
    num_steps = int((duration * 60) / update_interval)  # Calculate number of steps based on duration and update interval
    rate_increment = (end_rate - start_rate) / num_steps  # Calculate the rate change increment for each step
    current_rate = start_rate  # Initialize the current rate to the start rate

    # Loop to update the pump rate at each step
    for _ in range(num_steps):
        await ble_device.send_pump_rate(int(current_rate))  # Send the current rate to the pump
        current_rate += rate_increment  # Increment the current rate by the calculated increment
        await asyncio.sleep(update_interval)  # Wait for the specified update interval

    # Ensure the final rate is sent to the pump at the end of the ramp
    await ble_device.send_pump_rate(int(end_rate))

async def execute_static(ble_device, rate, duration):
    """
    Executes a static experiment where the pump rate is set to a fixed rate for a specified duration.

    Args:
        ble_device: An instance of BLEDevice that handles communication with the pump.
        rate (int): The pump rate in µL/min to maintain during the static phase.
        duration (float): Duration of the static phase in minutes.
    """
    await ble_device.send_pump_rate(rate)  # Set the pump to the specified rate
    await asyncio.sleep(duration * 60)  # Wait for the duration specified (converted from minutes to seconds)

async def run_experiment(ble_device, stages):
    """
    Runs a complete experiment consisting of multiple stages, where each stage can either be a static or ramp phase.

    Args:
        ble_device: An instance of BLEDevice that handles communication with the pump.
        stages (list): A list of dictionaries, where each dictionary represents a stage with type ('static' or 'ramp'),
                       rate(s), and duration.
    """
    # Iterate through each stage in the experiment
    for stage in stages:
        validate_stage(stage)  # Validate the stage data
        # Check if the stage is a 'static' type and execute the static phase
        if stage['type'] == 'static':
            await execute_static(ble_device, stage['rate'], stage['duration'])
        # Check if the stage is a 'ramp' type and execute the ramp phase
        elif stage['type'] == 'ramp':
            await execute_ramp(ble_device, stage['start_rate'], stage['end_rate'], stage['duration'])

def create_experiment(initial_rate, ramp_up_rate, ramp_up_duration, hold_duration, ramp_down_rate, ramp_down_duration):
    """
    Creates a structured list of experimental stages for a pump control experiment, consisting of static and ramp phases.

    Args:
        initial_rate (int): The initial pump rate for the first static stage in µL/min.
        ramp_up_rate (int): The target pump rate for the ramp-up stage in µL/min.
        ramp_up_duration (float): The duration for the ramp-up stage in minutes.
        hold_duration (float): The duration for the static hold stage in minutes.
        ramp_down_rate (int): The target pump rate for the ramp-down stage in µL/min.
        ramp_down_duration (float): The duration for the ramp-down stage in minutes.

    Returns:
        list: A list of dictionaries, each representing a stage with type ('static' or 'ramp'), rate(s), and duration.
    """
    # Return a list of stages representing the experiment sequence
    return [
        {'type': 'static', 'rate': initial_rate, 'duration': ramp_up_duration},  # Initial static stage
        {'type': 'ramp', 'start_rate': initial_rate, 'end_rate': ramp_up_rate, 'duration': ramp_up_duration},  # Ramp up stage
        {'type': 'static', 'rate': ramp_up_rate, 'duration': hold_duration},  # Static hold stage
        {'type': 'ramp', 'start_rate': ramp_up_rate, 'end_rate': ramp_down_rate, 'duration': ramp_down_duration},  # Ramp down stage
    ]
