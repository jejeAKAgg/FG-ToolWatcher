# CORE/Services/mail.py
import os
import smtplib

from email.message import EmailMessage



class MailService:
    
    """
    Service dedicated to sending emails via SMTP (default: Gmail SSL).
    Supports single or multiple recipients, with or without attachments.
    
    """

    def __init__(self, sender_email: str, password: str, smtp_server: str = "smtp.gmail.com", smtp_port: int = 465):
        
        """
        Initializes the mail sending service.

        Args:
            sender_email (str): The sender's email address.
            password (str): The email account password or app-specific password (recommended for Gmail).
            smtp_server (str): SMTP server address (default: Gmail).
            smtp_port (int): SMTP port (default: 465 for SSL).
        
        """

        # === INPUT VARIABLES ===
        self.sender_email = sender_email
        self.password = password
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        

    def _create_message(self, recipients, subject, body, attachments=None, html=False) -> EmailMessage:
        
        """
        Builds an EmailMessage object ready to be sent.

        Args:
            recipients (str | list[str]): Recipient(s) email address(es).
            subject (str): Email subject.
            body (str): Email body (plain text or HTML).
            attachments (list[str] | None): List of file paths to attach.
            html (bool): Whether to send the body as HTML.

        Returns:
            EmailMessage: The prepared email message.
        
        """

        msg = EmailMessage()
        
        # === PARAMETERS SETUP  ===
        msg["Subject"] = subject
        msg["From"] = self.sender_email
        msg["To"] = recipients if isinstance(recipients, str) else ", ".join(recipients)

        if html:
            msg.add_alternative(body, subtype="html")
        else:
            msg.set_content(body)

        # === ATTACHMENTS ===
        if attachments:
            for filepath in attachments:
                if not os.path.exists(filepath):
                    continue
                with open(filepath, "rb") as f:
                    file_data = f.read()
                    file_name = os.path.basename(filepath)
                msg.add_attachment(file_data, maintype="application", subtype="octet-stream", filename=file_name)

        return msg

    def send_mail(self, recipients, subject: str, body: str, attachments=None, html=False):
        
        """
        Sends an email via SMTP (SSL).

        Args:
            recipients (str | list[str]): Recipient(s) email address(es).
            subject (str): Email subject.
            body (str): Email body content.
            attachments (list[str] | None): List of file paths to attach.
            html (bool): Whether to send the body as HTML.

        Raises:
            Exception: If the email fails to send, the error is logged but not re-raised.
        
        """
        
        msg = self._create_message(recipients, subject, body, attachments, html)

        try:
            with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port) as smtp:
                smtp.login(self.sender_email, self.password)
                smtp.send_message(msg)

        except Exception as e:
            return