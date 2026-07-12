import os
import sys
import argparse
from datetime import datetime
import sqlite3
import json
import base64
import uuid
import smtplib
from email.utils import formatdate
import unicodedata

# Import meteo_core localement
sys.path.append(os.path.dirname(__file__))
import meteo_core

REGIONS = {
    "hauts-de-france": ["02", "59", "60", "62", "80"],
    "ile-de-france": ["75", "77", "78", "91", "92", "93", "94", "95"],
    "normandie": ["14", "27", "50", "61", "76"],
    "bretagne": ["22", "29", "35", "56"],
    "pays de la loire": ["44", "49", "53", "72", "85"],
    "centre-val de loire": ["18", "28", "36", "37", "41", "45"],
    "nouvelle-aquitaine": ["16", "17", "19", "23", "24", "33", "40", "47", "64", "79", "86", "87"],
    "occitanie": ["09", "11", "12", "30", "31", "32", "34", "46", "48", "65", "66", "81", "82"],
    "auvergne-rhone-alpes": ["01", "03", "07", "15", "26", "38", "42", "43", "63", "69", "73", "74"],
    "provence-alpes-cote d'azur": ["04", "05", "06", "13", "83", "84"],
    "corse": ["2A", "2B", "20"],
    "bourgogne-franche-comte": ["21", "25", "39", "58", "70", "71", "89", "90"],
    "grand est": ["08", "10", "51", "52", "54", "55", "57", "67", "68", "88"]
}
import re

def normalize_text(text):
    text = text.lower().strip()
    text = re.sub(r'[éèêë]', 'e', text)
    text = re.sub(r'[àâä]', 'a', text)
    text = re.sub(r'[îï]', 'i', text)
    text = re.sub(r'[ôö]', 'o', text)
    text = re.sub(r'[ûü]', 'u', text)
    text = re.sub(r'[ç]', 'c', text)
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s-]+', ' ', text)
    return text.strip()

def send_email_report(html_body, subject, recipient):
    gmail_email = os.environ.get("GMAIL_EMAIL", "langlet.gregory@gmail.com")
    gmail_password = os.environ.get("GMAIL_APP_PASSWORD")
    if not gmail_password:
        print("[SMTP] ERREUR : GMAIL_APP_PASSWORD non configuré. Annulation envoi.")
        return
        
    gmail_email = gmail_email.replace('\ufeff', '').replace('\ufffe', '').strip()
    gmail_password = gmail_password.replace('\ufeff', '').replace('\ufffe', '').strip()
    
    recipients = [r.strip() for r in recipient.split(",") if r.strip()]
    sender = gmail_email
    
    # Nettoyage ASCII du sujet pour éviter les rejets SMTP
    clean_subj = unicodedata.normalize('NFKD', subject).encode('ASCII', 'ignore').decode('ASCII')
    
    # Corps HTML en Base64
    html_body = html_body.replace('\ufeff', '').replace('\ufffe', '')
    text_b64 = base64.b64encode(html_body.encode('utf-8')).decode('ascii')
    
    boundary = uuid.uuid4().hex
    
    raw_message = (
        f'From: Gregory LANGLET <{sender}>\r\n'
        f'To: {", ".join(recipients)}\r\n'
        f'Subject: {clean_subj}\r\n'
        f'Date: {formatdate(localtime=True)}\r\n'
        f'MIME-Version: 1.0\r\n'
        f'Content-Type: multipart/mixed; boundary="{boundary}"\r\n'
        f'\r\n'
        f'--{boundary}\r\n'
        f'Content-Type: text/html; charset=utf-8\r\n'
        f'Content-Transfer-Encoding: base64\r\n'
        f'\r\n'
        f'{text_b64}\r\n'
        f'\r\n'
        f'--{boundary}--\r\n'
    )
    
    print(f"[SMTP] Envoi via Gmail à {', '.join(recipients)}...")
    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(gmail_email, gmail_password)
            server.sendmail(gmail_email, recipients, raw_message.encode('ascii'))
        print("[SMTP] E-mail de Bilan Régional (HTML Premium) envoyé avec succès !")
    except Exception as e:
        print(f"[SMTP] Erreur d'envoi du bilan régional : {e}")

