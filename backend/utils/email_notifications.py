
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class EmailNotifications:
    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER")
        self.smtp_port = int(os.getenv("SMTP_PORT", 587))
        self.smtp_user = os.getenv("SMTP_USER")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
        self.sender_email = os.getenv("SENDER_EMAIL")
        self.recipient_email = None  # To be set from settings
        self.enabled = False

    def configure(self, recipient_email: str, enabled: bool):
        self.recipient_email = recipient_email
        self.enabled = enabled
        logger.info(f"Email notifications configured for {recipient_email}, enabled: {enabled}")

    def is_configured(self) -> bool:
        return all([
            self.smtp_server,
            self.smtp_port,
            self.smtp_user,
            self.smtp_password,
            self.sender_email,
            self.recipient_email
        ])

    def send_email(self, subject: str, body: str):
        if not self.enabled or not self.is_configured():
            logger.warning("Email not sent. Notifications are disabled or configuration is incomplete.")
            return

        message = MIMEMultipart()
        message["From"] = self.sender_email
        message["To"] = self.recipient_email
        message["Subject"] = subject
        message.attach(MIMEText(body, "plain"))

        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.sendmail(self.sender_email, self.recipient_email, message.as_string())
                logger.info(f"Email sent to {self.recipient_email} with subject: {subject}")
        except Exception as e:
            logger.error(f"Failed to send email: {e}")

# Global instance
email_notifications = EmailNotifications()

def send_notification_email(subject: str, body: str):
    email_notifications.send_email(subject, body)

