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

# 1. Collecte RSS — Google News multi-requêtes par thème
# ponytail: Google News RSS est public, anonyme, ~50-200 résultats/requête depuis des centaines de sources
GNEWS_BASE = "https://news.google.com/rss/search?q={query}&hl=fr&gl=FR&ceid=FR:fr"

def _gnews_fetch(queries, max_articles=200):
    """Interroge Google News RSS pour chaque requête, déduplique, filtre <24h. Retourne jusqu'à max_articles items."""
    user_agent = "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"
    seen_urls = set()
    all_articles = []
    for source_name, q in queries.items():
        url = GNEWS_BASE.format(query=urllib.parse.quote(q))
        try:
            req = urllib.request.Request(url, headers={"User-Agent": user_agent})
            with urllib.request.urlopen(req, timeout=15) as resp:
                root = ET.fromstring(resp.read())
            for item in root.findall(".//item"):
                title_el = item.find("title")
                link_el  = item.find("link")
                date_el  = item.find("pubDate")
                src_el   = item.find("source")
                title = title_el.text if title_el is not None else ""
                link  = link_el.text  if link_el  is not None else ""
                if not link or link in seen_urls:
                    continue
                seen_urls.add(link)
                all_articles.append({
                    "title":  title.strip(),
                    "url":    link,
                    "date":   date_el.text if date_el is not None else "",
                    "source": src_el.text  if src_el  is not None else source_name,
                })
        except Exception as e:
            print(f"[RSS] Échec Google News '{q}' : {e}")

    # Filtre strict 24h puis tri du plus récent au plus ancien
    recent = filter_recent_articles(all_articles, 24)
    recent.sort(key=lambda x: x.get("age_seconds", 999999))
    return recent[:max_articles]


def _fetch_actu():
    """Collecte presse nationale + internationale : vise 80+ articles <24h."""
    queries = {
        "une_france":   "actualités France politiques société économie",
        "monde":        "actualités monde international breaking news",
        "geopolitique": "géopolitique Europe Etats-Unis guerre diplomatie",
        "politique_fr": "politique française gouvernement parlement élections",
        "société_fr":   "société faits divers France justice police",
        "economie":     "économie entreprises marchés inflation bourse",
        "europe":       "actualités Europe Commission Parlement europeen",
        "usa":          "United States politics news Trump Biden White House",
    }
    return _gnews_fetch(queries, max_articles=150)


def _fetch_ia():
    """Collecte IA & Tech : vise 80+ articles <24h."""
    queries = {
        "llm_models":   "LLM ChatGPT Claude Gemini Llama DeepSeek GPT release",
        "openai":       "OpenAI announcement model release update",
        "anthropic":    "Anthropic Claude AI update",
        "google_ai":    "Google Gemini AI DeepMind update",
        "ia_outils":    "intelligence artificielle outils IA France nouveauté",
        "github_ai":    "GitHub Copilot open source AI tools developer",
        "securite_ia":  "AI safety cybersecurity LLM jailbreak vulnerability",
        "hacker_news":  "AI machine learning software engineering Hacker News",
        "robotique":    "robotique robots autonomes IA industrielle",
        "ia_emploi":    "intelligence artificielle emploi automatisation impact société",
    }
    return _gnews_fetch(queries, max_articles=150)


def _fetch_meteo():
    """Collecte météo & climat : vise 80+ articles <24h."""
    queries = {
        "vigilance_mf": "Météo-France vigilance orange rouge alerte",
        "canicule":     "canicule chaleur record température France Europe",
        "inondation":   "inondations crues pluies torrentielles France",
        "tempete":      "tempête vents violents ouragan cyclone",
        "orage":        "orages grêle foudre tornade France",
        "climat_global": "changement climatique records OMM NOAA Copernicus",
        "neige":        "neige gel verglas grand froid montagne",
        "secheresse":   "sécheresse incendies de forêt canicule été",
        "meteo_monde":  "weather extreme events flooding hurricane wildfire",
        "previsions":   "prévisions météo semaine France températures",
    }
    return _gnews_fetch(queries, max_articles=150)


