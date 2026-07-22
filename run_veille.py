# -*- coding: utf-8 -*-
"""
run_veille.py
Superviseur autonome de veille globale.
Collecte les données via flux RSS directs (BFM TV, Le Figaro, Le Monde, FranceInfo, Libération,
L'Obs, France 3 HDF, France 3 Nord-Pas-de-Calais, Hacker News),
appelle l'API de l'IA (Gemini ou OpenRouter) pour rédiger les rapports et la synthèse de 10 éléments,
compile le tout en HTML premium responsive et l'envoie par e-mail via SMTP Gmail.
"""
import os
import sys
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))
except ImportError:
    pass
import json
import time
import argparse
import datetime
import urllib.request
import urllib.parse
import urllib.error
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
def filter_recent_articles(articles, max_hours=48):
    """Filtre souple : on garde tout article de moins de 48h.
    ponytail: le filtre strict à 24h causait des listes vides sur GitHub Actions car
    les dates des flux RSS peuvent avoir un léger décalage. Le LLM se charge du tri final."""
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

# Flux RSS nationaux (presse générale)
FEEDS_NATIONAL = {
    "Le Monde":    "https://www.lemonde.fr/rss/une.xml",
    "FranceInfo":  "https://www.francetvinfo.fr/titres.rss",
    "BFM TV":      "https://www.bfmtv.com/rss/news-24-7/",
    "Le Figaro":   "https://www.lefigaro.fr/rss/figaro_actualites.xml",
    "Liberation":  "https://www.liberation.fr/arc/outboundfeeds/rss/?outputType=xml",
    "L'Obs":       "https://www.nouvelobs.com/rss.xml",
}
# Flux RSS Hauts-de-France uniquement
FEEDS_HDF = {
    "France 3 HDF":    "https://france3-regions.francetvinfo.fr/hauts-de-france/rss",
    "France 3 NPC":    "https://france3-regions.francetvinfo.fr/hauts-de-france/nord-pas-de-calais/rss",
    "La Voix du Nord": "https://www.lavoixdunord.fr/arc/outboundfeeds/rss/?outputType=xml",
}
# Flux RSS IA / Tech
FEEDS_IA = {
    "Hacker News":      "https://hnrss.org/frontpage",
    "PresseCitron":     "https://www.presse-citron.net/feed/",
    "Numerama":         "https://www.numerama.com/feed/",
    "TechCrunch":       "https://techcrunch.com/feed/",
    "MIT Tech Review":  "https://www.technologyreview.com/feed/",
}
# Flux RSS Bons Plans IA uniquement
FEEDS_BONSPLANS = {
    "ProductHunt":  "https://www.producthunt.com/feed",
    "PresseCitron": "https://www.presse-citron.net/feed/",
    "Numerama":     "https://www.numerama.com/feed/",
    "TechCrunch":   "https://techcrunch.com/feed/",
}
# Flux RSS Météo / Climat
FEEDS_METEO = {
    "FranceInfo":       "https://www.francetvinfo.fr/titres.rss",
    "La Chaîne Météo": "https://www.lachainemeteo.com/rss/actualites.xml",
    "BFM TV":           "https://www.bfmtv.com/rss/news-24-7/",
    "Science & Vie":    "https://www.science-et-vie.com/feed",
}
# Flux RSS Intempéries & Cyclones (dédiés)
FEEDS_INTEMPERIES = {
    "La Chaîne Météo": "https://www.lachainemeteo.com/rss/actualites.xml",
    "FranceInfo":       "https://www.francetvinfo.fr/titres.rss",
    "BFM TV":           "https://www.bfmtv.com/rss/news-24-7/",
    "Le Monde":         "https://www.lemonde.fr/rss/une.xml",
}

def _fetch_feeds(feeds, max_articles=50, max_hours=48):
    """Collecte RSS générique depuis un dict {nom: url}."""
    all_articles = []
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    for name, url in feeds.items():
        try:
            req = urllib.request.Request(url, headers={"User-Agent": user_agent})
            with urllib.request.urlopen(req, timeout=12) as response:
                xml_data = response.read()
            root = ET.fromstring(xml_data)
            for item in root.findall(".//item"):
                title = item.find("title").text if item.find("title") is not None else ""
                link = item.find("link").text if item.find("link") is not None else ""
                pub_date = item.find("pubDate").text if item.find("pubDate") is not None else ""
                all_articles.append({
                    "title": title.strip() if title else "",
                    "url": link,
                    "date": pub_date,
                    "source": name
                })
        except Exception as e:
            print(f"[RSS] Flux {name} inaccessible : {e}")
    print(f"[RSS] {len(feeds)} flux → {len(all_articles)} articles bruts")
    recent = filter_recent_articles(all_articles, max_hours)
    recent = sorted(recent, key=lambda x: x.get("age_seconds", 999999))
    print(f"[RSS] {len(recent)} articles retenus apres filtre {max_hours}h")
    return recent[:max_articles]

