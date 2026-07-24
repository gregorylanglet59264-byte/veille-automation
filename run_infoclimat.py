import urllib.request
import urllib.error
import re
import sys
import os
import json
import base64
import uuid
import datetime
import smtplib
from email.utils import formatdate

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

import socket
import time

socket.setdefaulttimeout(10)

INDEX_URL = "https://forums.infoclimat.fr/f/forum/20-evolution-%C3%A0-plus-long-terme/"
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'

def fetch_url(url, timeout=8):
    req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return response.read().decode('utf-8', errors='ignore')

def call_llm(system_prompt, user_prompt, max_retries=3):
    openrouter_key = os.environ.get("OPENROUTER_API_KEY", "").replace('\ufeff', '').strip()
    if not openrouter_key:
        print("[LLM] ERREUR : OPENROUTER_API_KEY non configurée.")
        return None
    
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
    
    for attempt in range(1, max_retries + 1):
        print(f"[LLM] Tentative {attempt}/{max_retries} — DeepSeek V4 Flash via OpenRouter...")
        try:
            req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=120) as response:
                res_data = json.loads(response.read().decode("utf-8"))
                text = res_data["choices"][0]["message"]["content"]
                return text.replace('\ufeff', '').replace('\ufffe', '')
        except urllib.error.HTTPError as http_err:
            print(f"[LLM] Tentative {attempt} échouée : HTTP {http_err.code}")
        except Exception as e:
            print(f"[LLM] Tentative {attempt} échouée : {e}")
        
        if attempt < max_retries:
            time.sleep(5 * attempt)
            
    return None