def _fetch_hdf():
    """Collecte Hauts-de-France : vise 60+ articles <24h."""
    queries = {
        "lille":        "Lille actualités Nord faits divers",
        "pas_de_calais": "Pas-de-Calais Calais Boulogne Lens Béthune actualités",
        "picardie":     "Amiens Somme Oise Aisne Picardie actualités",
        "nord_faits":   "Nord faits divers accidents justice police",
        "hdf_economie": "Hauts-de-France économie emploi usines industrie",
        "hdf_culture":  "Hauts-de-France culture sport événements",
        "dunkerque":    "Dunkerque Valenciennes Douai actualités",
        "arras":        "Arras Saint-Quentin Soissons actualités",
    }
    return _gnews_fetch(queries, max_articles=150)


def _fetch_intemperies():
    """Collecte intempéries & cyclones : vise 60+ articles <24h."""
    queries = {
        "orages":       "orages grêle foudre tornade France Europe",
        "cyclones":     "cyclone ouragan typhon tropical storm",
        "inondations":  "inondations crues catastrophe naturelle",
        "vigilance":    "Météo-France vigilance rouge orange alerte météo",
        "tornades":     "tornado tornades Etats-Unis France Europe",
        "canicule_ex":  "canicule record chaleur extrême Europe monde",
        "tempete_vent": "tempête vents violents gusts storm damage",
        "neige_montagne": "neige avalanche montagne alerte grand froid",
    }
    return _gnews_fetch(queries, max_articles=150)


# Rétrocompat: fetch_google_news conservée pour process_youtube_report ou autres appels
def fetch_google_news(query):
    """Alias de compatibilité — routes vers le bon collecteur thématique."""
    q = query.lower()
    if any(w in q for w in ["météo", "meteo", "climat", "vigilance", "canicule"]):
        return _fetch_meteo()[:45]
    if any(w in q for w in ["hauts-de-france", "hdf", "lille", "pas-de-calais"]):
        return _fetch_hdf()[:45]
    if any(w in q for w in ["ia", "ai", "claude", "gemini", "llama", "deepseek", "chatgpt", "openai", "github"]):
        return _fetch_ia()[:45]
    if any(w in q for w in ["intempéries", "orages", "cyclone", "tornade", "inondation"]):
        return _fetch_intemperies()[:45]
    return _fetch_actu()[:45]

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

def _repair_truncated_json(text):
    """Tente de réparer un JSON tronqué en fermant les structures ouvertes."""
    text = text.strip()
    # Supprimer la dernière entrée incomplète (après la dernière virgule ou accolade/crochet ouvrant)
    for cutoff in [',', '{', '[']:
        idx = text.rfind(cutoff)
        if idx > 0:
            candidate = text[:idx]
            # Fermer les structures JSON ouvertes
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
                # Tentative de réparation automatique si JSON tronqué
                repaired = _repair_truncated_json(response_clean)
                if repaired is not None:
                    print(f"[LLM] JSON réparé automatiquement pour {label} ({len(repaired) if isinstance(repaired, list) else 'dict'} éléments récupérés).")
                    return repaired
        if attempt < retries - 1:
            print(f"[LLM] Nouvelle tentative dans {delay}s...")
            time.sleep(delay)
    print(f"[LLM] ERREUR : {retries} tentatives échouées pour {label}.")
    return None

