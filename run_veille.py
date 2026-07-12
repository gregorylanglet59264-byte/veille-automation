# -*- coding: utf-8 -*-
"""
run_veille.py
Superviseur autonome de veille globale.
Collecte les données (Actualités, Météo, IA via Google News RSS, Vidéos via fetch_youtube_feed),
appelle l'API de l'IA (Gemini ou OpenRouter) pour rédiger les rapports et la synthèse de 10 éléments,
compile le tout en HTML premium responsive et l'envoie par e-mail via SMTP SFR.
"""
import os
import sys
import json
import argparse
import datetime
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import make_msgid, formatdate

# Dictionnaires de traduction pour les dates dynamiques
MONTHS_FR = [
    "janvier", "février", "mars", "avril", "mai", "juin",
    "juillet", "août", "septembre", "octobre", "novembre", "décembre"
]

def get_date_fr():
    now = datetime.datetime.now()
    return f"{now.day} {MONTHS_FR[now.month - 1]} {now.year}"

# 1. Collecte Google News RSS
def fetch_google_news(query):
    try:
        encoded_query = urllib.parse.quote(query)
        url = f"https://news.google.com/rss/search?q={encoded_query}&hl=fr&gl=FR&ceid=FR:fr"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as response:
            xml_data = response.read()
        
        root = ET.fromstring(xml_data)
        articles = []
        for item in root.findall(".//item")[:20]: # On récupère 20 candidats pour en garder 10 de qualité
            title = item.find("title").text if item.find("title") is not None else ""
            link = item.find("link").text if item.find("link") is not None else ""
            pub_date = item.find("pubDate").text if item.find("pubDate") is not None else ""
            source = item.find("source").text if item.find("source") is not None else ""
            articles.append({
                "title": title,
                "url": link,
                "date": pub_date,
                "source": source
            })
        return articles
    except Exception as e:
        print(f"Erreur de collecte pour la requête '{query}': {e}")
        return []

