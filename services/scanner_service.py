# services/scanner_service.py
"""
Scanner service for USB barcode scanner and RFID reader
Supports mock mode for development without hardware
"""
import os
import threading
import time
import queue
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Mock mode if no hardware
MOCK_MODE = os.getenv("SCANNER_MOCK_MODE", "True").lower() == "true"

class ScannerService:
    def __init__(self):
        self.scan_queue = queue.Queue()
        self.running = False
        self.thread = None
        
        # RFID settings
        self.rfid_port = os.getenv("RFID_PORT", "/dev/ttyAMA10")
        self.rfid_baud = int(os.getenv("RFID_BAUD", 9600))
        self.rfid_connection = None
        
    def start(self):
        """Start scanner listener in background thread."""
        if self.running:
            logger.info("Scanner service already running")
            return
        
        self.running = True
        
        if not MOCK_MODE:
            # Real hardware mode
            self.thread = threading.Thread(target=self._listen_rfid, daemon=True)
            self.thread.start()
            logger.info("✅ Scanner service started (RFID mode)")
        else:
            # Mock mode for development
            logger.info("⚠️ Scanner service started (MOCK mode)")
    
    def stop(self):
        """Stop scanner service."""
        self.running = False
        if self.rfid_connection:
            try:
                self.rfid_connection.close()
            except:
                pass
        logger.info("Scanner service stopped")
    
    def _listen_rfid(self):
        """Listen to RFID reader (real hardware)."""
        try:
            import serial
            self.rfid_connection = serial.Serial(
                self.rfid_port, 
                self.rfid_baud, 
                timeout=1
            )
            logger.info(f"Connected to RFID reader at {self.rfid_port}")
            
            while self.running:
                try:
                    serial_data = self.rfid_connection.readline()
                    if serial_data:
                        try:
                            tag_id = serial_data.decode('utf-8').strip()
                            if tag_id:
                                logger.info(f"RFID scanned: {tag_id}")
                                self.scan_queue.put({"type": "rfid", "code": tag_id})
                        except UnicodeDecodeError:
                            logger.warning("Could not decode RFID data")
                    time.sleep(0.1)
                except Exception as e:
                    logger.error(f"RFID read error: {e}")
                    time.sleep(1)
                    
        except Exception as e:
            logger.error(f"RFID connection error: {e}")
    
    def scan_barcode_input(self, barcode):
        """
        Simulate barcode scan input (for USB barcode scanner or manual input).
        USB barcode scanners act as keyboards, so this can be called from form input.
        """
        if barcode:
            logger.info(f"Barcode scanned: {barcode}")
            self.scan_queue.put({"type": "barcode", "code": barcode})
            return True
        return False
    
    def scan_rfid_manual(self, rfid_code):
        """Manually add RFID scan (for testing or backup input)."""
        if rfid_code:
            logger.info(f"RFID manual input: {rfid_code}")
            self.scan_queue.put({"type": "rfid", "code": rfid_code})
            return True
        return False
    
    def get_scan(self, timeout=0.1):
        """
        Get next scan from queue (non-blocking).
        Returns: {"type": "barcode"|"rfid", "code": "..."} or None
        """
        try:
            return self.scan_queue.get(timeout=timeout)
        except queue.Empty:
            return None
    
    def has_pending_scans(self):
        """Check if there are pending scans."""
        return not self.scan_queue.empty()
    
    # Mock data for testing
    def generate_mock_scan(self, product_type="beverage"):
        """Generate mock scan data for testing."""
        mock_data = {
            "beverage": [
                {"type": "barcode", "code": "012000001234"},
                {"type": "rfid", "code": "E200001234567890ABCD"}
            ],
            "snack": [
                {"type": "barcode", "code": "028400005678"},
                {"type": "rfid", "code": "E200009876543210DCBA"}
            ]
        }
        
        scans = mock_data.get(product_type, mock_data["beverage"])
        import random
        scan = random.choice(scans)
        self.scan_queue.put(scan)
        return scan


# Global scanner instance
scanner_service = ScannerService()

# Auto-start if requested
if os.getenv("SCANNER_AUTO_START", "false").lower() in ("1", "true", "yes"):
    scanner_service.start()
