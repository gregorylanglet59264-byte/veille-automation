# -*- coding: utf-8 -*-
"""
run_veille_intemperies.py
Script autonome cloud-compatible pour la Veille Intempéries & Cyclones.
Collecte les données via Google News RSS (avec temporalité forcée),
récupère les tweets météo via gnewsdecoder sans connexion ni cookies,
appelle l'API LLM (Gemini ou OpenRouter) pour générer un rapport de 10 points cliquables,
et envoie le rapport formaté en HTML premium par e-mail via SMTP Gmail.
"""
import os
import sys
import json
import re
import time
import datetime
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import smtplib
import base64
import uuid
import unicodedata
import email.utils
from email.utils import formatdate
from googlenewsdecoder import gnewsdecoder

# Comptes météo à suivre (issus de votre liste d'abonnements)
ACCOUNTS = [
    "laradiometeo", "AEMET_Esp", "AEMET_Aragon", "Aigle_e", "stormchaser_a81", "AlexyMeteo",
    "AnthoGrillon", "Arameteo_france", "globerourdiales", "ChroChao", "Cycloneoi", "DorianDziadula",
    "TropicalTidbits", "SergeZaka", "ElTiempoes", "Estofex", "EtienneFargetMC", "EvelyneDheliat",
    "extremetemps", "FayenceMeteo", "FeuxdeForet_FR", "Florent_Boutet", "FloC36", "ForceThirteen",
    "l_garcelon", "GregCornard", "GJauseau", "Meteovilles", "GWoznica", "Guitri13", "hurrtrackerapp",
    "GlobalCyclones", "ROrage09", "infoccitanie", "InfoMeteoTuit", "Infosyclone_44", "peacockreports",
    "Alpenweerman", "JulienSugier", "KeraunosObs", "StormChaser220", "Kevin_Fillin", "Firinga_le_site",
    "lachainemeteo", "meteo_reunion", "LyonMeteo69", "Marc_Hay_Meteo", "MatthieuSorel", "MaxenceLeDrogo1",
    "metofficestorms", "tiempo_guada", "meteo60", "meteociel", "meteophile", "MeteoredFR", "Meteouragans",
    "T2mike", "MeteoMonsieur", "Vincent_06v", "37Meteo", "MeteoBretagne", "meteoconcept", "MeteoExpress",
    "MeteoNord", "MeteoHerault", "MeteoLanguedoc", "MeteoNordParis", "msa6768", "Meteoinfo_FR", "meteofrance",
    "MeteoFrance_AG", "meteo_76", "MeteoCarnoux", "meteosuisse", "meteovillages", "nicolasberrod",
    "NicolasLeFriant", "Ninofishing", "meteo_tropicale", "ouragans", "Pat_wx", "La_Meteo_du_13",
    "philklotzbach", "SkyPhilippe", "previneige", "Prefet971", "Prefet972", "Prefet974", "romumartinik",
    "smlmrn", "Thom_Wx", "Stormyalert", "StevenTual_off", "sxmcyclone", "ThomasBlanchar2", "lePlaymobil28",
    "TimeoLepert", "Djpuco", "Navarrameteo", "AutanTramontane", "VigiMeteoFrance", "StormchaserUKEU",
    "wxcharts", "Zactus_re"
]

WEATHER_KEYWORDS = [
    'orage', 'grêle', 'grele', 'vent', 'rafale', 'tornade', 'inondation', 
    'débordement', 'crues', 'foudre', 'cyclone', 'ouragan', 'typhon', 
    'tempête', 'tempete', 'antilles', 'guadeloupe', 'martinique', 
    'réunion', 'reunion', 'tropical', 'haishen', 'caraïbes'
]

def fetch_gnews_xml_with_retry(query):
    encoded_query = urllib.parse.quote(query)
    url = f"https://news.google.com/rss/search?q={encoded_query}&hl=fr&gl=FR&ceid=FR:fr"
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    
    for attempt in range(4):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": user_agent})
            with urllib.request.urlopen(req, timeout=15) as response:
                return response.read()
        except Exception as e:
            if attempt == 3:
                raise e
            print(f"[RSS] Erreur temporaire '{query}' (tentative {attempt+1}/4) : {e}. Pause...")
            time.sleep(attempt * 2 + 2)