# 2. Appel API IA (Gemini ou OpenRouter) sans dépendances lourdes
def call_llm(system_prompt, user_prompt):
    gemini_key = os.environ.get("GEMINI_API_KEY")
    openrouter_key = os.environ.get("OPENROUTER_API_KEY")
    
    if gemini_key:
        print("[LLM] Appel de Gemini API...")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_key}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{
                "parts": [{"text": f"{system_prompt}\n\n{user_prompt}"}]
            }]
        }
        try:
            req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=45) as response:
                res_data = json.loads(response.read().decode("utf-8"))
                return res_data["candidates"][0]["content"]["parts"][0]["text"]
        except Exception as e:
            print(f"[LLM] Erreur Gemini API: {e}")
            
    if openrouter_key:
        print("[LLM] Appel de OpenRouter API (DeepSeek)...")
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {openrouter_key}"
        }
        payload = {
            "model": "deepseek/deepseek-v4-flash",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        }
        try:
            req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=45) as response:
                res_data = json.loads(response.read().decode("utf-8"))
                return res_data["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"[LLM] Erreur OpenRouter API: {e}")
            
    print("[LLM] ERREUR : Aucune clé API configurée ou échec des appels.")
    return None

# 3. Rédacteurs thématiques (avec règle stricte des 10 articles)
def build_actu_report(date_str):
    print("[Rapport] Collecte et rédaction Actualités...")
    queries = {
        "mondial": "monde actualités grands titres breaking news",
        "international": "actualités internationales géopolitique Europe US Asie",
        "france": "actualités France politique société économie",
        "hdf": "actualités Hauts-de-France Nord Pas-de-Calais Picardie Lille"
    }
    
    raw_data = {}
    for key, q in queries.items():
        raw_data[key] = fetch_google_news(q)
        
    system_prompt = (
        "Tu es un analyste de presse senior. Ton rôle est de trier et de synthétiser les actualités fournies.\n"
        "RÈGLE CRITIQUE : Tu DOIS lister EXACTEMENT 10 articles pour chaque catégorie (Mondial, International, France, Hauts-de-France).\n"
        "Pour chaque article, fournis son titre en français, sa source, son URL d'origine et une courte description (1 à 2 lignes).\n"
        "Format de sortie attendu : JSON uniquement avec la structure suivante (sans blocs de code markdown ```json) :\n"
        "{\n"
        "  \"mondial\": [ {\"title\": \"...\", \"source\": \"...\", \"url\": \"...\", \"summary\": \"...\"}, ... (10 items) ],\n"
        "  \"international\": [ ... (10 items) ],\n"
        "  \"france\": [ ... (10 items) ],\n"
        "  \"hdf\": [ ... (10 items) ]\n"
        "}"
    )
    user_prompt = f"Données récoltées pour le {date_str} :\n{json.dumps(raw_data, ensure_ascii=False)}"
    
    response = call_llm(system_prompt, user_prompt)
    if not response:
        return None
    # Nettoyer d'éventuels marqueurs markdown
    response_clean = response.strip().replace("```json", "").replace("```", "")
    return json.loads(response_clean)

def build_ia_report(date_str):
    print("[Rapport] Collecte et rédaction Intelligence Artificielle...")
    query = "AI models tools releases benchmark github cursor claude gemini llama deepseek"
    raw_articles = fetch_google_news(query)
    
    system_prompt = (
        "Tu es un analyste IA senior. Ton rôle est de sélectionner et décrire les nouveautés majeures de l'écosystème IA.\n"
        "RÈGLE CRITIQUE : Tu DOIS lister EXACTEMENT 10 actualités/outils majeurs.\n"
        "Pour chaque élément, fournis un titre, l'outil/modèle concerné, sa description technique succincte, son URL et une note d'intérêt éditorial /10.\n"
        "Format de sortie attendu : JSON uniquement avec la structure suivante (sans blocs ```json) :\n"
        "[\n"
        "  {\"title\": \"...\", \"tool\": \"...\", \"summary\": \"...\", \"url\": \"...\", \"score\": 8.5},\n"
        "  ... (10 items)\n"
        "]"
    )
    user_prompt = f"Données récoltées pour le {date_str} :\n{json.dumps(raw_articles, ensure_ascii=False)}"
    
    response = call_llm(system_prompt, user_prompt)
    if not response:
        return None
    response_clean = response.strip().replace("```json", "").replace("```", "")
    return json.loads(response_clean)

def build_meteo_report(date_str):
    print("[Rapport] Collecte et rédaction Météo & Climat...")
    query = "météo france vigilance climat records Copernicus NOAA OMM intempéries"
    raw_articles = fetch_google_news(query)
    
    system_prompt = (
        "Tu es un prévisionniste météo senior. Ton rôle est de lister les événements météo et climatologiques clés.\n"
        "RÈGLE CRITIQUE : Tu DOIS lister EXACTEMENT 10 actualités/vigilances/records.\n"
        "Pour chaque élément, fournis un titre, la zone géographique, le phénomène concerné, sa description détaillée et son URL source.\n"
        "Format de sortie attendu : JSON uniquement avec la structure suivante (sans blocs ```json) :\n"
        "[\n"
        "  {\"title\": \"...\", \"location\": \"...\", \"phenomenon\": \"...\", \"summary\": \"...\", \"url\": \"...\"},\n"
        "  ... (10 items)\n"
        "]"
    )
    user_prompt = f"Données récoltées pour le {date_str} :\n{json.dumps(raw_articles, ensure_ascii=False)}"
    
    response = call_llm(system_prompt, user_prompt)
    if not response:
        return None
    response_clean = response.strip().replace("```json", "").replace("```", "")
    return json.loads(response_clean)

def process_youtube_report():
    print("[Rapport] Chargement et filtrage Vidéos YouTube...")
    try:
        with open("youtube_recommandations.json", "r", encoding="utf-8") as f:
            videos = json.load(f)
        # Garder exactement les 10 vidéos avec le plus fort score d'intérêt
        top_videos = sorted(videos, key=lambda x: -x.get("score", 0))[:10]
        return top_videos
    except Exception as e:
        print(f"Erreur de chargement des recommandations YouTube : {e}")
        return []

# 4. Générateur de Synthèse Globale
def build_synthesis(actu, ia, meteo, yt, date_str):
    print("[Synthèse] Rédaction de la synthèse globale...")
    system_prompt = (
        "Tu es un rédacteur en chef. Ton rôle est de compiler une synthèse quotidienne pour un créateur de contenu.\n"
        "À partir des quatre thématiques fournies (Presse, IA, Météo, YouTube), rédige une synthèse condensée contenant :\n"
        "1. Une introduction de 3-4 lignes décrivant la situation globale du jour.\n"
        "2. Les 10 actualités presse majeures à retenir.\n"
        "3. Les 10 nouveautés IA clés.\n"
        "4. Les 10 événements/alertes météo clés.\n"
        "5. Les 10 vidéos YouTube recommandées (en mentionnant le score /10).\n"
        "6. Un planning éditorial suggéré (3 sujets de vidéos ou posts, avec accroches et formats conseillés).\n"
        "Format de sortie attendu : JSON uniquement avec la structure suivante (sans blocs ```json) :\n"
        "{\n"
        "  \"intro\": \"...\",\n"
        "  \"top_press\": [ \"...\", ... (10 items) ],\n"
        "  \"top_ia\": [ \"...\", ... (10 items) ],\n"
        "  \"top_meteo\": [ \"...\", ... (10 items) ],\n"
        "  \"top_youtube\": [ \"...\", ... (10 items) ],\n"
        "  \"editorial_plan\": [ {\"subject\": \"...\", \"hook\": \"...\", \"format\": \"...\"}, ... (3 items) ]\n"
        "}"
    )
    user_prompt = f"Données pour le {date_str} :\n- Presse : {json.dumps(actu, ensure_ascii=False)[:3000]}\n- IA : {json.dumps(ia, ensure_ascii=False)[:3000]}\n- Météo : {json.dumps(meteo, ensure_ascii=False)[:3000]}\n- YouTube : {json.dumps(yt, ensure_ascii=False)[:3000]}"
    
    response = call_llm(system_prompt, user_prompt)
    if not response:
        return None
    response_clean = response.strip().replace("```json", "").replace("```", "")
    return json.loads(response_clean)

# 5. Compilation HTML Premium Responsive
def compile_html(synthesis, actu, ia, meteo, yt, date_str):
    print("[HTML] Compilation du template premium...")
    
    # CSS Inline pour compatibilité e-mail maximale
    style = """
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f6f9fc; color: #32325d; margin: 0; padding: 0; }
    .wrapper { width: 100%; max-width: 750px; margin: 0 auto; padding: 20px; box-sizing: border-box; }
    header { text-align: center; padding: 30px 0; background: linear-gradient(135deg, #1f2937 0%, #111827 100%); color: #ffffff; border-radius: 12px; margin-bottom: 25px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    h1 { margin: 0 0 10px 0; font-size: 28px; font-weight: 700; letter-spacing: -0.5px; }
    .subtitle { font-size: 15px; color: #9ca3af; margin: 0; }
    .intro-box { background-color: #ffffff; border-left: 4px solid #4f46e5; border-radius: 8px; padding: 20px; margin-bottom: 25px; box-shadow: 0 2px 4px rgba(0,0,0,0.02); }
    .intro-text { margin: 0; font-size: 15px; line-height: 1.6; color: #4b5563; font-style: italic; }
    .section-title { font-size: 20px; font-weight: 700; border-bottom: 2px solid #e5e7eb; padding-bottom: 8px; margin: 35px 0 15px 0; color: #111827; }
    .badge { display: inline-block; padding: 3px 8px; border-radius: 12px; font-size: 11px; font-weight: 700; text-transform: uppercase; margin-bottom: 8px; }
    .badge-mondial { background-color: #fee2e2; color: #ef4444; }
    .badge-inter { background-color: #ffedd5; color: #f97316; }
    .badge-france { background-color: #dbeafe; color: #3b82f6; }
    .badge-hdf { background-color: #e0f2fe; color: #0284c7; }
    .badge-ia { background-color: #ede9fe; color: #8b5cf6; }
    .badge-meteo { background-color: #dcfce7; color: #22c55e; }
    .badge-yt { background-color: #fce7f3; color: #db2777; }
    
    .card { background-color: #ffffff; border: 1px solid #e5e7eb; border-radius: 8px; padding: 18px; margin-bottom: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.02); transition: transform 0.2s; }
    .card-title { font-size: 16px; font-weight: 600; margin: 0 0 8px 0; }
    .card-title a { color: #111827; text-decoration: none; }
    .card-title a:hover { color: #4f46e5; text-decoration: underline; }
    .card-meta { font-size: 12px; color: #6b7280; margin-bottom: 8px; }
    .card-summary { font-size: 14px; line-height: 1.5; color: #4b5563; margin: 0; }
    .score-badge { float: right; font-weight: 700; color: #b45309; background-color: #fef3c7; padding: 2px 6px; border-radius: 4px; font-size: 12px; }
    
    .synthesis-list { background-color: #ffffff; border-radius: 8px; padding: 20px; border: 1px solid #e5e7eb; margin-bottom: 25px; }
    .synthesis-list ul { margin: 0; padding-left: 20px; }
    .synthesis-list li { margin-bottom: 10px; font-size: 14px; line-height: 1.5; color: #374151; }
    
    .editorial-grid { display: table; width: 100%; border-spacing: 10px 0; margin-bottom: 25px; }
    .editorial-col { display: table-cell; width: 33.33%; background-color: #ffffff; border: 1px solid #e5e7eb; border-radius: 8px; padding: 15px; box-sizing: border-box; vertical-align: top; }
    .ed-title { font-size: 14px; font-weight: 700; color: #4f46e5; margin: 0 0 6px 0; text-transform: uppercase; }
    .ed-hook { font-size: 13px; line-height: 1.4; color: #4b5563; font-style: italic; margin-bottom: 8px; }
    .ed-format { font-size: 11px; background-color: #f3f4f6; padding: 2px 6px; border-radius: 4px; color: #374151; display: inline-block; }
    
    footer { text-align: center; padding: 30px 0; font-size: 12px; color: #9ca3af; border-top: 1px solid #e5e7eb; margin-top: 50px; }
    """
    
    html = f"""<!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Veille Globale Unifiée - {date_str}</title>
        <style>{style}</style>
    </head>
    <body>
        <div class="wrapper">
            <header>
                <h1>Veille Globale Unifiée</h1>
                <p class="subtitle">Actualités, IA, Météo & Vidéos YouTube du {date_str}</p>
            </header>
            
            <div class="intro-box">
                <p class="intro-text">{synthesis.get('intro', '')}</p>
            </div>
            
            <div class="section-title">📌 Synthèse Rapide du Jour</div>
            
            <div class="synthesis-list">
                <h3>Presse Générale</h3>
                <ul>
    """
    for item in synthesis.get('top_press', []):
        html += f"<li>{item}</li>"
    html += """
                </ul>
                <h3>Intelligence Artificielle</h3>
                <ul>
    """
    for item in synthesis.get('top_ia', []):
        html += f"<li>{item}</li>"
    html += """
                </ul>
                <h3>Météo & Climat</h3>
                <ul>
    """
    for item in synthesis.get('top_meteo', []):
        html += f"<li>{item}</li>"
    html += """
                </ul>
                <h3>Vidéos YouTube</h3>
                <ul>
    """
    for item in synthesis.get('top_youtube', []):
        html += f"<li>{item}</li>"
    html += """
                </ul>
            </div>
            
            <div class="section-title">💡 Idées Éditoriales du Jour</div>
            <div class="editorial-grid">
    """
    for plan in synthesis.get('editorial_plan', []):
        html += f"""
                <div class="editorial-col">
                    <div class="ed-title">{plan.get('subject', '')}</div>
                    <div class="ed-hook">"{plan.get('hook', '')}"</div>
                    <span class="ed-format">Format: {plan.get('format', '')}</span>
                </div>
        """
    html += """
            </div>
            
            <div class="section-title">📺 Recommandations Vidéos YouTube (10)</div>
    """
    for v in yt:
        html += f"""
            <div class="card">
                <span class="score-badge">Intérêt: {v.get('score', 0)}/10</span>
                <span class="badge badge-yt">YouTube</span>
                <div class="card-title">
                    <a href="{v.get('url', '#')}" target="_blank">{v.get('title', '')}</a>
                </div>
                <div class="card-meta">Chaîne: <strong>{v.get('channel_name', '')}</strong></div>
                <p class="card-summary">{v.get('summary', '')}</p>
            </div>
        """
        
    html += """
            <div class="section-title">🌐 Presse & Actualités Générales (40)</div>
    """
    
    # 10 de chaque catégorie
    categories = [("mondial", "Mondial", "badge-mondial"), ("international", "International", "badge-inter"), ("france", "France", "badge-france"), ("hdf", "Hauts-de-France", "badge-hdf")]
    for key, label, badge_style in categories:
        for item in actu.get(key, []):
            html += f"""
            <div class="card">
                <span class="badge {badge_style}">{label}</span>
                <div class="card-title">
                    <a href="{item.get('url', '#')}" target="_blank">{item.get('title', '')}</a>
                </div>
                <div class="card-meta">Source: <strong>{item.get('source', '')}</strong></div>
                <p class="card-summary">{item.get('summary', '')}</p>
            </div>
            """
            
    html += """
            <div class="section-title">🤖 Intelligence Artificielle (10)</div>
    """
    for item in ia:
        html += f"""
        <div class="card">
            <span class="score-badge">Éditorial: {item.get('score', 0)}/10</span>
            <span class="badge badge-ia">IA & Tech</span>
            <div class="card-title">
                <a href="{item.get('url', '#')}" target="_blank">{item.get('title', '')}</a>
            </div>
            <div class="card-meta">Techno/Modèle: <strong>{item.get('tool', '')}</strong></div>
            <p class="card-summary">{item.get('summary', '')}</p>
        </div>
        """
        
    html += """
            <div class="section-title">🌤️ Météo & Climat (10)</div>
    """
    for item in meteo:
        html += f"""
        <div class="card">
            <span class="badge badge-meteo">Météo & Climat</span>
            <div class="card-title">
                <a href="{item.get('url', '#')}" target="_blank">{item.get('title', '')}</a>
            </div>
            <div class="card-meta">Phénomène: <strong>{item.get('phenomenon', '')}</strong> | Zone: <strong>{item.get('location', '')}</strong></div>
            <p class="card-summary">{item.get('summary', '')}</p>
        </div>
        """
        
    html += """
            <footer>
                <p>Veille automatique générée le """ + date_str + """ par l'assistant Anti-Gravity</p>
            </footer>
        </div>
    </body>
    </html>
    """
    return html

# 6. Envoi de l'e-mail
def send_email(html_body, date_str):
    smtp_email = os.environ.get("SMTP_EMAIL", "gregory.langlet@sfr.fr")
    smtp_password = os.environ.get("SMTP_PASSWORD")
    
    if not smtp_password:
        print("[SMTP] ERREUR : SMTP_PASSWORD manquant dans l'environnement. Impossible d'envoyer le mail.")
        sys.exit(1)
        
    print(f"[SMTP] Connexion à smtp.sfr.fr pour envoi à {smtp_email}...")
    try:
        msg = MIMEMultipart('alternative')
        display_name = "Gregory LANGLET"
        msg['From'] = f"{display_name} <{smtp_email}>"
        msg['To'] = f"{display_name} <{smtp_email}>"
        msg['Subject'] = f"Veille Quotidienne Unifiee - {date_str}"
        msg['Message-ID'] = make_msgid()
        msg['Date'] = formatdate(localtime=True)
        msg['MIME-Version'] = '1.0'
        msg['X-Mailer'] = 'Python/smtplib (Linux)'
        
        msg.attach(MIMEText(html_body, 'html', 'utf-8'))
        
        with smtplib.SMTP_SSL("smtp.sfr.fr", 465) as server:
            server.login(smtp_email, smtp_password)
            server.sendmail(smtp_email, [smtp_email], msg.as_string())
        print("[SMTP] E-mail envoyé avec succès !")
    except Exception as e:
        print(f"[SMTP] Erreur d'envoi de l'e-mail : {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Superviseur Veille Globale")
    parser.add_argument("--dry-run", action="store_true", help="Génère le HTML en local sans envoyer de mail")
    args = parser.parse_args()
    
    date_str = get_date_fr()
    print(f"==========================================")
    print(f"Démarrage de la veille unifiée du {date_str}")
    print(f"==========================================")
    
    # 1. Scanne YouTube
    print("\n--- Étape 1 : YouTube Feed Scan ---")
    try:
        import fetch_youtube_feed
        fetch_youtube_feed.main()
    except Exception as e:
        print(f"Erreur lors du scan YouTube : {e}")
        
    yt_report = process_youtube_report()
    
    # 2. Collecte & Rédaction IA/Météo/Actu
    print("\n--- Étape 2 : Rédactions Thématiques ---")
    actu_report = build_actu_report(date_str)
    ia_report = build_ia_report(date_str)
    meteo_report = build_meteo_report(date_str)
    
    if not (actu_report and ia_report and meteo_report):
        print("Erreur : La collecte ou la rédaction IA a échoué. Arrêt.")
        sys.exit(1)
        
    # 3. Rédaction de la Synthèse
    print("\n--- Étape 3 : Synthèse ---")
    synthesis_report = build_synthesis(actu_report, ia_report, meteo_report, yt_report, date_str)
    
    if not synthesis_report:
        print("Erreur : Impossible de rédiger la synthèse. Arrêt.")
        sys.exit(1)
        
    # 4. Compilation HTML
    print("\n--- Étape 4 : Compilation HTML ---")
    html_output = compile_html(synthesis_report, actu_report, ia_report, meteo_report, yt_report, date_str)
    
    # 5. Envoi ou Sauvegarde locale
    if args.dry_run:
        output_file = "veille_globale_dryrun.html"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(html_output)
        print(f"\n[Terminé] Mode simulation : HTML écrit localement dans '{output_file}'")
    else:
        print("\n--- Étape 5 : Envoi de l'e-mail ---")
        send_email(html_output, date_str)
        print("\n[Terminé] Veille automatisée exécutée avec succès !")

if __name__ == "__main__":
    main()