# 3. Rédacteurs thématiques — format complet conforme aux compétences veille
def build_actu_report(date_str):
    print("[Rapport] Collecte et rédaction Actualités...")
    raw_data = {
        "mondial":       _fetch_actu()[:80],
        "international": _fetch_actu()[:80],
        "france":        _fetch_actu()[:80],
    }
    system_prompt = (
        f"Tu es un journaliste d'investigation senior spécialisé dans l'actualité nationale et internationale. Aujourd'hui nous sommes le {date_str}.\n\n"
        "RÈGLE ABSOLUE N°1 : Ne conserver QUE des articles publiés depuis MOINS DE 24 HEURES. Ignore tout article sans date claire.\n"
        "DÉDOUBLONNAGE : Si plusieurs médias parlent du même événement, ne conserve qu'une seule actualité (la meilleure source).\n"
        "PRIORITÉ : Géopolitique, conflits, réformes, crises économiques, sécurité, justice, catastrophes, grondements sociaux. Ignore sport/culture/agenda/pub.\n"
        "RÈGLE CRITIQUE POUR L'URL : Copie-colle EXACTEMENT la valeur 'url' de la source. N'invente jamais une URL.\n\n"
        "FORMAT OBLIGATOIRE pour chaque actualité dans le champ 'summary' :\n"
        "Le résumé doit être un paragraphe unique et fluide de 5 lignes exactes expliquant les faits, le contexte, les conséquences géopolitiques/nationales, les réactions et les suites. Terminer par : '**Source :** [Nom](URL)'.\n\n"
        "Format JSON attendu (sans blocs ```json) :\n"
        "{\n"
        "  \"mondial\": [ {\"title\": \"1. Titre complet (Pays/Zone)\", \"source\": \"...\", \"url\": \"...\", \"summary\": \"Paragraphe 5 lignes...\\n**Source :** [Nom](URL)\"}, ... ],\n"
        "  \"international\": [ ... ],\n"
        "  \"france\": [ ... ]\n"
        "}"
    )
    user_prompt = f"Données récoltées pour le {date_str} :\n{json.dumps(raw_data, ensure_ascii=False)}"
    return llm_parse_json(system_prompt, user_prompt, label="build_actu_report")

def build_ia_report(date_str):
    print("[Rapport] Collecte et rédaction Intelligence Artificielle...")
    raw_articles = _fetch_ia()
    system_prompt = (
        f"Tu es un journaliste d'investigation et analyste senior spécialisé dans l'Intelligence Artificielle et l'écosystème Tech. Aujourd'hui nous sommes le {date_str}.\n\n"
        "RÈGLE ABSOLUE N°1 : Ne conserver QUE des articles publiés depuis MOINS DE 24 HEURES. Ignore tout article sans date claire.\n"
        "PÉRIMÈTRE : Modèles LLM, Outils/IDE développeur, Recherche ArXiv/benchmarks, Entreprises/financement/régulation.\n"
        "PRIORITÉ : Releases, découvertes scientifiques, nouveaux outils, régulation, failles sécurité, investissements, benchmarks. Ignore rumeurs/pub/opinions.\n"
        "DÉDOUBLONNAGE : une seule actualité par modèle/outil, source officielle prioritaire.\n"
        "RÈGLE CRITIQUE POUR L'URL : Copie-colle EXACTEMENT la valeur 'url'. N'invente jamais une URL.\n\n"
        "FORMAT OBLIGATOIRE pour chaque actualité dans le champ 'summary' :\n"
        "Paragraphe unique et fluide de 5 lignes exactes expliquant les faits et spécifications techniques, le contexte, les conséquences pour l'écosystème et les développeurs, et les suites/accès. Terminer par : '**Source :** [Nom](URL)'.\n\n"
        "Format JSON attendu (sans blocs ```json) :\n"
        "[ {\"title\": \"1. Titre complet\", \"tool\": \"...\", \"url\": \"...\", \"score\": 8.5, \"summary\": \"Paragraphe 5 lignes...\\n**Source :** [Nom](URL)\"}, ... ]"
    )
    user_prompt = f"Données récoltées pour le {date_str} :\n{json.dumps(raw_articles, ensure_ascii=False)}"
    return llm_parse_json(system_prompt, user_prompt, label="build_ia_report")

