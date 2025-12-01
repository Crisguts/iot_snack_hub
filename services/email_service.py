import smtplib
import ssl
import imaplib
import email
import os
import json
import time
import threading
from datetime import datetime
from dotenv import load_dotenv
import logging

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        # SMTP/IMAP setup
        self.smtp_host = "smtp.gmail.com"
        self.smtp_port = 465
        self.imap_host = "imap.gmail.com"

        # Credentials (use .env)
        self.login = os.getenv("EMAIL_LOGIN", "example@gmail.com")
        self.password = os.getenv("EMAIL_APP_PASSWORD", "")
        self.recipient = os.getenv("EMAIL_RECIPIENT", self.login)

        # SSL context
        self.context = ssl.create_default_context()

        # State handling - use absolute paths to ensure consistency
        self.state_file = os.path.abspath("email_state.json")
        self.processed_emails_file = os.path.abspath("processed_emails.json")
        print(f"📧 Email state file: {self.state_file}")
        self.processed_emails = self._load_processed_emails()  # Persistent tracking
        
        # Alert cooldown tracking (prevent spam)
        self.last_alert_time = {}  # {fridge_id: timestamp}
        self.alert_cooldown = 300  # 5 minutes between alerts for same fridge

        # Background thread
        self.monitoring = False
        self.monitor_thread = None

    def _send_email(self, subject, body, recipient=None):
        """Send email to specified recipient or default admin."""
        to_email = recipient if recipient else self.recipient
        try:
            email_msg = f"Subject: {subject}\nTo: {to_email}\nFrom: {self.login}\n\n{body}"
            with smtplib.SMTP_SSL(self.smtp_host, self.smtp_port, context=self.context, timeout=30) as server:
                server.login(self.login, self.password)
                server.sendmail(self.login, to_email, email_msg.encode("utf-8"))
            logger.info(f"Email sent to {to_email}: {subject}")
            return True
        except Exception as e:
            logger.error(f"Email send failed to {to_email}: {e}")
            return False

    def send_test(self):
        body = f"""This is a test email from your IoT Smart Store.

Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Reply 'YES' to activate the fan.
Reply 'NO' to ignore."""
        return self._send_email("🔧 IoT Test Email", body)

    def send_temp_alert(self, fridge_name, current_temp, threshold):
        """Legacy method name - calls send_temperature_alert"""
        return self.send_temperature_alert(
            fridge_id=1, 
            current_temp=current_temp, 
            threshold=threshold, 
            fridge_name=fridge_name
        )
    
    def send_temperature_alert(self, fridge_id, current_temp, threshold, fridge_name=None):
        """Send temperature alert email when threshold is exceeded.
        Includes cooldown to prevent spam (5 min between alerts per fridge)."""
        # Check cooldown
        current_time = time.time()
        last_sent = self.last_alert_time.get(fridge_id, 0)
        
        if current_time - last_sent < self.alert_cooldown:
            time_remaining = int(self.alert_cooldown - (current_time - last_sent))
            logger.info(f"Alert cooldown active for fridge {fridge_id}. {time_remaining}s remaining.")
            return False
        
        if not fridge_name:
            fridge_name = f"Refrigerator {fridge_id}"
        
        body = f"""⚠️ Temperature Alert!

{fridge_name} exceeded its threshold.
Current: {current_temp}°C
Threshold: {threshold}°C
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Reply 'YES' to activate cooling fan.
Reply 'NO' to ignore this alert.

Fridge ID: {fridge_id}"""
        
        success = self._send_email(f"🚨 IoT Alert - {fridge_name}", body)
        
        if success:
            # Update last alert time
            self.last_alert_time[fridge_id] = current_time
            logger.info(f"Temperature alert sent for fridge {fridge_id}. Cooldown active for {self.alert_cooldown}s")
        
        return success

    def send_confirmation(self, fridge_id):
        body = f"""Fan activation confirmed for Refrigerator {fridge_id}.
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""
        return self._send_email(f"✅ Fan Activated - Fridge {fridge_id}", body)

    def send_fan_error(self, fridge_id, error_message):
        """Send email notification when fan activation fails."""
        body = f"""⚠️ Fan Activation Failed