# ponytail: conservé pour compatibilité avec build_ia_report, build_meteo_report, build_intemperies_report
def fetch_google_news(query):
    """Collecte depuis les flux nationaux + IA selon le contexte."""
    feeds = {**FEEDS_NATIONAL, **FEEDS_IA, **FEEDS_METEO}
    return _fetch_feeds(feeds, max_articles=50)

def _repair_truncated_json(text):
    """Tente de réparer un JSON tronqué en fermant les structures ouvertes."""
    text = text.strip()
    # Supprimer la dernière entrée incomplète
    for cutoff in [',', '{', '[']:
        idx = text.rfind(cutoff)
        if idx > 0:
            candidate = text[:idx]
            opens = candidate.count('{') - candidate.count('}')
            close_obj = '}' * max(0, opens)
            opens_arr = candidate.count('[') - candidate.count(']')
            close_arr = ']' * max(0, opens_arr)
            repaired = candidate + close_obj + close_arr
            try:
                return json.loads(repaired, strict=False)
            except Exception:
                continue
    return None

# 2. Appel API IA (Gemini ou OpenRouter) sans dépendances lourdes
def call_llm(system_prompt, user_prompt):
    gemini_key = (os.environ.get("GEMINI_API_KEY") or "").strip()
    openrouter_key = (os.environ.get("OPENROUTER_API_KEY") or "").strip()

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
            "model": "deepseek/deepseek-v4-flash",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        }
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

def llm_parse_json(system_prompt, user_prompt, label="", retries=3, delay=20):
    """Appelle call_llm et parse le JSON. Retry x3 si réponse vide ou JSON invalide. Repair auto si tronqué."""
    for attempt in range(retries):
        response = call_llm(system_prompt, user_prompt)
        if not response or not response.strip():
            print(f"[LLM] Tentative {attempt+1}/{retries} : réponse vide pour {label}.")
        else:
            response_clean = response.strip().replace("```json", "").replace("```", "")
            try:
                return json.loads(response_clean, strict=False)
            except json.JSONDecodeError as e:
                print(f"[LLM] Tentative {attempt+1}/{retries} : JSON invalide pour {label} : {e}")
                # Tentative de réparation si JSON tronqué
                repaired = _repair_truncated_json(response_clean)
                if repaired is not None:
                    print(f"[LLM] JSON réparé automatiquement pour {label}.")
                    return repaired
        if attempt < retries - 1:
            print(f"[LLM] Nouvelle tentative dans {delay}s...")
            time.sleep(delay)
    print(f"[LLM] ERREUR : {retries} tentatives échouées pour {label}.")
    return None