def build_meteo_report(date_str):
    print("[Rapport] Collecte et rédaction Météo & Climat...")
    raw_articles = _fetch_meteo()
    system_prompt = (
        f"Tu es un journaliste d'investigation et prévisionniste senior spécialisé en Météorologie et Climatologie. Aujourd'hui nous sommes le {date_str}.\n\n"
        "RÈGLE ABSOLUE N°1 : Ne conserver QUE des articles publiés depuis MOINS DE 24 HEURES.\n"
        "DOMÀINES : Vigilances Météo-France, modèles numériques, intempéries confirmées, météo mondiale (cyclones/vagues de chaleur), climatologie (Copernicus/NOAA/OMM).\n"
        "PRIORITÉ : Vigilances orange/rouge, dégâts confirmés, évolution modèles, cyclones actifs, records. Ignore prévisions >14j non fiables et rumeurs réseaux sociaux.\n"
        "DÉDOUBLONNAGE : une seule actualité par phénomène/événement.\n"
        "RÈGLE CRITIQUE POUR L'URL : Copie-colle EXACTEMENT la valeur 'url'. N'invente jamais une URL.\n\n"
        "FORMAT OBLIGATOIRE pour chaque actualité dans le champ 'summary' :\n"
        "Paragraphe unique et fluide de 5 lignes exactes expliquant les faits et mesures observées, le contexte météorologique, les conséquences et les prévisions/tendances. Terminer par : '**Source :** [Nom](URL)'.\n\n"
        "Format JSON attendu (sans blocs ```json) :\n"
        "[ {\"title\": \"1. Titre complet (Zone/Pays)\", \"location\": \"...\", \"phenomenon\": \"...\", \"url\": \"...\", \"summary\": \"Paragraphe 5 lignes...\\n**Source :** [Nom](URL)\"}, ... ]"
    )
    user_prompt = f"Données récoltées pour le {date_str} :\n{json.dumps(raw_articles, ensure_ascii=False)}"
    return llm_parse_json(system_prompt, user_prompt, label="build_meteo_report")

def build_hdf_report(date_str):
    print("[Rapport] Collecte et rédaction Hauts-de-France...")
    raw_articles = _fetch_hdf()
    system_prompt = (
        f"Tu es un journaliste d'investigation senior spécialisé dans l'actualité régionale des Hauts-de-France. Aujourd'hui nous sommes le {date_str}.\n\n"
        "RÈGLE ABSOLUE N°1 : Ne conserver QUE des articles publiés depuis MOINS DE 24 HEURES. Ignore tout article sans date claire.\n"
        "ZONE : Uniquement Nord (59), Pas-de-Calais (62), Somme (80), Oise (60), Aisne (02).\n"
        "PRIORITÉ : Faits divers majeurs, incendies, accidents graves, disparitions, justice, police, santé publique, intempéries, économie régionale, grondements politiques locaux. Ignore sport/culture/agenda/pub SAUF si exceptionnel.\n"
        "DÉDOUBLONNAGE : un seul article par événement, source régionale prioritaire (La Voix du Nord, France Bleu Nord, France 3 HDF, Actu.fr).\n"
        "RÈGLE CRITIQUE POUR L'URL : Copie-colle EXACTEMENT la valeur 'url'. N'invente jamais une URL.\n\n"
        "FORMAT OBLIGATOIRE pour chaque actualité dans le champ 'summary' :\n"
        "Paragraphe unique et fluide de 5 lignes exactes expliquant les faits, le contexte local, les conséquences, la réaction des secours/police et les suites de l'affaire. Terminer par : '**Source :** [Nom](URL)'.\n\n"
        "Format JSON attendu (sans blocs ```json) :\n"
        "[ {\"title\": \"1. Titre complet (Département + Code)\", \"source\": \"...\", \"url\": \"...\", \"summary\": \"Paragraphe 5 lignes...\\n**Source :** [Nom](URL)\"}, ... ]"
    )
    user_prompt = f"Données récoltées pour le {date_str} :\n{json.dumps(raw_articles, ensure_ascii=False)}"
    return llm_parse_json(system_prompt, user_prompt, label="build_hdf_report")


