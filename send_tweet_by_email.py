# -*- coding: utf-8 -*-
"""
send_tweet_by_email.py
Sends the generated tweet text and image to the user's email address.
Uses the robust Base64/ASCII email template from the github-actions skill.
"""
import os
import sys
import argparse
import smtplib
import uuid
import base64
import datetime
import unicodedata
from email.utils import formatdate

def send_email_with_image(image_path, text_path, subject):
    # Read and clean UTF-8 text (removing BOM \ufeff if present)
    with open(text_path, "r", encoding="utf-8-sig") as f:
        tweet_text = f.read().strip()

    # Get email configuration from environment
    gmail_email = os.environ.get("GMAIL_EMAIL", "langlet.gregory@gmail.com").strip().replace("\ufeff", "")
    gmail_password = os.environ.get("GMAIL_APP_PASSWORD", "").strip().replace("\ufeff", "")
    smtp_email = os.environ.get("SMTP_EMAIL", "gregory.langlet@sfr.fr").strip().replace("\ufeff", "")
    smtp_password = os.environ.get("SMTP_PASSWORD", "").strip().replace("\ufeff", "")
    recipient_env = os.environ.get("RECIPIENT_EMAILS", "langlet.gregory@gmail.com").strip().replace("\ufeff", "")
    
    recipients = [r.strip() for r in recipient_env.split(",") if r.strip()]
    if not recipients:
        recipients = [gmail_email]

    sender = gmail_email if gmail_password else smtp_email
    if not sender:
        print("Error: No sender email address configured.", file=sys.stderr)
        sys.exit(1)

    # Clean Subject: Remove non-ASCII characters (emojis, accents) to comply with SMTP headers
    clean_subject = unicodedata.normalize('NFKD', subject).encode('ASCII', 'ignore').decode('ASCII')

    print(f"Sending tweet email to: {', '.join(recipients)}")
    print(f"Clean Subject: {clean_subject}")
    print(f"Tweet Text:\n---\n{tweet_text}\n---")

    # Read and base64-encode the image attachment
    with open(image_path, "rb") as img_f:
        img_data = img_f.read()
    img_b64 = base64.b64encode(img_data).decode("ascii")
    img_name = os.path.basename(image_path)

    # HTML Body with styled copy-paste block
    html_body = f"""<html>
<body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 8px;">
    <h2 style="color: #1DA1F2; border-bottom: 2px solid #1DA1F2; padding-bottom: 10px;">Monsieur Meteo - Pret a publier</h2>
    <p>Bonjour Gregory,</p>
    <p>Voici le contenu genere automatiquement pour votre prochain post Twitter/X :</p>
    
    <div style="background-color: #f5f8fa; border: 1px dashed #1DA1F2; padding: 15px; border-radius: 6px; margin: 20px 0; font-family: monospace; font-size: 14px; white-space: pre-wrap; color: #0f1419;">{tweet_text}</div>
    
    <p style="font-size: 12px; color: #666;">💡 <i>Copiez le texte ci-dessus et ajoutez l'image jointe a ce mail (<b>{img_name}</b>) lors de la publication.</i></p>
    <br>
    <hr style="border: 0; border-top: 1px solid #eee;">
    <p style="font-size: 11px; color: #999; text-align: center;">Genere automatiquement par le workflow GitHub Actions.</p>
</body>
</html>"""

    boundary = uuid.uuid4().hex
    
    # Encodage complet en base64 pour le HTML pour garantir que tout passe en ASCII pur sur le canal SMTP
    html_b64 = base64.b64encode(html_body.encode('utf-8')).decode('ascii')
    
    # Construction du MIME brut (ASCII pur obligatoire)
    raw_message = (
        f'From: Monsieur Meteo <{sender}>\r\n'
        f'To: {", ".join(recipients)}\r\n'
        f'Subject: {clean_subject}\r\n'
        f'Date: {formatdate(localtime=True)}\r\n'
        f'MIME-Version: 1.0\r\n'
        f'Content-Type: multipart/mixed; boundary="{boundary}"\r\n'
        f'\r\n'
        f'--{boundary}\r\n'
        f'Content-Type: text/html; charset=utf-8\r\n'
        f'Content-Transfer-Encoding: base64\r\n'
        f'\r\n'
        f'{html_b64}\r\n'
        f'\r\n'
        f'--{boundary}\r\n'
        f'Content-Type: image/jpeg; name="{img_name}"\r\n'
        f'Content-Disposition: attachment; filename="{img_name}"\r\n'
        f'Content-Transfer-Encoding: base64\r\n'
        f'\r\n'
        f'{img_b64}\r\n'
        f'\r\n'
        f'--{boundary}--\r\n'
    )

    message_bytes = raw_message.encode('ascii')

    # Send via Gmail (default)
    if gmail_password:
        print("[SMTP] Sending via Gmail...")
        try:
            with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(gmail_email, gmail_password)
                server.sendmail(gmail_email, recipients, message_bytes)
            print("✅ Email sent successfully via Gmail!")
            return
        except Exception as e:
            print(f"[SMTP] Gmail failed: {e}. Trying fallback SFR...", file=sys.stderr)

    # Fallback to SFR
    if smtp_password:
        print("[SMTP] Sending via SFR...")
        try:
            with smtplib.SMTP_SSL("smtp.sfr.fr", 465, timeout=30) as server:
                server.login(smtp_email, smtp_password)
                server.sendmail(smtp_email, recipients, message_bytes)
            print("✅ Email sent successfully via SFR!")
            return
        except Exception as e:
            print(f"[SMTP] SFR failed: {e}", file=sys.stderr)

    print("ERROR: Failed to send email through all SMTP relays.", file=sys.stderr)
    sys.exit(1)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", required=True)
    parser.add_argument("--text-file", required=True)
    parser.add_argument("--subject", required=True)
    args = parser.parse_args()

    send_email_with_image(args.image, args.text_file, args.subject)

if __name__ == "__main__":
    main()
