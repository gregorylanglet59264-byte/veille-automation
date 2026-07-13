#!/usr/bin/env python3
import os
import sys
import datetime
import urllib.request
import json
import re
import smtplib
import base64
import uuid
import unicodedata
from email.utils import formatdate

# Ajout du répertoire courant pour les imports locaux
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from download_data import download_bulletins
from generer_rapport import generer_bulletin_premium, REGIONS

def normalize_name(name):
    n = unicodedata.normalize('NFKD', name).encode('ASCII', 'ignore').decode('ASCII')
    return n.lower().replace(" ", "_").replace("-", "_").replace("'", "_")

def call_llm_summary(bulletin_content):
    """
    Rédige un résumé à l'aide de l'API OpenRouter (DeepSeek) ou de l'API Gemini.
    Si aucune clé n'est configurée, utilise un résumé statique extrait du bulletin.
    """
    gemini_key = os.environ.get("GEMINI_API_KEY")
    openrouter_key = os.environ.get("OPENROUTER_API_KEY")
    
    prompt = (
        "Rédige un résumé très court et impactant en français (sous forme de 4 ou 5 puces clés avec émojis) "
        "du bulletin météo national de la France suivant. Concentre-toi uniquement sur les éléments critiques "
        "(vigilance canicule/orages, températures extrêmes, etc.) :\n\n" + bulletin_content
    )
    
    # Tentative avec Gemini
    if gemini_key:
        print("[LLM] Appel de l'API Gemini...")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_key}"
        data = {
            "contents": [{"parts": [{"text": prompt}]}]
        }
        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(data).encode('utf-8'),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=20) as response:
                res = json.loads(response.read().decode('utf-8'))
                text = res["candidates"][0]["content"]["parts"][0]["text"]
                return text.replace('\ufeff', '').replace('\ufffe', '').strip()
        except Exception as e:
            print(f"[LLM] Échec appel Gemini : {e}")

    # Tentative avec OpenRouter (DeepSeek)
    if openrouter_key:
        print("[LLM] Appel de l'API OpenRouter (DeepSeek)...")
        url = "https://openrouter.ai/api/v1/chat/completions"
        data = {
            "model": "deepseek/deepseek-chat",
            "messages": [{"role": "user", "content": prompt}]
        }
        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(data).encode('utf-8'),
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {openrouter_key}"
                },
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=20) as response:
                res = json.loads(response.read().decode('utf-8'))
                text = res["choices"][0]["message"]["content"]
                return text.replace('\ufeff', '').replace('\ufffe', '').strip()
        except Exception as e:
            print(f"[LLM] Échec appel OpenRouter : {e}")
            
    # Fallback si pas de clés d'API ou si échec des appels
    print("[LLM] Utilisation du fallback d'extraction textuelle...")
    lines = bulletin_content.split('\n')
    summary_parts = []
    capture = False
    for line in lines:
        if "## ⚠️ Vigilance Institutionnelle" in line:
            capture = True
        elif "## 🌊 Vigilance Hydrologique" in line:
            capture = False
        if capture and line.strip() and not line.startswith('#'):
            summary_parts.append(line.strip())
            
    if summary_parts:
        return "### ⚠️ Vigilances actives :\n" + "\n".join(summary_parts[:10])
    return "Consultez le bulletin national en pièce jointe pour plus de détails."