def fetch_google_news(query):
    try:
        xml_data = fetch_gnews_xml_with_retry(query)
        root = ET.fromstring(xml_data)
        articles = []
        for item in root.findall(".//item")[:15]:
            title = item.findtext("title") or ""
            link = item.findtext("link") or ""
            pub_date = item.findtext("pubDate") or ""
            source = item.findtext("source") or ""
            articles.append({
                "title": title,
                "url": link,
                "date": pub_date,
                "source": source
            })
        return articles
    except Exception as e:
        print(f"[RSS] Échec final de récupération pour '{query}': {e}", file=sys.stderr)
        return []

def clean_accents(s):
    nfkd = unicodedata.normalize('NFKD', s)
    return "".join([c for c in nfkd if not unicodedata.combining(c)]).lower()

def fetch_twitter_tweets_gnews():
    print("[Twitter] Collecte indirecte via Google News RSS...")
    # Regrouper les requêtes en chunks de 10 comptes
    chunks = [ACCOUNTS[i:i+10] for i in range(0, len(ACCOUNTS), 10)]
    all_items = []
    
    # Étape 1 : Récupérer les liens Google News correspondants aux comptes
    for chunk in chunks[:4]:  # On limite à 40 comptes clés pour rester rapide
        q = " OR ".join([f"site:x.com/{acc}" for acc in chunk])
        try:
            xml_data = fetch_gnews_xml_with_retry(q)
            root = ET.fromstring(xml_data)
            for item in root.findall('.//item')[:12]:
                all_items.append({
                    "title": item.findtext('title') or "",
                    "link": item.findtext('link') or "",
                    "pubDate": item.findtext('pubDate') or ""
                })
        except Exception as e:
            print(f"[Twitter] Erreur chunk : {e}", file=sys.stderr)
            
    # Étape 2 : Décoder les URLs Google News et filtrer
    filtered_tweets = []
    now = datetime.datetime.now(datetime.timezone.utc)
    for item in all_items:
        try:
            res = gnewsdecoder(item["link"])
            if res.get("status") and res.get("decoded_url"):
                real_url = res["decoded_url"]
                match = re.search(r'x\.com/([^/]+)/status/(\d+)', real_url)
                if match:
                    username = match.group(1)
                    text = item["title"]
                    if text.endswith(" - x.com"):
                        text = text[:-8]
                        
                    # Filtrer par mots-clés
                    text_lower = clean_accents(text)
                    if any(kw in text_lower for kw in WEATHER_KEYWORDS) or username.lower() in ["globalcyclones", "cycloneoi", "meteo_reunion"]:
                        pub_dt = email.utils.parsedate_to_datetime(item["pubDate"])
                        if pub_dt.tzinfo is None:
                            pub_dt = pub_dt.replace(tzinfo=datetime.timezone.utc)
                        age = now - pub_dt
                        
                        # Limiter aux dernières 36 heures pour la fraîcheur
                        if age <= datetime.timedelta(hours=36):
                            filtered_tweets.append({
                                "author": username,
                                "text": text,
                                "url": real_url,
                                "date": item["pubDate"]
                            })
        except Exception:
            pass
            
    return filtered_tweets[:15]

