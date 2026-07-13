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
    # Échapper les caractères HTML d'abord pour plus de sécurité
    escaped = md_text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    
    lines = escaped.splitlines()
    html_lines = []
    
    in_blockquote = False
    blockquote_type = "standard"  # "standard" ou "important"
    blockquote_lines = []
    
    for line in lines:
        if line.startswith("&gt;"):
            in_blockquote = True
            content = line[4:].strip() if line.startswith("&gt; ") else line[3:].strip()
            if "[!IMPORTANT]" in content:
                blockquote_type = "important"
                content = content.replace("[!IMPORTANT]", "").strip()
            # Nettoyer les gras à l'intérieur
            content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', content)
            blockquote_lines.append(content)
        else:
            if in_blockquote:
                # Clôture du bloc de citation
                bq_content = "<br>".join(blockquote_lines)
                if blockquote_type == "important":
                    html_lines.append(
                        f'<div style="background-color:#fee2e2; border-left:4px solid #ef4444; padding:12px; margin:15px 0; border-radius:4px; color:#991b1b; font-size:14px; font-family:\'Outfit\',sans-serif; line-height:1.5;">'
                        f'<strong>⚠️ IMPORTANT</strong><br>{bq_content}'
                        f'</div>'
                    )
                else:
                    html_lines.append(
                        f'<div style="background-color:#f8fafc; border-left:4px solid #64748b; padding:10px 14px; margin:12px 0; font-style:italic; color:#475569; font-family:\'Outfit\',sans-serif; border-radius:4px; line-height:1.5;">'
                        f'{bq_content}'
                        f'</div>'
                    )
                in_blockquote = False
                blockquote_lines = []
                blockquote_type = "standard"
            
            processed_line = line.strip()
            if not processed_line:
                html_lines.append("<br>")
                continue
            
            if processed_line.startswith("###"):
                title = processed_line[3:].strip()
                html_lines.append(f'<h3 style="color:#0f172a; margin-top:20px; font-family:\'Outfit\',sans-serif; font-size:16px; font-weight:600;">{title}</h3>')
            elif processed_line.startswith("##"):
                title = processed_line[2:].strip()
                html_lines.append(f'<h2 style="color:#1e3a8a; border-bottom:1px solid #e2e8f0; padding-bottom:5px; margin-top:30px; font-family:\'Outfit\',sans-serif; font-size:18px; font-weight:600;">{title}</h2>')
            elif processed_line.startswith("#"):
                title = processed_line[1:].strip()
                html_lines.append(f'<h1 style="color:#1e40af; font-family:\'Outfit\',sans-serif; margin-bottom:15px; font-size:22px; font-weight:700;">{title}</h1>')
            elif processed_line.startswith("-"):
                item = processed_line[1:].strip()
                item = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', item)
                html_lines.append(f'<li style="margin-bottom:6px; margin-left:20px; color:#334155; font-size:14px; font-family:\'Outfit\',sans-serif; line-height:1.5;">{item}</li>')
            elif processed_line == "---":
                html_lines.append('<hr style="border:0; border-top:1px solid #e2e8f0; margin:20px 0;">')
            else:
                processed_line = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', processed_line)
                html_lines.append(f'<p style="margin:6px 0; color:#334155; font-size:14px; font-family:\'Outfit\',sans-serif; line-height:1.6;">{processed_line}</p>')
                
    if in_blockquote:
        bq_content = "<br>".join(blockquote_lines)
        if blockquote_type == "important":
            html_lines.append(
                f'<div style="background-color:#fee2e2; border-left:4px solid #ef4444; padding:12px; margin:15px 0; border-radius:4px; color:#991b1b; font-size:14px; font-family:\'Outfit\',sans-serif; line-height:1.5;">'
                f'<strong>⚠️ IMPORTANT</strong><br>{bq_content}'
                f'</div>'
            )
        else:
            html_lines.append(
                f'<div style="background-color:#f8fafc; border-left:4px solid #64748b; padding:10px 14px; margin:12px 0; font-style:italic; color:#475569; font-family:\'Outfit\',sans-serif; border-radius:4px; line-height:1.5;">'
                f'{bq_content}'
                f'</div>'
            )
            
    return "\n".join(html_lines)

import zipfile