def make_html_section(title, icon, data_list, param_type):
    html = f"""
    <div class="section-card">
        <div class="section-title">
            <span class="section-title-icon">{icon}</span>
            <span>{title}</span>
        </div>
        <div class="list-container">"""
        
    if not data_list:
        html += '<p style="font-size: 13px; color: #64748b; font-style: italic; margin-left: 12px; margin-top: 0;">Aucune donnée disponible pour aujourd\'hui.</p>'
    else:
        for idx, (name, dept, val, rec_m, rec_date) in enumerate(data_list):
            if idx == 0:
                rank_class = "rank-1"
                rank_str = "🥇"
            elif idx == 1:
                rank_class = "rank-2"
                rank_str = "🥈"
            elif idx == 2:
                rank_class = "rank-3"
                rank_str = "🥉"
            else:
                rank_class = "rank-other"
                rank_str = str(idx + 1)
                
            rec_str = ""
            if rec_m is not None:
                if (param_type == 'froid' and val <= rec_m) or (param_type != 'froid' and val >= rec_m):
                    rec_str = '<span class="record-alert">Record</span>'
                    
            if param_type == 'chaleur' or param_type == 'froid':
                val_str = f"{val:.1f}°C"
            elif param_type == 'pluie':
                val_str = f"{val:.1f} mm"
            else:
                val_str = f"{val:.0f} km/h"
                
            html += f"""
            <div class="list-item">
                <div class="station-info">
                    <span class="rank-badge {rank_class}">{rank_str}</span>
                    <span class="station-name">{name}</span>
                    <span class="dept-code">({dept})</span>
                    {rec_str}
                </div>
                <div class="val-badge val-{param_type}">{val_str}</div>
            </div>"""
            
    html += "</div></div>"
    return html