def call_llm(system_prompt, user_prompt):
    gemini_key = (os.environ.get("GEMINI_API_KEY") or "").strip()
    openrouter_key = (os.environ.get("OPENROUTER_API_KEY") or "").strip()

    if gemini_key:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_key}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{
                "parts": [{"text": f"{system_prompt}\n\n{user_prompt}"}]
            }]
        }
        try:
            req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=90) as response:
                res_data = json.loads(response.read().decode("utf-8"))
                return res_data["candidates"][0]["content"]["parts"][0]["text"]
        except Exception as e:
            print(f"[LLM] Échec Gemini API: {e}")
            
    if openrouter_key:
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {openrouter_key}"
        }
        payload = {
            "model": "deepseek/deepseek-chat",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        }
        try:
            req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=90) as response:
                res_data = json.loads(response.read().decode("utf-8"))
                return res_data["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"[LLM] Échec OpenRouter API: {e}")
            
    return None

def build_report_data(raw_news, tweets, date_str):
    system_prompt = (
        "Tu es un expert en météorologie opérationnelle et analyste en risques climatiques senior.\n"
        "Ton rôle est de rédiger un bulletin de veille complet et extrêmement détaillé sur les intempéries (orages, grêle, vent, tornades, inondations) en France et DOM-TOM, ainsi que l'activité cyclonique mondiale.\n\n"
        f"Tu dois générer une structure JSON contenant deux clés :\n"
        "1. \"email_report\": Une chaîne HTML contenant le rapport de veille rédigé de manière fluide, littéraire, journalistique et prête à être envoyée dans le corps de l'e-mail. Cette chaîne DOIT suivre la structure suivante :\n"
        f"   - Titre principal : H2 avec le texte '⛈️ Rapport de Veille Intempéries & Cyclones — {date_str}'\n"
        "   - Section 'Résumé exécutif' : Une introduction de 3-4 lignes décrivant l'objet de la veille, la fraîcheur des données (moins de 24h/48h) et la situation d'ensemble.\n"
        "   - Les 10 points critiques, numérotés de 1 à 10. Chaque point doit avoir son titre en gras (H3 ou div) et une description rédigée de façon fluide (4-5 lignes minimum) qui explique l'événement. RÈGLE CRITIQUE : Tu DOIS intégrer les sources sous forme de liens HTML cliquables directement dans le texte, par exemple : '(lire la dépêche de <a href=\"URL\" style=\"color: #2563eb; text-decoration: underline;\">franceinfo</a> ou le suivi sur <a href=\"URL\" style=\"color: #2563eb; text-decoration: underline;\">Météo Express</a>)'. Copie-colle sans modification la clé 'url' de l'article source.\n"
        f"   - Signature de fin : Un paragraphe en italique 'Rapport de veille spécifique rédigé le {date_str} par Gregory Langlet.'\n\n"
        "2. \"cards\": Une liste d'exactement 10 objets pour la pièce jointe HTML premium. Chaque objet doit avoir la structure suivante :\n"
        "   - \"title\": Le titre précis et percutant de l'événement.\n"
        "   - \"summary\": Une description technique très approfondie et développée (6 à 8 lignes minimum) décrivant le contexte thermodynamique, les valeurs mesurées (rafales, pluie, grêle) et les impacts constatés.\n"
        "   - \"url\": L'URL d'origine de l'article ou du tweet (recopiée à la lettre sans modification).\n\n"
        "Format de sortie attendu : JSON uniquement avec la structure suivante (sans blocs ```json) :\n"
        "{\n"
        "  \"email_report\": \"...\",\n"
        "  \"cards\": [\n"
        "    {\"title\": \"...\", \"summary\": \"...\", \"url\": \"...\"},\n"
        "    ... (10 items)\n"
        "  ]\n"
        "}"
    )
    
    user_prompt = f"Données météo :\n{json.dumps(raw_news, ensure_ascii=False)}\n\nDonnées Twitter :\n{json.dumps(tweets, ensure_ascii=False)}"
    
    for attempt in range(3):
        response = call_llm(system_prompt, user_prompt)
        if response:
            try:
                response_clean = response.strip().replace("```json", "").replace("```", "")
                parsed = json.loads(response_clean, strict=False)
                if isinstance(parsed, dict) and "email_report" in parsed and "cards" in parsed and len(parsed["cards"]) == 10:
                    return parsed
            except Exception as e:
                print(f"[LLM] Tentative {attempt+1} échec parsing JSON: {e}")
        time.sleep(10)
    return None

def get_badge_info(title, summary):
    text = (title + " " + summary).lower()
    if any(k in text for k in ["cyclone", "ouragan", "typhon"]):
        return "CYCLONE / OURAGAN", "#7c3aed", "#f5f3ff" # Purple
    elif any(k in text for k in ["orage", "foudre", "supercellule"]):
        return "ORAGES VIOLENTS", "#dc2626", "#fef2f2" # Red
    elif any(k in text for k in ["grêle", "grele"]):
        return "GRÊLE MAJEURE", "#b91c1c", "#fef2f2" # Dark Red
    elif any(k in text for k in ["inondation", "crues", "débordement", "crue"]):
        return "INONDATIONS / CRUES", "#2563eb", "#eff6ff" # Blue
    elif any(k in text for k in ["vent", "rafale", "tornade", "tempête", "tempete"]):
        return "RAFALES / TORNADES", "#d97706", "#fffbeb" # Orange
    else:
        return "VIGILANCE MÉTÉO", "#4b5563", "#f9fafb" # Gray

def send_email(report_json, date_str):
    gmail_email = os.environ.get("GMAIL_EMAIL", "langlet.gregory@gmail.com")
    gmail_password = os.environ.get("GMAIL_APP_PASSWORD")
    if gmail_email:
        gmail_email = gmail_email.replace('\ufeff', '').replace('\ufffe', '').strip()
    if gmail_password:
        gmail_password = gmail_password.replace('\ufeff', '').replace('\ufffe', '').strip()
        
    if not gmail_password:
        print("[SMTP] Erreur: GMAIL_APP_PASSWORD non configuré.", file=sys.stderr)
        return
        
    raw_recipients = os.environ.get("RECIPIENT_EMAILS", gmail_email)
    recipients = [r.strip() for r in raw_recipients.split(",") if r.strip()]
    
    # Récupérer les deux composants du rapport JSON
    email_report_html = report_json.get("email_report", "")
    cards_list = report_json.get("cards", [])
    
    # 1. Construction du corps HTML du rapport en pièce jointe (fiches techniques ultra-premium)
    html_items = ""
    for idx, item in enumerate(cards_list, 1):
        label, color, bg = get_badge_info(item.get('title', ''), item.get('summary', ''))
        html_items += f"""
        <div class="card">
            <span class="badge" style="background-color: {bg}; color: {color}; border: 1px solid {color}40;">{label} — Point {idx}</span>
            <h3 class="card-title">{item.get('title')}</h3>
            <p class="card-summary">{item.get('summary')}</p>
            <a href="{item.get('url', '#')}" target="_blank" class="btn-source">Consulter la source officielle</a>
        </div>
        """
        
    attachment_style = """
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f8fafc; color: #1e293b; margin: 0; padding: 0; }
    .wrapper { width: 100%; max-width: 850px; margin: 0 auto; padding: 30px; box-sizing: border-box; }
    header { text-align: center; padding: 40px 20px; background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 50%, #1e40af 100%); color: #ffffff; border-radius: 16px; margin-bottom: 30px; box-shadow: 0 10px 25px -5px rgba(0,0,0,0.1); }
    h1 { margin: 0 0 12px 0; font-size: 32px; font-weight: 800; letter-spacing: -0.5px; }
    .subtitle { font-size: 16px; color: #93c5fd; margin: 0; font-weight: 500; text-transform: uppercase; letter-spacing: 1px; }
    .card { background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 14px; padding: 24px; margin-bottom: 20px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); }
    .card-title { font-size: 19px; font-weight: 700; margin: 0 0 12px 0; color: #0f172a; line-height: 1.4; }
    .card-summary { font-size: 14.5px; line-height: 1.7; color: #334155; margin: 0; text-align: justify; }
    .badge { display: inline-block; padding: 4px 10px; border-radius: 6px; font-size: 11px; font-weight: 700; text-transform: uppercase; margin-bottom: 12px; }
    .btn-source { display: inline-block; padding: 9px 18px; background-color: #1e3a8a; color: #ffffff !important; text-decoration: none; border-radius: 8px; font-size: 12px; font-weight: 600; margin-top: 16px; text-transform: uppercase; letter-spacing: 0.5px; }
    .btn-source:hover { background-color: #2563eb; }
    footer { text-align: center; padding: 30px 0; font-size: 13px; color: #64748b; border-top: 1px solid #e2e8f0; margin-top: 50px; }
    """
    
    html_attachment = f"""<!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Bulletin Veille Intempéries &amp; Cyclones - {date_str}</title>
        <style>{attachment_style}</style>
    </head>
    <body>
        <div class="wrapper">
            <header>
                <h1>Veille Spécifique Intempéries &amp; Cyclones</h1>
                <p class="subtitle">Bulletin technique du {date_str}</p>
            </header>
            {html_items}
            <footer>
                <p>Ce bulletin a été compilé de manière autonome par le robot de veille météorologique.</p>
            </footer>
        </div>
    </body>
    </html>
    """
    
    # 2. Construction du corps de l'e-mail au format HTML contenant le rapport fluide rédigé
    html_email_body = f"""<html>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #1e293b; background-color: #f8fafc; padding: 25px; margin: 0; line-height: 1.65;">
      <div style="max-width: 750px; margin: 0 auto; background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 35px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);">
        
        {email_report_html}
        
        <div style="background-color: #eff6ff; border: 1px dashed #2563eb; padding: 20px; border-radius: 8px; margin: 30px 0; text-align: center;">
          <h3 style="color: #1e3a8a; margin: 0 0 8px 0; font-size: 16px; font-weight: 700;">📂 Rapport Technique Joint</h3>
          <p style="margin: 0; font-size: 13.5px; color: #334155;">Le fichier joint <strong>{filename}</strong> contient les fiches techniques approfondies et les valeurs physiques relevées (rafales, pluie, grêle) prêtes pour diffusion.</p>
        </div>
        
        <hr style="border: 0; border-top: 1px solid #e2e8f0; margin: 30px 0;">
        <p style="font-size: 11px; color: #94a3b8; text-align: center; margin: 0;">Généré automatiquement par le workflow GitHub Actions de Veille Météo.</p>
      </div>
    </body>
    </html>
    """
    
    # Encodages
    boundary = uuid.uuid4().hex
    html_att_b64 = base64.b64encode(html_attachment.encode('utf-8')).decode('ascii')
    html_email_b64 = base64.b64encode(html_email_body.encode('utf-8')).decode('ascii')
    
    # Nettoyage ASCII strict du sujet pour éviter les spams
    subject_raw = f"Veille actu meteo - {date_str}"
    clean_subject = unicodedata.normalize('NFKD', subject_raw).encode('ASCII', 'ignore').decode('ASCII')
    
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
        f'{html_email_b64}\r\n'
        f'\r\n'
        f'--{boundary}\r\n'
        f'Content-Type: text/html; charset=utf-8; name="{filename}"\r\n'
        f'Content-Disposition: attachment; filename="{filename}"\r\n'
        f'Content-Transfer-Encoding: base64\r\n'
        f'\r\n'
        f'{html_att_b64}\r\n'
        f'\r\n'
        f'--{boundary}--\r\n'
    )
    
    with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as server:
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(gmail_email, gmail_password)
        server.sendmail(gmail_email, recipients, raw_message.encode('ascii', 'ignore'))
    print("[SMTP] Email envoyé avec succès !")

