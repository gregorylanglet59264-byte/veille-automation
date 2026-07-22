# -*- coding: utf-8 -*-
"""
veille_orchestrator.py
Orchestrateur local de collecte de données pour la veille quotidienne.
Interroge gratuitement les flux RSS de Google News, scrape le forum Infoclimat,
pilote le collecteur Twitter, gère le scan YouTube des abonnements et la veille des bons plans,
puis compile le tout au format JSON brut attendu par les compétences de l'agent.
"""
import os
import sys
import json
import argparse
import datetime
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import email.utils
import re
import subprocess

def clean_xml_text(text):
    if not text:
        return ""
    return text.strip()

def fetch_rss_google_news(query, max_items=15, timeframe="1d"):
    full_query = query
    if timeframe and "when:" not in query:
        full_query = f"{query} when:{timeframe}"
        
    encoded_query = urllib.parse.quote(full_query)
    url = f"https://news.google.com/rss/search?q={encoded_query}&hl=fr&gl=FR&ceid=FR:fr"
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    
    articles = []
    try:
        req = urllib.request.Request(url, headers={"User-Agent": user_agent})
        with urllib.request.urlopen(req, timeout=15) as response:
            xml_data = response.read()
        
        root = ET.fromstring(xml_data)
        now = datetime.datetime.now(datetime.timezone.utc)
        
        for item in root.findall(".//item"):
            if len(articles) >= max_items:
                break
                
            title = clean_xml_text(item.find("title").text) if item.find("title") is not None else ""
            link = clean_xml_text(item.find("link").text) if item.find("link") is not None else ""
            pub_date = clean_xml_text(item.find("pubDate").text) if item.find("pubDate") is not None else ""
            
            # Strict date validation
            if pub_date:
                try:
                    pub_dt = email.utils.parsedate_to_datetime(pub_date)
                    if pub_dt.tzinfo is None:
                        pub_dt = pub_dt.replace(tzinfo=datetime.timezone.utc)
                    else:
                        pub_dt = pub_dt.astimezone(datetime.timezone.utc)
                        
                    age = now - pub_dt
                    max_hours = 24 if timeframe == "1d" else 168
                    if age > datetime.timedelta(hours=max_hours):
                        continue
                except Exception:
                    pass
            
            source = "Google News"
            source_el = item.find("source")
            if source_el is not None and source_el.text:
                source = source_el.text.strip()
                suffix = f" - {source}"
                if title.endswith(suffix):
                    title = title[:-len(suffix)].strip()
            
            articles.append({
                "title": title,
                "url": link,
                "date": pub_date,
                "source": source
            })
    except Exception as e:
        print(f"[RSS] Échec de la requête pour '{query}': {e}", file=sys.stderr)
        
    # Auto-decode Google News RSS links to clean direct URLs
    if articles:
        try:
            from googlenewsdecoder.decoderv4 import decode_google_news_url
            raw_urls = [a["url"] for a in articles]
            decoded_res = decode_google_news_url(raw_urls)
            for idx, res_item in enumerate(decoded_res):
                if isinstance(res_item, dict) and res_item.get("status") and res_item.get("url"):
                    articles[idx]["url"] = res_item.get("url")
        except Exception as err:
            print(f"[RSS Decoder] Warning: {err}", file=sys.stderr)

    return articles

def format_articles_to_text(articles, label):
    if not articles:
        return f"=== {label} ===\nAucun bon plan récent ou offre trouvé."
    
    text_lines = [f"=== {label} ==="]
    for art in articles:
        text_lines.append(f"- {art['title']}")
        text_lines.append(f"  Source: {art['source']} | Date: {art['date']}")
        text_lines.append(f"  URL: {art['url']}")
    return "\n".join(text_lines)

