# Pump Controller Hardware and BLE Communication Guide

## Hardware Overview

The controller hardware is powered by a Nordic nRF52840 chip and designed to interface with a Waters 515 HPLC pump system via BLE (Bluetooth Low Energy). It simulates button presses on the 515 pump, reads the pressure transducer, and monitors the motor function. Below is a description of the key BLE characteristics and their configuration.

### BLE UUIDs and Characteristics

The following UUIDs are used to define services and characteristics for BLE communication:

- **Measurement Service UUID:** `000012A3-0000-1000-8000-00805F9B34FB`
  - Provides all measurement and control functionalities.

#### Characteristics

- **Pump Measurement Characteristic UUID:** `000055A5-0000-1000-8000-00805F9B34FB`
  - Provides notifications of measurement records (12 bytes, with the last 2 bytes unused).
- **Measurement Interval Characteristic UUID:** `000055A6-0000-1000-8000-00805F9B34FB`
  - Allows setting the measurement interval (2 bytes, write-only).
- **Synchronization Command Characteristic UUID:** `000055A7-0000-1000-8000-00805F9B34FB`
  - Accepts synchronization commands (variable length, write-only).
- **Button Press Characteristic UUID:** `000055A8-0000-1000-8000-00805F9B34FB`
  - Triggers button press simulations on the pump (2 bytes, write-only).
- **Pump Rate Characteristic UUID:** `000055A9-0000-1000-8000-00805F9B34FB`
  - Allows setting the pump rate (2 bytes, write-only).

### Measurement Record Structure

A 12-byte measurement record is sent over BLE using the Pump Measurement Characteristic:

| Byte Index | Field         | Description                                      |
|------------|---------------|--------------------------------------------------|
| 0-3        | `timeStamp`   | 4 bytes, measured in milliseconds since start    |
| 4-5        | `PSI`         | 2 bytes, analog input A0 from PSI sensor         |
| 6-7        | `motorCurrent`| 2 bytes, analog input A1 from motor current sensor|
| 8-9        | `pumpRate`    | 2 bytes, current pump rate                       |
| 10-11      | Unused        | Reserved for future use                          |

## BLE Communication

The hardware is set up to communicate via BLE using the above characteristics. Here is a guide on how to interact with the hardware from any software tool:

### Receiving Data

To receive data packets from the pump controller, listen for notifications on the Pump Measurement Characteristic (`000055A5-0000-1000-8000-00805F9B34FB`). Each notification will contain a 12-byte packet as described above.

### Sending Commands

To control the pump and send commands to the controller, you can write to the following characteristics:

- **Measurement Interval Characteristic (`000055A6-0000-1000-8000-00805F9B34FB`):**
  - Write a 2-byte value representing the desired measurement interval in milliseconds. For example, to set a 1-second interval, write `0xE8 0x03` (1000 in decimal). The longest measurement interval can be 65.5 seconds, and the shortest should be no less than 0.40 seconds to avoid interference from receiving pump commands.
  
- **Synchronization Command Characteristic (`000055A7-0000-1000-8000-00805F9B34FB`):**
  - Write the ASCII string "SYNC" to synchronize the internal clock. This command resets the internal timestamp to 0, useful for synchronizing multiple pump controllers and HPLC detector controllers.
  
- **Button Press Characteristic (`000055A8-0000-1000-8000-00805F9B34FB`):**
  - Write a 2-byte command to simulate a button press on the front panel of the pump. The table below details the byte values for each button function:

### Button Press Command Table

To simulate button presses on the HPLC pump, send a 2-byte command to the **Button Press Characteristic** (`000055A8-0000-1000-8000-00805F9B34FB`).