# 3. Rédacteurs thématiques
def build_actu_report(date_str):
    print("[Rapport] Collecte et rédaction Actualités...")
    # Collectes séparées : national d'un côté, HDF de l'autre (flux dédiés)
    raw_national = _fetch_feeds({**FEEDS_NATIONAL}, max_articles=50)
    raw_hdf      = _fetch_feeds(FEEDS_HDF, max_articles=50)
    raw_data = {
        "mondial":       raw_national,
        "international": raw_national,
        "france":        raw_national,
        "hdf":           raw_hdf,   # UNIQUEMENT des articles des flux HDF
    }
    system_prompt = (
        "Tu es un analyste de presse senior. Ton rôle est de trier et de synthétiser les actualités fournies.\n"
        "RÈGLE ABSOLUE N°1 : Ne conserver QUE des informations et articles publiés depuis MOINS DE 48 HEURES.\n"
        "RÈGLE CRITIQUE : Tu DOIS lister jusqu'à 10 articles pertinents pour chaque catégorie.\n"
        "Pour chaque article, fournis son titre en français, sa source, son URL d'origine et une courte description (1 à 2 lignes).\n"
        "RÈGLE HAUTS-DE-FRANCE : La clé 'hdf' doit contenir EXCLUSIVEMENT des articles parlant de la région Hauts-de-France (Nord, Pas-de-Calais, Somme, Aisne, Oise) : faits divers, société, emploi, élus locaux, événements régionaux. N'inclus JAMAIS un article national dans 'hdf'.\n"
        "RÈGLE CRITIQUE POUR L'URL : Tu DOIS copier-coller EXACTEMENT sans modification la valeur de la clé 'url'. N'invente pas d'URL.\n"
        "Format de sortie attendu : JSON uniquement (sans blocs ```json) :\n"
        "{\n"
        "  \"mondial\": [ {\"title\": \"...\", \"source\": \"...\", \"url\": \"...\", \"summary\": \"...\"}, ... ],\n"
        "  \"international\": [ ... ],\n"
        "  \"france\": [ ... ],\n"
        "  \"hdf\": [ ... ]\n"
        "}"
    )
    user_prompt = f"Données récoltées pour le {date_str} :\n{json.dumps(raw_data, ensure_ascii=False)}"
    return llm_parse_json(system_prompt, user_prompt, label="build_actu_report")

def build_ia_report(date_str):
    print("[Rapport] Collecte et rédaction Intelligence Artificielle...")
    raw_articles = _fetch_feeds(FEEDS_IA, max_articles=50, max_hours=48)

    system_prompt = (
        "Tu es un analyste IA senior. Ton rôle est de sélectionner et décrire les nouveautés majeures de l'écosystème IA.\n"
        "RÈGLE ABSOLUE N°1 : Ne conserver QUE des nouveautés publiées depuis MOINS DE 48 HEURES.\n"
        "RÈGLE CRITIQUE : Tu DOIS lister jusqu'à 15 actualités/outils majeurs.\n"
        "Pour chaque élément, fournis un titre, l'outil/modèle concerné, sa description technique succincte, son URL et une note d'intérêt éditorial /10.\n"
        "RÈGLE CRITIQUE POUR L'URL : Tu DOIS copier-coller EXACTEMENT sans modification la valeur de la clé 'url' de l'article source choisi. N'invente pas d'URL, ne la modifie pas.\n"
        "Format de sortie attendu : JSON uniquement avec la structure suivante (sans blocs ```json) :\n"
        "[\n"
        "  {\"title\": \"...\", \"tool\": \"...\", \"summary\": \"...\", \"url\": \"...\", \"score\": 8.5},\n"
        "  ...\n"
        "]"
    )
    user_prompt = f"Données récoltées pour le {date_str} :\n{json.dumps(raw_articles, ensure_ascii=False)}"
    return llm_parse_json(system_prompt, user_prompt, label="build_ia_report")

def build_meteo_report(date_str):
    print("[Rapport] Collecte et rédaction Météo & Climat...")
    raw_articles = _fetch_feeds(FEEDS_METEO, max_articles=40, max_hours=48)

    system_prompt = (
        "Tu es un prévisionniste météo senior. Ton rôle est de lister les événements météo et climatologiques clés.\n"
        "RÈGLE ABSOLUE N°1 : Ne conserver QUE des événements publiés depuis MOINS DE 48 HEURES.\n"
        "RÈGLE CRITIQUE : Tu DOIS lister jusqu'à 15 actualités/vigilances/records liés à la météo ou au climat.\n"
        "EXCLURE : les articles sans rapport avec la météo ou le climat.\n"
        "Pour chaque élément, fournis un titre, la zone géographique, le phénomène concerné, sa description détaillée et son URL source.\n"
        "RÈGLE CRITIQUE POUR L'URL : Tu DOIS copier-coller EXACTEMENT sans modification la valeur de la clé 'url'. N'invente pas d'URL.\n"
        "Format de sortie attendu : JSON uniquement (sans blocs ```json) :\n"
        "[\n"
        "  {\"title\": \"...\", \"location\": \"...\", \"phenomenon\": \"...\", \"summary\": \"...\", \"url\": \"...\"},\n"
        "  ...\n"
        "]"
    )
    user_prompt = f"Données récoltées pour le {date_str} :\n{json.dumps(raw_articles, ensure_ascii=False)}"
    return llm_parse_json(system_prompt, user_prompt, label="build_meteo_report")