def scrape_infoclimat_forum(max_topics=2):
    print("[Infoclimat] Scraping du forum de tendances à long terme...")
    index_url = "https://forums.infoclimat.fr/f/forum/20-evolution-%C3%A0-plus-long-terme/"
    user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    
    try:
        req = urllib.request.Request(index_url, headers={'User-Agent': user_agent})
        with urllib.request.urlopen(req, timeout=15) as response:
            html = response.read().decode('utf-8', errors='ignore')
        
        # Extraire les URLs de sujets
        topic_urls = re.findall(r'href="(https://forums\.infoclimat\.fr/t/[^"]+)"', html)
        # Supprimer les doublons en préservant l'ordre
        seen = set()
        unique_topics = []
        for url in topic_urls:
            base_url = url.split('?')[0].rstrip('/')
            if base_url not in seen:
                seen.add(base_url)
                unique_topics.append(base_url)
        
        infoclimat_data = ["=== ANALYSES INFOCLIMAT FORUM ==="]
        
        for idx, topic_url in enumerate(unique_topics[:max_topics]):
            decoded_topic = urllib.parse.unquote(topic_url)
            topic_title = decoded_topic.rstrip('/').split('/')[-1].replace('-', ' ').title()
            topic_title = re.sub(r'^\d+\s*', '', topic_title) # Enlever ID de sujet
            
            print(f"[Infoclimat] Scraping du sujet : {topic_title}")
            try:
                # Charger la première page du sujet pour extraire la pagination et aller à la dernière page
                t_req = urllib.request.Request(topic_url, headers={'User-Agent': user_agent})
                with urllib.request.urlopen(t_req, timeout=15) as t_resp:
                    topic_html = t_resp.read().decode('utf-8', errors='ignore')
                
                pages = re.findall(r'\?page=(\d+)', topic_html)
                last_page = max(int(p) for p in pages) if pages else 1
                
                # Charger les commentaires de la dernière page
                last_page_url = f"{topic_url}?page={last_page}"
                p_req = urllib.request.Request(last_page_url, headers={'User-Agent': user_agent})
                with urllib.request.urlopen(p_req, timeout=15) as p_resp:
                    page_html = p_resp.read().decode('utf-8', errors='ignore')
                
                comments = re.findall(r'<div[^>]*data-role=["\']commentContent["\'][^>]*>(.*?)</div>\s*</div>', page_html, re.DOTALL)
                authors = re.findall(r'<strong>\s*<a href=[^>]*class=["\']ipsType_break["\'][^>]*>(.*?)</a>', page_html)
                
                cleaned_comments = []
                for c_idx, comment in enumerate(comments[-5:]): # Garder les 5 derniers messages
                    clean_comment = re.sub(r'<br\s*/?>', '\n', comment)
                    clean_comment = re.sub(r'<[^>]+>', '', clean_comment).strip()
                    clean_comment = re.sub(r'\n\s*\n', '\n', clean_comment)
                    author = authors[c_idx] if c_idx < len(authors) else "Membre"
                    # Raccourcir les messages trop longs
                    if len(clean_comment) > 300:
                        clean_comment = clean_comment[:297] + "..."
                    cleaned_comments.append(f"  * Auteur: {author} | Message: {clean_comment.replace('\n', ' ')}")
                
                infoclimat_data.append(f"\nSujet : {topic_title}\nURL : {topic_url}")
                infoclimat_data.extend(cleaned_comments)
            except Exception as e:
                print(f"[Infoclimat] Erreur lors du scraping du sujet {topic_title}: {e}")
                
        return "\n".join(infoclimat_data)
    except Exception as e:
        print(f"[Infoclimat] Échec global de récupération du forum: {e}", file=sys.stderr)
        return "=== ANALYSES INFOCLIMAT FORUM ===\nÉchec du scraping des discussions."

def fetch_local_tweets():
    print("[Twitter] Lancement du script de collecte locale des tweets...")
    automation_dir = r"C:\Users\grego\Documents\METEO_CLIMAT\veille-automation"
    latest_tweets_file = os.path.join(automation_dir, "data", "latest_tweets.json")
    
    # 1. Lancer fetch_tweets.py via subprocess
    try:
        script_path = os.path.join(automation_dir, "fetch_tweets.py")
        if os.path.exists(script_path):
            print(f"[Twitter] Exécution de fetch_tweets.py (heures=6)...")
            subprocess.run([sys.executable, script_path, "--hours", "6.0"], cwd=automation_dir, timeout=60, check=True)
        else:
            print(f"[Twitter] Script fetch_tweets.py introuvable à {script_path}")
    except Exception as e:
        print(f"[Twitter] Erreur d'exécution de fetch_tweets.py : {e}")
        
    # 2. Lire le fichier généré
    twitter_data_text = ["=== ALERTES TERRAIN & RÉSEAUX (TWITTER/X) ==="]
    if os.path.exists(latest_tweets_file):
        try:
            with open(latest_tweets_file, "r", encoding="utf-8") as f:
                tweets = json.load(f)
            
            for tw in tweets[:12]:
                text = tw.get("text", "").replace('\n', ' ').strip()
                username = tw.get("username", tw.get("name", "MeteoAlert"))
                created_at = tw.get("created_at", "Récemment")
                url = tw.get("url", f"https://twitter.com/{username}")
                twitter_data_text.append(f"- @{username} : {text}\n  Date: {created_at} | URL: {url}")
        except Exception as e:
            print(f"[Twitter] Erreur de lecture des tweets: {e}")
    else:
        twitter_data_text.append("Aucun tweet de veille collecté ou fichier latest_tweets.json manquant.")
        
    return "\n".join(twitter_data_text)

