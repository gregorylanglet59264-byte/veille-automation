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

def send_email_report(body_text, subject, recipient):
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
    
    # Corps textuel
    body_text = body_text.replace('\ufeff', '').replace('\ufffe', '')
    text_b64 = base64.b64encode(body_text.encode('utf-8')).decode('ascii')
    
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
        f'Content-Type: text/plain; charset=utf-8\r\n'
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
        print("[SMTP] E-mail de Bilan Régional envoyé avec succès !")
    except Exception as e:
        print(f"[SMTP] Erreur d'envoi du bilan régional : {e}")

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
    
    # 3. Formater le rapport régional sans astérisques (identique au modèle national)
    post_content = f"BILAN METEO REGIONAL - REGION {zone_label.upper()} - CE {date_str}\n\n"
    post_content += f"Synthèse des postes les plus remarquables pour chaque paramètre relevé sur le réseau régional.\n\n"
    
    # Chaleur
    post_content += "🔥 TOP TEMPÉRATURES MAXIMALES (CHALEUR) :\n"
    if tmax_list:
        for idx, (name, dept, val, rec_m, rec_date) in enumerate(tmax_list):
            rec_str = ""
            if rec_m is not None and val >= rec_m:
                rec_str = f" [RECORDBATTU] (ancien : {rec_m}°C le {rec_date})"
            post_content += f"{idx+1}. {name} ({dept}) : {val:.1f}°C{rec_str}\n"
    else:
        post_content += "Aucune donnée disponible.\n"
    post_content += "\n"
    
    # Froid
    post_content += "❄️ TOP TEMPÉRATURES MINIMALES (FRAÎCHEUR/FROID) :\n"
    if tmin_list:
        for idx, (name, dept, val, rec_m, rec_date) in enumerate(tmin_list):
            rec_str = ""
            if rec_m is not None and val <= rec_m:
                rec_str = f" [RECORDBATTU] (ancien : {rec_m}°C le {rec_date})"
            post_content += f"{idx+1}. {name} ({dept}) : {val:.1f}°C{rec_str}\n"
    else:
        post_content += "Aucune donnée disponible.\n"
    post_content += "\n"
    
    # Pluie
    post_content += "🌧️ TOP CUMULS DE PRÉCIPITATIONS (PLUIE) :\n"
    if precip_list:
        for idx, (name, dept, val, rec_m, rec_date) in enumerate(precip_list):
            rec_str = ""
            if rec_m is not None and val >= rec_m:
                rec_str = f" [RECORDBATTU] (ancien : {rec_m} mm le {rec_date})"
            post_content += f"{idx+1}. {name} ({dept}) : {val:.1f} mm{rec_str}\n"
    else:
        post_content += "Aucun cumul significatif enregistré.\n"
    post_content += "\n"
    
    # Vent
    post_content += "💨 TOP RAFALES DE VENT :\n"
    if gust_list:
        for idx, (name, dept, val, rec_m, rec_date) in enumerate(gust_list):
            rec_str = ""
            if rec_m is not None and val >= rec_m:
                rec_str = f" [RECORDBATTU] (ancien : {rec_m} km/h le {rec_date})"
            post_content += f"{idx+1}. {name} ({dept}) : {val:.0f} km/h{rec_str}\n"
    else:
        post_content += "Aucune rafale remarquable enregistrée.\n"
        
    post_content += f"""
---
Données climatologiques basées sur les relevés officiels Météo-France comparés aux normales de référence.

#Meteo #Climat #BilanRegional #{zone_label.replace(' ', '').replace('-', '')}
"""
    
    print(post_content)
    
    # Send Email
    if not args.no_email:
        subject = f"Bilan Regional {zone_label} - {date_str}"
        send_email_report(post_content, subject, args.to)

if __name__ == "__main__":
    main()
