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

        # State handling
        self.state_file = "email_state.json"
        self.processed_emails = set()

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
        body = f"""⚠️ Temperature Alert!

{fridge_name} exceeded its threshold.
Current: {current_temp}°C
Threshold: {threshold}°C
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Reply 'YES' to activate cooling.
Reply 'NO' to ignore."""
        return self._send_email(f"🚨 IoT Alert - {fridge_name}", body)

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

    # --- Receiving replies ---
    def _check_email(self):
        """Checks latest emails for YES replies"""
        try:
            mail = imaplib.IMAP4_SSL(self.imap_host)
            mail.login(self.login, self.password)
            mail.select("inbox")

            status, data = mail.search(None, "UNSEEN")
            email_ids = data[0].split()
            if not email_ids:
                mail.logout()
                return None

            for eid in reversed(email_ids[-5:]):  # Check only last 5
                eid_str = eid.decode()
                if eid_str in self.processed_emails:
                    continue

                status, msg_data = mail.fetch(eid, "(RFC822)")
                msg = email.message_from_bytes(msg_data[0][1])
                subject = msg.get("subject", "")
                body = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/plain":
                            body = part.get_payload(decode=True).decode(errors="ignore")
                            break
                else:
                    body = msg.get_payload(decode=True).decode(errors="ignore")

                if "YES" in body.upper():
                    fridge_id = self._extract_fridge_id(subject, body)
                    logger.info(f"YES reply detected for fridge {fridge_id}")
                    self._signal_fan(fridge_id)
                    self.send_confirmation(fridge_id)
                    self.processed_emails.add(eid_str)
                    mail.logout()
                    return {"fan_on": True, "fridge_id": fridge_id}

                self.processed_emails.add(eid_str)

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
            logger.info(f"Fan activation signaled for fridge {fridge_id}")
        except Exception as e:
            logger.error(f"Failed to write fan activation: {e}")

    def get_and_clear_state(self):
        """Read and clear state file"""
        try:
            if not os.path.exists(self.state_file):
                return None
            with open(self.state_file, "r") as f:
                state = json.load(f)
            os.remove(self.state_file)
            return state
        except Exception as e:
            logger.error(f"State read error: {e}")
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
        while self.monitoring:
            try:
                result = self._check_email()
                if result:
                    logger.info(f"Fan activation signal received: {result}")
                time.sleep(30)
            except Exception as e:
                logger.error(f"Monitor loop error: {e}")
                time.sleep(60)

# Global instance
email_service = EmailService()
