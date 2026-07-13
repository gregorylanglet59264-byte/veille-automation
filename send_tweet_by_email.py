# -*- coding: utf-8 -*-
"""
send_tweet_by_email.py
Sends the generated tweet text and image to the user's email address.
Uses Python's standard email library for robust MIME/UTF-8/BOM handling.
"""
import os
import sys
import argparse
import smtplib
from email.message import EmailMessage
from email.headerregistry import Address

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", required=True, help="Path to the generated infographic or map")
    parser.add_argument("--text-file", required=True, help="Path to the file containing the tweet text")
    parser.add_argument("--subject", required=True, help="Email subject")
    args = parser.parse_args()

    if not os.path.exists(args.text_file):
        print(f"Error: Text file not found at {args.text_file}", file=sys.stderr)
        sys.exit(1)
    if not os.path.exists(args.image):
        print(f"Error: Image not found at {args.image}", file=sys.stderr)
        sys.exit(1)

    # Read and clean UTF-8 text (removing BOM \ufeff if present)
    with open(args.text_file, "r", encoding="utf-8-sig") as f:
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

    print(f"Sending tweet email to: {', '.join(recipients)}")
    print(f"Subject: {args.subject}")
    print(f"Tweet Text:\n---\n{tweet_text}\n---")

    # Read image
    with open(args.image, "rb") as img_f:
        img_data = img_f.read()
    img_name = os.path.basename(args.image)

    # HTML Body with styled copy-paste block
    html_body = f"""<html>
<body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 8px;">
    <h2 style="color: #1DA1F2; border-bottom: 2px solid #1DA1F2; padding-bottom: 10px;">🌤️ Monsieur Météo — Prêt à publier</h2>
    <p>Bonjour Gregory,</p>
    <p>Voici le contenu généré automatiquement pour votre prochain post Twitter/X :</p>
    
    <div style="background-color: #f5f8fa; border: 1px dashed #1DA1F2; padding: 15px; border-radius: 6px; margin: 20px 0; font-family: monospace; font-size: 14px; white-space: pre-wrap; color: #0f1419;">{tweet_text}</div>
    
    <p style="font-size: 12px; color: #666;">💡 <i>Copiez le texte ci-dessus et ajoutez l'image jointe à ce mail (<b>{img_name}</b>) lors de la publication.</i></p>
    <br>
    <hr style="border: 0; border-top: 1px solid #eee;">
    <p style="font-size: 11px; color: #999; text-align: center;">Généré automatiquement par le workflow GitHub Actions.</p>
</body>
</html>"""

    # Build Email Message using modern EmailMessage class (bulletproof)
    msg = EmailMessage()
    msg["Subject"] = args.subject
    msg["From"] = f"Monsieur Meteo <{sender}>"
    msg["To"] = ", ".join(recipients)
    
    # Set HTML content
    msg.set_content("Veuillez utiliser un client mail compatible HTML pour voir ce message.")
    msg.add_alternative(html_body, subtype="html")
    
    # Add attachment
    msg.add_attachment(img_data, maintype="image", subtype="jpeg", filename=img_name)

    # Send via Gmail (default)
    if gmail_password:
        print("[SMTP] Sending via Gmail...")
        try:
            with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(gmail_email, gmail_password)
                server.send_message(msg)
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
                server.send_message(msg)
            print("✅ Email sent successfully via SFR!")
            return
        except Exception as e:
            print(f"[SMTP] SFR failed: {e}", file=sys.stderr)

    print("ERROR: Failed to send email through all SMTP relays.", file=sys.stderr)
    sys.exit(1)

if __name__ == "__main__":
    main()
