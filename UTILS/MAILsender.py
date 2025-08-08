import os
import smtplib
from email.message import EmailMessage

def MAILsender(sender_email, password, recipient_email, subject, body, filename):

    attachment_name = os.path.basename(filename)

    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = "FG-ToolWatcher <fgtoolwatcher@gmail.com>"
    msg['To'] = recipient_email
    msg.set_content(body, subtype='html')

    with open(filename, 'rb') as f:
        file_data = f.read()
        msg.add_attachment(file_data, maintype='application', subtype='octet-stream', filename=attachment_name)

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(sender_email, password)
            smtp.send_message(msg)
        print("Mail envoyé avec succès.")
    except Exception as e:
        print("Erreur lors de l’envoi du mail :", e)