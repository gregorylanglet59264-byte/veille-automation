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
import re
import email.utils
from email.utils import make_msgid, formatdate

# Dictionnaires de traduction pour les dates dynamiques
MONTHS_FR = [
    "janvier", "février", "mars", "avril", "mai", "juin",
    "juillet", "août", "septembre", "octobre", "novembre", "décembre"
]

def get_date_fr():
    now = datetime.datetime.now()
    return f"{now.day} {MONTHS_FR[now.month - 1]} {now.year}"

# Helper pour filtrer les articles récents
def filter_recent_articles(articles, max_hours=24):
    recent = []
    now = datetime.datetime.now(datetime.timezone.utc)
    for art in articles:
        pub_str = art.get("date")
        if not pub_str:
            recent.append(art)
            continue
        try:
            pub_dt = email.utils.parsedate_to_datetime(pub_str)
            if pub_dt.tzinfo is None:
                pub_dt = pub_dt.replace(tzinfo=datetime.timezone.utc)
            else:
                pub_dt = pub_dt.astimezone(datetime.timezone.utc)
            
            age = now - pub_dt
            art["age_seconds"] = age.total_seconds()
            if age <= datetime.timedelta(hours=max_hours):
                recent.append(art)
        except Exception:
            recent.append(art)
    return recent

