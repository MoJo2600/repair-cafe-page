"""
Email service for sending exports and notifications.
"""

import base64
import os
from datetime import datetime
from io import BytesIO
from pathlib import Path

import pyzipper
from mailtrap import Address, Attachment, Disposition, Mail, MailtrapClient


class EmailService:
    """Service for handling email operations."""

    def __init__(self, config):
        """
        Initialize email service.

        Args:
            config: Flask app config object
        """
        self.config = config
        self.enabled = config.get("EMAIL_ENABLED", False)
        self.mail_token = config.get("MAIL_TOKEN")
        self.sender = config.get("MAIL_SENDER")
        self.sender_name = config.get("MAIL_SENDER_NAME", "RepairCafe")
        self.receiver = config.get("EXPORT_MAIL_RECEIVER")
        self.zip_password = config.get("ZIP_PASSWORD", "password")

    def send_export_email(self, csv_data, filename_prefix="export"):
        """
        Send export email with CSV data as password-protected ZIP attachment.

        Args:
            csv_data: CSV data as bytes or string
            filename_prefix: Prefix for the filename (default: 'export')

        Returns:
            dict with reply status and recipient
        """
        if not self.enabled:
            return {"reply": "error", "error": "Email sending is disabled"}

        if not all([self.mail_token, self.sender, self.receiver]):
            return {"reply": "error", "error": "Email configuration incomplete"}

        # Prepare CSV data
        if isinstance(csv_data, str):
            csv_data = csv_data.encode("utf-8")

        # Create password-protected ZIP file
        zip_buffer = BytesIO()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_filename = f"{filename_prefix}_{timestamp}.csv"

        with pyzipper.AESZipFile(
            zip_buffer,
            "w",
            compression=pyzipper.ZIP_DEFLATED,
            encryption=pyzipper.WZ_AES,
        ) as zipf:
            zipf.setpassword(self.zip_password.encode("utf-8"))
            zipf.writestr(csv_filename, csv_data)

        zip_buffer.seek(0)
        zip_data = zip_buffer.read()
        zip_encoded = base64.b64encode(zip_data)

        # Create email
        mail = Mail(
            sender=Address(email=self.sender, name=self.sender_name),
            to=[Address(email=self.receiver)],
            subject=f"RepairCafe Export - {timestamp}",
            text=f"Export data attached as password-protected ZIP.\n\nGenerated: {timestamp}",
            category="Integration Test",
            attachments=[
                Attachment(
                    content=zip_encoded,
                    filename=f"{filename_prefix}_{timestamp}.zip",
                    disposition=Disposition.ATTACHMENT,
                    mimetype="application/zip",
                )
            ],
        )

        # Send email
        try:
            client = MailtrapClient(token=self.mail_token)
            client.send(mail)
            print(f"Email with attachment sent successfully to {self.receiver}")
            return {"reply": "done", "recipient": self.receiver}
        except Exception as e:
            print(f"Error sending email: {e}")
            return {"reply": "error", "error": str(e)}