def process_topic(topic_url, topic_idx, date_context_str):
    print(f"\n--- Sujet [{topic_idx+1}] : {topic_url} ---")
    
    # 1. Charger le titre et la pagination du sujet
    try:
        html_first = fetch_url(topic_url)
    except Exception as e:
        print(f"Erreur chargement sujet : {e}")
        return None
        
    topic_title_match = re.search(r'<h1[^>]*class=["\']ipsType_pageTitle[^>]*>(.*?)</h1>', html_first, re.DOTALL)
    topic_title_clean = "Sujet de prévisions"
    if topic_title_match:
        topic_title_clean = re.sub(r'<[^>]+>', '', topic_title_match.group(1)).strip()
        topic_title_clean = re.sub(r'\s+', ' ', topic_title_clean)
        
    print(f"[{topic_idx+1}] Analyse de la pagination...")
    pages = [1]
    pagination_match = re.search(r'class=["\']ipsPagination_pageList["\']>(.*?)</ul>', html_first, re.DOTALL)
    if pagination_match:
        page_nums = re.findall(r'data-page=["\'](\d+)["\']', pagination_match.group(1))
        if page_nums:
            pages = sorted(list(set(int(p) for p in page_nums)))
            
    print(f"[{topic_idx+1}] Pages détectées : {len(pages)}")
    
    # Charger les 3 dernières pages pour avoir les commentaires récents
    pages_to_load = pages[-3:] if len(pages) >= 3 else pages
    all_comments = []
    all_authors = []
    
    print(f"[{topic_idx+1}] Chargement des commentaires des pages {pages_to_load[0]} à {pages_to_load[-1]}...")
    for page in pages_to_load:
        page_url = f"{topic_url}?page={page}"
        try:
            html_page = fetch_url(page_url)
            page_comments = re.findall(r'<div[^>]*data-role=["\']commentContent["\'][^>]*>(.*?)</div>\s*</div>', html_page, re.DOTALL)
            page_authors = re.findall(r'<strong>\s*<a href=[^>]*class=["\']ipsType_break["\'][^>]*>(.*?)</a>', html_page)
            all_comments.extend(page_comments)
            all_authors.extend(page_authors)
        except Exception as e:
            print(f"Erreur page {page} : {e}")
            
    # Nettoyer les commentaires pour l'IA
    cleaned_comments_data = []
    for idx, comment in enumerate(all_comments):
        clean_comment = re.sub(r'<br\s*/?>', '\n', comment)
        clean_comment = re.sub(r'<[^>]+>', '', clean_comment).strip()
        clean_comment = re.sub(r'\n\s*\n', '\n', clean_comment)
        author = all_authors[idx] if idx < len(all_authors) else "Membre"
        cleaned_comments_data.append(f"Auteur: {author}\nMessage:\n{clean_comment}")
        
    # Garder les 20 derniers messages pour l'analyse
    recent_messages_text = "\n\n=======================\n\n".join(cleaned_comments_data[-20:])
    
    # Extraire et télécharger les graphiques candidats
    print(f"[{topic_idx+1}] Extraction des graphiques...")
    candidate_imgs = []
    seen_imgs = set()
    for comment in all_comments:
        imgs = re.findall(r'<img[^>]+src=["\'](https?://[^"\']+)["\']', comment)
        for img in imgs:
            if any(x in img.lower() for x in ["emoji", "theme", "reactions", "avatar", "profile", "default", "giphy"]):
                continue
            if img not in seen_imgs:
                seen_imgs.add(img)
                priority = 2 if "uploads/monthly_" in img else 1
                candidate_imgs.append((img, priority))
                
    candidate_imgs.sort(key=lambda x: x[1], reverse=True)
    
    os.makedirs("candidates", exist_ok=True)
    downloaded_images = []
    for idx, (img_url, prio) in enumerate(candidate_imgs[:3]):
        ext = "png"
        if ".gif" in img_url.lower(): ext = "gif"
        elif ".jpg" in img_url.lower() or ".jpeg" in img_url.lower(): ext = "jpg"
        
        dest_file = f"candidates/topic_{topic_idx+1}_candidate_{idx+1}.{ext}"
        print(f"[{topic_idx+1}] Téléchargement graphique {idx+1} : {img_url} -> {dest_file}")
        try:
            req = urllib.request.Request(img_url, headers={'User-Agent': USER_AGENT})
            with urllib.request.urlopen(req, timeout=6) as img_resp:
                with open(dest_file, 'wb') as f_out:
                    f_out.write(img_resp.read())
            downloaded_images.append(dest_file)
        except Exception as e:
            print(f"Erreur téléchargement graphique {idx+1} : {e}")

    # Appeler l'IA pour l'analyse des scénarios et la rédaction du pack réseaux sociaux
    print(f"[{topic_idx+1}] Appel de l'IA pour l'analyse des scénarios météo...")
    system_prompt = """Tu es Patrick Marlière, météorologue expert de renommée nationale pour Monsieur Météo.

MISSION
À partir EXCLUSIVEMENT des discussions et analyses météorologiques fournies en entrée, tu dois produire un bulletin d'analyse météorologique professionnel, grand public, hyper-visuel, pédagogique et directement exploitable sur le web et les réseaux sociaux sans aucune modification manuelle.

RÈGLE D'OR N°1 : DATES EXACTES ET JOURS NOMMÉS DANS 100% DES SECTIONS
Dans TOUTES les sections (Alerte, Dashboard, Chronologie, Régions, Scénarios, Incertitudes, À Retenir, Posts Sociaux), tu devez mentionner les jours précis associés à leurs dates exactes (ex: Lundi 20 juillet, Mardi 21 juillet, Mercredi 22 juillet, Jeudi 23 juillet, Vendredi 24 juillet, Samedi 25 juillet, Dimanche 26 juillet). Ne dis plus jamais "début de semaine" ou "week-end" sans les associer directement à leur date.

RÈGLE D'OR N°2 : INTÉGRATION DE LA DATE DE GÉNÉRATION & PÉRIODE PERTINENTE
- Analyse avec attention la "Date actuelle de génération" transmise dans l'invite.
- Si le sujet correspond à la "Semaine en cours" : toute journée précédant cette date est déjà passée. Les prévisions doivent se concentrer EXCLUSIVEMENT sur la période allant de la date de génération au dimanche de cette semaine. Ignore ou mentionne comme "déjà écoulées" les journées passées.
- Si le sujet correspond à la "Semaine suivante" (Semaine future) : c'est la véritable semaine de tendance à moyen terme. Rédige les prévisions complètes jour par jour, du lundi au dimanche.

RÈGLE D'OR N°3 : CHRONOLOGIE EN BLOCS DE PHASES
- Rédige la chronologie sous forme de 4 phases distinctes : Phase 1 (Montée en puissance), Phase 2 (Pic d'intensité), Phase 3 (Maintien), Phase 4 (Dégradation ou Variable).
- Rédige chaque phase de manière hyper-synthétique, avec seulement 2 lignes maximum.
- Commence impérativement chaque phase par un émoji météo représentatif (ex: ☀️, ⛈️, 🌧️, 💨) suivi du jour et de la date précise. Mets en évidence les températures principales.

RÈGLE D'OR N°4 : RÉGIONS EN LIGNE STRUCTURÉE (POUR LE TABLEAU)
- Rédige obligatoirement une seule ligne contenant exactement ces 4 valeurs séparées par des barres verticales `|` : 
  Température attendue | Niveau de pluie | Risque dominant | Indice de confiance
  Exemple : 18°C à 24°C | Faible | Aucun | 4/5
- Pour le niveau de pluie et le risque, utilise obligatoirement un qualificatif simple et lisible par tous parmi : Très faible, Faible, Modéré, Fort, Très fort (sans longue phrase explicative).

RÈGLE D'OR N°5 : VALEURS DE CARTES ULTRA-COURTES (DASHBOARD ET ALERTE)
- Pour le bandeau d'alerte et le tableau de bord (DASHBOARD), les valeurs doivent être très courtes (1 à 3 mots max) pour être lisibles instantanément :
  - `[DASHBOARD_TEMP_MAX]` : ex: "45°C" (pas de phrase)
  - `[DASHBOARD_TEMP_MIN]` : ex: "22-26°C" (pas de phrase)
  - `[DASHBOARD_DURATION]` : ex: "5 jours" (pas de phrase)
  - `[DASHBOARD_EVOLUTION_TREND]` : ex: "↗️ ↘️" ou "↗️ Hausse"
- Pour les jauges de risques physiques, propose à la fois un score (de 0/5 à 5/5) et une phrase d'interprétation courte :
  - `[INTERP_HEAT]` : ex: "Situation exceptionnelle" ou "Risque élevé"
  - `[INTERP_RAIN]` : ex: "Déficit marqué" ou "Situation normale"
  - `[INTERP_STORM]` : ex: "Risque modéré" ou "Situation calme"
  - `[INTERP_WIND]` : ex: "Situation normale" ou "Risque faible"

RÈGLE D'OR N°6 : RÉDUCTION DRASTIQUE DES TEXTES DÉTAILLÉS (60-70%)
- Le Scénario Majoritaire doit faire ~50-80 mots max, et les Scénarios Alternatif et Minoritaire ~40-60 mots max chacun.
- Utilise des listes à puces pour lister les impacts réels. Mets en gras les valeurs numériques importantes.

RÈGLE D'OR N°7 : PACK MULTI-RÉSEAUX SOCIAUX CONÇU POUR MOBILES
Rédige 5 publications distinctes, spécifiquement adaptées à l'audience de chaque plateforme (LinkedIn, Facebook, X/Twitter, TikTok, Instagram).

RÈGLE D'OR N°8 : FIDÉLITÉ ABSOLUE AUX DONNÉES ET ANALYSES SOURCES (PAS D'EXAGÉRATION)
- Tu ne dois jamais sur-interpréter, accentuer ou exagérer une formulation météo. Si les prévisionnistes parlent de "risque d'orage" ou d'une "tendance incertaine", décris-le exactement comme un risque ou une incertitude. Ne transforme jamais une hypothèse en certitude.
- Ne cherche pas à rendre le titre ou les résumés plus accrocheurs en déformant la réalité scientifique fournie dans les discussions. Conserve strictement le niveau de nuance, les réserves et l'indice de confiance donnés par les experts.

FORMAT DE SORTIE OBLIGATOIRE - Utilise EXACTEMENT ces balises :

[SUBJECT_TITLE_LINE1]
Semaine X - Du Lundi DD au Dimanche DD Mois AAAA

[SUBJECT_TITLE_LINE2]
Accroche météo courte résumant le temps de la semaine avec dates exactes

[ALERT_EVENT_TYPE]
Canicule historique (ou autre type d'événement marquant)

[ALERT_LEVEL]
Rouge (Vert, Jaune, Orange, Rouge)

[ALERT_START]
Jour et date de début de l'alerte (ex: Mercredi 29 Juillet)

[ALERT_END]
Jour et date de fin de l'alerte (ex: Dimanche 2 Août)

[ALERT_TEMP_MAX]
45°C (Température maximale écrite en très grand)

[ALERT_MAIN_RISK]
Canicule, orages, incendies

[ALERT_CONFIDENCE]
4/5

[SUMMARY_10S]
- Début de l'épisode : ...
- Pic attendu : ...
- Température maximale : ...
- Durée : ...
- Principal risque : ...
- Confiance : ...

[EXPRESS_SUMMARY]
2 phrases ultra-concises allant à l'essentiel avec les jours et dates précis

[EXPRESS_TREND]
1 à 3 mots max

[EXPRESS_TEMPERATURES]
1 à 3 mots max

[EXPRESS_PRECIPITATIONS]
1 à 3 mots max

[EXPRESS_MAIN_RISK]
1 à 3 mots max

[GLOBAL_CONFIDENCE_SCORE]
4/5 (ou 3/5, 5/5)

[GLOBAL_CONFIDENCE_DESC]
Une phrase courte expliquant la raison du niveau de confiance.

[DASHBOARD_START]
Lundi 27 Juillet

[DASHBOARD_PIC]
Jeudi 30 Juillet

[DASHBOARD_END]
Dimanche 2 Août

[DASHBOARD_TEMP_MAX]
45°C

[DASHBOARD_TEMP_MIN]
22-26°C

[DASHBOARD_DURATION]
5 jours

[DASHBOARD_CONFIDENCE]
4/5

[DASHBOARD_EVOLUTION_TREND]
↗️ ↘️

[SCORE_HEAT]
Note sur 5 (ex: 3/5)

[INTERP_HEAT]
Situation exceptionnelle

[SCORE_RAIN]
Note sur 5 (ex: 1/5)

[INTERP_RAIN]
Situation normale

[SCORE_STORM]
Note sur 5 (ex: 4/5)

[INTERP_STORM]
Risque élevé

[SCORE_WIND]
Note sur 5 (ex: 2/5)

[INTERP_WIND]
Risque faible

[KEY_NUMBERS]
Valeur 1 | Libellé 1
Valeur 2 | Libellé 2
Valeur 3 | Libellé 3
Valeur 4 | Libellé 4
Valeur 5 | Libellé 5

[TIMELINE_PHASE_1]
Emoji + Montée en puissance (Jours et dates exacts) : Description (2 lignes max).

[TIMELINE_PHASE_2]
Emoji + Pic d'intensité (Jours et dates exacts) : Description (2 lignes max).

[TIMELINE_PHASE_3]
Emoji + Maintien (Jours et dates exacts) : Description (2 lignes max).

[TIMELINE_PHASE_4]
Emoji + Dégradation (Jours et dates exacts) : Description (2 lignes max).

[REGIONAL_HDF_NORTH]
Température | Pluie | Risque dominant | Confiance

[REGIONAL_ATLANTIC]
Température | Pluie | Risque dominant | Confiance

[REGIONAL_CENTRAL]
Température | Pluie | Risque dominant | Confiance

[REGIONAL_SOUTH]
Température | Pluie | Risque dominant | Confiance

[REGIONAL_MEDITERRANEAN]
Température | Pluie | Risque dominant | Confiance

[REGIONAL_MOUNTAINS]
Température | Pluie | Risque dominant | Confiance

[SCENARIO_MAJORITAIRE_PROB]
65%

[SCENARIO_MAJORITAIRE_TITLE]
Titre court

[SCENARIO_MAJORITAIRE_DESC]
Description très concise avec puces pour les impacts (~50-80 mots max)

[SCENARIO_MEDIAN_PROB]
25%

[SCENARIO_MEDIAN_TITLE]
Titre court

[SCENARIO_MEDIAN_DESC]
Description très concise (~40-60 mots max)

[SCENARIO_MINORITAIRE_PROB]
10%

[SCENARIO_MINORITAIRE_TITLE]
Titre court

[SCENARIO_MINORITAIRE_DESC]
Description très concise (~40-60 mots max)

[KEY_UNCERTAINTIES]
- Incertitude 1
- Incertitude 2

[MONITORING_POINTS]
- Point de vigilance 1
- Point de vigilance 2

[KEY_TAKEAWAYS]
- Puce essentielle 1 (5 à 6 puces max)
- Puce essentielle 2
- Puce essentielle 3
- Puce essentielle 4
- Puce essentielle 5
- Puce essentielle 6

[SOCIAL_LINKEDIN]
Post LinkedIn réseaux sociaux captivant en texte brut (250-300 mots)

[SOCIAL_FACEBOOK]
Post Facebook chaleureux et aéré pour grand public

[SOCIAL_TWITTER]
Post X (Twitter) percutant et court (MAXIMUM 280 caractères, espaces compris)

[SOCIAL_TIKTOK]
Description TikTok avec accroches, émojis et hashtags ciblés

[SOCIAL_INSTAGRAM]
Légende Instagram soignée et esthétique

[LINKEDIN_HASHTAGS]
#Meteo #Previsions #France #Climat #MonsieurMeteo"""

    user_prompt = f"""Contexte de date : {date_context_str}

Voici les 20 derniers messages des prévisionnistes pour le sujet : {topic_title_clean}

{recent_messages_text}

Analyse ces discussions en appliquant scrupuleusement la vérification de cohérence et génère le rapport complet."""

    response = call_llm(system_prompt, user_prompt)
    
    data = None
    if response:
        try:
            print(f"[{topic_idx+1}] Parsing de la réponse de l'IA...")
            blocks = {
                "title_line1": r"\[SUBJECT_TITLE_LINE1\]\s*\n(.*?)(?=\n\s*\[|$)",
                "title_line2": r"\[SUBJECT_TITLE_LINE2\]\s*\n(.*?)(?=\n\s*\[|$)",
                
                "alert_event_type": r"\[ALERT_EVENT_TYPE\]\s*\n(.*?)(?=\n\s*\[|$)",
                "alert_level": r"\[ALERT_LEVEL\]\s*\n(.*?)(?=\n\s*\[|$)",
                "alert_start": r"\[ALERT_START\]\s*\n(.*?)(?=\n\s*\[|$)",
                "alert_end": r"\[ALERT_END\]\s*\n(.*?)(?=\n\s*\[|$)",
                "alert_temp_max": r"\[ALERT_TEMP_MAX\]\s*\n(.*?)(?=\n\s*\[|$)",
                "alert_main_risk": r"\[ALERT_MAIN_RISK\]\s*\n(.*?)(?=\n\s*\[|$)",
                "alert_confidence": r"\[ALERT_CONFIDENCE\]\s*\n(.*?)(?=\n\s*\[|$)",

                "summary_10s": r"\[SUMMARY_10S\]\s*\n(.*?)(?=\n\s*\[|$)",

                "express_summary": r"\[EXPRESS_SUMMARY\]\s*\n(.*?)(?=\n\s*\[|$)",
                "express_trend": r"\[EXPRESS_TREND\]\s*\n(.*?)(?=\n\s*\[|$)",
                "express_temperatures": r"\[EXPRESS_TEMPERATURES\]\s*\n(.*?)(?=\n\s*\[|$)",
                "express_precipitations": r"\[EXPRESS_PRECIPITATIONS\]\s*\n(.*?)(?=\n\s*\[|$)",
                "express_main_risk": r"\[EXPRESS_MAIN_RISK\]\s*\n(.*?)(?=\n\s*\[|$)",
                
                "global_confidence_score": r"\[GLOBAL_CONFIDENCE_SCORE\]\s*\n(.*?)(?=\n\s*\[|$)",
                "global_confidence_desc": r"\[GLOBAL_CONFIDENCE_DESC\]\s*\n(.*?)(?=\n\s*\[|$)",

                "dashboard_start": r"\[DASHBOARD_START\]\s*\n(.*?)(?=\n\s*\[|$)",
                "dashboard_pic": r"\[DASHBOARD_PIC\]\s*\n(.*?)(?=\n\s*\[|$)",
                "dashboard_end": r"\[DASHBOARD_END\]\s*\n(.*?)(?=\n\s*\[|$)",
                "dashboard_temp_max": r"\[DASHBOARD_TEMP_MAX\]\s*\n(.*?)(?=\n\s*\[|$)",
                "dashboard_temp_min": r"\[DASHBOARD_TEMP_MIN\]\s*\n(.*?)(?=\n\s*\[|$)",
                "dashboard_duration": r"\[DASHBOARD_DURATION\]\s*\n(.*?)(?=\n\s*\[|$)",
                "dashboard_confidence": r"\[DASHBOARD_CONFIDENCE\]\s*\n(.*?)(?=\n\s*\[|$)",
                "dashboard_evolution_trend": r"\[DASHBOARD_EVOLUTION_TREND\]\s*\n(.*?)(?=\n\s*\[|$)",
                
                "score_heat": r"\[SCORE_HEAT\]\s*\n(.*?)(?=\n\s*\[|$)",
                "interp_heat": r"\[INTERP_HEAT\]\s*\n(.*?)(?=\n\s*\[|$)",
                "score_rain": r"\[SCORE_RAIN\]\s*\n(.*?)(?=\n\s*\[|$)",
                "interp_rain": r"\[INTERP_RAIN\]\s*\n(.*?)(?=\n\s*\[|$)",
                "score_storm": r"\[SCORE_STORM\]\s*\n(.*?)(?=\n\s*\[|$)",
                "interp_storm": r"\[INTERP_STORM\]\s*\n(.*?)(?=\n\s*\[|$)",
                "score_wind": r"\[SCORE_WIND\]\s*\n(.*?)(?=\n\s*\[|$)",
                "interp_wind": r"\[INTERP_WIND\]\s*\n(.*?)(?=\n\s*\[|$)",
                "key_numbers": r"\[KEY_NUMBERS\]\s*\n(.*?)(?=\n\s*\[|$)",

                "timeline_phase_1": r"\[TIMELINE_PHASE_1\]\s*\n(.*?)(?=\n\s*\[|$)",
                "timeline_phase_2": r"\[TIMELINE_PHASE_2\]\s*\n(.*?)(?=\n\s*\[|$)",
                "timeline_phase_3": r"\[TIMELINE_PHASE_3\]\s*\n(.*?)(?=\n\s*\[|$)",
                "timeline_phase_4": r"\[TIMELINE_PHASE_4\]\s*\n(.*?)(?=\n\s*\[|$)",

                "regional_hdf_north": r"\[REGIONAL_HDF_NORTH\]\s*\n(.*?)(?=\n\s*\[|$)",
                "regional_atlantic": r"\[REGIONAL_ATLANTIC\]\s*\n(.*?)(?=\n\s*\[|$)",
                "regional_central": r"\[REGIONAL_CENTRAL\]\s*\n(.*?)(?=\n\s*\[|$)",
                "regional_south": r"\[REGIONAL_SOUTH\]\s*\n(.*?)(?=\n\s*\[|$)",
                "regional_mediterranean": r"\[REGIONAL_MEDITERRANEAN\]\s*\n(.*?)(?=\n\s*\[|$)",
                "regional_mountains": r"\[REGIONAL_MOUNTAINS\]\s*\n(.*?)(?=\n\s*\[|$)",
                
                "majoritaire_prob": r"\[SCENARIO_MAJORITAIRE_PROB\]\s*\n(.*?)(?=\n\s*\[|$)",
                "majoritaire_title": r"\[SCENARIO_MAJORITAIRE_TITLE\]\s*\n(.*?)(?=\n\s*\[|$)",
                "majoritaire_desc": r"\[SCENARIO_MAJORITAIRE_DESC\]\s*\n(.*?)(?=\n\s*\[|$)",
                
                "median_prob": r"\[SCENARIO_MEDIAN_PROB\]\s*\n(.*?)(?=\n\s*\[|$)",
                "median_title": r"\[SCENARIO_MEDIAN_TITLE\]\s*\n(.*?)(?=\n\s*\[|$)",
                "median_desc": r"\[SCENARIO_MEDIAN_DESC\]\s*\n(.*?)(?=\n\s*\[|$)",
                
                "minoritaire_prob": r"\[SCENARIO_MINORITAIRE_PROB\]\s*\n(.*?)(?=\n\s*\[|$)",
                "minoritaire_title": r"\[SCENARIO_MINORITAIRE_TITLE\]\s*\n(.*?)(?=\n\s*\[|$)",
                "minoritaire_desc": r"\[SCENARIO_MINORITAIRE_DESC\]\s*\n(.*?)(?=\n\s*\[|$)",
                
                "key_uncertainties": r"\[KEY_UNCERTAINTIES\]\s*\n(.*?)(?=\n\s*\[|$)",
                "monitoring_points": r"\[MONITORING_POINTS\]\s*\n(.*?)(?=\n\s*\[|$)",
                "key_takeaways": r"\[KEY_TAKEAWAYS\]\s*\n(.*?)(?=\n\s*\[|$)",
                
                "social_linkedin": r"\[SOCIAL_LINKEDIN\]\s*\n(.*?)(?=\n\s*\[|$)",
                "social_facebook": r"\[SOCIAL_FACEBOOK\]\s*\n(.*?)(?=\n\s*\[|$)",
                "social_twitter": r"\[SOCIAL_TWITTER\]\s*\n(.*?)(?=\n\s*\[|$)",
                "social_tiktok": r"\[SOCIAL_TIKTOK\]\s*\n(.*?)(?=\n\s*\[|$)",
                "social_instagram": r"\[SOCIAL_INSTAGRAM\]\s*\n(.*?)(?=\n\s*\[|$)",
                "linkedin_hashtags": r"\[LINKEDIN_HASHTAGS\]\s*\n(.*?)(?=\n\s*\[|$)",
            }
            
            parsed = {}
            for key, pattern in blocks.items():
                match = re.search(pattern, response, re.DOTALL)
                if match:
                    parsed[key] = match.group(1).strip()
                else:
                    parsed[key] = ""
            
            if (parsed["title_line1"] or parsed["title_line2"]) and (parsed["express_summary"] or parsed["majoritaire_desc"]):
                data = {
                    "title_line1": parsed["title_line1"] or topic_title_clean,
                    "title_line2": parsed["title_line2"] or "Tendances et synthèses météorologiques",
                    
                    "alert": {
                        "event_type": parsed["alert_event_type"],
                        "level": parsed["alert_level"] or "Vert",
                        "start": parsed["alert_start"],
                        "end": parsed["alert_end"],
                        "temp_max": parsed["alert_temp_max"],
                        "main_risk": parsed["alert_main_risk"],
                        "confidence": parsed["alert_confidence"],
                    },
                    "summary_10s": parsed["summary_10s"],
                    
                    "express": {
                        "summary": parsed["express_summary"],
                        "trend": parsed["express_trend"],
                        "temperatures": parsed["express_temperatures"],
                        "precipitations": parsed["express_precipitations"],
                        "main_risk": parsed["express_main_risk"],
                    },
                    "confidence": {
                        "score": parsed["global_confidence_score"] or "4/5",
                        "desc": parsed["global_confidence_desc"],
                    },
                    "dashboard": {
                        "start": parsed["dashboard_start"],
                        "pic": parsed["dashboard_pic"],
                        "end": parsed["dashboard_end"],
                        "temp_max": parsed["dashboard_temp_max"],
                        "temp_min": parsed["dashboard_temp_min"],
                        "duration": parsed["dashboard_duration"],
                        "confidence": parsed["dashboard_confidence"],
                        "evolution_trend": parsed["dashboard_evolution_trend"],
                        "score_heat": parsed["score_heat"] or "0/5",
                        "interp_heat": parsed["interp_heat"] or "Situation normale",
                        "score_rain": parsed["score_rain"] or "0/5",
                        "interp_rain": parsed["interp_rain"] or "Situation normale",
                        "score_storm": parsed["score_storm"] or "0/5",
                        "interp_storm": parsed["interp_storm"] or "Situation normale",
                        "score_wind": parsed["score_wind"] or "0/5",
                        "interp_wind": parsed["interp_wind"] or "Situation normale",
                    },
                    "key_numbers": parsed["key_numbers"],
                    "timeline": {
                        "phase_1": parsed["timeline_phase_1"],
                        "phase_2": parsed["timeline_phase_2"],
                        "phase_3": parsed["timeline_phase_3"],
                        "phase_4": parsed["timeline_phase_4"],
                    },
                    "regional": {
                        "hdf_north": parsed["regional_hdf_north"],
                        "atlantic": parsed["regional_atlantic"],
                        "central": parsed["regional_central"],
                        "south": parsed["regional_south"],
                        "mediterranean": parsed["regional_mediterranean"],
                        "mountains": parsed["regional_mountains"],
                    },
                    "scenarios": {
                        "majoritaire": {"prob": parsed["majoritaire_prob"] or "65%", "title": parsed["majoritaire_title"] or "Scénario Majoritaire", "desc": parsed["majoritaire_desc"]},
                        "median": {"prob": parsed["median_prob"] or "25%", "title": parsed["median_title"] or "Scénario Alternatif", "desc": parsed["median_desc"]},
                        "minoritaire": {"prob": parsed["minoritaire_prob"] or "10%", "title": parsed["minoritaire_title"] or "Scénario Minoritaire", "desc": parsed["minoritaire_desc"]}
                    },
                    "key_uncertainties": parsed["key_uncertainties"],
                    "monitoring_points": parsed["monitoring_points"],
                    "key_takeaways": parsed["key_takeaways"],
                    "social_pack": {
                        "linkedin": parsed["social_linkedin"],
                        "facebook": parsed["social_facebook"],
                        "twitter": parsed["social_twitter"],
                        "tiktok": parsed["social_tiktok"],
                        "instagram": parsed["social_instagram"],
                    },
                    "linkedin_hashtags": parsed["linkedin_hashtags"],
                }
                print(f"[{topic_idx+1}] Parsing textuel réussi avec succès !")
        except Exception as e:
            print(f"Erreur parsing : {e}")
            
    return {"data": data, "images": downloaded_images}