def md_to_html(md_text):
    """
    Convertit le Markdown de base en HTML avec un style élégant.
    """
    # Échapper les caractères HTML
    html = md_text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    
    # Remplacer les titres
    html = re.sub(r'^###\s*(.*?)$', r'<h3 style="color:#0f172a; margin-top:20px; font-family:\'Outfit\',sans-serif;">\1</h3>', html, flags=re.MULTILINE)
    html = re.sub(r'^##\s*(.*?)$', r'<h2 style="color:#1e3a8a; border-bottom:1px solid #e2e8f0; padding-bottom:5px; margin-top:30px; font-family:\'Outfit\',sans-serif;">\1</h2>', html, flags=re.MULTILINE)
    html = re.sub(r'^#\s*(.*?)$', r'<h1 style="color:#1e40af; font-family:\'Outfit\',sans-serif; margin-bottom:10px;">\1</h1>', html, flags=re.MULTILINE)
    
    # Remplacer le gras
    html = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html)
    
    # Blocs de citation (Alertes Github / Markdown)
    # Remplacement des > [!IMPORTANT]
    html = re.sub(
        r'^&gt;\s*\[!IMPORTANT\]\s*\n(.*?)(?=\n\n|\n&gt;|$)',
        r'<div style="background-color:#fee2e2; border-left:4px solid #ef4444; padding:12px; margin:15px 0; border-radius:4px; color:#991b1b; font-size:14px;"><strong>[IMPORTANT]</strong><br>\1</div>',
        html,
        flags=re.MULTILINE | re.DOTALL
    )
    # Remplacement des blocs > standards
    html = re.sub(
        r'^&gt;\s*(.*?)$',
        r'<div style="background-color:#f8fafc; border-left:4px solid #64748b; padding:8px 12px; margin:10px 0; font-style:italic; color:#475569;">\1</div>',
        html,
        flags=re.MULTILINE
    )
    
    # Remplacer les puces (listes)
    html = re.sub(r'^\s*-\s*(.*?)$', r'<li style="margin-bottom:6px; margin-left:20px; color:#334155;">\1</li>', html, flags=re.MULTILINE)
    
    # Remplacer les lignes de séparation
    html = html.replace('---', '<hr style="border:0; border-top:1px solid #e2e8f0; margin:20px 0;">')
    
    # Gérer les retours à la ligne restants
    html = html.replace('\n', '<br>')
    
    return html

