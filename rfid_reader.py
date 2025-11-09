import serial
import threading
from datetime import datetime
from db import supabase

class RFIDReader:
    def __init__(self, port="/dev/ttyUSB0", baudrate=9600):
        self.port = port
        self.baudrate = baudrate
        self.serial_conn = None
        self.thread = None
        self.running = False
        self.last_epc = None

    def start(self):
        """Start reading RFID tags continuously in a background thread."""
        try:
            self.serial_conn = serial.Serial(self.port, self.baudrate, timeout=1)
            self.running = True
            self.thread = threading.Thread(target=self._read_loop, daemon=True)
            self.thread.start()
            print(f"✅ RFID Reader started on {self.port}")
        except Exception as e:
            print(f"❌ Failed to open RFID port {self.port}: {e}")

    def _read_loop(self):
        """Continuously read EPC data from the RFID device."""
        while self.running:
            try:
                if self.serial_conn and self.serial_conn.in_waiting > 0:
                    line = self.serial_conn.readline().decode("utf-8").strip()
                    if line:
                        print(f"🎫 EPC Tag Read: {line}")
                        self.last_epc = line
                        self.save_epc_to_db(line)
            except Exception as e:
                print(f"⚠️ RFID read error: {e}")

    def save_epc_to_db(self, epc_code):
        """Insert EPC data into Supabase table `rfid_tags`."""
        try:
            data = {
                "epc": epc_code,
                "created_at": datetime.now().isoformat()
            }
            print("💾 Inserting EPC into DB:", data)
            response = supabase.table("rfid_tags").insert(data).execute()
            if getattr(response, "data", None):
                print("✅ EPC saved:", response.data)
            else:
                print("⚠️ Insert returned no data. Check Supabase.")
        except Exception as e:
            print(f"❌ Error saving EPC to DB: {e}")

    def stop(self):
        self.running = False
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
        print("🛑 RFID Reader stopped")