def create_zip_archive(today_str, rapports_dir, zip_output_path):
    with zipfile.ZipFile(zip_output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file in os.listdir(rapports_dir):
            if file.endswith('.md'):
                file_path = os.path.join(rapports_dir, file)
                with open(file_path, 'r', encoding='utf-8') as f:
                    md_content = f.read()
                
                html_body = md_to_html(md_content)
                title_clean = file.replace('.md', '').replace('bulletin_', '').replace('_', ' ').title()
                
                # Document HTML complet autonome et premium
                full_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{title_clean}</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap" rel="stylesheet">
    <style>
        body {{
            font-family: 'Outfit', sans-serif;
            background-color: #f1f5f9;
            color: #1e293b;
            padding: 30px;
            line-height: 1.6;
        }}
        .container {{
            max-width: 800px;
            margin: 0 auto;
            background-color: #ffffff;
            border-radius: 12px;
            padding: 40px;
            box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
            border: 1px solid #e2e8f0;
        }}
    </style>
</head>
<body>
    <div class="container">
        {html_body}
    </div>
</body>
</html>"""
                
                html_filename = file.replace('.md', '.html')
                if "bulletin_france" in file:
                    zipf.writestr(html_filename, full_html)
                else:
                    zipf.writestr(os.path.join("bulletins_regionaux", html_filename), full_html)

def send_email_with_summary(national_md, date_str, zip_path):
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
    
    # Conversion du bulletin national complet en HTML
    national_html = md_to_html(national_md)
    
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
                    {national_html}
                </div>
                
                <div class="section-card" style="margin-top: 20px;">
                    <h2>📦 Pieces Jointes (Dossiers)</h2>
                    <p style="font-size: 13px; color: #334155; line-height: 1.5;">
                        Tous vos bulletins météo Premium (les 13 bulletins régionaux ainsi que le bulletin national) sont archivés et classés dans des dossiers à l'intérieur de l'archive ZIP ci-jointe :<br>
                        📂 <strong>bulletins_meteo_france_{date_str.replace('/', '_')}.zip</strong>
                    </p>
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
    
    # Encodage Base64 du corps
    html_b64 = base64.b64encode(email_body.encode('utf-8')).decode('ascii')
    
    # Encodage Base64 de l'archive ZIP
    zip_filename = f"bulletins_meteo_france_{date_str.replace('/', '_')}.zip"
    with open(zip_path, 'rb') as f:
        zip_data = f.read()
    zip_b64 = base64.b64encode(zip_data).decode('ascii')
    
    boundary = uuid.uuid4().hex
    
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
        f'Content-Type: application/zip; name="{zip_filename}"\r\n'
        f'Content-Disposition: attachment; filename="{zip_filename}"\r\n'
        f'Content-Transfer-Encoding: base64\r\n'
        f'\r\n'
        f'{zip_b64}\r\n'
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
    national_content = ""
    
    for region in REGIONS.keys():
        region_norm = normalize_name(region)
        filename = f"bulletin_{region_norm}_{today_str}.md"
        output_file = os.path.join(rapports_dir, filename)
        
        print(f"Generation pour {region} -> {filename}")
        try:
            generer_bulletin_premium(region, source_dir, output_file)
            
            # Si c'est le bulletin national, on garde le contenu
            if region == "France":
                if os.path.exists(output_file):
                    with open(output_file, 'r', encoding='utf-8') as f:
                        national_content = f.read()
        except Exception as e:
            print(f"[ERREUR] Echec de la generation pour {region} : {e}")
            
    # 4. Créer l'archive ZIP
    print("\n=== Etape 3 : Creation de l'archive ZIP ===")
    zip_path = os.path.join(meteo_dir, "rapports", f"bulletins_{today_str}.zip")
    create_zip_archive(today_str, rapports_dir, zip_path)
    print(f"Archive ZIP creee avec succes dans : {zip_path}")
    
    # 5. Envoyer l'email avec le bulletin national en corps de mail et le ZIP attaché
    print("\n=== Etape 4 : Envoi de l'e-mail ===")
    if national_content:
        send_email_with_summary(national_content, date_display, zip_path)
    else:
        print("[ERREUR] Impossible d'envoyer l'e-mail: contenu national vide.")

if __name__ == "__main__":
    main()