# 1. Collecte Google News RSS & Flux Directs récents
def fetch_google_news(query):
    feeds = {
        "Le Monde": "https://www.lemonde.fr/rss/une.xml",
        "FranceInfo": "https://www.francetvinfo.fr/titres.rss",
        "France 3 HDF": "https://france3-regions.francetvinfo.fr/hauts-de-france/rss",
        "PresseCitron": "https://www.presse-citron.net/feed/"
    }
    
    all_articles = []
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    for name, url in feeds.items():
        try:
            req = urllib.request.Request(url, headers={"User-Agent": user_agent})
            with urllib.request.urlopen(req, timeout=10) as response:
                xml_data = response.read()
            
            root = ET.fromstring(xml_data)
            for item in root.findall(".//item"):
                title = item.find("title").text if item.find("title") is not None else ""
                link = item.find("link").text if item.find("link") is not None else ""
                pub_date = item.find("pubDate").text if item.find("pubDate") is not None else ""
                all_articles.append({
                    "title": title,
                    "url": link,
                    "date": pub_date,
                    "source": name
                })
        except Exception as e:
            print(f"[RSS] Échec de récupération du flux {name} : {e}")
            
    # Filtrer d'abord à < 24h
    recent_articles = filter_recent_articles(all_articles, 24)
    # Fallback à 48h si on n'a pas assez d'articles récents
    if len(recent_articles) < 15:
        recent_articles = filter_recent_articles(all_articles, 48)
    if len(recent_articles) < 15:
        recent_articles = all_articles

    # Trier du plus récent au plus ancien
    recent_articles = sorted(recent_articles, key=lambda x: x.get("age_seconds", 999999))

    query_lower = query.lower()
    is_meteo = any(w in query_lower for w in ["météo", "meteo", "climat", "vigilance", "records", "intempéries", "canicule"])
    is_ia = any(re.search(r'\b' + w + r'\b', query_lower) for w in ["ai", "ia"]) or any(w in query_lower for w in ["models", "tools", "claude", "gemini", "llama", "deepseek", "chatgpt", "openai"])
    is_hdf = any(w in query_lower for w in ["hauts-de-france", "hdf", "lille", "pas-de-calais", "nord"])
    
    filtered = []
    
    if is_meteo:
        meteo_keywords = ["météo", "meteo", "climat", "température", "chaleur", "pluie", "inondation", "vent", "tempête", "orage", "vigilance", "sécheresse", "neige", "copernicus", "records", "noaa", "canicule"]
        for art in recent_articles:
            title_lower = art["title"].lower()
            if any(kw in title_lower for kw in meteo_keywords):
                filtered.append(art)
    elif is_ia:
        ia_keywords = ["ia", "ai", "chatgpt", "openai", "claude", "gemini", "llama", "deepseek", "anthropic", "copilot", "midjourney", "sora", "robot", "algorithme", "machine learning", "technologie"]
        for art in recent_articles:
            title_lower = art["title"].lower()
            has_ia = False
            for kw in ia_keywords:
                if kw in ["ia", "ai"]:
                    if re.search(r'\b' + kw + r'\b', title_lower):
                        has_ia = True
                        break
                else:
                    if kw in title_lower:
                        has_ia = True
                        break
            if has_ia:
                filtered.append(art)
    elif is_hdf:
        hdf_keywords = ["nord", "pas-de-calais", "picardie", "lille", "hdf", "amiens", "arras", "dunkerque", "douai", "calais", "somme", "aisne", "oise"]
        for art in recent_articles:
            if art["source"] == "France 3 HDF":
                filtered.append(art)
            else:
                title_lower = art["title"].lower()
                if any(kw in title_lower for kw in hdf_keywords):
                    filtered.append(art)
    else:
        # Actualités générales (Le Monde, FranceInfo)
        for art in recent_articles:
            if art["source"] in ["Le Monde", "FranceInfo"]:
                filtered.append(art)
                
    # Si on a trop peu de résultats ciblés, on comble avec des articles récents du Monde ou FranceInfo
    if len(filtered) < 15:
        seen_urls = {art["url"] for art in filtered}
        for art in recent_articles:
            if len(filtered) >= 20:
                break
            if art["url"] not in seen_urls:
                if is_ia and art["source"] != "PresseCitron":
                    continue
                filtered.append(art)
                seen_urls.add(art["url"])
                
    return filtered[:25]

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
            with urllib.request.urlopen(req, timeout=90) as response:
                res_data = json.loads(response.read().decode("utf-8"))
                text = res_data["candidates"][0]["content"]["parts"][0]["text"]
                return text.replace('\ufeff', '').replace('\ufffe', '')
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
            "model": "deepseek/deepseek-chat",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        }
        import urllib.error
        try:
            req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=90) as response:
                res_data = json.loads(response.read().decode("utf-8"))
                text = res_data["choices"][0]["message"]["content"]
                return text.replace('\ufeff', '').replace('\ufffe', '')
        except urllib.error.HTTPError as http_err:
            print(f"[LLM] Erreur HTTP OpenRouter API ({http_err.code})")
            try:
                err_body = http_err.read().decode("utf-8")
                print(f"[LLM] Corps de l'erreur HTTP : {err_body[:600]}")
            except Exception:
                pass
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
        "RÈGLE CRITIQUE POUR L'URL : Tu DOIS copier-coller EXACTEMENT sans modification la valeur de la clé 'url' de l'article source choisi. N'invente pas d'URL, ne la modifie pas.\n"
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
        "RÈGLE CRITIQUE POUR L'URL : Tu DOIS copier-coller EXACTEMENT sans modification la valeur de la clé 'url' de l'article source choisi. N'invente pas d'URL, ne la modifie pas.\n"
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
        "RÈGLE CRITIQUE POUR L'URL : Tu DOIS copier-coller EXACTEMENT sans modification la valeur de la clé 'url' de l'article source choisi. N'invente pas d'URL, ne la modifie pas.\n"
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
    print("[Rapport] Chargement, notation et rédaction Vidéos YouTube...")
    try:
        with open("youtube_recommandations.json", "r", encoding="utf-8") as f:
            videos = json.load(f)
        
        if not videos:
            return []
            
        # On va passer les vidéos à l'IA pour qu'elle sélectionne et justifie les 10 meilleures
        system_prompt = (
            "Tu es un analyste éditorial média senior. Ton rôle est de trier, noter et résumer les vidéos récentes proposées.\n"
            "RÈGLE CRITIQUE : Tu DOIS sélectionner les 10 vidéos les plus pertinentes et intéressantes de la liste fournie (ou toutes si moins de 10) et les ordonner par note décroissante.\n"
            "Pour chaque vidéo sélectionnée, fournis :\n"
            "1. Une note d'intérêt de 0 à 10 pour Gregory (expert météo, IA, programmation et automatisation).\n"
            "2. Un résumé de 2-3 phrases en français expliquant POURQUOI il doit regarder cette vidéo en se basant sur son titre, sa chaîne et sa description.\n"
            "Format de sortie attendu : JSON uniquement avec la structure suivante (sans blocs ```json) :\n"
            "[\n"
            "  {\n"
            "    \"channel_name\": \"...\",\n"
            "    \"category\": \"...\",\n"
            "    \"title\": \"...\",\n"
            "    \"url\": \"...\",\n"
            "    \"score\": 9.5,\n"
            "    \"summary\": \"...\"\n"
            "  },\n"
            "  ... (jusqu'à 10 éléments)\n"
            "]"
        )
        
        # Pour limiter la taille des tokens, on ne passe que les champs essentiels
        input_data = []
        for v in videos:
            input_data.append({
                "channel_name": v.get("channel_name", ""),
                "category": v.get("category", ""),
                "title": v.get("title", ""),
                "url": v.get("url", ""),
                "description": v.get("description", "")
            })
            
        user_prompt = f"Vidéos récentes récoltées :\n{json.dumps(input_data, ensure_ascii=False)}"
        
        response = call_llm(system_prompt, user_prompt)
        if response:
            response_clean = response.strip().replace("```json", "").replace("```", "")
            return json.loads(response_clean)
            
        # Fallback si l'IA échoue : tri classique par score d'origine
        print("Fallback YouTube : Échec de l'IA, utilisation du tri par défaut.")
        top_videos = sorted(videos, key=lambda x: -x.get("score", 0))[:10]
        return top_videos
    except Exception as e:
        print(f"Erreur lors du traitement des recommandations YouTube : {e}")
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
    
    # Gmail optionnel (fonctionne depuis GitHub Actions contrairement à SFR)
    gmail_email = os.environ.get("GMAIL_EMAIL", "langlet.gregory@gmail.com")
    gmail_password = os.environ.get("GMAIL_APP_PASSWORD")
    
    # Récupération des destinataires (par défaut toi, sinon liste séparée par des virgules)
    recipients_raw = os.environ.get("RECIPIENT_EMAILS", smtp_email)
    recipients = [r.strip() for r in recipients_raw.split(",") if r.strip()]

    import base64
    import uuid
    
    # Suppression totale de tout BOM ou caractère non-ASCII parasite
    html_body = html_body.replace('\ufeff', '').replace('\ufffe', '')
    
    sender = gmail_email if gmail_password else smtp_email
    boundary = uuid.uuid4().hex
    filename = f"veille_globale_{datetime.datetime.now().strftime('%Y_%m_%d')}.html"
    
    # Encodage complet en base64 pour garantir que tout passe en ASCII pur sur le canal SMTP
    html_b64 = base64.b64encode(html_body.encode('utf-8')).decode('ascii')
    text_body = f"Bonjour,\n\nVeuillez trouver ci-joint le rapport de veille unifiee pour aujourd'hui ({date_str}).\n\nCordialement,\nL'assistant de Veille"
    text_b64 = base64.b64encode(text_body.encode('utf-8')).decode('ascii')
    
    # Construction du MIME brut
    raw_message = (
        f'From: Gregory LANGLET <{sender}>\r\n'
        f'To: {", ".join(recipients)}\r\n'
        f'Subject: Veille Quotidienne Unifiee - {date_str}\r\n'
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
    
    # Gmail (seul relais fiable depuis GitHub Actions — SFR bloque les IP cloud avec erreur 550)
    if not gmail_password:
        print("[SMTP] ERREUR : GMAIL_APP_PASSWORD non configure. Impossible d'envoyer.")
        sys.exit(1)
        
    print(f"[SMTP] Envoi via Gmail a {', '.join(recipients)}...")
    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(gmail_email, gmail_password)
            server.sendmail(gmail_email, recipients, raw_message.encode('ascii'))
        print("[SMTP] E-mail envoye avec succes via Gmail !")
    except Exception as e:
        print(f"[SMTP] Erreur Gmail : {e}")
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