def main():
    def parse_region_line(region_str):
        if not region_str:
            return ["-", "-", "-", "-"]
        parts = [p.strip() for p in region_str.split("|")]
        while len(parts) < 4:
            parts.append("-")
        return parts[:4]

    def parse_score(val):
        if not val:
            return 0
        match = re.search(r'(\d+)', val)
        if match:
            num = int(match.group(1))
            if num <= 5:
                return num
            elif num <= 100:
                return round(num / 20)
        return 0

    def extract_emoji_and_text(text_str):
        if not text_str:
            return "🌤️", "-"
        emoji_match = re.match(r'^([𐀀-􏿿☀-⟿⭐⬆←-⇿⛅⛈⚡☂☁☀]+)\s*(.*)', text_str)
        if emoji_match:
            return emoji_match.group(1), emoji_match.group(2)
        return "🌤️", text_str

    def get_score_label(score_val):
        score = parse_score(score_val)
        labels = {
            0: "Très faible",
            1: "Très faible",
            2: "Faible",
            3: "Modéré",
            4: "Élevé",
            5: "Très élevé"
        }
        return labels.get(score, "Modéré")

    def get_level_badge(val):
        val_clean = val.strip().lower()
        if "très fort" in val_clean or "tres fort" in val_clean:
            return '<span class="badge-level-tres-fort">🔴 Très fort</span>'
        elif "fort" in val_clean:
            return '<span class="badge-level-fort">🟠 Fort</span>'
        elif "modéré" in val_clean or "modere" in val_clean:
            return '<span class="badge-level-modere">🟡 Modéré</span>'
        elif "très faible" in val_clean or "tres faible" in val_clean:
            return '<span class="badge-level-tres-faible">⚪ Très faible</span>'
        elif "faible" in val_clean:
            return '<span class="badge-level-faible">🔵 Faible</span>'
        else:
            return f'<span class="badge-level-modere">{val}</span>'

    def get_conf_badge(val):
        val_clean = val.strip().lower()
        if "5/5" in val_clean or "très élevé" in val_clean:
            return '<span class="badge-level-tres-fort" style="background:#d1fae5; color:#065f46;">🟢 Très élevé</span>'
        elif "4/5" in val_clean or "élevé" in val_clean:
            return '<span class="badge-level-fort" style="background:#d1fae5; color:#065f46;">🟢 Élevé</span>'
        elif "3/5" in val_clean or "modéré" in val_clean:
            return '<span class="badge-level-modere" style="background:#fef3c7; color:#92400e;">🟡 Modéré</span>'
        elif "2/5" in val_clean or "faible" in val_clean:
            return '<span class="badge-level-faible" style="background:#fee2e2; color:#991b1b;">🔴 Faible</span>'
        elif "1/5" in val_clean or "très faible" in val_clean:
            return '<span class="badge-level-tres-faible" style="background:#fee2e2; color:#991b1b;">🔴 Très faible</span>'
        else:
            return f'<span class="badge-level-modere" style="background:#f1f5f9; color:#475569;">{val}</span>'

    def get_badge_color_class(label):
        l = label.lower()
        if "très élevé" in l or "très fort" in l:
            return "background-color: #dc2626;"
        elif "élevé" in l or "fort" in l:
            return "background-color: #ea580c;"
        elif "modéré" in l:
            return "background-color: #eab308;"
        elif "faible" in l:
            return "background-color: #2563eb;"
        else:
            return "background-color: #6b7280;"

    print(f"1. Chargement de l'index du forum : {INDEX_URL}")
    try:
        html_index = fetch_url(INDEX_URL)
    except Exception as e:
        print(f"Erreur index : {e}")
        sys.exit(1)
        
    topic_links = re.findall(r'href=["\'](https://forums.infoclimat.fr/f/topic/\d+-[^"\']+)["\']', html_index)
    
    # Élimination des doublons et filtrage des prévisions
    clean_topics = []
    seen = set()
    for link in topic_links:
        base_link = link.split('?')[0].strip()
        if base_link not in seen and ("previsions" in base_link or "pr%C3%A9visions" in base_link or "semaine" in base_link):
            seen.add(base_link)
            clean_topics.append(base_link)
            
    if not clean_topics:
        print("Aucun sujet de prévisions trouvé.")
        sys.exit(1)
        
    # Calcul dynamique des dates de référence en français
    now = datetime.datetime.now()
    DAYS_FR = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
    MONTHS_FR = ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin", "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"]
    
    def get_french_date(dt):
        return f"{DAYS_FR[dt.weekday()]} {dt.day} {MONTHS_FR[dt.month - 1]} {dt.year}"
        
    def fmt_date_range(d1, d2):
        m1 = MONTHS_FR[d1.month - 1]
        m2 = MONTHS_FR[d2.month - 1]
        if m1 == m2:
            return f"du Lundi {d1.day} au Dimanche {d2.day} {m1} {d1.year}"
        else:
            return f"du Lundi {d1.day} {m1} au Dimanche {d2.day} {m2} {d1.year}"
            
    lundi_cours = now - datetime.timedelta(days=now.weekday())
    dimanche_cours = lundi_cours + datetime.timedelta(days=6)
    lundi_suiv = lundi_cours + datetime.timedelta(days=7)
    dimanche_suiv = lundi_suiv + datetime.timedelta(days=6)
    
    today_str = get_french_date(now)
    semaine_cours_str = fmt_date_range(lundi_cours, dimanche_cours)
    semaine_suivante_str = fmt_date_range(lundi_suiv, dimanche_suiv)
    jours_restants_cours_str = f"du {DAYS_FR[now.weekday()]} {now.day} {MONTHS_FR[now.month-1]} au Dimanche {dimanche_cours.day} {MONTHS_FR[dimanche_cours.month-1]} {dimanche_cours.year}"

    # Semaine future en premier, Semaine en cours en second
    topics_to_process = []
    if len(clean_topics) >= 2:
        topics_to_process = [
            (clean_topics[0], "future", f"Date actuelle de génération : {today_str}\nType de semaine : Semaine suivante (Tendance à moyen terme)\nPériode à analyser : {semaine_suivante_str} (semaine complète)."),
            (clean_topics[1], "cours", f"Date actuelle de génération : {today_str}\nType de semaine : Semaine en cours\nPériode à analyser : {jours_restants_cours_str} (jours restants uniquement). Les journées antérieures au {today_str} sont déjà passées, concentre-toi sur la fin de semaine.")
        ]
    else:
        topics_to_process = [
            (clean_topics[0], "cours", f"Date actuelle de génération : {today_str}\nSemaine en cours : {semaine_cours_str} (jours restants à prévoir : {jours_restants_cours_str})\nSemaine suivante : {semaine_suivante_str}.\nDétermine selon le titre du sujet s'il s'agit de la semaine en cours ou de la semaine suivante, et applique les règles correspondantes.")
        ]
        
    results = []
    for idx, (topic, sem_type, date_context) in enumerate(topics_to_process):
        res = process_topic(topic, idx, date_context)
        if res:
            results.append(res)
            
    if not results:
        print("Aucun sujet n'a pu être traité.")
        sys.exit(1)
        
    # Style CSS Premium & Responsive (Design System v4)
    style = """
    :root {
        --font-sans: 'Segoe UI', system-ui, -apple-system, sans-serif;
        --text-xs: 11px;
        --text-sm: 13px;
        --text-base: 14.5px;
        --text-lg: 16px;
        --text-xl: 20px;
        --text-huge: 72px;
        --radius-lg: 24px;
        --radius-md: 16px;
        --radius-sm: 10px;
        --spacing-xs: 10px;
        --spacing-sm: 15px;
        --spacing-md: 24px;
        --spacing-lg: 35px;
    }
    body { font-family: var(--font-sans); font-size: var(--text-base); line-height: 1.6; color: #0f172a; background-color: #f1f5f9; margin: 0; padding: 25px 12px; }
    .container { max-width: 900px; background-color: #ffffff; margin: 0 auto; border-radius: var(--radius-lg); overflow: hidden; box-shadow: 0 20px 40px rgba(0, 0, 0, 0.04); border: 1px solid #e2e8f0; }
    .header { background: linear-gradient(135deg, #0b0f19 0%, #1e293b 100%); color: #ffffff; padding: 45px 30px; text-align: center; position: relative; }
    .header::after { content: ''; position: absolute; bottom: 0; left: 0; right: 0; height: 6px; background: linear-gradient(90deg, #2563eb, #7c3aed, #ec4899); }
    .header h1 { margin: 0; font-size: 26px; font-weight: 900; letter-spacing: -0.5px; text-transform: uppercase; }
    .header p { margin: 8px 0 0 0; font-size: 13px; opacity: 0.85; font-weight: 500; }
    .content { padding: var(--spacing-lg) 30px; display: flex; flex-direction: column; gap: var(--spacing-lg); }
    .week-divider { border-top: 4px dashed #cbd5e1; margin: var(--spacing-lg) 0; }
    
    .week-title-box { padding-left: 20px; border-left: 6px solid #2563eb; }
    .week-title-line1 { font-size: var(--text-xl); font-weight: 900; color: #0f172a; text-transform: uppercase; letter-spacing: 0.5px; margin: 0; }
    .week-title-line2 { font-size: var(--text-base); font-weight: 600; color: #64748b; margin-top: 6px; }

    .section-title { font-size: var(--text-xs); font-weight: 850; text-transform: uppercase; letter-spacing: 1.5px; color: #475569; border-bottom: 2px solid #f1f5f9; padding-bottom: 8px; display: flex; align-items: center; gap: 8px; margin: 0; }
    
    /* Bandeau d'alerte supérieur */
    .alert-banner { padding: 30px; color: #ffffff; border-radius: var(--radius-md); box-shadow: 0 10px 25px rgba(0, 0, 0, 0.05); display: flex; flex-direction: column; gap: 20px; position: relative; overflow: hidden; }
    .alert-banner-Rouge { background: linear-gradient(135deg, #7f1d1d 0%, #dc2626 100%); }
    .alert-banner-Orange { background: linear-gradient(135deg, #7c2d12 0%, #ea580c 100%); }
    .alert-banner-Jaune { background: linear-gradient(135deg, #713f12 0%, #eab308 100%); }
    .alert-banner-Vert { background: linear-gradient(135deg, #064e3b 0%, #10b981 100%); }
    
    .alert-main-row { display: flex; justify-content: space-between; align-items: center; gap: 20px; }
    .alert-left { display: flex; flex-direction: column; gap: 8px; }
    .alert-badge-top { font-size: 9px; font-weight: 900; background: rgba(255,255,255,0.22); padding: 5px 12px; border-radius: 9999px; text-transform: uppercase; align-self: flex-start; letter-spacing: 1px; }
    .alert-title-lg { font-size: 26px; font-weight: 900; line-height: 1.1; text-transform: uppercase; margin: 0; letter-spacing: -0.5px; }
    .alert-date-block { display: flex; flex-direction: column; font-size: var(--text-xs); background: rgba(0,0,0,0.25); padding: 8px 14px; border-radius: var(--radius-sm); font-weight: 700; max-width: fit-content; margin-top: 4px; }
    
    .alert-right-temp { font-size: 84px; font-weight: 900; line-height: 1; letter-spacing: -3px; display: flex; align-items: flex-start; text-shadow: 0 4px 15px rgba(0,0,0,0.15); }
    .alert-right-temp span { font-size: 42px; margin-top: 5px; }

    .alert-details-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; border-top: 1px solid rgba(255,255,255,0.2); padding-top: 15px; }
    .alert-detail-item { display: flex; flex-direction: column; }
    .alert-detail-lbl { font-size: 9px; font-weight: 800; text-transform: uppercase; opacity: 0.8; letter-spacing: 0.5px; margin-bottom: 2px; }
    .alert-detail-val { font-size: var(--text-base); font-weight: 800; }

    /* Résumé 10 secondes */
    .summary-10s-box { background: #f8fafc; border: 1px solid #cbd5e1; border-left: 6px solid #2563eb; border-radius: var(--radius-md); padding: 22px; }
    .summary-10s-box h3 { margin: 0 0 12px 0; font-size: var(--text-sm); font-weight: 850; color: #1e293b; text-transform: uppercase; letter-spacing: 1px; }
    .summary-10s-list { margin: 0; padding: 0; list-style: none; font-size: var(--text-sm); color: #334155; line-height: 1.6; }
    .summary-10s-list li { margin-bottom: 6px; padding-left: 18px; position: relative; }
    .summary-10s-list li::before { content: '•'; position: absolute; left: 0; color: #2563eb; font-weight: 900; }

    /* Dashboard Redesigned (3 colonnes larges & clean) */
    .dashboard-grid-10 { display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; }
    @media (max-width: 600px) {
        .dashboard-grid-10 { grid-template-columns: repeat(2, 1fr); }
    }
    .dash-card-10 { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: var(--radius-md); padding: 18px; text-align: center; display: flex; flex-direction: column; align-items: center; justify-content: space-between; min-height: 130px; transition: transform 0.2s; position: relative; }
    .dash-card-10:hover { transform: translateY(-2px); box-shadow: 0 10px 20px rgba(0, 0, 0, 0.02); }
    .dash-card-10-icon { font-size: 18px; width: 32px; height: 32px; display: flex; align-items: center; justify-content: center; border-radius: 50%; margin-bottom: 6px; }
    
    .dc-temp-max { border-top: 4px solid #dc2626; }
    .dc-temp-max .dash-card-10-icon { background: #fee2e2; }
    .dc-temp-min { border-top: 4px solid #2563eb; }
    .dc-temp-min .dash-card-10-icon { background: #dbeafe; }
    .dc-start { border-top: 4px solid #4b5563; }
    .dc-start .dash-card-10-icon { background: #f3f4f6; }
    .dc-pic { border-top: 4px solid #ea580c; }
    .dc-pic .dash-card-10-icon { background: #ffedd5; }
    .dc-end { border-top: 4px solid #4b5563; }
    .dc-end .dash-card-10-icon { background: #f3f4f6; }
    .dc-duration { border-top: 4px solid #10b981; }
    .dc-duration .dash-card-10-icon { background: #d1fae5; }
    .dc-conf { border-top: 4px solid #7c3aed; }
    .dc-conf .dash-card-10-icon { background: #f3e8ff; }
    .dc-trend { border-top: 4px solid #06b6d4; }
    .dc-trend .dash-card-10-icon { background: #ecfeff; }
    
    .dash-card-10-val { font-size: 22px; font-weight: 900; margin-bottom: 2px; color: #0f172a; line-height: 1.1; letter-spacing: -0.5px; }
    .dash-card-10-lbl { font-size: 9.5px; font-weight: 800; color: #64748b; text-transform: uppercase; }

    /* Jauges et scores */
    .dashboard-meters-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }
    @media (max-width: 768px) {
        .dashboard-meters-row { grid-template-columns: repeat(2, 1fr); }
    }
    @media (max-width: 480px) {
        .dashboard-meters-row { grid-template-columns: 1fr; }
    }
    .meter-card-premium { background: #f8fafc; border: 1px solid #cbd5e1; border-radius: var(--radius-md); padding: 14px; display: flex; flex-direction: column; gap: 8px; }
    .meter-card-header { display: flex; align-items: center; justify-content: space-between; }
    .meter-card-header h4 { margin: 0; font-size: var(--text-xs); font-weight: 850; color: #475569; text-transform: uppercase; letter-spacing: 0.5px; }
    .meter-badge { font-size: 8.5px; font-weight: 900; padding: 3px 10px; border-radius: 9999px; text-transform: uppercase; color: #ffffff; }
    .mb-chaleur { background-color: #dc2626; }
    .mb-pluie { background-color: #2563eb; }
    .mb-orage { background-color: #7c3aed; }
    .mb-vent { background-color: #4b5563; }
    
    .meter-track-premium { width: 100%; height: 8px; background: #e2e8f0; border-radius: 9999px; overflow: hidden; }
    .meter-fill-premium { height: 100%; border-radius: 9999px; }
    .mf-heat { background: linear-gradient(90deg, #fca5a5, #dc2626); }
    .mf-rain { background: linear-gradient(90deg, #93c5fd, #2563eb); }
    .mf-storm { background: linear-gradient(90deg, #c084fc, #7c3aed); }
    .mf-wind { background: linear-gradient(90deg, #cbd5e1, #4b5563); }
    
    .meter-info { display: flex; align-items: center; justify-content: space-between; font-size: var(--text-xs); font-weight: 800; color: #1e293b; }
    .meter-lbl-text { text-transform: uppercase; font-size: 8.5px; letter-spacing: 0.5px; color: #0284c7; }

    /* Chiffres à retenir */
    .numbers-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 12px; }
    @media (max-width: 768px) {
        .numbers-grid { grid-template-columns: repeat(2, 1fr); }
    }
    @media (max-width: 480px) {
        .numbers-grid { grid-template-columns: 1fr; }
    }
    .number-card { background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%); border: 1px solid #cbd5e1; border-radius: var(--radius-md); padding: 15px; text-align: center; }
    .number-val { font-size: 24px; font-weight: 900; color: #1e3a8a; line-height: 1.1; margin-bottom: 2px; }
    .number-lbl { font-size: 9.5px; font-weight: 800; color: #475569; line-height: 1.3; }

    /* Chronologie par blocs de phases colorés connectés */
    .timeline-phases-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }
    @media (max-width: 768px) {
        .timeline-phases-grid { grid-template-columns: 1fr; }
    }
    .phase-block { border-radius: var(--radius-md); padding: 18px; border: 1px solid #e2e8f0; display: flex; flex-direction: column; gap: 8px; position: relative; }
    .pb-phase1 { background: linear-gradient(135deg, #fef3c7 0%, #fffbeb 100%); border-left: 6px solid #eab308; }
    .pb-phase1 .phase-name { color: #b45309; }
    .pb-phase2 { background: linear-gradient(135deg, #fee2e2 0%, #fef2f2 100%); border-left: 6px solid #dc2626; }
    .pb-phase2 .phase-name { color: #b91c1c; }
    .pb-phase3 { background: linear-gradient(135deg, #ffedd5 0%, #fff7ed 100%); border-left: 6px solid #ea580c; }
    .pb-phase3 .phase-name { color: #c2410c; }
    .pb-phase4 { background: linear-gradient(135deg, #dbeafe 0%, #eff6ff 100%); border-left: 6px solid #2563eb; }
    .pb-phase4 .phase-name { color: #1d4ed8; }
    
    .phase-header { display: flex; justify-content: space-between; align-items: center; }
    .phase-name { font-size: 10px; font-weight: 900; text-transform: uppercase; letter-spacing: 0.8px; }
    .phase-emoji { font-size: 22px; }
    .phase-title { font-size: var(--text-sm); font-weight: 900; color: #0f172a; line-height: 1.2; text-transform: uppercase; }
    .phase-desc { margin: 0; font-size: 12px; color: #334155; line-height: 1.5; }

    /* Tableau régional épuré */
    .table-responsive { width: 100%; overflow-x: auto; border-radius: var(--radius-md); border: 1px solid #cbd5e1; box-shadow: 0 4px 6px rgba(0,0,0,0.01); }
    .regional-table { width: 100%; border-collapse: collapse; text-align: left; font-size: var(--text-sm); }
    .regional-table th { background-color: #0f172a; color: #ffffff; font-weight: 900; text-transform: uppercase; letter-spacing: 0.5px; padding: 12px 15px; border-bottom: 2px solid #cbd5e1; }
    .regional-table td { padding: 12px 15px; border-bottom: 1px solid #cbd5e1; color: #334155; }
    .regional-table tr:last-child td { border-bottom: none; }
    .badge-temp { font-weight: 900; color: #ffffff; background: #dc2626; padding: 5px 10px; border-radius: 8px; font-size: 12.5px; display: inline-block; box-shadow: 0 2px 5px rgba(220,38,38,0.15); }

    /* Graphiques Météo plein format */
    .meteo-images-container { display: flex; flex-direction: column; gap: 25px; }
    .meteo-image-card { background-color: #ffffff; border: 1px solid #cbd5e1; border-radius: var(--radius-lg); padding: 20px; box-shadow: 0 10px 20px rgba(0,0,0,0.01); text-align: center; }
    .meteo-image-card span { font-weight: 900; font-size: var(--text-sm); color: #0f172a; display: block; margin-bottom: 12px; text-transform: uppercase; letter-spacing: 0.5px; }
    .meteo-image-card img { width: 100%; height: auto; border-radius: var(--radius-md); border: 1px solid #e2e8f0; }

    /* Section Analyse Détaillée */
    .detailed-analysis-panel { background: #f8fafc; border-radius: var(--radius-lg); padding: 25px; border: 1px solid #cbd5e1; display: flex; flex-direction: column; gap: 20px; }
    .detailed-analysis-title { font-size: 14px; font-weight: 900; text-transform: uppercase; letter-spacing: 1.5px; color: #0f172a; margin: 0; display: flex; align-items: center; gap: 8px; border-bottom: 2px solid #cbd5e1; padding-bottom: 8px; }

    .scenarios-container { display: flex; flex-direction: column; gap: 12px; }
    .scenario-card { border-radius: var(--radius-md); padding: 16px; border: 1px solid #cbd5e1; background: #ffffff; }
    .sc-major { border-left: 6px solid #10b981; }
    .sc-median { border-left: 6px solid #f59e0b; }
    .sc-minor { border-left: 6px solid #ef4444; }
    .sc-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
    .sc-header h3 { margin: 0; font-size: 13.5px; font-weight: 900; color: #0f172a; text-transform: uppercase; }
    .sc-prob { font-size: 10px; padding: 3px 10px; border-radius: 9999px; color: #ffffff; font-weight: 900; }
    .bg-major { background-color: #10b981; }
    .bg-median { background-color: #f59e0b; }
    .bg-minor { background-color: #ef4444; }
    .sc-text { margin: 0; font-size: 12.5px; line-height: 1.5; color: #334155; }
    .sc-text ul { margin: 6px 0 0 0; padding-left: 15px; }
    .sc-text li { margin-bottom: 3px; }

    .confidence-panel { background: #ffffff; border-radius: var(--radius-md); padding: 18px; border: 1px solid #cbd5e1; display: flex; flex-direction: column; gap: 10px; }
    .confidence-head { display: flex; justify-content: space-between; align-items: center; }
    .confidence-head strong { font-size: var(--text-sm); color: #0f172a; text-transform: uppercase; letter-spacing: 0.5px; }
    .uncertainties-box { background: #fff1f2; border-radius: var(--radius-sm); padding: 15px; border: 1px solid #fecdd3; border-left: 5px solid #f43f5e; font-size: 12.5px; color: #334155; line-height: 1.5; }
    .uncertainties-box ul { margin: 5px 0 0 0; padding-left: 15px; }
    .uncertainties-box li { margin-bottom: 3px; }

    .takeaways-panel { background: #f0fdf4; border: 1px solid #bbf7d0; border-left: 6px solid #10b981; border-radius: var(--radius-md); padding: 18px; }
    .takeaways-panel h3 { margin: 0 0 10px 0; font-size: var(--text-sm); font-weight: 900; color: #166534; text-transform: uppercase; letter-spacing: 0.5px; }
    .takeaways-panel ul { margin: 0; padding-left: 15px; color: #15803d; font-size: 12.5px; line-height: 1.55; }
    .takeaways-panel li { margin-bottom: 4px; }

    /* Pack Réseaux Sociaux */
    .social-pack-container { display: flex; flex-direction: column; gap: 15px; }
    .social-platform-card { background: #ffffff; border: 1px solid #cbd5e1; border-radius: var(--radius-md); overflow: hidden; }
    .social-platform-header { display: flex; align-items: center; justify-content: space-between; padding: 12px 18px; font-weight: 900; font-size: 12px; color: #ffffff; text-transform: uppercase; letter-spacing: 0.5px; }
    .sp-linkedin { background: #0077b5; }
    .sp-facebook { background: #1877f2; }
    .sp-twitter { background: #0f1419; }
    .sp-tiktok { background: #fe2c55; }
    .sp-instagram { background: linear-gradient(45deg, #f09433 0%, #e6683c 25%, #dc2743 50%, #cc2366 75%, #bc1888 100%); }
    .social-platform-body { padding: 16px; font-size: 12.5px; white-space: pre-wrap; color: #334155; line-height: 1.6; font-family: var(--font-sans); }
    .copy-btn { background: rgba(255, 255, 255, 0.22); border: none; color: #ffffff; font-size: 9px; font-weight: 800; padding: 4px 10px; border-radius: 6px; cursor: pointer; text-transform: uppercase; letter-spacing: 0.5px; }
    .copy-btn:hover { background: rgba(255, 255, 255, 0.35); }
    """

    weeks_html = ""
    for w_idx, w_res in enumerate(results):
        data = w_res["data"]
        downloaded_images = w_res["images"]
        
        # Encodage des graphiques
        html_images_block = ""
        for idx, img_path in enumerate(downloaded_images):
            try:
                with open(img_path, "rb") as f_img:
                    img_b64 = base64.b64encode(f_img.read()).decode('ascii')
                ext = img_path.split('.')[-1]
                html_images_block += f"""
                <div class="meteo-image-card">
                    <span>📈 Modélisation Météo {idx+1}</span>
                    <img src="data:image/{ext};base64,{img_b64}" alt="Graphique Météo {idx+1}">
                </div>
                """
            except Exception as e:
                print(f"Erreur encodage base64 pour {img_path} : {e}")
        
        if html_images_block:
            html_images_block = f"""
            <div class="section-title">📊 MODÉLISATIONS & GRAPHIQUES DE TENDANCE</div>
            <div class="meteo-images-container">{html_images_block}</div>
            """
        
        express = data.get("express", {})
        timeline = data.get("timeline", {})
        regional = data.get("regional", {})
        conf = data.get("confidence", {})
        dash = data.get("dashboard", {}) or {}
        scenarios = data.get("scenarios", {})
        social = data.get("social_pack", {}) or {}
        alert = data.get("alert", {}) or {}

        # Nettoyage des posts sociaux pour éviter les backslashes dans le f-string
        linkedin_clean = social.get('linkedin', '').replace('<br>', '\n').replace('<br/>', '\n')
        facebook_clean = social.get('facebook', '').replace('<br>', '\n').replace('<br/>', '\n')
        twitter_clean = social.get('twitter', '').replace('<br>', '\n').replace('<br/>', '\n')
        tiktok_clean = social.get('tiktok', '').replace('<br>', '\n').replace('<br/>', '\n')
        instagram_clean = social.get('instagram', '').replace('<br>', '\n').replace('<br/>', '\n')

        # Couleur dynamique du badge de confiance et calcul du score de confiance
        conf_score_raw = conf.get('score', '4/5')
        conf_percent = parse_score(conf_score_raw) * 20
        conf_class = "conf-badge-green"
        if "3/" in conf_score_raw:
            conf_class = "conf-badge-orange"
        elif "1/" in conf_score_raw or "2/" in conf_score_raw:
            conf_class = "conf-badge-red"

        # Traitement des puces "À Retenir"
        takeaways_raw = data.get("key_takeaways", "")
        takeaways_items = [t.strip("-* ").strip() for t in takeaways_raw.split("\n") if t.strip()]
        takeaways_li_html = "".join([f"<li>{t}</li>" for t in takeaways_items if t])
        if not takeaways_li_html:
            takeaways_li_html = "<li>Synthèse des prévisions établie avec succès.</li>"

        # Traitement des scores physiques pour le tableau de bord
        heat_score = parse_score(dash.get('score_heat', '0/5'))
        rain_score = parse_score(dash.get('score_rain', '0/5'))
        storm_score = parse_score(dash.get('score_storm', '0/5'))
        wind_score = parse_score(dash.get('score_wind', '0/5'))

        heat_label = get_score_label(dash.get('score_heat', '0/5'))
        rain_label = get_score_label(dash.get('score_rain', '0/5'))
        storm_label = get_score_label(dash.get('score_storm', '0/5'))
        wind_label = get_score_label(dash.get('score_wind', '0/5'))
        conf_label = get_score_label(conf_score_raw)

        # Génération des chiffres clés
        key_numbers_html = ""
        key_numbers_raw = data.get("key_numbers", "")
        if key_numbers_raw:
            lines = [l.strip() for l in key_numbers_raw.split("\n") if l.strip()]
            for l in lines:
                if "|" in l:
                    parts = [p.strip() for p in l.split("|")]
                    if len(parts) == 2:
                        val, lbl = parts[0], parts[1]
                        key_numbers_html += f"""
                        <div class="number-card">
                            <div class="number-val">{val}</div>
                            <div class="number-lbl">{lbl}</div>
                        </div>
                        """
        if not key_numbers_html:
            key_numbers_html = "<div style='grid-column: span 5; text-align: center; color: #64748b; font-style: italic; padding: 15px;'>Aucune donnée chiffrée remarquable.</div>"

        # Extraction des émojis et textes pour la frise chronologique
        p1_emoji, p1_text = extract_emoji_and_text(timeline.get('phase_1', ''))
        p2_emoji, p2_text = extract_emoji_and_text(timeline.get('phase_2', ''))
        p3_emoji, p3_text = extract_emoji_and_text(timeline.get('phase_3', ''))
        p4_emoji, p4_text = extract_emoji_and_text(timeline.get('phase_4', ''))

        # Traitement du tableau régional
        hdf_data = parse_region_line(regional.get('hdf_north', ''))
        atl_data = parse_region_line(regional.get('atlantic', ''))
        cen_data = parse_region_line(regional.get('central', ''))
        sou_data = parse_region_line(regional.get('south', ''))
        med_data = parse_region_line(regional.get('mediterranean', ''))
        mnt_data = parse_region_line(regional.get('mountains', ''))

        def format_region_row(name, region_data):
            temp = region_data[0]
            rain = region_data[1]
            risk = region_data[2]
            conf_val = region_data[3]
            return f"""
            <tr>
                <td><strong>{name}</strong></td>
                <td><span class="badge-temp">{temp}</span></td>
                <td>{get_level_badge(rain)}</td>
                <td>{get_level_badge(risk)}</td>
                <td>{get_conf_badge(conf_val)}</td>
            </tr>
            """

        regional_table_rows = (
            format_region_row("Hauts-de-France & Nord", hdf_data) +
            format_region_row("Façade Atlantique", atl_data) +
            format_region_row("Régions Centrales", cen_data) +
            format_region_row("Moitié Sud", sou_data) +
            format_region_row("Pourtour Méditerranéen", med_data) +
            format_region_row("Reliefs & Montagnes", mnt_data)
        )

        # Traitement du résumé en 10s
        summary_10s_html = ""
        summary_10s_raw = data.get("summary_10s", "")
        if summary_10s_raw:
            lines_10s = [l.strip("-* ").strip() for l in summary_10s_raw.split("\n") if l.strip()]
            for l in lines_10s:
                if l:
                    summary_10s_html += f"<li>{l}</li>"
        if not summary_10s_html:
            summary_10s_html = "<li>Résumé des tendances en cours d'établissement.</li>"

        # Traitement du bandeau d'alerte supérieur
        alert_lvl = alert.get('level', 'Vert').strip().replace('[', '').replace(']', '')
        alert_lvl_clean = alert_lvl.lower()
        if "rouge" in alert_lvl_clean:
            alert_class_suffix = "Rouge"
        elif "orange" in alert_lvl_clean:
            alert_class_suffix = "Orange"
        elif "jaune" in alert_lvl_clean:
            alert_class_suffix = "Jaune"
        else:
            alert_class_suffix = "Vert"
        alert_bg_class = f"alert-banner-{alert_class_suffix}"

        # Mini Sparklines (Inline SVG)
        # 1. Temp Max Trend SVG (Ascending Curve with Red Dot & Label)
        spark_temp_max = '<svg width="100" height="30" viewBox="0 0 100 30" style="display:block; margin: 10px auto 0 auto;"><path d="M 10,25 L 30,20 L 50,8 L 70,12 L 90,22" fill="none" stroke="#dc2626" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/><circle cx="50" cy="8" r="4" fill="#dc2626"/></svg>'
        # 2. Temp Min Trend SVG (Stable-low Blue Curve)
        spark_temp_min = '<svg width="100" height="30" viewBox="0 0 100 30" style="display:block; margin: 10px auto 0 auto;"><path d="M 10,18 L 30,16 L 50,22 L 70,18 L 90,16" fill="none" stroke="#2563eb" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/><circle cx="50" cy="22" r="3.5" fill="#2563eb"/></svg>'
        # 3. Anomaly Trend SVG (Peak Curve)
        spark_anomaly = '<svg width="100" height="30" viewBox="0 0 100 30" style="display:block; margin: 10px auto 0 auto;"><path d="M 10,26 L 30,22 L 50,10 L 70,24 L 90,26" fill="none" stroke="#f97316" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/><circle cx="50" cy="10" r="3.5" fill="#f97316"/></svg>'
        # 4. Duration SVG (Horizontal Progress bar)
        spark_duration = '<svg width="100" height="15" viewBox="0 0 100 15" style="display:block; margin: 12px auto 0 auto;"><rect x="0" y="3" width="100" height="8" rx="4" fill="#e2e8f0"/><rect x="0" y="3" width="80" height="8" rx="4" fill="#4b5563"/></svg>'
        # 5. Risk SVG (Vivid Risk progression bar)
        spark_risk = '<svg width="100" height="15" viewBox="0 0 100 15" style="display:block; margin: 12px auto 0 auto;"><rect x="0" y="3" width="100" height="8" rx="4" fill="#e2e8f0"/><rect x="0" y="3" width="90" height="8" rx="4" fill="#ea580c"/></svg>'
        # 6. Confidence SVG (Target target dot)
        spark_conf = '<svg width="100" height="30" viewBox="0 0 100 30" style="display:block; margin: 10px auto 0 auto;"><circle cx="50" cy="15" r="10" fill="none" stroke="#10b981" stroke-width="2"/><circle cx="50" cy="15" r="3.5" fill="#10b981"/></svg>'
        # 7. Precip expected SVG (Histogram bars)
        spark_precip = '<svg width="100" height="30" viewBox="0 0 100 30" style="display:block; margin: 10px auto 0 auto;"><rect x="15" y="20" width="8" height="6" rx="2" fill="#93c5fd"/><rect x="35" y="12" width="8" height="14" rx="2" fill="#3b82f6"/><rect x="55" y="24" width="8" height="2" rx="2" fill="#93c5fd"/><rect x="75" y="17" width="8" height="9" rx="2" fill="#3b82f6"/></svg>'
        # 8. Wind expected SVG (Wind Waves)
        spark_wind = '<svg width="100" height="30" viewBox="0 0 100 30" style="display:block; margin: 10px auto 0 auto;"><path d="M 10,12 C 25,12 30,8 40,12 C 50,16 55,12 70,12 C 80,12 90,15" fill="none" stroke="#4b5563" stroke-width="2" stroke-linecap="round"/><path d="M 15,22 C 30,22 35,20 45,22 C 55,24 60,22 75,22" fill="none" stroke="#9ca3af" stroke-width="1.2" stroke-linecap="round"/></svg>'
        # 9. General Trend SVG (Arrows shape path)
        spark_trend = '<svg width="100" height="30" viewBox="0 0 100 30" style="display:block; margin: 10px auto 0 auto;"><path d="M 15,22 L 45,8 L 60,8 L 85,22" fill="none" stroke="#8b5cf6" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/><path d="M 73,22 L 85,22 L 85,12" fill="none" stroke="#8b5cf6" stroke-width="3" stroke-linecap="round"/></svg>'
        # 10. Probability SVG (Arc gauge)
        spark_prob = '<svg width="100" height="30" viewBox="0 0 100 30" style="display:block; margin: 10px auto 0 auto;"><path d="M 20,25 A 30,30 0 0,1 80,25" fill="none" stroke="#cbd5e1" stroke-width="4" stroke-linecap="round"/><path d="M 20,25 A 30,30 0 0,1 68,10" fill="none" stroke="#06b6d4" stroke-width="4" stroke-linecap="round"/></svg>'

        divider = '<div class="week-divider"></div>' if w_idx > 0 else ""
        weeks_html += f"""
        {divider}
        
        <!-- TITRE DE SEMAINE EN 2 LIGNES -->
        <div class="week-title-box">
            <h2 class="week-title-line1">📅 {data.get('title_line1', 'SEMAINE')}</h2>
            <div class="week-title-line2">{data.get('title_line2', 'Synthèse des prévisions')}</div>
        </div>
        
        <!-- BANDEAU D'ALERTE SPECTACULAIRE -->
        <div class="alert-banner {alert_bg_class}">
            <div class="alert-main-row">
                <div class="alert-left">
                    <span class="alert-badge-top">Alerte Météo {alert_lvl}</span>
                    <h2 class="alert-title-lg">{alert.get('event_type', 'Événement')}</h2>
                    <div class="alert-date-block">
                        <span>PÉRIODE :</span>
                        <span>{alert.get('start', '-')} au {alert.get('end', '-')}</span>
                    </div>
                </div>
                <div class="alert-right-temp">
                    {alert.get('temp_max', '-').replace('°C','').replace('°','') or '-'}<span>°</span>
                </div>
            </div>
            <div class="alert-details-grid">
                <div class="alert-detail-item">
                    <span class="alert-detail-lbl">Risque Dominant</span>
                    <span class="alert-detail-val">{alert.get('main_risk', '-')}</span>
                </div>
                <div class="alert-detail-item">
                    <span class="alert-detail-lbl">Indice de Confiance</span>
                    <span class="alert-detail-val">🟢 {alert.get('confidence', '-')}</span>
                </div>
                <div class="alert-detail-item">
                    <span class="alert-detail-lbl">Impact Population</span>
                    <span class="alert-detail-val">⚠️ ÉLEVÉ (Vigilance)</span>
                </div>
            </div>
        </div>

        <!-- RÉSUMÉ EN 10 SECONDES -->
        <div class="summary-10s-box">
            <h3>⏱️ L'Essentiel en 10 Secondes</h3>
            <ul class="summary-10s-list">
                {summary_10s_html}
            </ul>
        </div>

        <!-- TABLEAU DE BORD (10 CARTES VISUELLES & SPARKLINES) -->
        <div class="section-title">📊 TABLEAU DE BORD DE L'ÉPISODE</div>
        <div class="dashboard-grid-10">
            <div class="dash-card-10 dc-start">
                <div class="dash-card-10-icon">📅</div>
                <div class="dash-card-10-val">{dash.get('start', '-')}</div>
                <div class="dash-card-10-lbl">Début</div>
                {spark_duration}
            </div>
            <div class="dash-card-10 dc-pic">
                <div class="dash-card-10-icon">📈</div>
                <div class="dash-card-10-val">{dash.get('pic', '-')}</div>
                <div class="dash-card-10-lbl">Date du Pic</div>
                {spark_temp_max}
            </div>
            <div class="dash-card-10 dc-end">
                <div class="dash-card-10-icon">🛑</div>
                <div class="dash-card-10-val">{dash.get('end', '-')}</div>
                <div class="dash-card-10-lbl">Fin</div>
                {spark_duration}
            </div>
            <div class="dash-card-10 dc-temp-max">
                <div class="dash-card-10-icon">🔥</div>
                <div class="dash-card-10-val">{dash.get('temp_max', '-')}</div>
                <div class="dash-card-10-lbl">Temp. Max</div>
                {spark_temp_max}
            </div>
            <div class="dash-card-10 dc-temp-min">
                <div class="dash-card-10-icon">🌙</div>
                <div class="dash-card-10-val">{dash.get('temp_min', '-')}</div>
                <div class="dash-card-10-lbl">Temp. Min Nuit</div>
                {spark_temp_min}
            </div>
            <div class="dash-card-10 dc-duration">
                <div class="dash-card-10-icon">⏱️</div>
                <div class="dash-card-10-val">{dash.get('duration', '-')}</div>
                <div class="dash-card-10-lbl">Durée</div>
                {spark_duration}
            </div>
            <div class="dash-card-10 dc-conf">
                <div class="dash-card-10-icon">🎯</div>
                <div class="dash-card-10-val">{dash.get('confidence', '-')}</div>
                <div class="dash-card-10-lbl">Confiance</div>
                {spark_conf}
            </div>
            <div class="dash-card-10 dc-trend">
                <div class="dash-card-10-icon">🔄</div>
                <div class="dash-card-10-val">{dash.get('evolution_trend', '-')}</div>
                <div class="dash-card-10-lbl">Tendance</div>
                {spark_trend}
            </div>
        </div>

        <!-- JAUGES DE RISQUES & CONFIANCE QUALIFIÉES ET DÉTAILLÉES -->
        <div class="dashboard-meters-row">
            <div class="meter-card-premium">
                <div class="meter-card-header">
                    <h4>🔥 Chaleur</h4>
                    <span class="meter-badge mb-chaleur">{get_score_label(dash.get('score_heat', '0/5'))}</span>
                </div>
                <div class="meter-track-premium">
                    <div class="meter-fill-premium mf-heat" style="width: {heat_score * 20}%;"></div>
                </div>
                <div class="meter-info">
                    <span class="meter-lbl-text">{dash.get('interp_heat', 'Situation normale')}</span>
                    <span>{heat_score}/5</span>
                </div>
            </div>
            <div class="meter-card-premium">
                <div class="meter-card-header">
                    <h4>🌧️ Précipitations</h4>
                    <span class="meter-badge mb-pluie">{get_score_label(dash.get('score_rain', '0/5'))}</span>
                </div>
                <div class="meter-track-premium">
                    <div class="meter-fill-premium mf-rain" style="width: {rain_score * 20}%;"></div>
                </div>
                <div class="meter-info">
                    <span class="meter-lbl-text">{dash.get('interp_rain', 'Situation normale')}</span>
                    <span>{rain_score}/5</span>
                </div>
            </div>
            <div class="meter-card-premium">
                <div class="meter-card-header">
                    <h4>⛈️ Orages</h4>
                    <span class="meter-badge mb-orage">{get_score_label(dash.get('score_storm', '0/5'))}</span>
                </div>
                <div class="meter-track-premium">
                    <div class="meter-fill-premium mf-storm" style="width: {storm_score * 20}%;"></div>
                </div>
                <div class="meter-info">
                    <span class="meter-lbl-text">{dash.get('interp_storm', 'Situation normale')}</span>
                    <span>{storm_score}/5</span>
                </div>
            </div>
            <div class="meter-card-premium">
                <div class="meter-card-header">
                    <h4>💨 Vent Fort</h4>
                    <span class="meter-badge mb-vent">{get_score_label(dash.get('score_wind', '0/5'))}</span>
                </div>
                <div class="meter-track-premium">
                    <div class="meter-fill-premium mf-wind" style="width: {wind_score * 20}%;"></div>
                </div>
                <div class="meter-info">
                    <span class="meter-lbl-text">{dash.get('interp_wind', 'Situation normale')}</span>
                    <span>{wind_score}/5</span>
                </div>
            </div>
        </div>

        <!-- 2. GRAPHIQUES METEO PLEIN FORMAT (REMONTÉS) -->
        {html_images_block}

        <!-- 3. RUBRIQUE "LES CHIFFRES À RETENIR" -->
        <div class="section-title">🔢 LES CHIFFRES À RETENIR</div>
        <div class="numbers-grid">
            {key_numbers_html}
        </div>

        <!-- 4. CHRONOLOGIE EN BLOCS DE PHASES COLORÉS CONNECTÉS -->
        <div class="section-title">🗓️ CHRONOLOGIE EN PHASES</div>
        <div class="timeline-phases-grid">
            <div class="phase-block pb-phase1">
                <div class="phase-header">
                    <span class="phase-name">Phase 1</span>
                    <span class="phase-emoji">{p1_emoji}</span>
                </div>
                <div class="phase-title">Montée en puissance</div>
                <p class="phase-desc">{p1_text}</p>
            </div>
            <div class="phase-block pb-phase2">
                <div class="phase-header">
                    <span class="phase-name">Phase 2</span>
                    <span class="phase-emoji">{p2_emoji}</span>
                </div>
                <div class="phase-title">Pic d'intensité</div>
                <p class="phase-desc">{p2_text}</p>
            </div>
            <div class="phase-block pb-phase3">
                <div class="phase-header">
                    <span class="phase-name">Phase 3</span>
                    <span class="phase-emoji">{p3_emoji}</span>
                </div>
                <div class="phase-title">Maintien chaud</div>
                <p class="phase-desc">{p3_text}</p>
            </div>
            <div class="phase-block pb-phase4">
                <div class="phase-header">
                    <span class="phase-name">Phase 4</span>
                    <span class="phase-emoji">{p4_emoji}</span>
                </div>
                <div class="phase-title">Dégradation / Tempêtes</div>
                <p class="phase-desc">{p4_text}</p>
            </div>
        </div>

        <!-- 5. TABLEAU DE SYNTHÈSE RÉGIONALE SYNTHÉTIQUE -->
        <div class="section-title">🗺️ SYNTHÈSE DES RÉGIONS</div>
        <div class="table-responsive">
            <table class="regional-table">
                <thead>
                    <tr>
                        <th>Grande Région</th>
                        <th>🌡️ Temp. Attendue</th>
                        <th>🌧️ Niveau de Pluie</th>
                        <th>⚠️ Risque Dominant</th>
                        <th>🎯 Confiance</th>
                    </tr>
                </thead>
                <tbody>
                    {regional_table_rows}
                </tbody>
            </table>
        </div>

        <!-- 6. ANALYSE DÉTAILLÉE (SCÉNARIOS & INCERTITUDES) DÉPORTÉE PLUS BAS -->
        <div class="detailed-analysis-panel">
            <h3 class="detailed-analysis-title">🔮 ANALYSE DÉTAILLÉE & SCÉNARIOS</h3>
            
            <div class="scenarios-container">
                <div class="scenario-card sc-major">
                    <div class="sc-header">
                        <h3>🟢 {scenarios.get('majoritaire', {}).get('title', 'Scénario Majoritaire')}</h3>
                        <span class="sc-prob bg-major">{scenarios.get('majoritaire', {}).get('prob', '65%')}</span>
                    </div>
                    <p class="sc-text">{scenarios.get('majoritaire', {}).get('desc', '')}</p>
                </div>
                
                <div class="scenario-card sc-median">
                    <div class="sc-header">
                        <h3>🟡 {scenarios.get('median', {}).get('title', 'Scénario Alternatif')}</h3>
                        <span class="sc-prob bg-median">{scenarios.get('median', {}).get('prob', '25%')}</span>
                    </div>
                    <p class="sc-text">{scenarios.get('median', {}).get('desc', '')}</p>
                </div>
                
                <div class="scenario-card sc-minor">
                    <div class="sc-header">
                        <h3>🔴 {scenarios.get('minoritaire', {}).get('title', 'Scénario Minoritaire')}</h3>
                        <span class="sc-prob bg-minor">{scenarios.get('minoritaire', {}).get('prob', '10%')}</span>
                    </div>
                    <p class="sc-text">{scenarios.get('minoritaire', {}).get('desc', '')}</p>
                </div>
            </div>

            <!-- INCERTITUDES -->
            <div class="confidence-panel" style="padding: 15px; margin-bottom: 20px;">
                <div class="confidence-head" style="margin-bottom: 8px;">
                    <strong>Fiabilité du Consensus des Modèles</strong>
                    <span class="{conf_class}" style="padding: 4px 12px; border-radius: 9999px; font-weight: 800; font-size: 11px; color: white; {get_badge_color_class(conf_label)}">Note : {conf_score_raw} ({conf_label})</span>
                </div>
                <div class="uncertainties-box">
                    <strong style="display: block; margin-bottom: 6px; color: #dc2626; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px;">❓ Incertitudes Majeures & Points à Surveiller :</strong>
                    {data.get('key_uncertainties', '')}\n{data.get('monitoring_points', '')}
                </div>
            </div>

            <!-- À RETENIR -->
            <div class="takeaways-panel">
                <h3>📌 À Retenir — L'Essentiel</h3>
                <ul>
                    {takeaways_li_html}
                </ul>
            </div>
        </div>

        <!-- 7. PACK RÉSEAUX SOCIAUX PRÊT À PUBLIER -->
        <div class="section-title">📢 PACK RÉSEAUX SOCIAUX (PRÊT À DIFFUSER)</div>
        <div class="social-pack-container">
            <!-- LinkedIn -->
            <div class="social-platform-card">
                <div class="social-platform-header sp-linkedin">
                    <span>🔗 LinkedIn (Storytelling Expert - {len(linkedin_clean)} car.)</span>
                    <button class="copy-btn" onclick="navigator.clipboard.writeText(this.parentNode.parentNode.querySelector('.social-platform-body').innerText); alert('Copié dans le presse-papiers !');">Copier</button>
                </div>
                <div class="social-platform-body">{linkedin_clean}</div>
            </div>

            <!-- Facebook -->
            <div class="social-platform-card">
                <div class="social-platform-header sp-facebook">
                    <span>👥 Facebook (Communautaire - {len(facebook_clean)} car.)</span>
                    <button class="copy-btn" onclick="navigator.clipboard.writeText(this.parentNode.parentNode.querySelector('.social-platform-body').innerText); alert('Copié dans le presse-papiers !');">Copier</button>
                </div>
                <div class="social-platform-body">{facebook_clean}</div>
            </div>

            <!-- X (Twitter) -->
            <div class="social-platform-card">
                <div class="social-platform-header sp-twitter">
                    <span>🐦 X (Twitter - {len(twitter_clean)} / 280 car.)</span>
                    <button class="copy-btn" onclick="navigator.clipboard.writeText(this.parentNode.parentNode.querySelector('.social-platform-body').innerText); alert('Copié dans le presse-papiers !');">Copier</button>
                </div>
                <div class="social-platform-body">{twitter_clean}</div>
            </div>

            <!-- TikTok -->
            <div class="social-platform-card">
                <div class="social-platform-header sp-tiktok">
                    <span>🎵 TikTok (Description - {len(tiktok_clean)} car.)</span>
                    <button class="copy-btn" onclick="navigator.clipboard.writeText(this.parentNode.parentNode.querySelector('.social-platform-body').innerText); alert('Copié dans le presse-papiers !');">Copier</button>
                </div>
                <div class="social-platform-body">{tiktok_clean}</div>
            </div>

            <!-- Instagram -->
            <div class="social-platform-card">
                <div class="social-platform-header sp-instagram">
                    <span>📸 Instagram (Légende - {len(instagram_clean)} car.)</span>
                    <button class="copy-btn" onclick="navigator.clipboard.writeText(this.parentNode.parentNode.querySelector('.social-platform-body').innerText); alert('Copié dans le presse-papiers !');">Copier</button>
                </div>
                <div class="social-platform-body">{instagram_clean}</div>
            </div>
        </div>
        """

    html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Analyses & Tendances Météo - Forum</title>
    <style>{style}</style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div style="font-size: 11px; font-weight: 800; letter-spacing: 2px; text-transform: uppercase; margin-bottom: 8px;">MONSIEUR MÉTÉO</div>
            <h1>📊 BULLETIN ÉVOLUTION & TENDANCES MÉTÉO</h1>
            <p>Analyse consolidée du {datetime.datetime.now().strftime('%d/%m/%Y')} pour les 2 prochaines semaines</p>
        </div>
        <div class="content">
            {weeks_html}
        </div>
    </div>