Refrigerator {fridge_id} fan could not be activated.
Error: {error_message}
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Please check the system manually or contact technical support."""
        return self._send_email(f"❌ Fan Activation Error - Fridge {fridge_id}", body)

    # --- Persistent email tracking ---
    def _load_processed_emails(self):
        """Load processed email IDs from disk."""
        try:
            if os.path.exists(self.processed_emails_file):
                with open(self.processed_emails_file, 'r') as f:
                    data = json.load(f)
                    # Keep only recent emails (last 1000) to prevent file bloat
                    return set(data[-1000:])
            return set()
        except Exception as e:
            logger.error(f"Failed to load processed emails: {e}")
            return set()
    
    def _save_processed_emails(self):
        """Save processed email IDs to disk."""
        try:
            with open(self.processed_emails_file, 'w') as f:
                json.dump(list(self.processed_emails), f)
        except Exception as e:
            logger.error(f"Failed to save processed emails: {e}")

    # --- Receiving replies ---
    def _check_email(self):
        """Checks latest emails for YES replies"""
        try:
            logger.info("Checking inbox for email replies...")
            mail = imaplib.IMAP4_SSL(self.imap_host)
            mail.login(self.login, self.password)
            mail.select("inbox")

            status, data = mail.search(None, "UNSEEN")
            email_ids = data[0].split()
            if not email_ids:
                logger.info("No unread emails found")
                mail.logout()
                return None
            
            logger.info(f"Found {len(email_ids)} unread email(s)")

            for eid in reversed(email_ids[-5:]):  # Check only last 5
                eid_str = eid.decode()
                if eid_str in self.processed_emails:
                    print(f"   Email {eid_str} already processed, skipping")
                    continue

                # Fetch without marking as read - use BODY.PEEK instead of RFC822
                status, msg_data = mail.fetch(eid, "(BODY.PEEK[])")
                msg = email.message_from_bytes(msg_data[0][1])
                subject = msg.get("subject", "")
                from_addr = msg.get("from", "unknown")
                body = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/plain":
                            body = part.get_payload(decode=True).decode(errors="ignore")
                            break
                else:
                    body = msg.get_payload(decode=True).decode(errors="ignore")

                print(f"   📬 Email from {from_addr}: {subject[:50]}")
                print(f"   Body preview: {body[:100]}")

                # Stricter YES matching - must be standalone word, not in instructions
                body_upper = body.upper()
                # Check if YES is a standalone reply (not part of "Reply 'YES' to activate")
                is_yes_reply = False
                for line in body_upper.split('\n'):
                    line_stripped = line.strip()
                    # Match YES as standalone word or at start of line
                    if line_stripped == 'YES' or line_stripped.startswith('YES ') or line_stripped.startswith('YES,'):
                        is_yes_reply = True
                        print(f"   ✅ Found YES in line: {line_stripped[:50]}")
                        break
                
                if is_yes_reply:
                    fridge_id = self._extract_fridge_id(subject, body)
                    logger.info(f"YES reply detected for fridge {fridge_id}")
                    print(f"🎯 YES REPLY DETECTED! Fridge {fridge_id}")
                    print(f"   From: {from_addr}")
                    print(f"   Subject: {subject}")
                    self._signal_fan(fridge_id)
                    self.send_confirmation(fridge_id)
                    # Mark as read and processed
                    mail.store(eid, '+FLAGS', '\\Seen')
                    self.processed_emails.add(eid_str)
                    self._save_processed_emails()
                    mail.logout()
                    return {"fan_on": True, "fridge_id": fridge_id}
                else:
                    print(f"   ❌ No YES found in email")

            mail.logout()
            return None
        except Exception as e:
            logger.error(f"Error checking inbox: {e}")
            return None

    def _extract_fridge_id(self, subject, body):
        for txt in (subject + body).lower().split():
            if "2" in txt:
                return 2
        return 1

    def _signal_fan(self, fridge_id):
        """Writes state file Flask can read"""
        try:
            state = {
                "action": "activate_fan",
                "fridge_id": fridge_id,
                "timestamp": datetime.now().isoformat()
            }
            with open(self.state_file, "w") as f:
                json.dump(state, f)
            print(f"✅ Wrote state file: {self.state_file}")
            print(f"   State: {state}")
            logger.info(f"Fan activation signaled for fridge {fridge_id}")
        except Exception as e:
            logger.error(f"Failed to write fan activation: {e}")
            print(f"❌ Failed to write state file: {e}")

    def get_and_clear_state(self):
        """Read and clear state file"""
        try:
            if not os.path.exists(self.state_file):
                return None
            with open(self.state_file, "r") as f:
                state = json.load(f)
            os.remove(self.state_file)
            print(f"📬 Read and cleared state file: {state}")
            return state
        except Exception as e:
            logger.error(f"State read error: {e}")
            print(f"❌ Failed to read state file: {e}")
            return None

    # --- Background thread ---
    def start_monitoring(self):
        if self.monitoring:
            logger.info("Email monitor already running")
            return
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("Started email monitor")

    def stop_monitoring(self):
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("Stopped email monitor")

    def _monitor_loop(self):
        print("📧 Email monitoring thread started")
        while self.monitoring:
            try:
                print("🔍 Checking inbox...")
                result = self._check_email()
                if result:
                    logger.info(f"Fan activation signal received: {result}")
                    print(f"✅ Fan signal sent: {result}")
                time.sleep(10)  # Check every 10 seconds for faster response
            except Exception as e:
                logger.error(f"Monitor loop error: {e}")
                print(f"❌ Email check error: {e}")
                time.sleep(30)  # Retry after 30s on error

# Global instance
email_service = EmailService()