def main():
    parser = argparse.ArgumentParser(description="Pipeline Bilan Régionalisé (Top 10)")
    parser.add_argument("--date", help="Date au format DD/MM/YYYY (par défaut aujourd'hui)")
    parser.add_argument("--region", default="Hauts-de-France", help="Nom de la région cible (ex: Normandie, Île-de-France...)")
    parser.add_argument("--depts", help="Liste de départements séparés par des virgules (ex: 75,77,78)")
    parser.add_argument("--to", default="gregory.langlet@sfr.fr, langlet.gregory@gmail.com, patrick.marliere@wanadoo.fr", help="Destinataire de l'email")
    parser.add_argument("--no-email", action="store_true", help="Ne pas envoyer d'email")
    parser.add_argument("--no-nlm", action="store_true", help="Ne pas lancer la génération NotebookLM")
    args = parser.parse_args()
    
    target_depts = []
    zone_label = ""
    
    if args.depts:
        target_depts = [d.strip() for d in args.depts.split(",")]
        zone_label = f"Départements {', '.join(target_depts)}"
    else:
        norm_region = normalize_text(args.region)
        matched_key = None
        for key in REGIONS.keys():
            if normalize_text(key) == norm_region:
                matched_key = key
                break
        if not matched_key:
            print(f"Erreur : Région '{args.region}' non reconnue.")
            sys.exit(1)
        target_depts = REGIONS[matched_key]
        zone_label = args.region
        
    if args.date:
        dt = datetime.strptime(args.date, "%d/%m/%Y")
    else:
        dt = datetime.now()
        
    day, month, year = dt.day, dt.month, dt.year
    date_str = f"{day:02d}/{month:02d}/{year}"
    date_compact = f"{year}{month:02d}{day:02d}"
    print(f"=== Lancement du pipeline Bilan Régional ({zone_label}) pour le {date_str} ===")
    
    # 1. Scraper les archives nationales Météociel (cache)
    print("Scraping des archives Météociel...")
    try:
        meteo_core.scrape_national_archive(date_compact)
    except Exception as e:
        print(f"Erreur de scraping : {e}")
        
    # 2. Se connecter à la base et exécuter les requêtes Top 10 régionales
    conn = sqlite3.connect(meteo_core.get_db_path())
    cursor = conn.cursor()
    
    placeholders = ",".join("?" for _ in target_depts)
    params = [date_compact] + target_depts
    
    # Top 10 Températures Maximales (Chaleur)
    cursor.execute(f"""
        SELECT s.name, s.dept, o.tmax, o.tmax_rec_m, o.tmax_rec_m_date
        FROM observations o
        JOIN stations s ON o.station_code = s.code
        WHERE o.date = ? AND s.dept IN ({placeholders}) AND o.tmax IS NOT NULL
        ORDER BY o.tmax DESC
        LIMIT 10
    """, params)
    tmax_list = cursor.fetchall()
    
    # Top 10 Températures Minimales (Froid)
    cursor.execute(f"""
        SELECT s.name, s.dept, o.tmin, o.tmin_rec_m, o.tmin_rec_m_date
        FROM observations o
        JOIN stations s ON o.station_code = s.code
        WHERE o.date = ? AND s.dept IN ({placeholders}) AND o.tmin IS NOT NULL
        ORDER BY o.tmin ASC
        LIMIT 10
    """, params)
    tmin_list = cursor.fetchall()
    
    # Top 10 Cumuls de Précipitations (Pluie)
    cursor.execute(f"""
        SELECT s.name, s.dept, o.precip, o.precip_rec_m, o.precip_rec_m_date
        FROM observations o
        JOIN stations s ON o.station_code = s.code
        WHERE o.date = ? AND s.dept IN ({placeholders}) AND o.precip > 0
        ORDER BY o.precip DESC
        LIMIT 10
    """, params)
    precip_list = cursor.fetchall()
    
    # Top 10 Rafales de Vent (Vent)
    cursor.execute(f"""
        SELECT s.name, s.dept, o.gust, o.gust_rec_m, o.gust_rec_m_date
        FROM observations o
        JOIN stations s ON o.station_code = s.code
        WHERE o.date = ? AND s.dept IN ({placeholders}) AND o.gust > 0
        ORDER BY o.gust DESC
        LIMIT 10
    """, params)
    gust_list = cursor.fetchall()
    conn.close()
    
    # 3. Formater les sections HTML
    html_sections = []
    html_sections.append(make_html_section("Top Températures Maximales (Chaleur)", "🔥", tmax_list, "chaleur"))
    html_sections.append(make_html_section("Top Températures Minimales (Froid)", "❄️", tmin_list, "froid"))
    html_sections.append(make_html_section("Top Cumuls de Précipitations (Pluie)", "🌧️", precip_list, "pluie"))
    html_sections.append(make_html_section("Top Rafales de Vent", "💨", gust_list, "vent"))

    # Style CSS et Template HTML
    style_css = """
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;800&family=Plus+Jakarta+Sans:wght@400;500;700&display=swap');
    body { font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif; background-color: #f8fafc; color: #1e293b; padding: 30px; margin: 0; }
    .card { max-width: 620px; background: #ffffff; margin: 0 auto; border-radius: 24px; border: 1px solid #e2e8f0; box-shadow: 0 10px 15px -3px rgba(15, 23, 42, 0.05), 0 4px 6px -4px rgba(15, 23, 42, 0.05); overflow: hidden; }
    .header { background: linear-gradient(135deg, #1e3a8a 0%, #0f172a 100%); padding: 40px 30px; text-align: center; color: #ffffff; }
    .header-badge { display: inline-block; padding: 4px 12px; border-radius: 20px; background: rgba(255, 255, 255, 0.15); font-family: 'Outfit', sans-serif; font-size: 11px; font-weight: 800; text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 12px; }
    .header h1 { font-family: 'Outfit', sans-serif; font-size: 26px; font-weight: 800; margin: 0; letter-spacing: -0.5px; }
    .header p { font-size: 13.5px; margin: 8px 0 0 0; opacity: 0.85; }
    .content { padding: 35px 30px; }
    .section-card { margin-bottom: 35px; }
    .section-title { font-family: 'Outfit', sans-serif; font-size: 14px; font-weight: 800; text-transform: uppercase; letter-spacing: 1px; color: #475569; display: flex; align-items: center; margin-bottom: 16px; }
    .section-title-icon { margin-right: 8px; font-size: 18px; }
    .list-container { display: flex; flex-direction: column; gap: 8px; }
    .list-item { background: #ffffff; border: 1px solid #f1f5f9; border-radius: 12px; padding: 12px 16px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.02); }
    .station-info { display: flex; align-items: center; gap: 8px; font-size: 13.5px; color: #334155; }
    .rank-badge { width: 22px; height: 22px; display: flex; align-items: center; justify-content: center; font-size: 11px; font-weight: 800; border-radius: 50%; }
    .rank-1 { background-color: #fef08a; color: #854d0e; }
    .rank-2 { background-color: #f1f5f9; color: #475569; }
    .rank-3 { background-color: #ffedd5; color: #c2410c; }
    .rank-other { background-color: #f8fafc; color: #64748b; }
    .station-name { font-weight: 700; color: #0f172a; }
    .dept-code { color: #64748b; font-size: 12px; }
    .val-badge { font-family: 'Outfit', sans-serif; font-size: 13px; font-weight: 800; padding: 4px 12px; border-radius: 20px; color: #ffffff; min-width: 60px; text-align: center; }
    .val-chaleur { background: linear-gradient(135deg, #f97316 0%, #ef4444 100%); }
    .val-froid { background: linear-gradient(135deg, #3b82f6 0%, #06b6d4 100%); }
    .val-pluie { background: linear-gradient(135deg, #10b981 0%, #059669 100%); }
    .val-vent { background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%); }
    .record-alert { font-family: 'Outfit', sans-serif; font-size: 9px; font-weight: 800; text-transform: uppercase; color: #ffffff; background-color: #ef4444; padding: 2px 8px; border-radius: 4px; margin-left: 6px; display: inline-block; vertical-align: middle; }
    .footer { text-align: center; padding: 25px; font-size: 11.5px; color: #64748b; border-top: 1px solid #f1f5f9; background-color: #f8fafc; line-height: 1.5; }
    """
    
    html_body = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <style>{style_css}</style>
</head>
<body>
    <div class="card">
        <div class="header">
            <div class="header-badge">MÉTÉO REGIONAL</div>
            <h1>BILAN METEO REGIONAL</h1>
            <p>Région {zone_label} • Synthèse des postes clés du {date_str}</p>
        </div>
        <div class="content">
            {"".join(html_sections)}
        </div>
        <div class="footer">
            Données climatologiques basées sur les relevés officiels Météo-France comparés aux normales de référence.
        </div>
    </div>
</body>
</html>
"""
    
    # Send Email
    if not args.no_email:
        subject = f"Bilan Regional {zone_label} - {date_str}"
        send_email_report(html_body, subject, args.to)
    else:
        print("Mode no-email activé. Affichage du code HTML.")

if __name__ == "__main__":
    main()
