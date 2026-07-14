"""
Test rapide de l'envoi email Gmail — sans lancer toute la veille.
Usage : python test_email.py
"""
import smtplib, os, sys
from email.message import EmailMessage
from email.policy import SMTP
from email.utils import formatdate

gmail_email = os.environ.get("GMAIL_EMAIL", "langlet.gregory@gmail.com")
gmail_password = os.environ.get("GMAIL_APP_PASSWORD", "vwewsvwuindvtzif")
recipients = ["gregory.langlet@sfr.fr", "langlet.gregory@gmail.com"]

msg = EmailMessage(policy=SMTP)
msg['From'] = f"Gregory LANGLET <{gmail_email}>"
msg['To'] = ", ".join(recipients)
msg['Subject'] = "TEST - Veille Quotidienne"
msg['Date'] = formatdate(localtime=True)

msg.set_content("Ceci est un mail de test pour valider l'envoi Gmail depuis le script Python.", charset='utf-8')

html_test = "<html><body><h1>Test OK ✅</h1><p>Si tu vois ce mail, l'envoi Gmail fonctionne parfaitement.</p></body></html>"
msg.add_attachment(html_test.encode('utf-8'), maintype='text', subtype='html', filename='test_veille.html')

print(f"[TEST] Envoi a {', '.join(recipients)}...")
try:
    with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as server:
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(gmail_email, gmail_password)
        server.send_message(msg)
    print("[TEST] ✅ Mail envoye avec succes !")
except Exception as e:
    print(f"[TEST] ❌ Erreur : {e}")
    sys.exit(1)