def build_intemperies_report(date_str):
    print("[Rapport] Collecte et rédaction Intempéries & Cyclones...")
    raw_articles = _fetch_feeds(FEEDS_INTEMPERIES, max_articles=40, max_hours=48)

    system_prompt = (
        "Tu es un expert en risques naturels et météorologiques. Ton rôle est de lister les événements d'intempéries et d'activité cyclonique clés.\n"
        "RÈGLE ABSOLUE N°1 : Ne conserver QUE des événements publiés depuis MOINS DE 48 HEURES.\n"
        "RÈGLE CRITIQUE : Ne retenir QUE les articles parlant d'intempéries (orages, inondations, cyclones, tempêtes, grêle, tornade, canicule, etc.). EXCLURE tout article sans rapport avec les intempéries.\n"
        "Pour chaque élément, fournis un titre, la zone concernée (location), le phénomène (phenomenon), une courte description (summary) et son URL source (url).\n"
        "RÈGLE CRITIQUE POUR L'URL : Tu DOIS copier-coller EXACTEMENT sans modification la valeur de la clé 'url'. N'invente pas d'URL.\n"
        "Format de sortie attendu : JSON uniquement (sans blocs ```json) :\n"
        "[\n"
        "  {\"title\": \"...\", \"location\": \"...\", \"phenomenon\": \"...\", \"summary\": \"...\", \"url\": \"...\"},\n"
        "  ...\n"
        "]"
    )
    user_prompt = f"Données récoltées pour le {date_str} :\n{json.dumps(raw_articles, ensure_ascii=False)}"
    return llm_parse_json(system_prompt, user_prompt, label="build_intemperies_report")

def build_bonsplans_report(date_str):
    print("[Rapport] Collecte et rédaction Bons Plans IA & Outils...")
    raw_articles = _fetch_feeds(FEEDS_BONSPLANS, max_articles=30, max_hours=168)  # 7 jours
    if not raw_articles:
        print("[Rapport] Bons Plans : aucun article trouvé dans les flux dédiés.")
        return []
    system_prompt = (
        "Tu es un expert veille IA et Tech. Ton rôle est de repérer UNIQUEMENT les bons plans liés à l'intelligence artificielle.\n"
        "RÈGLE ABSOLUE : Ne retenir QUE les articles concernant l'IA : nouveaux abonnements ChatGPT/Claude/Gemini, nouveaux outils IA gratuits, lancements de modèles, nouveaux sites IA, offres d'essai gratuit, open source IA.\n"
        "EXCLURE impérativement : électroménager, vêtements, jeux vidéo, voyages, et tout ce qui n'est pas lié à l'IA ou au Tech.\n"
        "RÈGLE CRITIQUE : Lister jusqu'à 10 bons plans. Si peu d'articles correspondent, ne liste que ceux qui sont vraiment liés à l'IA.\n"
        "Pour chaque bon plan : titre (title), outil/service IA (tool), type (offer_type : 'Gratuit', 'Nouveau lancement', 'Open Source', 'Promo abonnement', 'Essai gratuit'...), description courte (summary), URL (url).\n"
        "RÈGLE URL : copier-coller EXACTEMENT la valeur 'url' sans modification. N'invente pas d'URL.\n"
        "Format JSON uniquement (sans ```json) :\n"
        "[{\"title\": \"...\", \"tool\": \"...\", \"offer_type\": \"...\", \"summary\": \"...\", \"url\": \"...\"},...]\n"
    )
    user_prompt = f"Articles récoltés pour le {date_str} :\n{json.dumps(raw_articles, ensure_ascii=False)}"
    return llm_parse_json(system_prompt, user_prompt, label="build_bonsplans_report")

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
        
        result = llm_parse_json(system_prompt, user_prompt, label="process_youtube_report")
        if result:
            return result
        # Fallback si l'IA échoue : tri classique par score d'origine
        print("Fallback YouTube : Échec de l'IA, utilisation du tri par défaut.")
        top_videos = sorted(videos, key=lambda x: -x.get("score", 0))[:10]
        return top_videos
    except Exception as e:
        print(f"Erreur lors du traitement des recommandations YouTube : {e}")
        return []

