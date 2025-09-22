import os
import smtplib

from email.message import EmailMessage

from APP.UTILS.LOGmaker import logger


class MailService:
    """
    Service dédié à l'envoi d'emails via SMTP (par défaut Gmail SSL).
    Gère les envois simples ou multiples, avec ou sans pièce jointe.
    """

    def __init__(self, sender_email: str, password: str, smtp_server: str = "smtp.gmail.com", smtp_port: int = 465):
        """
        Initialise le service d'envoi de mails.

        Args:
            sender_email (str): Adresse email de l'expéditeur.
            password (str): Mot de passe ou App Password (recommandé pour Gmail).
            smtp_server (str): Serveur SMTP (par défaut Gmail).
            smtp_port (int): Port SMTP (465 pour SSL).
        """
        self.sender_email = sender_email
        self.password = password
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.logger = logger("MailService")

    def _create_message(self, recipients, subject, body, attachments=None, html=False) -> EmailMessage:
        """
        Crée un objet EmailMessage prêt à être envoyé.

        Args:
            recipients (str | list[str]): Destinataire(s).
            subject (str): Sujet du mail.
            body (str): Corps du mail.
            attachments (list[str] | None): Liste de chemins de fichiers à attacher.
            html (bool): True si le corps doit être envoyé en HTML.
        """
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = self.sender_email
        msg["To"] = recipients if isinstance(recipients, str) else ", ".join(recipients)

        if html:
            msg.add_alternative(body, subtype="html")
        else:
            msg.set_content(body)

        # Ajout des pièces jointes
        if attachments:
            for filepath in attachments:
                if not os.path.exists(filepath):
                    self.logger.warning(f"Pièce jointe introuvable: {filepath}")
                    continue
                with open(filepath, "rb") as f:
                    file_data = f.read()
                    file_name = os.path.basename(filepath)
                msg.add_attachment(file_data, maintype="application", subtype="octet-stream", filename=file_name)

        return msg

    def send_mail(self, recipients, subject: str, body: str, attachments=None, html=False):
        """
        Envoie un email.

        Args:
            recipients (str | list[str]): Adresse(s) email des destinataires.
            subject (str): Sujet du mail.
            body (str): Corps du mail (texte ou HTML).
            attachments (list[str] | None): Liste de fichiers à attacher.
            html (bool): Active l'envoi en HTML.
        """
        msg = self._create_message(recipients, subject, body, attachments, html)

        try:
            with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port) as smtp:
                smtp.login(self.sender_email, self.password)
                smtp.send_message(msg)

            self.logger.info(f"Email envoyé à {recipients} (sujet: {subject})")

        except Exception as e:
            self.logger.warning(f"Erreur lors de l'envoi du mail: {e}")
