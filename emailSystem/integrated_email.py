#!/usr/bin/env python3
"""
Integrated Email System for IoT Smart Store

This system integrates email monitoring with the Flask app's fan control.
It shares state through a simple file-based communication system.
"""

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

load_dotenv()

class IntegratedEmailSystem:
    def __init__(self):
        # SMTP Configuration
        self.smtp_host = "smtp.gmail.com"
        self.smtp_port = 465
        self.imap_host = "imap.gmail.com"
        
        # Credentials
        self.login = os.getenv("EMAIL_LOGIN", "default-email@gmail.com")
        self.password = os.getenv("EMAIL_APP_PASSWORD", "default-app-password")
        self.recipient = os.getenv("EMAIL_RECIPIENT", self.login)
        
        # SSL context
        self.context = ssl.create_default_context()
        
        # State file for communication with Flask
        self.state_file = "email_state.json"
        self.processed_emails = set()
        
        # Monitoring control
        self.monitoring = False
        self.monitor_thread = None
    
    def send_test_email(self):
        """Send a simple test email"""
        try:
            subject = "IoT Test Email"
            body = f"""This is a test email from your IoT Smart Store system.

Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Reply 'YES' to this email to turn on the fan.
Reply 'NO' to take no action.

This is an automated message from your IoT monitoring system.
"""
            
            email_message = f"Subject: {subject}\nTo: {self.recipient}\nFrom: {self.login}\n\n{body}"
            
            with smtplib.SMTP_SSL(self.smtp_host, self.smtp_port, context=self.context) as server:
                server.login(self.login, self.password)
                server.sendmail(self.login, self.recipient, email_message.encode('utf-8'))
                
            print("✅ Test email sent successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Email test failed: {e}")
            return False
    
    def check_for_yes_replies(self):
        """Check for YES replies in recent emails"""
        try:
            # Connect to Gmail
            mail = imaplib.IMAP4_SSL(self.imap_host)
            mail.login(self.login, self.password)
            mail.select("inbox")
            
            # Get recent emails
            status, messages = mail.search(None, "ALL")
            email_ids = messages[0].split()
            
            if not email_ids:
                mail.logout()
                return False
            
            # Check last 5 emails for YES replies
            for email_id in reversed(email_ids[-5:]):
                email_id_str = email_id.decode()
                
                # Skip processed emails
                if email_id_str in self.processed_emails:
                    continue
                
                status, msg_data = mail.fetch(email_id, "(RFC822)")
                msg = email.message_from_bytes(msg_data[0][1])
                
                subject = msg.get("subject", "")
                
                # Get email body
                body = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/plain":
                            try:
                                body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                                break
                            except:
                                continue
                else:
                    try:
                        body = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
                    except:
                        body = ""
                
                # Check if this is an IoT-related reply
                is_iot_reply = (
                    "IoT" in subject or 
                    "test email" in subject.lower() or
                    "temperature alert" in subject.lower() or
                    "IoT" in body or
                    "fan" in body.lower() or
                    "refrigerator" in body.lower()
                )
                
                # Check for YES reply
                if is_iot_reply and "YES" in body.upper():
                    print(f"🎯 Found YES reply! Analyzing for fridge ID...")
                    
                    # Try to determine which fridge from the email content
                    fridge_id = self.extract_fridge_id(subject, body)
                    
                    print(f"   Extracted Fridge ID: {fridge_id}")
                    print(f"   Subject: {subject}")
                    print(f"   Body preview: {body[:100]}...")
                    
                    # Mark this email as processed
                    self.processed_emails.add(email_id_str)
                    
                    # Signal Flask to activate fan for the specific fridge
                    self.signal_fan_activation(fridge_id)
                    
                    # Send confirmation
                    self.send_confirmation_email(fridge_id)
                    
                    mail.logout()
                    return True
                
                # Mark as processed
                self.processed_emails.add(email_id_str)
            
            mail.logout()
            return False
            
        except Exception as e:
            print(f"❌ Error checking emails: {e}")
            return False
    
    def extract_fridge_id(self, subject, body):
        """
        Extract fridge ID from email subject or body
        
        Args:
            subject (str): Email subject
            body (str): Email body
            
        Returns:
            int: Fridge ID (1 or 2), defaults to 1
        """
        # Check subject first
        if "refrigerator 2" in subject.lower() or "fridge 2" in subject.lower():
            return 2
        elif "refrigerator 1" in subject.lower() or "fridge 1" in subject.lower():
            return 1
            
        # Check body
        if "refrigerator 2" in body.lower() or "fridge 2" in body.lower():
            return 2
        elif "refrigerator 1" in body.lower() or "fridge 1" in body.lower():
            return 1
            
        # Default to fridge 1 for test emails
        return 1
    
    def signal_fan_activation(self, fridge_id=1):
        """Signal Flask app to activate fan through state file"""
        try:
            state = {
                "action": "activate_fan",
                "fridge_id": fridge_id,
                "timestamp": datetime.now().isoformat(),
                "activated_by": "email_reply"
            }
            
            with open(self.state_file, "w") as f:
                json.dump(state, f)
            
            print(f"📡 Signaled Flask app to activate fan for Fridge {fridge_id}")
            
        except Exception as e:
            print(f"❌ Error signaling fan activation: {e}")
    
    def send_confirmation_email(self, fridge_id=1):
        """Send confirmation that fan was activated"""
        try:
            subject = f"Fan Activated - Refrigerator {fridge_id}"
            body = f"""Fan Activation Confirmed!

The cooling fan for Refrigerator {fridge_id} has been successfully activated via your email reply.

Activation Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Your IoT Smart Store system is now cooling Refrigerator {fridge_id}.
"""
            
            email_message = f"Subject: {subject}\nTo: {self.recipient}\nFrom: {self.login}\n\n{body}"
            
            with smtplib.SMTP_SSL(self.smtp_host, self.smtp_port, context=self.context) as server:
                server.login(self.login, self.password)
                server.sendmail(self.login, self.recipient, email_message.encode('utf-8'))
                
            print(f"📧 Confirmation email sent for Refrigerator {fridge_id}!")
            
        except Exception as e:
            print(f"⚠️  Could not send confirmation email: {e}")
    
    def start_monitoring(self):
        """Start background email monitoring"""
        if self.monitoring:
            print("📧 Email monitoring already running")
            return
        
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        print("🔄 Started email monitoring thread")
    
    def stop_monitoring(self):
        """Stop email monitoring"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        print("🛑 Stopped email monitoring")
    
    def _monitor_loop(self):
        """Background monitoring loop"""
        print("📧 Email monitoring started...")
        
        while self.monitoring:
            try:
                self.check_for_yes_replies()
                time.sleep(30)  # Check every 30 seconds
            except Exception as e:
                print(f"❌ Monitor error: {e}")
                time.sleep(60)  # Wait longer on error
    
    def get_and_clear_state(self):
        """Get current state and clear it (for Flask to check)"""
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, "r") as f:
                    state = json.load(f)
                
                # Clear the state file
                os.remove(self.state_file)
                
                return state
            return None
            
        except Exception as e:
            print(f"❌ Error reading state: {e}")
            return None

# Global instance
email_system = IntegratedEmailSystem()