| Function         | Byte 1 | Byte 2 | Description                              |
|------------------|--------|--------|------------------------------------------|
| **Run/Stop**     | `0x00` | `0x00` | Simulate pressing the Run/Stop button    |
| **Up Arrow**     | `0x01` | `0x00` | Simulate pressing the Up Arrow button    |
| **Down Arrow**   | `0x01` | `0x01` | Simulate pressing the Down Arrow button  |
| **Edit**         | `0x02` | `0x01` | Simulate pressing the Edit button        |
| **Menu**         | `0x02` | `0x00` | Simulate pressing the Menu button        |

### Usage Example

To interact with the pump:

1. **Run/Stop**: Write `0x00 0x00` to the characteristic to simulate the Run/Stop button.
2. **Up Arrow**: Write `0x01 0x00` to simulate the Up Arrow button.
3. **Down Arrow**: Write `0x01 0x01` to simulate the Down Arrow button.
4. **Edit**: Write `0x02 0x01` to simulate the Edit button.
5. **Menu**: Write `0x02 0x00` to simulate the Menu button.

Simply send the corresponding two-byte value to the BLE characteristic to control the desired function.

  
- **Pump Rate Characteristic (`000055A9-0000-1000-8000-00805F9B34FB`):**
  - Write a 2-byte value representing the new pump rate in microliters per minute (µL/min). The value should be in little-endian format (least significant byte first). The valid range for the pump rate is 1 to 10,000 µL/min. Note that the rates are displayed as milliliters per minute (mL/min) on the pump's LCD display.

### Example of Sending Data via BLE

Here's an example of sending data using a BLE software tool:

1. **Set Measurement Interval to 500ms:**
   - Write `0xF4 0x01` to the UUID `000055A6-0000-1000-8000-00805F9B34FB`.

2. **Synchronize Time:**
   - Write the ASCII bytes for "SYNC" to the UUID `000055A7-0000-1000-8000-00805F9B34FB`.

3. **Set Pump Rate to 1500 µL/min (1.500 mL/min):**
   - Write `0xDC 0x05` to the UUID `000055A9-0000-1000-8000-00805F9B34FB`.

## Troubleshooting BLE Communication

If you encounter any issues while communicating with the pump controller via BLE, you can connect the hardware to a PC using a USB-C cable. To do this, remove the four screws that secure the case top to the pump base, carefully lift this up and away from the pump. The controller board is near the rear of the case, and is connected with enough ribbon cable that it can be safely moved to make a connection to its' USB-C port. By opening a serial monitor (such as the one included in the Arduino IDE) set to a baud rate of 9600, you can receive debug messages directly from the hardware. These messages provide valuable insights into the device's internal state and actions.

### Summary of Serial Print Statements

- **"Setup complete"**: Printed after the hardware has been initialized successfully.
- **"BLE Connected"**: Printed when a BLE connection is established.
- **"BLE Disconnected"**: Printed when the BLE connection is lost or disconnected.
- **"Notification sent successfully" / "Failed to send notification"**: Printed after attempting to send a BLE notification with the current measurement record.
- **"Data received for Measurement Interval..."**: Printed upon receiving a new measurement interval, showing the data length and content in hexadecimal.
- **"Received 2-byte unsigned integer: [value]"**: Printed to display the new measurement interval received.
- **"Time synchronized"**: Printed when a synchronization command is successfully received.
- **"Received button press command:"**: Printed after a valid button press command is received, showing the corresponding data.
- **"Invalid button press command received"**: Printed if the button press command received is not valid (incorrect length).
- **"Received pump rate: [value]"**: Printed to display the new pump rate received.
- **"Adjusting pump rate from [currentRate] to [newPumpRate]"**: Printed when adjusting the pump rate.
- **"Pump rate set successfully."**: Printed once the pump rate has been updated.

By reviewing these serial print statements, you can diagnose issues, verify commands received, and ensure proper operation of the pump controller.
  
## Conclusion

This guide provides a detailed overview of the hardware and BLE communication for the pump controller. By using the defined UUIDs and characteristics, users can control the pump and receive sensor data using any BLE-capable software tool. The packet structure, command examples, and troubleshooting tips will help you develop your software tools for integrating with this hardware.
