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

def fetch_google_news(query):
    try:
        encoded_query = urllib.parse.quote(query)
        url = f"https://news.google.com/rss/search?q={encoded_query}&hl=fr&gl=FR&ceid=FR:fr"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as response:
            xml_data = response.read()
        
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
        print(f"[RSS] Échec de récupération de la requête '{query}': {e}", file=sys.stderr)
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
        url = f"https://news.google.com/rss/search?q={urllib.parse.quote(q)}&hl=fr&gl=FR&ceid=FR:fr"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        try:
            with urllib.request.urlopen(req, timeout=15) as r:
                root = ET.fromstring(r.read())
                for item in root.findall('.//item')[:12]:
                    all_items.append({
                        "title": item.findtext('title') or "",
                        "link": item.findtext('link') or "",
                        "pubDate": item.findtext('pubDate') or ""
                    })
        except Exception as e:
            print(f"[Twitter] Erreur chunk: {e}", file=sys.stderr)
            
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

def build_report_data(raw_news, tweets):
    system_prompt = (
        "Tu es un prévisionniste météo et analyste climatique senior.\n"
        "Ton rôle est de rédiger un rapport condensé d'intempéries et de veille cyclonique.\n"
        "RÈGLE CRITIQUE : Tu DOIS obligatoirement lister EXACTEMENT 10 points numérotés de 1 à 10.\n"
        "Pour chaque point, fournis :\n"
        "- Le titre de l'information en français\n"
        "- La description condensée et explicative en français (2-3 lignes)\n"
        "- L'URL exacte de l'article ou du tweet correspondant. Copie-colle sans modification la clé 'url' de l'élément sélectionné.\n"
        "Format de sortie attendu : JSON uniquement avec la structure suivante (sans blocs ```json) :\n"
        "[\n"
        "  {\"title\": \"...\", \"summary\": \"...\", \"url\": \"...\"},\n"
        "  ... (10 items)\n"
        "]"
    )
    
    user_prompt = f"Données météo :\n{json.dumps(raw_news, ensure_ascii=False)}\n\nDonnées Twitter :\n{json.dumps(tweets, ensure_ascii=False)}"
    
    for attempt in range(3):
        response = call_llm(system_prompt, user_prompt)
        if response:
            try:
                response_clean = response.strip().replace("```json", "").replace("```", "")
                parsed = json.loads(response_clean, strict=False)
                if len(parsed) == 10:
                    return parsed
            except Exception as e:
                print(f"[LLM] Tentative {attempt+1} échec parsing JSON: {e}")
        time.sleep(10)
    return None

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
    
    # Construction du corps HTML
    html_items = ""
    for idx, item in enumerate(report_json, 1):
        html_items += f"""
        <div class="card">
            <span class="badge badge-meteo">Actualité {idx}</span>
            <h3 class="card-title">
                <a href="{item.get('url', '#')}" target="_blank">{item.get('title')}</a>
            </h3>
            <p class="card-summary">{item.get('summary')}</p>
        </div>
        """
        
    style = """
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; background-color: #f3f4f6; color: #1f2937; margin: 0; padding: 0; }
    .wrapper { width: 100%; max-width: 700px; margin: 0 auto; padding: 20px; box-sizing: border-box; }
    header { text-align: center; padding: 25px 0; background: linear-gradient(135deg, #1e3a8a 0%, #0f172a 100%); color: #ffffff; border-radius: 12px; margin-bottom: 20px; }
    h1 { margin: 0 0 8px 0; font-size: 24px; }
    .subtitle { font-size: 14px; color: #9ca3af; margin: 0; }
    .card { background-color: #ffffff; border: 1px solid #e5e7eb; border-radius: 8px; padding: 15px; margin-bottom: 12px; }
    .card-title { font-size: 15px; margin: 0 0 6px 0; font-weight: 600; }
    .card-title a { color: #1e3a8a; text-decoration: none; }
    .card-title a:hover { text-decoration: underline; }
    .card-summary { font-size: 13.5px; line-height: 1.5; color: #4b5563; margin: 0; }
    .badge { display: inline-block; padding: 2px 6px; border-radius: 4px; font-size: 10px; font-weight: bold; text-transform: uppercase; margin-bottom: 6px; }
    .badge-meteo { background-color: #dbeafe; color: #1e40af; }
    footer { text-align: center; padding: 20px 0; font-size: 11px; color: #9ca3af; }
    """
    
    html_body = f"""<!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <style>{style}</style>
    </head>
    <body>
        <div class="wrapper">
            <header>
                <h1>Veille Spécifique Intempéries &amp; Cyclones</h1>
                <p class="subtitle">Bulletin du {date_str}</p>
            </header>
            {html_items}
            <footer>
                <p>Veille générée automatiquement et envoyée via GitHub Actions.</p>
            </footer>
        </div>
    </body>
    </html>
    """
    
    # Construction du résumé textuel pour le corps du mail
    summary_text = "Bonjour,\n\nVoici le résumé rapide de votre veille actu meteo du jour :\n\n"
    for idx, item in enumerate(report_json, 1):
        summary_text += f"{idx}. {item.get('title')}\n"
    summary_text += "\nVous trouverez le rapport complet avec tous les liens cliquables dans le fichier HTML joint à ce message.\n\nCordialement,\nL'assistant de Veille"
    
    # Encodages
    boundary = uuid.uuid4().hex
    filename = f"veille_intemperies_{datetime.datetime.now().strftime('%Y_%m_%d')}.html"
    html_b64 = base64.b64encode(html_body.encode('utf-8')).decode('ascii')
    text_b64 = base64.b64encode(summary_text.encode('utf-8')).decode('ascii')
    
    # Nettoyage ASCII strict du sujet
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
        f'Content-Type: text/plain; charset=utf-8\r\n'
        f'Content-Transfer-Encoding: base64\r\n'
        f'\r\n'
        f'{text_b64}\r\n'
        f'\r\n'
        f'--{boundary}\r\n'
        f'Content-Type: text/html; charset=utf-8; name="{filename}"\r\n'
        f'Content-Disposition: attachment; filename="{filename}"\r\n'
        f'Content-Transfer-Encoding: base64\r\n'
        f'\r\n'
        f'{html_b64}\r\n'
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
    report_json = build_report_data(raw_news, tweets)
    
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