# 4. Générateur de Synthèse Globale
def build_synthesis(actu, ia, meteo, yt, date_str, intemperies=None, bonsplans=None):
    intemperies = intemperies or []
    bonsplans = bonsplans or []
    print("[Synthèse] Rédaction de la synthèse globale...")
    system_prompt = (
        "Tu es un rédacteur en chef. Ton rôle est de compiler une synthèse quotidienne pour un créateur de contenu météo et tech.\n"
        "RÈGLE ABSOLUE ANTI-HALLUCINATION : Tu ne dois JAMAIS inventer, extrapoler ou créer de toutes pièces des actualités.\n"
        "Chaque élément listé dans top_press, top_hdf, top_ia, top_meteo, top_intemperies et top_bonsplans DOIT correspondre EXACTEMENT à un article présent dans les données fournies ci-dessous.\n"
        "Si les données ne contiennent que 3 articles IA, liste UNIQUEMENT ces 3 articles — ne complète JAMAIS avec des items inventés.\n"
        "À partir des données fournies, rédige une synthèse condensée contenant :\n"
        "1. Une introduction de 3-4 lignes décrivant la situation globale du jour (basée uniquement sur les données).\n"
        "2. Jusqu'à 10 actualités presse majeures (titres exacts des articles fournis).\n"
        "3. Jusqu'à 5 actualités Hauts-de-France (titres exacts des articles fournis).\n"
        "4. Jusqu'à 10 nouveautés IA (titres exacts des articles fournis).\n"
        "5. Jusqu'à 10 événements météo (titres exacts des articles fournis).\n"
        "6. Jusqu'à 5 intempéries/cyclones (titres exacts des articles fournis).\n"
        "7. Jusqu'à 5 bons plans IA (titres exacts des articles fournis).\n"
        "8. Jusqu'à 10 vidéos YouTube (titres exacts des articles fournis, avec score /10).\n"
        "9. Un planning éditorial suggéré (3 sujets inspirés des données du jour).\n"
        "Format de sortie attendu : JSON uniquement (sans blocs ```json) :\n"
        "{\n"
        "  \"intro\": \"...\",\n"
        "  \"top_press\": [ \"...\", ... ],\n"
        "  \"top_hdf\": [ \"...\", ... ],\n"
        "  \"top_ia\": [ \"...\", ... ],\n"
        "  \"top_meteo\": [ \"...\", ... ],\n"
        "  \"top_intemperies\": [ \"...\", ... ],\n"
        "  \"top_bonsplans\": [ \"...\", ... ],\n"
        "  \"top_youtube\": [ \"...\", ... ],\n"
        "  \"editorial_plan\": [ {\"subject\": \"...\", \"hook\": \"...\", \"format\": \"...\"}, ... (3 items) ]\n"
        "}"
    )
    hdf_data = actu.get('hdf', []) if isinstance(actu, dict) else []
    user_prompt = (
        f"Données pour le {date_str} :\n"
        f"- Presse nationale : {json.dumps(actu, ensure_ascii=False)[:2500]}\n"
        f"- Hauts-de-France : {json.dumps(hdf_data, ensure_ascii=False)[:1500]}\n"
        f"- IA : {json.dumps(ia, ensure_ascii=False)[:2500]}\n"
        f"- Météo : {json.dumps(meteo, ensure_ascii=False)[:2500]}\n"
        f"- YouTube : {json.dumps(yt, ensure_ascii=False)[:2500]}\n"
        f"- Intempéries : {json.dumps(intemperies, ensure_ascii=False)[:1500]}\n"
        f"- Bons Plans IA : {json.dumps(bonsplans, ensure_ascii=False)[:1500]}"
    )
    return llm_parse_json(system_prompt, user_prompt, label="build_synthesis")