</body>
</html>
"""
    html_path = "bulletin_infoclimat.html"
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"HTML généré avec succès : {html_path}")

    # Envoi e-mail via Gmail SMTP Base64 brut
    gmail_email = os.environ.get("GMAIL_EMAIL", "langlet.gregory@gmail.com")
    gmail_password = os.environ.get("GMAIL_APP_PASSWORD")
    if gmail_email:
        gmail_email = gmail_email.replace('\ufeff', '').replace('\ufffe', '').strip()
    if gmail_password:
        gmail_password = gmail_password.replace('\ufeff', '').replace('\ufffe', '').strip()
        
    recipient = os.environ.get("RECIPIENT_EMAILS", "gregory.langlet@sfr.fr, langlet.gregory@gmail.com")
    recipients = [r.strip() for r in recipient.split(",") if r.strip()]
    
    if not gmail_password:
        print("[SMTP] ERREUR : GMAIL_APP_PASSWORD non configuré. Annulation envoi.")
        sys.exit(0)
        
    sender = gmail_email
    
    # Titres abrégés pour le sujet du mail
    subject_week_names = " & ".join([r["data"].get("title_line1", r["data"].get("subject_title", "Semaine")).split("-")[0].strip() for r in results])
    subject = f"Tendances de la semaine - {subject_week_names}"
    
    # Nettoyage ASCII du sujet pour éviter les rejets SMTP
    import unicodedata
    clean_subj = unicodedata.normalize('NFKD', subject).encode('ASCII', 'ignore').decode('ASCII')
    subject = clean_subj
    
    filename = f"analyse_infoclimat_{datetime.datetime.now().strftime('%Y_%m_%d')}.html"
    
    html_b64 = base64.b64encode(html.encode('utf-8')).decode('ascii')
    text_body = f"Bonjour,\n\nVeuillez trouver ci-joint l'analyse consolidée des tendances météo pour la semaine en cours (jours restants) et la semaine suivante.\n\nLe rapport HTML contenant le Pack Réseaux Sociaux multi-plateforme complet et prêt à diffuser ainsi que les graphiques de modélisation est joint à ce message.\n\nCordialement,\nMonsieur Météo"
    text_b64 = base64.b64encode(text_body.encode('utf-8')).decode('ascii')
    boundary = uuid.uuid4().hex
    
    raw_message = (
        f'From: Meteo Climat Pro <{sender}>\r\n'
        f'To: {", ".join(recipients)}\r\n'
        f'Reply-To: gregory.langlet@sfr.fr\r\n'
        f'Subject: {subject}\r\n'
        f'Date: {formatdate(localtime=True)}\r\n'
        f'X-Mailer: Python\r\n'
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
    
    print(f"[SMTP] Envoi via Gmail à {', '.join(recipients)}...")
    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(gmail_email, gmail_password)
            server.sendmail(gmail_email, recipients, raw_message.encode('ascii'))
        print("[SMTP] E-mail envoyé avec succès !")
    except Exception as e:
        print(f"[SMTP] Erreur d'envoi : {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
