import os
import sys
import argparse
import subprocess
import re
from datetime import datetime
import json
import base64
import uuid
import smtplib
from email.utils import formatdate
import unicodedata

# Import meteo_core & convert_to_pdf localement
sys.path.append(os.path.dirname(__file__))
import meteo_core
import convert_to_pdf

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

DEPTS_NAMES = {
    "01": "Ain", "02": "Aisne", "03": "Allier", "04": "Alpes-de-Haute-Provence", "05": "Hautes-Alpes",
    "06": "Alpes-Maritimes", "07": "Ardèche", "08": "Ardennes", "09": "Ariège", "10": "Aube",
    "11": "Aude", "12": "Aveyron", "13": "Bouches-du-Rhône", "14": "Calvados", "15": "Cantal",
    "16": "Charente", "17": "Charente-Maritime", "18": "Cher", "19": "Corrèze", "2A": "Corse-du-Sud",
    "2B": "Haute-Corse", "20": "Corse", "21": "Côte-d'Or", "22": "Côtes-d'Armor", "23": "Creuse",
    "24": "Dordogne", "25": "Doubs", "26": "Drôme", "27": "Eure", "28": "Eure-et-Loir",
    "29": "Finistère", "30": "Gard", "31": "Haute-Garonne", "32": "Gers", "33": "Gironde",
    "34": "Hérault", "35": "Ille-et-Vilaine", "36": "Indre", "37": "Indre-et-Loire", "38": "Isère",
    "39": "Jura", "40": "Landes", "41": "Loir-et-Cher", "42": "Loire", "43": "Haute-Loire",
    "44": "Loire-Atlantique", "45": "Loiret", "46": "Lot", "47": "Lot-et-Garonne", "48": "Lozère",
    "49": "Maine-et-Loire", "50": "Manche", "51": "Marne", "52": "Haute-Marne", "53": "Mayenne",
    "54": "Meurthe-et-Moselle", "55": "Meuse", "56": "Morbihan", "57": "Moselle", "58": "Nièvre",
    "59": "Nord", "60": "Oise", "61": "Orne", "62": "Pas-de-Calais", "63": "Puy-de-Dôme",
    "64": "Pyrénées-Atlantiques", "65": "Hautes-Pyrénées", "66": "Pyrénées-Orientales", "67": "Bas-Rhin",
    "68": "Haut-Rhin", "69": "Rhône", "70": "Haute-Saône", "71": "Saône-et-Loire", "72": "Sarthe",
    "73": "Savoie", "74": "Haute-Savoie", "75": "Paris", "76": "Seine-Maritime", "77": "Seine-et-Marne",
    "78": "Yvelines", "79": "Deux-Sèvres", "80": "Somme", "81": "Tarn", "82": "Tarn-et-Garonne",
    "83": "Var", "84": "Vaucluse", "85": "Vendée", "86": "Vienne", "87": "Haute-Vienne",
    "88": "Vosges", "89": "Yonne", "90": "Territoire de Belfort", "91": "Essonne", "92": "Hauts-de-Seine",
    "93": "Seine-Saint-Denis", "94": "Val-de-Marne", "95": "Val-d'Oise"
}

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

def run_command_live(cmd):
    return subprocess.run(cmd, shell=True)

