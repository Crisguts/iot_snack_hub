# services/scanner_service.py
"""
I KEPT THIS FILE EVEN THOUGH WE DONT USE IT ANYMORE (FOR NOW). INSTEAD SCANNERS ARE HANDLED 
USING SIMPLE JS + FLASK ENDPOINTS (hidden inputs with event listeners).

Scanner service for USB barcode scanner and RFID reader.
- USB barcode scanners work as keyboard input (no special config needed)
- RFID readers connect via serial port
- Mock mode available for development without hardware
"""
import os
import threading
import time
import queue
import logging
import glob

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Mock mode if no hardware detected
MOCK_MODE = os.getenv("SCANNER_MOCK_MODE", "True").lower() == "true"

class ScannerService:
    def __init__(self):
        self.scan_queue = queue.Queue()
        self.running = False
        self.thread = None
        
        # RFID settings - will auto-detect if not specified
        self.rfid_port = os.getenv("RFID_PORT", None)
        self.rfid_baud = int(os.getenv("RFID_BAUD", 9600))
        self.rfid_connection = None
        
    def _detect_rfid_port(self):
        """Auto-detect RFID reader serial port."""
        # Common serial port patterns
        patterns = [
            '/dev/ttyUSB*',  # Linux USB serial
            '/dev/ttyACM*',  # Linux ACM serial
            '/dev/ttyAMA*',  # Raspberry Pi serial
            '/dev/cu.usb*',  # macOS USB serial
        ]
        
        for pattern in patterns:
            ports = glob.glob(pattern)
            if ports:
                logger.info(f"Detected potential RFID port: {ports[0]}")
                return ports[0]
        
        logger.warning("No RFID serial port detected")
        return None
        
    def start(self):
        """Start scanner listener in background thread."""
        if self.running:
            logger.info("Scanner service already running")
            return
        
        self.running = True
        
        if not MOCK_MODE:
            # Auto-detect RFID port if not specified
            if not self.rfid_port:
                self.rfid_port = self._detect_rfid_port()
            
            if self.rfid_port:
                # Real hardware mode - start RFID listener
                self.thread = threading.Thread(target=self._listen_rfid, daemon=True)
                self.thread.start()
                logger.info(f"✅ Scanner service started (RFID on {self.rfid_port})")
                logger.info("💡 USB barcode scanners work automatically as keyboard input")
            else:
                # No RFID detected - USB barcode only
                logger.info("✅ Scanner service started (USB barcode only)")
                logger.info("⚠️  No RFID reader detected. Set RFID_PORT env var if you have one.")
        else:
            # Mock mode for development
            logger.info("⚠️ Scanner service started (MOCK mode)")
            logger.info("💡 Set SCANNER_MOCK_MODE=False to use real hardware")
    
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