# 5. Compilation HTML Premium Responsive
def compile_html(synthesis, actu, ia, meteo, yt, date_str, intemperies=None, bonsplans=None):
    intemperies = intemperies or []
    bonsplans = bonsplans or []
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
    .badge-intemperies { background-color: #ffe4e6; color: #e11d48; }
    .badge-bonsplans { background-color: #faf5ff; color: #7e22ce; }
    
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
                <h3>📍 Hauts-de-France</h3>
                <ul>
    """
    for item in synthesis.get('top_hdf', []):
        html += f"<li>{item}</li>"
    html += """
                </ul>
                <h3>Intempéries &amp; Cyclones</h3>
                <ul>
    """
    for item in synthesis.get('top_intemperies', []):
        html += f"<li>{item}</li>"
    html += """
                </ul>
                <h3>🤖 Bons Plans IA &amp; Outils</h3>
                <ul>
    """
    for item in synthesis.get('top_bonsplans', []):
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
    
    # 10 de chaque catégorie (sans HDF qui est séparé ci-dessous)
    categories = [("mondial", "Mondial", "badge-mondial"), ("international", "International", "badge-inter"), ("france", "France", "badge-france")]
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
            <div class="section-title">📍 Hauts-de-France</div>
    """
    for item in actu.get("hdf", []):
        html += f"""
        <div class="card">
            <span class="badge badge-hdf">Hauts-de-France</span>
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
            <div class="section-title">🎁 Bons Plans IA & Outils</div>
    """
    for item in bonsplans:
        html += f"""
        <div class="card">
            <span class="badge badge-bonsplans">{item.get('offer_type', 'Bon Plan')}</span>
            <div class="card-title">
                <a href="{item.get('url', '#')}" target="_blank">{item.get('title', '')}</a>
            </div>
            <div class="card-meta">Outil: <strong>{item.get('tool', '')}</strong></div>
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
            <div class="section-title">🌪️ Intempéries & Cyclones</div>
    """
    for item in intemperies:
        html += f"""
        <div class="card">
            <span class="badge badge-intemperies">Intempérie</span>
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
    
    if gmail_email:
        gmail_email = gmail_email.replace('\ufeff', '').replace('\ufffe', '').strip()
    if gmail_password:
        gmail_password = gmail_password.replace('\ufeff', '').replace('\ufffe', '').strip()
        
    # Récupération des destinataires (par défaut toi, sinon liste séparée par des virgules)
    recipients_raw = os.environ.get("RECIPIENT_EMAILS", smtp_email)
    recipients = [r.strip() for r in recipients_raw.split(",") if r.strip()]

    # Suppression totale de tout BOM ou caractère non-ASCII parasite
    html_body = html_body.replace('\ufeff', '').replace('\ufffe', '')
    
    sender = gmail_email if gmail_password else smtp_email
    
    # Construction du message MIME propre avec corps HTML en ligne (sans pièce jointe)
    msg = MIMEMultipart('alternative')
    msg['Subject'] = f'Synthèse Veille - {date_str}'
    msg['From'] = f'Meteo Climat Pro <{sender}>'
    msg['To'] = ", ".join(recipients)
    msg['Reply-To'] = "gregory.langlet@sfr.fr"
    msg['Date'] = formatdate(localtime=True)
    
    # Attacher la version HTML directement
    msg.attach(MIMEText(html_body, 'html', 'utf-8'))
    
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
            server.sendmail(gmail_email, recipients, msg.as_string())
        print("[SMTP] E-mail envoye avec succes via Gmail !")
    except Exception as e:
        import traceback
        print(f"[SMTP] Erreur Gmail : {e}")
        traceback.print_exc()
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
    
    # 2. Collecte & Rédaction toutes thématiques
    print("\n--- Étape 2 : Rédactions Thématiques ---")
    actu_report        = build_actu_report(date_str)        or {"mondial": [], "international": [], "france": [], "hdf": []}
    ia_report          = build_ia_report(date_str)          or []
    meteo_report       = build_meteo_report(date_str)       or []
    intemperies_report = build_intemperies_report(date_str) or []
    bonsplans_report   = build_bonsplans_report(date_str)   or []
    
    # 3. Rédaction de la Synthèse
    print("\n--- Étape 3 : Synthèse ---")
    synthesis_report = build_synthesis(
        actu_report, ia_report, meteo_report, yt_report, date_str,
        intemperies=intemperies_report, bonsplans=bonsplans_report
    )
    
    if not synthesis_report:
        print("[Avertissement] Synthèse indisponible, utilisation d'un résumé minimal.")
        synthesis_report = {
            "intro": f"Veille du {date_str}.",
            "top_press": [], "top_ia": [], "top_meteo": [], "top_youtube": [],
            "top_intemperies": [], "top_bonsplans": [], "editorial_plan": []
        }
        
    # 4. Compilation HTML
    print("\n--- Étape 4 : Compilation HTML ---")
    html_output = compile_html(
        synthesis_report, actu_report, ia_report, meteo_report, yt_report, date_str,
        intemperies=intemperies_report, bonsplans=bonsplans_report
    )
    
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