def wait_and_download_artifacts(nb_id, out_dir):
    print("Suivi de la génération des infographies sur NotebookLM...")
    import time
    start_time = time.time()
    downloaded_paths = []
    
    retries = 0
    while time.time() - start_time < 300:
        res = subprocess.run(["nlm", "studio", "status", nb_id, "--json"], capture_output=True, text=True)
        try:
            status_list = json.loads(res.stdout)
        except:
            status_list = []
            
        infographics = [art for art in status_list if art["type"] == "infographic"]
        if not infographics:
            retries += 1
            if retries > 3:
                print("\nAucune infographie en cours d'exécution détectée.")
                break
            time.sleep(10)
            continue
            
        all_done = all(art["status"] == "completed" for art in infographics)
        failed = any(art["status"] == "failed" for art in infographics)
        
        if all_done:
            print("\nToutes les infographies ont été générées avec succès !")
            for art in infographics:
                art_id = art["id"]
                name = f"infographic_{art_id}"
                inst = art.get("custom_instructions") or ""
                if "département" in inst.lower():
                    m = re.search(r"département\s*:\s*([^\(]+)", inst, re.I)
                    if m:
                        name = f"infographie_{normalize_text(m.group(1)).replace(' ', '_')}"
                elif "tiktok" in inst.lower():
                    name = "infographie_generale_tiktok"
                    
                png_path = os.path.join(out_dir, f"{name}.png")
                jpg_path = os.path.join(out_dir, f"{name}.jpg")
                
                print(f"Téléchargement de {name}...")
                subprocess.run([
                    "nlm", "download", "infographic", nb_id,
                    "--id", art_id,
                    "--output", png_path
                ], capture_output=True)
                
                try:
                    from PIL import Image
                    im = Image.open(png_path)
                    rgb_im = im.convert("RGB")
                    rgb_im.save(jpg_path, "JPEG", quality=85)
                    downloaded_paths.append(jpg_path)
                    os.remove(png_path)
                except Exception as e:
                    print(f"Erreur de compression pour {name} : {e}")
            break
        elif failed:
            print("\nUne ou plusieurs infographies ont échoué.")
            break
        else:
            completed_count = sum(1 for art in infographics if art["status"] == "completed")
            sys.stdout.write(f"\rInfographies prêtes : {completed_count}/{len(infographics)}...")
            sys.stdout.flush()
            time.sleep(10)
            
    return downloaded_paths

def send_email_report(linkedin_post, report_pdf_path, subject, recipient):
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
    
    # Corps textuel avec le post LinkedIn rédigé
    linkedin_post = linkedin_post.replace('\ufeff', '').replace('\ufffe', '')
    text_b64 = base64.b64encode(linkedin_post.encode('utf-8')).decode('ascii')
    
    boundary = uuid.uuid4().hex
    
    # Pièce jointe PDF
    pdf_attachment_block = ""
    if report_pdf_path and os.path.exists(report_pdf_path):
        pdf_filename = os.path.basename(report_pdf_path)
        with open(report_pdf_path, "rb") as f_pdf:
            pdf_data = f_pdf.read()
        pdf_b64 = base64.b64encode(pdf_data).decode('ascii')
        pdf_attachment_block = (
            f'--{boundary}\r\n'
            f'Content-Type: application/pdf; name="{pdf_filename}"\r\n'
            f'Content-Disposition: attachment; filename="{pdf_filename}"\r\n'
            f'Content-Transfer-Encoding: base64\r\n'
            f'\r\n'
            f'{pdf_b64}\r\n'
            f'\r\n'
        )
        
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
        f'{pdf_attachment_block}'
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
        print("[SMTP] E-mail de Bilan envoyé avec succès !")
    except Exception as e:
        print(f"[SMTP] Erreur d'envoi du bilan : {e}")