def main():
    now = datetime.datetime.now()
    month_name = MONTHS_FR[now.month - 1]
    date_str = f"{now.day} {month_name} {now.year}"
    
    print(f"=== Lancement de la Veille Intempéries & Cyclones ({date_str}) ===")
    
    # 1. Collecte Google News
    queries = {
        "france_intemperies": "(orages OR grêle OR vent OR tornade OR inondation) France vigilance when:24h",
        "dom_tom_intemperies": "(orages OR inondations OR vigilance OR cyclone OR tempête) (Guadeloupe OR Martinique OR Réunion OR Mayotte OR Guyane) when:3d",
        "veille_cyclonique": "(cyclone OR ouragan OR typhon OR tempête OR tropicale) when:3d"
    }
    
    raw_news = {}
    for key, query in queries.items():
        print(f"[RSS] Collecte {key}...")
        raw_news[key] = fetch_google_news(query)
        
    # 2. Collecte Twitter
    tweets = fetch_twitter_tweets_gnews()
    
    # 3. Génération IA
    print("[LLM] Synthèse et rédaction du rapport final...")
    report_json = build_report_data(raw_news, tweets, date_str)
    
    if report_json:
        # Sauvegarde locale
        output_file = "veille_intemperies_final.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(report_json, f, ensure_ascii=False, indent=2)
        print(f"[✔] Rapport sauvegardé dans {output_file}")
        
        # 4. Envoi Email
        send_email(report_json, date_str)
    else:
        print("[❌] Erreur: impossible de générer la synthèse via le LLM.")

MONTHS_FR = [
    "janvier", "février", "mars", "avril", "mai", "juin",
    "juillet", "août", "septembre", "octobre", "novembre", "décembre"
]

if __name__ == "__main__":
    main()
