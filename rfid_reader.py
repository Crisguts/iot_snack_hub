import serial
import time

SERIAL_PORT = '/dev/ttyAMA10' # e.g., 'COM3' or '/dev/ttyUSB0'
BAUD_RATE = 9600 # Ensure this matches the reader's setting

try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    print(f"Connected to {SERIAL_PORT}")

    while True:
        # Read data from the serial port
        serial_data = ser.readline()
        if serial_data:
            try:
                tag_id = serial_data.decode('utf-8').strip()
                if tag_id:
                    print(f"Tag ID: {tag_id}")
                    
            except UnicodeDecodeError:
                print("Could not decode data to UTF-8")
        time.sleep(0.1)
except serial.SerialException as e:
    print(f"Serial port error: {e}")
except KeyboardInterrupt:
    print("Exiting Program")
except Exception as e:
    print(f"An error occurred: {e}")
finally:
    if 'ser' in locals() and ser.is_open:
        ser.close()
        print("Serial port closed.")