def main():
    parser = argparse.ArgumentParser(description="Pipeline Bilan Journalier Régionalisé (Unifié)")
    parser.add_argument("--date", help="Date au format DD/MM/YYYY (par défaut aujourd'hui)")
    parser.add_argument("--region", default="Hauts-de-France", help="Nom de la région cible (ex: Normandie, Île-de-France...)")
    parser.add_argument("--depts", help="Liste de départements séparés par des virgules (ex: 75,77,78)")
    parser.add_argument("--to", default="patrick.marliere@wanadoo.fr", help="Destinataire de l'email")
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
    print(f"=== Lancement du pipeline Bilan Journalier ({zone_label}) pour le {date_str} ===")
    
    # Check if Desktop CSV exists for this date, import it if present (local fallback)
    date_dash = f"{year}-{month:02d}-{day:02d}"
    export_path = f"C:\\Users\\grego\\Desktop\\meteo_export_rankings_{date_dash}_{date_dash}.csv"
    if os.path.exists(export_path):
        meteo_core.import_from_csv(export_path)
        
    # Get all stations in target departments
    all_stations = meteo_core.get_all_stations(only_dans_tx=False)
    stations = [s for s in all_stations if s["dept"] in target_depts]
    
    if not stations:
        print(f"Aucune station trouvée pour la zone {zone_label}.")
        sys.exit(1)
        
    print(f"Scraping et calcul de normales pour {len(stations)} stations...")
    stations_processed = []
    
    for s in stations:
        code = s["code"]
        obs = meteo_core.fetch_and_cache(code, date_compact)
        if obs and obs["tmax"] is not None:
            # Get normals
            nr, proxy_info = meteo_core.get_normales_records_with_proxy(code, month)
            norm_tmax = nr["tmax_norm"] if nr else None
            norm_tmin = nr["tmin_norm"] if nr else None
            
            tmax_anom = round(obs["tmax"] - norm_tmax, 1) if obs["tmax"] is not None and norm_tmax is not None else None
            tmin_anom = round(obs["tmin"] - norm_tmin, 1) if obs["tmin"] is not None and norm_tmin is not None else None
            
            records_broken_station = []
            
            # Tmax record
            if obs.get("tmax") is not None and obs.get("tmax_rec_m") is not None:
                if obs["tmax"] >= obs["tmax_rec_m"]:
                    is_abs = obs["tmax_rec_a"] is not None and obs["tmax"] >= obs["tmax_rec_a"]
                    rec_type = "ABSOLU 🌡️" if is_abs else "MENSUEL 🌡️"
                    records_broken_station.append({
                        "param": "Tmax", "type": rec_type, "val": obs["tmax"],
                        "prev_val": obs["tmax_rec_m"], "prev_date": obs["tmax_rec_m_date"]
                    })
                    
            # Tmin record
            if obs.get("tmin") is not None and obs.get("tmin_rec_m") is not None:
                if obs["tmin"] <= obs["tmin_rec_m"]:
                    is_abs = obs["tmin_rec_a"] is not None and obs["tmin"] <= obs["tmin_rec_a"]
                    rec_type = "ABSOLU ❄️" if is_abs else "MENSUEL ❄️"
                    records_broken_station.append({
                        "param": "Tmin", "type": rec_type, "val": obs["tmin"],
                        "prev_val": obs["tmin_rec_m"], "prev_date": obs["tmin_rec_m_date"]
                    })
                    
            # Precipitation record
            if obs.get("precip") is not None and obs.get("precip_rec_m") is not None and obs["precip"] > 0:
                if obs["precip"] >= obs["precip_rec_m"]:
                    is_abs = obs["precip_rec_a"] is not None and obs["precip"] >= obs["precip_rec_a"]
                    rec_type = "ABSOLU 🌧️" if is_abs else "MENSUEL 🌧️"
                    records_broken_station.append({
                        "param": "Pluie", "type": rec_type, "val": obs["precip"],
                        "prev_val": obs["precip_rec_m"], "prev_date": obs["precip_rec_m_date"]
                    })
                    
            # Wind record
            if obs.get("gust") is not None and obs.get("gust_rec_m") is not None and obs["gust"] > 0:
                if obs["gust"] >= obs["gust_rec_m"]:
                    is_abs = obs["gust_rec_a"] is not None and obs["gust"] >= obs["gust_rec_a"]
                    rec_type = "ABSOLU 💨" if is_abs else "MENSUEL 💨"
                    records_broken_station.append({
                        "param": "Vent", "type": rec_type, "val": obs["gust"],
                        "prev_val": obs["gust_rec_m"], "prev_date": obs["gust_rec_m_date"]
                    })
                    
            stations_processed.append({
                "name": s["name"],
                "dept": s["dept"],
                "tmax": obs["tmax"],
                "tmin": obs["tmin"],
                "precip": obs["precip"],
                "gust": obs["gust"],
                "tmax_anom": tmax_anom,
                "tmin_anom": tmin_anom,
                "records_broken": records_broken_station
            })
            
    stations_processed.sort(key=lambda x: (x["dept"], x["name"]))
    
    depts_data = {}
    for s in stations_processed:
        d = s["dept"]
        if d not in depts_data: depts_data[d] = []
        depts_data[d].append(s)
        
    tmax_vals = [s["tmax"] for s in stations_processed if s["tmax"] is not None]
    tmin_vals = [s["tmin"] for s in stations_processed if s["tmin"] is not None]
    tmax_anoms = [s["tmax_anom"] for s in stations_processed if s["tmax_anom"] is not None]
    
    avg_tmax = sum(tmax_vals) / len(tmax_vals) if tmax_vals else 0
    avg_tmin = sum(tmin_vals) / len(tmin_vals) if tmin_vals else 0
    avg_tmax_anom = sum(tmax_anoms) / len(tmax_anoms) if tmax_anoms else 0
    avg_precip = sum(s["precip"] for s in stations_processed if s["precip"] is not None) / len(stations_processed) if stations_processed else 0
    
    hotspot = max(stations_processed, key=lambda x: x["tmax"] if x["tmax"] is not None else -99) if tmax_vals else None
    coldspot = min(stations_processed, key=lambda x: x["tmin"] if x["tmin"] is not None else 99) if tmin_vals else None
    
    valid_gust = [s for s in stations_processed if s["gust"] is not None]
    windiest = max(valid_gust, key=lambda x: x["gust"]) if valid_gust else None
    
    all_broken = []
    for s in stations_processed:
        for r in s.get("records_broken", []):
            all_broken.append((s["name"], s["dept"], r))
            
    alert_txt_plain = ""
    alert_txt_md = ""
    if all_broken:
        alert_txt_plain = "🚨🔴 **ALERTE RECORDS CLIMATIQUES BATTUS AUJOURD'HUI !**\n"
        alert_txt_md = "## 🚨🔴 <font color=\"red\">**ALERTE : Records Climatologiques Battus Aujourd'hui !**</font>\n\n"
        for name, dept, r in all_broken:
            param = r["param"]
            val = r["val"]
            unit = "°C" if param in ("Tmax", "Tmin") else " mm" if param == "Pluie" else " km/h"
            prev_val = r["prev_val"]
            prev_date = r["prev_date"]
            type_str = r["type"]
            alert_txt_plain += f"🔴 **[{type_str}]** **{name} ({dept})** : **{val}{unit}** (ancien record : {prev_val}{unit} le {prev_date})\n"
            alert_txt_md += f"- 🔴 **[{type_str}]** <font color=\"red\">**{name} ({dept})** : **{val}{unit}** (ancien record : {prev_val}{unit} le {prev_date})</font>\n"
        alert_txt_plain += "\n"
        alert_txt_md += "\n"

    # LinkedIn post
    post_content = f"☀️🌡️ **BILAN METEO : REGION {zone_label.upper()} CE {date_str} !**\n\n"
    if alert_txt_plain:
        post_content += alert_txt_plain
    post_content += f"Les stations météo de la région {zone_label} révèlent des températures particulièrement remarquables pour la journée.\n\n"
    post_content += "📊 **Les Chiffres Clés de la Journée :**\n"
    post_content += f"- **Température Maximale Moyenne** : **{avg_tmax:.1f}°C**"
    if tmax_anoms:
        post_content += f" (soit une anomalie exceptionnelle de **{avg_tmax_anom:+.1f}°C** par rapport aux normales !)"
    post_content += f"\n- **Température Minimale Moyenne** : **{avg_tmin:.1f}°C**\n"
    if avg_precip > 0:
        post_content += f"- **Pluviométrie Moyenne** : **{avg_precip:.2f} mm**\n"
    if windiest:
        post_content += f"- **Rafale maximale** : **{windiest['gust']:.0f} km/h** à {windiest['name']} ({windiest['dept']})\n"
        
    if hotspot or coldspot:
        post_content += "\n🏆 **Les Extremes du Jour :**\n"
        if hotspot:
            anom_str = f", soit **{hotspot['tmax_anom']:+.1f}°C** au-dessus de la normale" if hotspot['tmax_anom'] is not None else ""
            post_content += f"- 🔥 **Point chaud** : **{hotspot['tmax']:.1f}°C** à **{hotspot['name']} ({hotspot['dept']})**{anom_str} !\n"
        if coldspot:
            post_content += f"- ❄️ **Point frais (matin)** : **{coldspot['tmin']:.1f}°C** à **{coldspot['name']} ({coldspot['dept']})**.\n"
            
    post_content += f"\n---\n\n📋 **RELEVÉS DÉTAILLÉS DE TOUTES LES STATIONS ({date_str}) :**\n"
    
    for dept_code in sorted(depts_data.keys()):
        name_dept = DEPTS_NAMES.get(dept_code, f"Département {dept_code}")
        post_content += f"\n📌 **{name_dept} ({dept_code}) :**\n"
        for s in depts_data[dept_code]:
            tmax_str = f"{s['tmax']:.1f}°C" if s['tmax'] is not None else "—"
            tmin_str = f"{s['tmin']:.1f}°C" if s['tmin'] is not None else "—"
            anom_str = f" ({s['tmax_anom']:+.1f}°C)" if s['tmax_anom'] is not None else ""
            gust_str = f" | 💨 {s['gust']:.0f} km/h" if s['gust'] else ""
            post_content += f"- **{s['name']}** : Min {tmin_str} / Max {tmax_str}{anom_str}{gust_str}\n"
            
    post_content += """
---
*Données climatologiques basées sur les relevés officiels Météo-France comparés aux normales de référence 1991-2020.*

#Meteo #Climat #Climatologie #MeteoFrance #Chaleur #Environnement
"""
    
    os.makedirs("reports", exist_ok=True)
    post_file = "reports/linkedin_post.txt"
    with open(post_file, "w", encoding="utf-8") as f:
        f.write(post_content)
        
    # Save markdown report
    report_md_path = f"reports/bilan_{normalize_text(zone_label).replace(' ','_')}_{day:02d}_{month:02d}_{year}.md"
    report_md_content = f"""# 🌤️ Bilan Climatologique : Région {zone_label} ({date_str})

Bilan complet des observations météorologiques répertoriant les températures extrêmes, précipitations et rafales maximales.

"""
    if alert_txt_md:
        report_md_content += alert_txt_md
    report_md_content += f"""## 📊 Les Chiffres Clés Régionaux
- **Température Maximale Moyenne** : **{avg_tmax:.1f}°C** (anomalie de **{avg_tmax_anom:+.1f}°C**)
- **Température Minimale Moyenne** : **{avg_tmin:.1f}°C**
"""
    if avg_precip > 0:
        report_md_content += f"- **Pluviométrie Moyenne** : **{avg_precip:.2f} mm**\n"
    if windiest:
        report_md_content += f"- **Rafale maximale** : **{windiest['gust']:.0f} km/h** à {windiest['name']} ({windiest['dept']})\n"
        
    if hotspot or coldspot:
        report_md_content += "\n## 🏆 Les Extremes du Jour\n"
        if hotspot:
            report_md_content += f"- 🔥 **Point chaud** : **{hotspot['tmax']:.1f}°C** à **{hotspot['name']} ({hotspot['dept']})**\n"
        if coldspot:
            report_md_content += f"- ❄️ **Point frais** : **{coldspot['tmin']:.1f}°C** à **{coldspot['name']} ({coldspot['dept']})**\n"
            
    report_md_content += "\n---\n"
    
    for dept_code in sorted(depts_data.keys()):
        report_md_content += f"\n### 📌 {DEPTS_NAMES.get(dept_code, dept_code)} ({dept_code})\n"
        for s in depts_data[dept_code]:
            tmax_str = f"{s['tmax']:.1f}°C" if s['tmax'] is not None else "—"
            tmin_str = f"{s['tmin']:.1f}°C" if s['tmin'] is not None else "—"
            anom_str = f" ({s['tmax_anom']:+.1f}°C)" if s['tmax_anom'] is not None else ""
            gust_str = f" | 💨 {s['gust']:.0f} km/h" if s['gust'] else ""
            report_md_content += f"- **{s['name']}** : Min {tmin_str} / Max {tmax_str}{anom_str}{gust_str}\n"
            
    with open(report_md_path, "w", encoding="utf-8") as f:
        f.write(report_md_content)
        
    print("Génération du rapport PDF...")
    pdf_path = report_md_path.replace(".md", ".pdf")
    html_path = report_md_path.replace(".md", ".html")
    convert_to_pdf.md_to_html(report_md_path, html_path, title=f"Bilan Meteo {zone_label} - {date_str}")
    success_pdf = convert_to_pdf.convert_html_to_pdf(html_path, pdf_path)
    if success_pdf:
        try: os.remove(html_path)
        except: pass
        print("Rapport PDF généré avec succès.")
    else:
        pdf_path = None
        print("Erreur de génération PDF.")
        
    # Send Email
    if not args.no_email:
        subject = f"Bilan Meteo {zone_label} - {date_str}"
        # Nettoyer les astérisques du post_content pour l'email
        email_body = post_content.replace('**', '').replace('*', '')
        send_email_report(email_body, None, subject, args.to)

if __name__ == "__main__":
    main()