def process_actu():
    print("Collecte du mode actualités générales...")
    queries = {
        "actu_mondial": ('"monde actualités" OR "breaking news"', "DÉPÊCHES MONDE (RSS)"),
        "actu_international": ('"actualités internationales" OR "géopolitique"', "DÉPÊCHES INTERNATIONALES (RSS)"),
        "actu_france": ('"actualités France"', "DÉPÊCHES FRANCE (RSS)"),
        "actu_hdf": ('"actualités Hauts-de-France" OR "Nord Pas-de-Calais" OR "Picardie" OR "Lille"', "DÉPÊCHES HAUTS-DE-FRANCE (RSS)"),
        "direct_rss": ('"Le Monde" OR "FranceInfo" actualités', "FLUX RSS DIRECTS (ACTU)")
    }
    
    result = {}
    for key, (query, label) in queries.items():
        articles = fetch_rss_google_news(query)
        result[key] = {
            "agent": f"Sous-agent Actu — {key.replace('actu_', '').capitalize()}",
            "status": "success",
            "data": format_articles_to_text(articles, label)
        }
    return result

def process_ia():
    print("Collecte du mode IA & Tech...")
    queries = {
        "ia_modeles": ("(GPT OR Claude OR Gemini OR Llama OR DeepSeek OR Qwen) (model OR release OR AI)", "MODÈLES & RELEASES (RSS)"),
        "ia_outils": ("(github OR cursor OR openrouter OR ollama OR mcp) (AI OR tech)", "OUTILS & ÉCOSYSTEME (RSS)"),
        "ia_recherche": ("(research OR benchmark OR arxiv) (AI OR \"intelligence artificielle\")", "RECHERCHE & SCIENTIFIQUE (RSS)"),
        "ia_strategie": ("(investment OR partnership OR regulation) (AI OR \"intelligence artificielle\")", "ENTREPRISES & STRATÉGIE (RSS)"),
        "direct_rss": ('"Hacker News" OR PresseCitron "intelligence artificielle" OR tech', "FLUX RSS DIRECTS (IA)")
    }
    
    result = {}
    for key, (query, label) in queries.items():
        articles = fetch_rss_google_news(query)
        result[key] = {
            "agent": f"Sous-agent IA — {key.replace('ia_', '').capitalize()}",
            "status": "success",
            "data": format_articles_to_text(articles, label)
        }
    return result

def process_meteo():
    print("Collecte du mode Météo & Climat...")
    queries = {
        "meteo_france": ('"météo france" OR vigilance OR bulletin', "MÉTÉO FRANCE (RSS)"),
        "meteo_previsions": ("prévisions météo (canicule OR orage OR tempête OR sécheresse OR feux)", "PRÉVISIONS FRANCE (RSS)"),
        "meteo_modeles": ("météo (AROME OR ARPEGE OR GFS OR IFS OR ICON)", "MODÈLES NUMÉRIQUES (RSS)"),
        "meteo_degats": ("météo (dégâts OR tempête OR inondation OR grêle OR victimes)", "INTEMPÉRIES & DÉGÂTS (RSS)"),
        "meteo_monde": ("météo (cyclone OR typhon OR record OR température OR catastrophe)", "MÉTÉO MONDIALE (RSS)"),
        "meteo_climat": ('climat (anomalie OR Copernicus OR NOAA OR OMM OR "El Nino")', "CLIMAT & ANOMALIES (RSS)")
    }
    
    result = {}
    for key, (query, label) in queries.items():
        articles = fetch_rss_google_news(query)
        # Pour les modèles, on adjoint aussi les discussions du forum Infoclimat !
        if key == "meteo_modeles":
            infoclimat_text = scrape_infoclimat_forum()
            data_text = format_articles_to_text(articles, label) + "\n\n" + infoclimat_text
        else:
            data_text = format_articles_to_text(articles, label)
            
        result[key] = {
            "agent": f"Sous-agent Météo — {key.replace('meteo_', '').capitalize()}",
            "status": "success",
            "data": data_text
        }
        
    # Collecter les tweets en direct pour remplir la section twitter_alerts !
    twitter_text = fetch_local_tweets()
    result["twitter_alerts"] = {
        "agent": "Sous-agent Météo — Twitter Alerts",
        "status": "success",
        "data": twitter_text
    }
    
    return result