def build_intemperies_report(date_str):
    print("[Rapport] Collecte et rédaction Intempéries & Cyclones...")
    raw_articles = _fetch_intemperies()
    system_prompt = (
        f"Tu es un journaliste d'investigation spécialisé dans les risques naturels majeurs, les intempéries graves et l'activité cyclonique mondiale. Aujourd'hui nous sommes le {date_str}.\n\n"
        "RÈGLE ABSOLUE N°1 : Ne conserver QUE des articles publiés depuis MOINS DE 24 HEURES.\n"
        "PÉRIMÈTRE : Inondations, tempêtes violentes, tornades homologuées, cyclones/typhons/ouragans actifs, feux de forêt hors contrôle, glissements meurtriers.\n"
        "PRIORITÉ : Bilans humains, évacuations d'urgence, destructions d'infrastructures, alertes rouge/violette, crues centennales, feux menaçant des zones urbaines. Ignore orages classiques sans dégâts.\n"
        "DÉDOUBLONNAGE : une seule actualité par événement, source officielle (NHC, Météo-France, Keraunos, AFP) prioritaire.\n"
        "RÈGLE CRITIQUE POUR L'URL : Copie-colle EXACTEMENT la valeur 'url'. N'invente jamais une URL.\n\n"
        "FORMAT OBLIGATOIRE pour chaque actualité dans le champ 'summary' :\n"
        "Paragraphe unique et fluide de 5 lignes exactes expliquant les faits et bilan provisoire, le contexte météorologique et dynamique, les conséquences humaines/matérielles et la trajectoire/évolution attendue. Terminer par : '**Source :** [Nom](URL)'.\n\n"
        "Format JSON attendu (sans blocs ```json) :\n"
        "[ {\"title\": \"1. Titre complet (Zone/Pays)\", \"category\": \"CYCLONE|ORAGES|GRÊLE|INONDATIONS|VENT|VIGILANCE\", \"location\": \"...\", \"url\": \"...\", \"summary\": \"Paragraphe 5 lignes...\\n**Source :** [Nom](URL)\"}, ... ]"
    )
    user_prompt = f"Données récoltées pour le {date_str} :\n{json.dumps(raw_articles, ensure_ascii=False)}"
    return llm_parse_json(system_prompt, user_prompt, label="build_intemperies_report")


def build_bonsplans_report(date_str):
    print("[Rapport] Collecte et rédaction Bons Plans IA & Outils...")
    queries = {
        "deals_ia":       "IA tools free plan promo deal discount coupon 2025",
        "outils_gratuits": "intelligence artificielle outil gratuit nouveauté offre lancement",
        "github_free":    "open source AI tool free release GitHub 2025",
        "promo_tech":     "SaaS promotion code promo outil développeur offre spéciale",
        "nouveautes":     "nouveauté IA outil gratuit lancement beta access 2025",
    }
    raw_articles = _gnews_fetch(queries, max_articles=80)
    system_prompt = (
        f"Tu es un chasseur de bons plans tech & IA. Aujourd'hui nous sommes le {date_str}.\n\n"
        "RÈGLE ABSOLUE N°1 : Ne conserver QUE des offres publiées depuis MOINS DE 24 HEURES.\n"
        "PÉRIMÈTRE : Outils gratuits, promotions, accès beta, codes promo, offres limitées dans l'écosystème IA & Tech.\n"
        "RÈGLE CRITIQUE POUR L'URL : Copie-colle EXACTEMENT la valeur 'url'. N'invente jamais une URL.\n\n"
        "FORMAT OBLIGATOIRE pour chaque actualité dans le champ 'summary' :\n"
        "Paragraphe unique et fluide de 5 lignes exactes décrivant ce que l'offre inclut, sa valeur réelle, les conditions d'utilisation, la date d'expiration si connue, et pourquoi Gregory devrait en profiter. Terminer par : '**Source :** [Nom](URL)'.\n\n"
        "Format JSON attendu (sans blocs ```json) :\n"
        "[ {\"title\": \"1. Titre de l'offre\", \"tool\": \"...\", \"offer_type\": \"...\", \"url\": \"...\", \"summary\": \"Paragraphe 5 lignes...\\n**Source :** [Nom](URL)\"}, ... ]"
    )
    user_prompt = f"Données récoltées pour le {date_str} :\n{json.dumps(raw_articles, ensure_ascii=False)}"
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
    
    return llm_parse_json(system_prompt, user_prompt, label="build_synthesis")