def send_email_with_summary(summary_md, national_md, date_str, reports_urls):
    gmail_email = os.environ.get("GMAIL_EMAIL", "langlet.gregory@gmail.com")
    gmail_password = os.environ.get("GMAIL_APP_PASSWORD")
    if not gmail_password:
        print("[SMTP] ERREUR : GMAIL_APP_PASSWORD non configuré. Annulation envoi.")
        return
        
    gmail_email = gmail_email.replace('\ufeff', '').replace('\ufffe', '').strip()
    gmail_password = gmail_password.replace('\ufeff', '').replace('\ufffe', '').strip()
    
    raw_recipients = os.environ.get("RECIPIENT_EMAILS", gmail_email)
    recipients = [r.strip() for r in raw_recipients.split(",") if r.strip()]
    
    subject = f"Meteo France - Bulletin National & Regional du {date_str}"
    clean_subject = unicodedata.normalize('NFKD', subject).encode('ASCII', 'ignore').decode('ASCII')
    
    # Conversion du résumé Markdown en HTML
    summary_html = md_to_html(summary_md)
    
    # Construction du corps HTML du mail
    links_html = ""
    for reg, url in reports_urls.items():
        links_html += f'<a href="{url}" style="display:inline-block; margin:4px; padding:6px 12px; background-color:#eff6ff; color:#1d4ed8; text-decoration:none; border-radius:4px; font-size:12px; font-weight:bold; border:1px solid #bfdbfe;">{reg}</a>'
        
    email_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap" rel="stylesheet">
        <style>
            body {{ font-family: 'Outfit', sans-serif; background-color: #f1f5f9; color: #1e293b; padding: 20px; }}
            .container {{ max-width: 650px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1); }}
            .header {{ background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%); padding: 30px 20px; text-align: center; color: #ffffff; }}
            .header h1 {{ margin: 0; font-size: 24px; font-weight: 700; }}
            .header p {{ margin: 5px 0 0 0; font-size: 14px; opacity: 0.9; }}
            .content {{ padding: 25px; }}
            .section-card {{ background-color: #f8fafc; border-radius: 8px; padding: 20px; margin-bottom: 20px; border: 1px solid #e2e8f0; }}
            .section-card h2 {{ margin-top: 0; font-size: 18px; color: #1e3a8a; border-bottom: 2px solid #3b82f6; padding-bottom: 6px; }}
            .links-container {{ padding: 15px; background-color: #fafafa; border-radius: 8px; text-align: center; border: 1px dashed #cbd5e1; }}
            .footer {{ background-color: #f8fafc; padding: 15px; text-align: center; font-size: 11px; color: #64748b; border-top: 1px solid #e2e8f0; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🌊 BULLETIN METEO PREMIUM</h1>
                <p>Synthese Officielle Meteo France du {date_str}</p>
            </div>
            <div class="content">
                <div class="section-card">
                    <h2>🎯 Resume National - A retenir</h2>
                    <div style="line-height: 1.6; font-size: 14px;">
                        {summary_html}
                    </div>
                </div>
                
                <div class="section-card">
                    <h2>📍 Bulletins Regionaux (Disponibles sur GitHub)</h2>
                    <p style="font-size: 13px; color: #475569; margin-bottom: 15px;">Cliquez sur votre region pour consulter son bulletin Premium detaille :</p>
                    <div class="links-container">
                        {links_html}
                    </div>
                </div>
            </div>
            <div class="footer">
                Ce rapport a ete genere et envoye automatiquement depuis GitHub Actions.<br>
                Meteo France - Meteotel Server
            </div>
        </div>
    </body>
    </html>
    """
    
    # Nettoyage BOM
    email_body = email_body.replace('\ufeff', '').replace('\ufffe', '')
    
    # Encodage Base64
    html_b64 = base64.b64encode(email_body.encode('utf-8')).decode('ascii')
    
    # Préparation du bulletin national complet en pièce jointe HTML
    national_html = md_to_html(national_md)
    attached_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap" rel="stylesheet">
        <style>
            body {{ font-family: 'Outfit', sans-serif; color: #1e293b; padding: 30px; line-height: 1.6; max-width: 800px; margin: 0 auto; }}
        </style>
    </head>
    <body>
        {national_html}
    </body>
    </html>
    """
    attached_b64 = base64.b64encode(attached_html.encode('utf-8')).decode('ascii')
    
    boundary = uuid.uuid4().hex
    filename = f"bulletin_national_{date_str.replace('/', '_')}.html"
    
    raw_message = (
        f'From: Gregory LANGLET <{gmail_email}>\r\n'
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
        f'Content-Type: text/html; charset=utf-8; name="{filename}"\r\n'
        f'Content-Disposition: attachment; filename="{filename}"\r\n'
        f'Content-Transfer-Encoding: base64\r\n'
        f'\r\n'
        f'{attached_b64}\r\n'
        f'\r\n'
        f'--{boundary}--\r\n'
    )
    
    print(f"[SMTP] Envoi de l'e-mail a {', '.join(recipients)}...")
    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(gmail_email, gmail_password)
            server.sendmail(gmail_email, recipients, raw_message.encode('ascii'))
        print("[SMTP] E-mail envoye avec succes !")
    except Exception as e:
        print(f"[SMTP] Erreur lors de l'envoi de l'e-mail : {e}")

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    meteo_dir = os.path.join(base_dir, "meteo_france")
    source_dir = os.path.join(meteo_dir, "meteo_data")
    
    # 1. Télécharger les bulletins
    print("=== Etape 1 : Telechargement des bulletins XML ===")
    download_bulletins("PREV_XML", source_dir)
    download_bulletins("COTE2", source_dir)
    
    # 2. Définir le dossier de sortie
    today_str = datetime.datetime.now().strftime("%Y-%m-%d")
    date_display = datetime.datetime.now().strftime("%d/%m/%Y")
    rapports_dir = os.path.join(meteo_dir, "rapports", today_str)
    os.makedirs(rapports_dir, exist_ok=True)
    
    # 3. Générer les bulletins pour toutes les régions
    print("\n=== Etape 2 : Generation des bulletins regionaux ===")
    reports_urls = {}
    github_repo = "gregorylanglet59264-byte/veille-automation"
    
    national_content = ""
    
    # Nous itérons sur la liste complète des régions définies
    for region in REGIONS.keys():
        region_norm = normalize_name(region)
        filename = f"bulletin_{region_norm}_{today_str}.md"
        output_file = os.path.join(rapports_dir, filename)
        
        print(f"Generation pour {region} -> {filename}")
        try:
            generer_bulletin_premium(region, source_dir, output_file)
            
            # Si c'est le bulletin national, on garde le contenu pour le résumé et la pièce jointe
            if region == "France":
                if os.path.exists(output_file):
                    with open(output_file, 'r', encoding='utf-8') as f:
                        national_content = f.read()
                        
            # URL relative de consultation sur GitHub
            url_github = f"https://github.com/{github_repo}/blob/main/meteo_france/rapports/{today_str}/{filename}"
            reports_urls[region] = url_github
        except Exception as e:
            print(f"[ERREUR] Echec de la generation pour {region} : {e}")
            
    # 4. Rédiger le résumé national
    print("\n=== Etape 3 : Resume national par LLM ===")
    if national_content:
        summary = call_llm_summary(national_content)
    else:
        summary = "Le bulletin meteo national n'a pas pu etre genere."
        
    print("\nResume genere :")
    print(summary)
    
    # 5. Envoyer l'email
    print("\n=== Etape 4 : Envoi de l'e-mail ===")
    send_email_with_summary(summary, national_content, date_display, reports_urls)

if __name__ == "__main__":
    main()