def process_hdf():
    print("Collecte du mode Hauts-de-France...")
    queries = {
        "hdf_politique_eco": ('(économie OR politique OR entreprises OR investissements) (Hauts-de-France OR "Nord Pas-de-Calais")', "HDF POLITIQUE & ÉCONOMIE (RSS)"),
        "hdf_societe_faits_divers": ('("faits divers" OR société) (Hauts-de-France OR "Nord Pas-de-Calais")', "HDF SOCIÉTÉ & FAITS DIVERS (RSS)"),
        "hdf_culture_tourisme": ('(culture OR tourisme OR patrimoine) (Hauts-de-France OR "Nord Pas-de-Calais")', "HDF CULTURE & TOURISME (RSS)"),
        "hdf_transports_infra": ('(transports OR routes OR trains OR travaux) (Hauts-de-France OR "Nord Pas-de-Calais")', "HDF TRANSPORTS & INFRA (RSS)"),
        "direct_rss": ('"France 3 HDF" OR "Nord Eclair" OR "Voix du Nord"', "FLUX RSS DIRECTS (HDF)")
    }
    
    result = {}
    for key, (query, label) in queries.items():
        articles = fetch_rss_google_news(query)
        result[key] = {
            "agent": f"Sous-agent HDF — {key.replace('hdf_', '').capitalize()}",
            "status": "success",
            "data": format_articles_to_text(articles, label)
        }
    return result

def process_youtube():
    print("[YouTube] Lancement du scan des abonnements YouTube...")
    automation_dir = r"C:\Users\grego\Documents\METEO_CLIMAT\veille-automation"
    yt_script = os.path.join(automation_dir, "fetch_youtube_feed.py")
    
    if os.path.exists(yt_script):
        try:
            print("[YouTube] Exécution de fetch_youtube_feed.py...")
            subprocess.run([sys.executable, yt_script], cwd=automation_dir, timeout=60, check=True)
            
            # Copier les résultats générés vers notre répertoire scratch local
            import shutil
            for filename in ["youtube_recommandations.json", "youtube_recommandations.md"]:
                src = os.path.join(automation_dir, filename)
                dest = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
                if os.path.exists(src):
                    shutil.copy(src, dest)
                    print(f"[YouTube] Fichier copié : {src} -> {dest}")
            return True
        except Exception as e:
            print(f"[YouTube] Erreur lors du scan YouTube : {e}")
    else:
        print(f"[YouTube] Script introuvable à {yt_script}")
    return False

def process_bonsplans():
    print("Collecte du mode Bons Plans IA & Outils...")
    query = '("ChatGPT" OR "Claude" OR "Gemini" OR "Cursor" OR "DeepSeek" OR "Midjourney" OR "outil IA") (promo OR promotion OR abonnement OR offre OR gratuit OR "bon plan" OR réduction OR "code promo" OR "moins cher")'
    articles = fetch_rss_google_news(query, max_items=12, timeframe="7d")
    
    result = {
        "bonsplans": {
            "agent": "Sous-agent Bons Plans IA",
            "status": "success",
            "data": format_articles_to_text(articles, "BONS PLANS & OFFRES IA (RSS)")
        }
    }
    return result

def main():
    parser = argparse.ArgumentParser(description="Collecteur de veille locale unifiée")
    parser.add_argument("--mode", required=True, choices=["actu", "ia", "meteo", "hdf", "youtube", "bonsplans"], help="Mode de veille à collecter")
    args = parser.parse_args()
    
    mode = args.mode
    if mode == "actu":
        data = process_actu()
        filename = "scout_actu_raw.json"
    elif mode == "ia":
        data = process_ia()
        filename = "scout_ia_raw.json"
    elif mode == "meteo":
        data = process_meteo()
        filename = "scout_meteo_raw.json"
    elif mode == "hdf":
        data = process_hdf()
        filename = "scout_hdf_raw.json"
    elif mode == "youtube":
        process_youtube()
        return
    elif mode == "bonsplans":
        data = process_bonsplans()
        filename = "scout_bonsplans_raw.json"
    
    filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"Collecte terminée avec succès ! Données écrites dans : {filepath}")

if __name__ == "__main__":
    main()