# 5. Compilation HTML Premium Responsive
def compile_html(synthesis, actu, ia, meteo, yt, date_str, hdf=None, intemperies=None, bonsplans=None):
    hdf = hdf or []
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
            <div class="section-title">🌐 Presse & Actualités Générales</div>
    """
    for key, label, badge_style in [("mondial", "Mondial", "badge-mondial"), ("international", "International", "badge-inter"), ("france", "France", "badge-france")]:
        for item in actu.get(key, []):
            html += f"""
            <div class="card">
                <span class="badge {badge_style}">{label}</span>
                <div class="card-title"><a href="{item.get('url', '#')}" target="_blank">{item.get('title', '')}</a></div>
                <div class="card-meta">Source: <strong>{item.get('source', '')}</strong></div>
                <p class="card-summary">{item.get('summary', '')}</p>
            </div>"""

    html += """
            <div class="section-title">📍 Hauts-de-France</div>
    """
    hdf_items = hdf if hdf else actu.get("hdf", [])
    for item in hdf_items:
        html += f"""
            <div class="card">
                <span class="badge badge-hdf">Hauts-de-France</span>
                <div class="card-title"><a href="{item.get('url', '#')}" target="_blank">{item.get('title', '')}</a></div>
                <div class="card-meta">Source: <strong>{item.get('source', '')}</strong></div>
                <p class="card-summary">{item.get('summary', '')}</p>
            </div>"""

    html += """
            <div class="section-title">🌩️ Intempéries & Cyclones</div>
    """
    for item in intemperies:
        badge_cat = item.get('category', 'VIGILANCE').upper()
        badge_color = "badge-meteo"
        if "CYCLONE" in badge_cat or "OURAGAN" in badge_cat: badge_color = "badge-ia"
        elif "VENT" in badge_cat or "TORNADE" in badge_cat: badge_color = "badge-inter"
        elif "INONDATION" in badge_cat or "CRUE" in badge_cat: badge_color = "badge-france"
        html += f"""
            <div class="card">
                <span class="badge {badge_color}">{item.get('category', 'VIGILANCE')}</span>
                <div class="card-title"><a href="{item.get('url', '#')}" target="_blank">{item.get('title', '')}</a></div>
                <div class="card-meta">Zone: <strong>{item.get('location', '')}</strong></div>
                <p class="card-summary">{item.get('summary', '')}</p>
            </div>"""

    html += """
            <div class="section-title">🤖 Intelligence Artificielle</div>
    """
    for item in ia:
        html += f"""
        <div class="card">
            <span class="score-badge">Éditorial: {item.get('score', 0)}/10</span>
            <span class="badge badge-ia">IA & Tech</span>
            <div class="card-title"><a href="{item.get('url', '#')}" target="_blank">{item.get('title', '')}</a></div>
            <div class="card-meta">Techno/Modèle: <strong>{item.get('tool', '')}</strong></div>
            <p class="card-summary">{item.get('summary', '')}</p>
        </div>"""

    html += """
            <div class="section-title">🎁 Bons Plans IA & Outils</div>
    """
    for item in bonsplans:
        html += f"""
        <div class="card">
            <span class="badge badge-yt">{item.get('offer_type', 'Bon Plan')}</span>
            <div class="card-title"><a href="{item.get('url', '#')}" target="_blank">{item.get('title', '')}</a></div>
            <div class="card-meta">Outil: <strong>{item.get('tool', '')}</strong></div>
            <p class="card-summary">{item.get('summary', '')}</p>
        </div>"""

    html += """
            <div class="section-title">🌤️ Météo & Climat</div>
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
    actu_report       = build_actu_report(date_str)        or {"mondial": [], "international": [], "france": [], "hdf": []}
    hdf_report        = build_hdf_report(date_str)         or []
    ia_report         = build_ia_report(date_str)          or []
    meteo_report      = build_meteo_report(date_str)       or []
    intemperies_report = build_intemperies_report(date_str) or []
    bonsplans_report  = build_bonsplans_report(date_str)   or []

    # 3. Rédaction de la Synthèse
    print("\n--- Étape 3 : Synthèse ---")
    synthesis_report = build_synthesis(actu_report, ia_report, meteo_report, yt_report, date_str)

    if not synthesis_report:
        print("[Avertissement] Synthèse indisponible, utilisation d'un résumé minimal.")
        synthesis_report = {"intro": "Veille du " + date_str, "top_press": [], "top_ia": [], "top_meteo": [], "top_youtube": [], "editorial_plan": []}

    # 4. Compilation HTML
    print("\n--- Étape 4 : Compilation HTML ---")
    html_output = compile_html(
        synthesis_report, actu_report, ia_report, meteo_report, yt_report, date_str,
        hdf=hdf_report, intemperies=intemperies_report, bonsplans=bonsplans_report
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
