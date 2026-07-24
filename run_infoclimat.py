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
À partir EXCLUSIVEMENT des discussions et analyses météorologiques fournies en entrée, tu dois produire un bulletin d'analyse météorologique sous forme de tableau de bord exécutif professionnel destiné à des clients grand public et professionnels. Le document doit être lisible en moins de 10 secondes tout en conservant une exactitude scientifique absolue et les nuances de probabilité (pas de sensationnalisme).

RÈGLE D'OR N°1 : DATES EXACTES ET JOURS NOMMÉS DANS 100% DES SECTIONS
Dans TOUTES les sections (KPI, Chronologie, Régions, Scénarios, Incertitudes, À Retenir, Posts Sociaux), tu devez mentionner les jours précis associés à leurs dates exactes (ex: Lundi 27 Juillet, Mardi 28 Juillet). Ne dis plus jamais "début de semaine" ou "week-end" sans les associer directement à leur date.

RÈGLE D'OR N°2 : INTÉGRATION DE LA DATE DE GÉNÉRATION & PÉRIODE PERTINENTE
- Analyse avec attention la "Date actuelle de génération" transmise dans l'invite.
- Si le sujet correspond à la "Semaine en cours" : toute journée précédant cette date est déjà passée. Les prévisions doivent se concentrer EXCLUSIVEMENT sur la période allant de la date de génération au dimanche de cette semaine. Ignore ou mentionne comme "déjà écoulées" les journées passées.
- Si le sujet correspond à la "Semaine suivante" (Semaine future) : c'est la véritable semaine de tendance à moyen terme. Rédige les prévisions complètes jour par jour, du lundi au dimanche.

RÈGLE D'OR N°3 : HANDLING DE LA TEMPÉRATURE (PAS DE CHIFFRE GÉANT)
- Ne propose JAMAIS une température maximale unique géante isolée, car cela donne l'impression d'une certitude et d'une uniformité fausse pour une tendance météo.
- Propose obligatoirement soit une plage de températures (ex: "38 à 42 °C"), soit une température maximale accompagnée de son qualificatif de localisation (ex: "jusqu'à 42 °C localement").
- Cet indicateur de température maximale attendue doit avoir la même taille, le même style et le même poids visuel que les autres indicateurs de la ligne de KPI.

RÈGLE D'OR N°4 : RÉGIONS EN LIGNE STRUCTURÉE (POUR LE TABLEAU)
- Rédige obligatoirement une seule ligne contenant exactement ces 4 valeurs séparées par des barres verticales `|` : 
  Température attendue | Niveau de pluie | Risque dominant | Indice de confiance
  Exemple : 18 à 24 °C | Faible | Aucun | 4/5
- Pour le niveau de pluie et le risque, utilise obligatoirement un qualificatif simple et lisible par tous parmi : Très faible, Faible, Modéré, Fort, Très fort (sans longue phrase explicative).

RÈGLE D'OR N°5 : INDICATION KPI COURTE
- Rédige des valeurs de KPI très courtes et condensées (1 à 3 mots max) :
  - `[KPI_TEMP_RANGE]` : ex: "38 à 42 °C" ou "jusqu'à 42 °C localement"
  - `[KPI_PERIOD]` : ex: "27 Juillet au 2 Août"
  - `[KPI_DURATION]` : ex: "5 jours"
  - `[KPI_CONFIDENCE]` : ex: "4/5 (Élevée)"
  - `[KPI_RISKS]` : ex: "Canicule & Orages"
  - `[KPI_ZONE]` : ex: "Sud-Ouest / Nord-Est"

RÈGLE D'OR N°6 : CHRONOLOGIE HORIZONTALE EN 4 ÉTAPES
- Rédige la chronologie sous forme de 4 étapes horizontales simples : Début, Montée, Pic, Fin.
- Pour chaque étape, écris uniquement la date exacte et une phrase très courte (10-15 mots maximum).

RÈGLE D'OR N°7 : RÉDUCTION DRASTIQUE DES TEXTES DÉTAILLÉS (60-70%)
- Le Scénario Majoritaire doit faire ~50-80 mots max, et les Scénarios Alternatif et Minoritaire ~40-60 mots max chacun.
- Utilise des listes à puces pour lister les impacts réels. Mets en gras les valeurs numériques importantes.
- Ne répète pas les informations déjà présentes en haut de document.

RÈGLE D'OR N°8 : FIDÉLITÉ ABSOLUE AUX DONNÉES ET ANALYSES SOURCES (PAS D'EXAGÉRATION)
- Tu ne devez jamais sur-interpréter, accentuer ou exagérer une formulation météo. Si les prévisionnistes parlent de "risque d'orage" ou d'une "tendance incertaine", décris-le exactement comme un risque ou une incertitude. Ne transforme jamais une hypothèse en certitude.
- Ne cherche pas à rendre le titre ou les résumés plus accrocheurs en déformant la réalité scientifique fournie dans les discussions. Conserve strictement le niveau de nuance, les réserves et l'indice de confiance donnés par les experts.

FORMAT DE SORTIE OBLIGATOIRE - Utilise EXACTEMENT ces balises :

[SUBJECT_TITLE_LINE1]
Semaine X - Du Lundi DD au Dimanche DD Mois AAAA

[SUBJECT_TITLE_LINE2]
Accroche météo courte résumant le temps de la semaine avec dates exactes

[ALERT_LEVEL]
Rouge (ou Vert, Jaune, Orange, Rouge)

[ALERT_EVENT_TYPE]
Canicule (ou autre phénomène attendu)

[ALERT_START]
Mercredi 29 Juillet

[ALERT_END]
Dimanche 2 Août

[ALERT_CONFIDENCE]
4/5

[KPI_TEMP_RANGE]
38 à 42 °C (ou jusqu'à 42 °C localement)

[KPI_PERIOD]
Du 27 Juillet au 2 Août

[KPI_DURATION]
6 jours

[KPI_CONFIDENCE]
4/5 (Élevée)

[KPI_RISKS]
Canicule, orages, incendies

[KPI_ZONE]
Axe Sud-Ouest / Nord-Est

[TAKEAWAYS_10S]
- Phrase courte 1 (maximum une ligne)
- Phrase courte 2 (maximum une ligne)
- Phrase courte 3 (maximum une ligne)
- Phrase courte 4 (maximum une ligne)
- Phrase courte 5 (maximum une ligne)
- Phrase courte 6 (maximum une ligne)

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

[IMPACT_POPULATION]
Quelques mots clairs résumant l'impact (ex: Vigilance canicule)

[IMPACT_TRAVEL]
Quelques mots clairs (ex: Risque de retards rails)

[IMPACT_WORK]
Quelques mots clairs (ex: Horaires décalés BTP)

[IMPACT_AGRI]
Quelques mots clairs (ex: Stress thermique cultures)

[IMPACT_STORM]
Quelques mots clairs (ex: Localement violents)

[IMPACT_DROUGHT]
Quelques mots clairs (ex: Sécheresse accentuée)

[TIMELINE_DATE_DEBUT]
Lundi 27 Juillet

[TIMELINE_DESC_DEBUT]
Début de l'épisode chaud sur l'extrême sud du pays.

[TIMELINE_DATE_MONTEE]
Mardi 28 Juillet

[TIMELINE_DESC_MONTEE]
Extension rapide de la chaleur sur les deux tiers sud de la France.

[TIMELINE_DATE_PIC]
Jeudi 30 et Vendredi 31 Juillet

[TIMELINE_DESC_PIC]
Pic de chaleur exceptionnelle de 38 à 42 °C localement.

[TIMELINE_DATE_FIN]
Dimanche 2 Août

[TIMELINE_DESC_FIN]
Baisse progressive des températures par l'ouest.

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
- Puce essentielle 1
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
                
                "alert_level": r"\[ALERT_LEVEL\]\s*\n(.*?)(?=\n\s*\[|$)",
                "alert_event_type": r"\[ALERT_EVENT_TYPE\]\s*\n(.*?)(?=\n\s*\[|$)",
                "alert_start": r"\[ALERT_START\]\s*\n(.*?)(?=\n\s*\[|$)",
                "alert_end": r"\[ALERT_END\]\s*\n(.*?)(?=\n\s*\[|$)",
                "alert_confidence": r"\[ALERT_CONFIDENCE\]\s*\n(.*?)(?=\n\s*\[|$)",

                "kpi_temp_range": r"\[KPI_TEMP_RANGE\]\s*\n(.*?)(?=\n\s*\[|$)",
                "kpi_period": r"\[KPI_PERIOD\]\s*\n(.*?)(?=\n\s*\[|$)",
                "kpi_duration": r"\[KPI_DURATION\]\s*\n(.*?)(?=\n\s*\[|$)",
                "kpi_confidence": r"\[KPI_CONFIDENCE\]\s*\n(.*?)(?=\n\s*\[|$)",
                "kpi_risks": r"\[KPI_RISKS\]\s*\n(.*?)(?=\n\s*\[|$)",
                "kpi_zone": r"\[KPI_ZONE\]\s*\n(.*?)(?=\n\s*\[|$)",

                "takeaways_10s": r"\[TAKEAWAYS_10S\]\s*\n(.*?)(?=\n\s*\[|$)",

                "score_heat": r"\[SCORE_HEAT\]\s*\n(.*?)(?=\n\s*\[|$)",
                "interp_heat": r"\[INTERP_HEAT\]\s*\n(.*?)(?=\n\s*\[|$)",
                "score_rain": r"\[SCORE_RAIN\]\s*\n(.*?)(?=\n\s*\[|$)",
                "interp_rain": r"\[INTERP_RAIN\]\s*\n(.*?)(?=\n\s*\[|$)",
                "score_storm": r"\[SCORE_STORM\]\s*\n(.*?)(?=\n\s*\[|$)",
                "interp_storm": r"\[INTERP_STORM\]\s*\n(.*?)(?=\n\s*\[|$)",
                "score_wind": r"\[SCORE_WIND\]\s*\n(.*?)(?=\n\s*\[|$)",
                "interp_wind": r"\[INTERP_WIND\]\s*\n(.*?)(?=\n\s*\[|$)",

                "impact_population": r"\[IMPACT_POPULATION\]\s*\n(.*?)(?=\n\s*\[|$)",
                "impact_travel": r"\[IMPACT_TRAVEL\]\s*\n(.*?)(?=\n\s*\[|$)",
                "impact_work": r"\[IMPACT_WORK\]\s*\n(.*?)(?=\n\s*\[|$)",
                "impact_agri": r"\[IMPACT_AGRI\]\s*\n(.*?)(?=\n\s*\[|$)",
                "impact_storm": r"\[IMPACT_STORM\]\s*\n(.*?)(?=\n\s*\[|$)",
                "impact_drought": r"\[IMPACT_DROUGHT\]\s*\n(.*?)(?=\n\s*\[|$)",

                "timeline_date_debut": r"\[TIMELINE_DATE_DEBUT\]\s*\n(.*?)(?=\n\s*\[|$)",
                "timeline_desc_debut": r"\[TIMELINE_DESC_DEBUT\]\s*\n(.*?)(?=\n\s*\[|$)",
                "timeline_date_montee": r"\[TIMELINE_DATE_MONTEE\]\s*\n(.*?)(?=\n\s*\[|$)",
                "timeline_desc_montee": r"\[TIMELINE_DESC_MONTEE\]\s*\n(.*?)(?=\n\s*\[|$)",
                "timeline_date_pic": r"\[TIMELINE_DATE_PIC\]\s*\n(.*?)(?=\n\s*\[|$)",
                "timeline_desc_pic": r"\[TIMELINE_DESC_PIC\]\s*\n(.*?)(?=\n\s*\[|$)",
                "timeline_date_fin": r"\[TIMELINE_DATE_FIN\]\s*\n(.*?)(?=\n\s*\[|$)",
                "timeline_desc_fin": r"\[TIMELINE_DESC_FIN\]\s*\n(.*?)(?=\n\s*\[|$)",

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
            
            if (parsed["title_line1"] or parsed["title_line2"]) and (parsed["takeaways_10s"] or parsed["majoritaire_desc"]):
                data = {
                    "title_line1": parsed["title_line1"] or topic_title_clean,
                    "title_line2": parsed["title_line2"] or "Tendances et synthèses météorologiques",
                    
                    "alert": {
                        "level": parsed["alert_level"] or "Vert",
                        "event_type": parsed["alert_event_type"],
                        "start": parsed["alert_start"],
                        "end": parsed["alert_end"],
                        "confidence": parsed["alert_confidence"],
                    },
                    "kpis": {
                        "temp_range": parsed["kpi_temp_range"],
                        "period": parsed["kpi_period"],
                        "duration": parsed["kpi_duration"],
                        "confidence": parsed["kpi_confidence"],
                        "risks": parsed["kpi_risks"],
                        "zone": parsed["kpi_zone"],
                    },
                    "takeaways_10s": parsed["takeaways_10s"],
                    "dashboard": {
                        "score_heat": parsed["score_heat"] or "0/5",
                        "interp_heat": parsed["interp_heat"] or "Situation normale",
                        "score_rain": parsed["score_rain"] or "0/5",
                        "interp_rain": parsed["interp_rain"] or "Situation normale",
                        "score_storm": parsed["score_storm"] or "0/5",
                        "interp_storm": parsed["interp_storm"] or "Situation normale",
                        "score_wind": parsed["score_wind"] or "0/5",
                        "interp_wind": parsed["interp_wind"] or "Situation normale",
                    },
                    "impacts": {
                        "population": parsed["impact_population"],
                        "travel": parsed["impact_travel"],
                        "work": parsed["impact_work"],
                        "agri": parsed["impact_agri"],
                        "storm": parsed["impact_storm"],
                        "drought": parsed["impact_drought"],
                    },
                    "timeline": {
                        "date_debut": parsed["timeline_date_debut"],
                        "desc_debut": parsed["timeline_desc_debut"],
                        "date_montee": parsed["timeline_date_montee"],
                        "desc_montee": parsed["timeline_desc_montee"],
                        "date_pic": parsed["timeline_date_pic"],
                        "desc_pic": parsed["timeline_desc_pic"],
                        "date_fin": parsed["timeline_date_fin"],
                        "desc_fin": parsed["timeline_desc_fin"],
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
        
    # Style CSS Premium & Responsive (Design System v5)
    style = """
    :root {
        --font-sans: 'Segoe UI', system-ui, -apple-system, sans-serif;
        --text-xs: 11px;
        --text-sm: 13px;
        --text-base: 14.5px;
        --text-lg: 16px;
        --text-xl: 20px;
        --radius-lg: 24px;
        --radius-md: 16px;
        --radius-sm: 10px;
        --spacing-xs: 10px;
        --spacing-sm: 15px;
        --spacing-md: 24px;
        --spacing-lg: 35px;
        --shadow-sm: 0 2px 8px rgba(0,0,0,0.02);
        --shadow-md: 0 10px 30px rgba(0,0,0,0.03);
    }
    body { font-family: var(--font-sans); font-size: var(--text-base); line-height: 1.6; color: #0f172a; background-color: #f1f5f9; margin: 0; padding: 25px 12px; }
    .container { max-width: 900px; background-color: #ffffff; margin: 0 auto; border-radius: var(--radius-lg); overflow: hidden; box-shadow: var(--shadow-md); border: 1px solid #e2e8f0; }
    .header { background: linear-gradient(135deg, #0b0f19 0%, #1e293b 100%); color: #ffffff; padding: 40px 30px; text-align: center; position: relative; }
    .header::after { content: ''; position: absolute; bottom: 0; left: 0; right: 0; height: 6px; background: linear-gradient(90deg, #2563eb, #7c3aed, #ec4899); }
    .header h1 { margin: 0; font-size: 24px; font-weight: 900; letter-spacing: -0.5px; text-transform: uppercase; }
    .header p { margin: 8px 0 0 0; font-size: 13px; opacity: 0.85; font-weight: 500; }
    .content { padding: var(--spacing-lg) 30px; display: flex; flex-direction: column; gap: var(--spacing-lg); }
    .week-divider { border-top: 4px dashed #cbd5e1; margin: var(--spacing-lg) 0; }
    
    .week-title-box { padding-left: 20px; border-left: 6px solid #2563eb; }
    .week-title-line1 { font-size: var(--text-xl); font-weight: 900; color: #0f172a; text-transform: uppercase; letter-spacing: 0.5px; margin: 0; }
    .week-title-line2 { font-size: var(--text-base); font-weight: 600; color: #64748b; margin-top: 6px; }

    .section-title { font-size: var(--text-xs); font-weight: 900; text-transform: uppercase; letter-spacing: 1.5px; color: #475569; border-bottom: 2px solid #f1f5f9; padding-bottom: 8px; display: flex; align-items: center; gap: 8px; margin: 0; }
    
    /* Bandeau d'alerte et de synthèse supérieur */
    .alert-banner { padding: 25px 30px; color: #ffffff; border-radius: var(--radius-md); display: flex; flex-direction: column; gap: 15px; position: relative; overflow: hidden; }
    .alert-banner-Rouge { background: linear-gradient(135deg, #7f1d1d 0%, #dc2626 100%); }
    .alert-banner-Orange { background: linear-gradient(135deg, #7c2d12 0%, #ea580c 100%); }
    .alert-banner-Jaune { background: linear-gradient(135deg, #713f12 0%, #eab308 100%); }
    .alert-banner-Vert { background: linear-gradient(135deg, #064e3b 0%, #10b981 100%); }
    
    .alert-main-row { display: flex; justify-content: space-between; align-items: center; gap: 20px; }
    .alert-left { display: flex; flex-direction: column; gap: 6px; }
    .alert-badge-top { font-size: 9px; font-weight: 900; background: rgba(255,255,255,0.22); padding: 5px 12px; border-radius: 9999px; text-transform: uppercase; align-self: flex-start; letter-spacing: 1px; }
    .alert-title-lg { font-size: 24px; font-weight: 900; line-height: 1.2; text-transform: uppercase; margin: 0; }
    .alert-date-block { font-size: var(--text-xs); font-weight: 700; opacity: 0.9; }

    /* Ligne de KPI compacte homogène */
    .kpi-row-6 { display: grid; grid-template-columns: repeat(6, 1fr); gap: 10px; }
    @media (max-width: 768px) {
        .kpi-row-6 { grid-template-columns: repeat(3, 1fr); }
    }
    @media (max-width: 480px) {
        .kpi-row-6 { grid-template-columns: repeat(2, 1fr); }
    }
    .kpi-card-6 { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: var(--radius-md); padding: 14px 10px; text-align: center; display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 95px; box-shadow: var(--shadow-sm); }
    .kpi-icon { font-size: 18px; margin-bottom: 5px; }
    .kpi-val { font-size: 13.5px; font-weight: 850; color: #0f172a; line-height: 1.2; word-break: break-word; }
    .kpi-lbl { font-size: 9px; font-weight: 800; color: #64748b; text-transform: uppercase; margin-top: 3px; letter-spacing: 0.5px; }

    /* À retenir en 10 secondes */
    .summary-10s-box { background: #f8fafc; border: 1px solid #cbd5e1; border-left: 5px solid #2563eb; border-radius: var(--radius-md); padding: 20px; }
    .summary-10s-box h3 { margin: 0 0 10px 0; font-size: var(--text-xs); font-weight: 900; color: #1e293b; text-transform: uppercase; letter-spacing: 1px; }
    .summary-10s-list { margin: 0; padding: 0; list-style: none; font-size: var(--text-sm); color: #334155; line-height: 1.5; }
    .summary-10s-list li { margin-bottom: 5px; padding-left: 15px; position: relative; }
    .summary-10s-list li::before { content: '•'; position: absolute; left: 0; color: #2563eb; font-weight: 900; }

    /* Jauges compactes */
    .dashboard-meters-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }
    @media (max-width: 768px) {
        .dashboard-meters-row { grid-template-columns: repeat(2, 1fr); }
    }
    @media (max-width: 480px) {
        .dashboard-meters-row { grid-template-columns: 1fr; }
    }
    .meter-card-premium { background: #f8fafc; border: 1px solid #cbd5e1; border-radius: var(--radius-md); padding: 12px; display: flex; flex-direction: column; gap: 6px; }
    .meter-card-header { display: flex; align-items: center; justify-content: space-between; }
    .meter-card-header h4 { margin: 0; font-size: 11px; font-weight: 850; color: #475569; text-transform: uppercase; }
    .meter-badge { font-size: 8px; font-weight: 900; padding: 2px 8px; border-radius: 9999px; text-transform: uppercase; color: #ffffff; }
    .meter-track-premium { width: 100%; height: 6px; background: #e2e8f0; border-radius: 9999px; overflow: hidden; }
    .meter-fill-premium { height: 100%; border-radius: 9999px; }
    .meter-info { display: flex; align-items: center; justify-content: space-between; font-size: 10.5px; font-weight: 800; color: #1e293b; }
    
    /* Bloc Impacts Attendus */
    .impacts-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
    @media (max-width: 768px) {
        .impacts-grid { grid-template-columns: 1fr; }
    }
    .impact-item { background: #ffffff; border: 1px solid #e2e8f0; border-radius: var(--radius-md); padding: 14px; display: flex; align-items: flex-start; gap: 12px; box-shadow: var(--shadow-sm); }
    .impact-icon { font-size: 18px; line-height: 1; }
    .impact-content { display: flex; flex-direction: column; gap: 1px; }
    .impact-title { font-size: 10.5px; font-weight: 900; color: #475569; text-transform: uppercase; letter-spacing: 0.5px; }
    .impact-text { font-size: 12.5px; color: #334155; line-height: 1.4; }

    /* Chiffres à retenir */
    .numbers-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 12px; }
    @media (max-width: 768px) {
        .numbers-grid { grid-template-columns: repeat(2, 1fr); }
    }
    @media (max-width: 480px) {
        .numbers-grid { grid-template-columns: 1fr; }
    }
    .number-card { background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%); border: 1px solid #cbd5e1; border-radius: var(--radius-md); padding: 15px; text-align: center; }
    .number-val { font-size: 22px; font-weight: 900; color: #1e3a8a; line-height: 1.1; margin-bottom: 2px; }
    .number-lbl { font-size: 9.5px; font-weight: 800; color: #475569; line-height: 1.3; }

    /* Chronologie Horizontale */
    .timeline-horizontal { display: flex; align-items: stretch; justify-content: space-between; gap: 8px; }
    @media (max-width: 768px) {
        .timeline-horizontal { flex-direction: column; gap: 15px; }
    }
    .timeline-item-h { flex: 1; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: var(--radius-md); padding: 15px; display: flex; flex-direction: column; align-items: center; text-align: center; gap: 6px; }
    .timeline-circle { width: 24px; height: 24px; border-radius: 50%; background: #2563eb; color: #ffffff; font-size: 11px; font-weight: 900; display: flex; align-items: center; justify-content: center; }
    .timeline-phase-h { font-size: 9.5px; font-weight: 900; text-transform: uppercase; color: #2563eb; letter-spacing: 0.5px; }
    .timeline-date-h { font-size: 13px; font-weight: 850; color: #0f172a; }
    .timeline-desc-h { font-size: 12px; color: #475569; margin: 0; line-height: 1.45; }
    .timeline-arrow { display: flex; align-items: center; justify-content: center; font-size: 18px; color: #94a3b8; }
    @media (max-width: 768px) {
        .timeline-arrow { display: none; }
    }

    /* Tableau régional épuré */
    .table-responsive { width: 100%; overflow-x: auto; border-radius: var(--radius-md); border: 1px solid #cbd5e1; box-shadow: 0 4px 6px rgba(0,0,0,0.01); }
    .regional-table { width: 100%; border-collapse: collapse; text-align: left; font-size: var(--text-sm); }
    .regional-table th { background-color: #0f172a; color: #ffffff; font-weight: 900; text-transform: uppercase; letter-spacing: 0.5px; padding: 12px 15px; }
    .regional-table td { padding: 12px 15px; border-bottom: 1px solid #e2e8f0; color: #334155; }
    .regional-table tr:nth-child(even) { background-color: #f8fafc; }
    .regional-table tr:last-child td { border-bottom: none; }
    .badge-temp { font-weight: 900; color: #ffffff; background: #dc2626; padding: 5px 10px; border-radius: 8px; font-size: 12.5px; display: inline-block; }

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
        
        timeline = data.get("timeline", {})
        regional = data.get("regional", {})
        conf = data.get("confidence", {})
        dash = data.get("dashboard", {}) or {}
        scenarios = data.get("scenarios", {})
        social = data.get("social_pack", {}) or {}
        alert = data.get("alert", {}) or {}
        kpis = data.get("kpis", {}) or {}
        impacts = data.get("impacts", {}) or {}

        # Nettoyage des posts sociaux pour éviter les backslashes dans le f-string
        linkedin_clean = social.get('linkedin', '').replace('<br>', '\n').replace('<br/>', '\n')
        facebook_clean = social.get('facebook', '').replace('<br>', '\n').replace('<br/>', '\n')
        twitter_clean = social.get('twitter', '').replace('<br>', '\n').replace('<br/>', '\n')
        tiktok_clean = social.get('tiktok', '').replace('<br>', '\n').replace('<br/>', '\n')
        instagram_clean = social.get('instagram', '').replace('<br>', '\n').replace('<br/>', '\n')

        # Couleur dynamique du badge de confiance
        conf_score_raw = conf.get('score', '4/5')
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
        summary_10s_raw = data.get("takeaways_10s", "")
        if summary_10s_raw:
            lines_10s = [l.strip("-* ").strip() for l in summary_10s_raw.split("\n") if l.strip()]
            for l in lines_10s:
                if l:
                    summary_10s_html += f"<li>{l}</li>"
        if not summary_10s_html:
            summary_10s_html = "<li>Synthèse des faits disponible.</li>"

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

        divider = '<div class="week-divider"></div>' if w_idx > 0 else ""
        weeks_html += f"""
        {divider}
        
        <!-- TITRE DE SEMAINE EN 2 LIGNES -->
        <div class="week-title-box">
            <h2 class="week-title-line1">📅 {data.get('title_line1', 'SEMAINE')}</h2>
            <div class="week-title-line2">{data.get('title_line2', 'Synthèse des prévisions')}</div>
        </div>
        
        <!-- BANDEAU DE SYNTHÈSE PLEINE LARGEUR (REMPLACE L'ANCIEN BANDEAU GEANT ROUGE) -->
        <div class="alert-banner {alert_bg_class}" style="margin-bottom: 25px;">
            <div class="alert-left">
                <span class="alert-badge-top">Synthèse Exécutive - Alerte {alert_lvl}</span>
                <h2 class="alert-title-lg">{alert.get('event_type', 'Événement')}</h2>
                <div class="alert-date-block">
                    PÉRIODE CONCERNÉE : {alert.get('start', '-')} au {alert.get('end', '-')} (Fiabilité : {alert.get('confidence', '-')})
                </div>
            </div>
        </div>

        <!-- LIGNE DE 6 KPI DE POIDS ÉGAL -->
        <div class="kpi-row-6" style="margin-bottom: 25px;">
            <div class="kpi-card-6">
                <div class="kpi-icon">🌡️</div>
                <div class="kpi-val">{kpis.get('temp_range', '-')}</div>
                <div class="kpi-lbl">Température</div>
            </div>
            <div class="kpi-card-6">
                <div class="kpi-icon">📅</div>
                <div class="kpi-val">{kpis.get('period', '-')}</div>
                <div class="kpi-lbl">Période</div>
            </div>
            <div class="kpi-card-6">
                <div class="kpi-icon">⏱️</div>
                <div class="kpi-val">{kpis.get('duration', '-')}</div>
                <div class="kpi-lbl">Durée</div>
            </div>
            <div class="kpi-card-6">
                <div class="kpi-icon">🎯</div>
                <div class="kpi-val">{kpis.get('confidence', '-')}</div>
                <div class="kpi-lbl">Confiance</div>
            </div>
            <div class="kpi-card-6">
                <div class="kpi-icon">⚠️</div>
                <div class="kpi-val">{kpis.get('risks', '-')}</div>
                <div class="kpi-lbl">Risques</div>
            </div>
            <div class="kpi-card-6">
                <div class="kpi-icon">📍</div>
                <div class="kpi-val">{kpis.get('zone', '-')}</div>
                <div class="kpi-lbl">Zone</div>
            </div>
        </div>

        <!-- RÉSUMÉ EN 10 SECONDES (4 à 6 phrases courtes) -->
        <div class="summary-10s-box" style="margin-bottom: 25px;">
            <h3>⏱️ À Retenir en 10 Secondes</h3>
            <ul class="summary-10s-list">
                {summary_10s_html}
            </ul>
        </div>

        <!-- JAUGES DE RISQUES & CONFIANCE COMPACTES -->
        <div class="section-title">📊 INDICES DE RISQUES PHYSIQUES</div>
        <div class="dashboard-meters-row" style="margin-bottom: 25px;">
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
                    <h4>🌧️ Pluie</h4>
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
                    <h4>💨 Vent</h4>
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

        <!-- BLOC IMPACTS SECTORIELS ATTENDUS -->
        <div class="section-title">⚠️ IMPACTS ATTENDUS PAR SECTEUR</div>
        <div class="impacts-grid" style="margin-bottom: 25px;">
            <div class="impact-item">
                <span class="impact-icon">👥</span>
                <div class="impact-content">
                    <strong class="impact-title">Population</strong>
                    <span class="impact-text">{impacts.get('population', '-')}</span>
                </div>
            </div>
            <div class="impact-item">
                <span class="impact-icon">🚗</span>
                <div class="impact-content">
                    <strong class="impact-title">Déplacements</strong>
                    <span class="impact-text">{impacts.get('travel', '-')}</span>
                </div>
            </div>
            <div class="impact-item">
                <span class="impact-icon">🏗️</span>
                <div class="impact-content">
                    <strong class="impact-title">Travaux & BTP</strong>
                    <span class="impact-text">{impacts.get('work', '-')}</span>
                </div>
            </div>
            <div class="impact-item">
                <span class="impact-icon">🌾</span>
                <div class="impact-content">
                    <strong class="impact-title">Agriculture</strong>
                    <span class="impact-text">{impacts.get('agri', '-')}</span>
                </div>
            </div>
            <div class="impact-item">
                <span class="impact-icon">⚡</span>
                <div class="impact-content">
                    <strong class="impact-title">Orages & Réseaux</strong>
                    <span class="impact-text">{impacts.get('storm', '-')}</span>
                </div>
            </div>
            <div class="impact-item">
                <span class="impact-icon">🌿</span>
                <div class="impact-content">
                    <strong class="impact-title">Sécheresse & Eau</strong>
                    <span class="impact-text">{impacts.get('drought', '-')}</span>
                </div>
            </div>
        </div>

        <!-- CHRONOLOGIE HORIZONTALE EN 4 ETAPES -->
        <div class="section-title">🗓️ CHRONOLOGIE DE L'ÉPISODE</div>
        <div class="timeline-horizontal" style="margin-bottom: 25px;">
            <div class="timeline-item-h">
                <div class="timeline-circle">1</div>
                <strong class="timeline-phase-h">Début</strong>
                <span class="timeline-date-h">{timeline.get('date_debut', '-')}</span>
                <p class="timeline-desc-h">{timeline.get('desc_debut', '-')}</p>
            </div>
            <div class="timeline-arrow">➔</div>
            <div class="timeline-item-h">
                <div class="timeline-circle">2</div>
                <strong class="timeline-phase-h">Montée</strong>
                <span class="timeline-date-h">{timeline.get('date_montee', '-')}</span>
                <p class="timeline-desc-h">{timeline.get('desc_montee', '-')}</p>
            </div>
            <div class="timeline-arrow">➔</div>
            <div class="timeline-item-h">
                <div class="timeline-circle">3</div>
                <strong class="timeline-phase-h">Pic</strong>
                <span class="timeline-date-h">{timeline.get('date_pic', '-')}</span>
                <p class="timeline-desc-h">{timeline.get('desc_pic', '-')}</p>
            </div>
            <div class="timeline-arrow">➔</div>
            <div class="timeline-item-h">
                <div class="timeline-circle">4</div>
                <strong class="timeline-phase-h">Fin</strong>
                <span class="timeline-date-h">{timeline.get('date_fin', '-')}</span>
                <p class="timeline-desc-h">{timeline.get('desc_fin', '-')}</p>
            </div>
        </div>

        <!-- TABLEAU DE SYNTHÈSE RÉGIONALE LISIBLE -->
        <div class="section-title">🗺️ TENDANCE PAR GRANDES RÉGIONS</div>
        <div class="table-responsive" style="margin-bottom: 25px;">
            <table class="regional-table">
                <thead>
                    <tr>
                        <th>Région</th>
                        <th>🌡️ Températures</th>
                        <th>🌧️ Pluviométrie</th>
                        <th>⚠️ Risque Majeur</th>
                        <th>🎯 Fiabilité</th>
                    </tr>
                </thead>
                <tbody>
                    {regional_table_rows}
                </tbody>
            </table>
        </div>

        <!-- GRAPHIQUES METEO DE TENDANCE (REMONTÉS JUSTE APRÈS LA SYNTHÈSE) -->
        {html_images_block}

        <!-- RUBRIQUE "LES CHIFFRES À RETENIR" -->
        <div class="section-title">🔢 LES CHIFFRES À RETENIR</div>
        <div class="numbers-grid" style="margin-bottom: 25px;">
            {key_numbers_html}
        </div>

        <!-- ANALYSE DÉTAILLÉE (SCÉNARIOS & INCERTITUDES) DÉPORTÉE PLUS BAS -->
        <div class="detailed-analysis-panel" style="margin-bottom: 25px;">
            <h3 class="detailed-analysis-title">🔮 SCÉNARIOS DE MODÉLISATIONS & ANALYSES</h3>
            
            <div class="scenarios-container">
                <div class="scenario-card sc-major">
                    <div class="sc-header">
                        <h3>🟢 Scénario Majoritaire ({scenarios.get('majoritaire', {}).get('prob', '65%')})</h3>
                    </div>
                    <strong style="font-size:12.5px; display:block; margin-bottom:4px; color:#10b981;">{scenarios.get('majoritaire', {}).get('title', '')}</strong>
                    <p class="sc-text">{scenarios.get('majoritaire', {}).get('desc', '')}</p>
                </div>
                
                <div class="scenario-card sc-median">
                    <div class="sc-header">
                        <h3>🟡 Scénario Alternatif ({scenarios.get('median', {}).get('prob', '25%')})</h3>
                    </div>
                    <strong style="font-size:12.5px; display:block; margin-bottom:4px; color:#f59e0b;">{scenarios.get('median', {}).get('title', '')}</strong>
                    <p class="sc-text">{scenarios.get('median', {}).get('desc', '')}</p>
                </div>
                
                <div class="scenario-card sc-minor">
                    <div class="sc-header">
                        <h3>🔴 Scénario Minoritaire ({scenarios.get('minoritaire', {}).get('prob', '10%')})</h3>
                    </div>
                    <strong style="font-size:12.5px; display:block; margin-bottom:4px; color:#ef4444;">{scenarios.get('minoritaire', {}).get('title', '')}</strong>
                    <p class="sc-text">{scenarios.get('minoritaire', {}).get('desc', '')}</p>
                </div>
            </div>

            <!-- INCERTITUDES -->
            <div class="confidence-panel" style="padding: 15px; margin-bottom: 0;">
                <div class="confidence-head" style="margin-bottom: 8px;">
                    <strong>Incertitudes Modélisations</strong>
                    <span class="{conf_class}" style="padding: 4px 12px; border-radius: 9999px; font-weight: 800; font-size: 11px; color: white; {get_badge_color_class(conf_label)}">Consensus : {conf_score_raw}</span>
                </div>
                <div class="uncertainties-box">
                    <strong style="display: block; margin-bottom: 6px; color: #dc2626; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px;">❓ Incertitudes & Points Clés :</strong>
                    {data.get('key_uncertainties', '')}\n{data.get('monitoring_points', '')}
                </div>
            </div>

            <!-- À RETENIR -->
            <div class="takeaways-panel" style="margin-bottom: 0;">
                <h3>📌 Synthèse Récapitulative</h3>
                <ul>
                    {takeaways_li_html}
                </ul>
            </div>
        </div>

        <!-- PACK RÉSEAUX SOCIAUX -->
        <div class="section-title">📢 PACK DE DIFFUSION RÉSEAUX SOCIAUX</div>
        <div class="social-pack-container">
            <div class="social-platform-card">
                <div class="social-platform-header sp-linkedin">
                    <span>🔗 LinkedIn ({len(linkedin_clean)} car.)</span>
                    <button class="copy-btn" onclick="navigator.clipboard.writeText(this.parentNode.parentNode.querySelector('.social-platform-body').innerText); alert('Copié !');">Copier</button>
                </div>
                <div class="social-platform-body">{linkedin_clean}</div>
            </div>

            <div class="social-platform-card">
                <div class="social-platform-header sp-facebook">
                    <span>👥 Facebook ({len(facebook_clean)} car.)</span>
                    <button class="copy-btn" onclick="navigator.clipboard.writeText(this.parentNode.parentNode.querySelector('.social-platform-body').innerText); alert('Copié !');">Copier</button>
                </div>
                <div class="social-platform-body">{facebook_clean}</div>
            </div>

            <div class="social-platform-card">
                <div class="social-platform-header sp-twitter">
                    <span>🐦 X (Twitter - {len(twitter_clean)} / 280 car.)</span>
                    <button class="copy-btn" onclick="navigator.clipboard.writeText(this.parentNode.parentNode.querySelector('.social-platform-body').innerText); alert('Copié !');">Copier</button>
                </div>
                <div class="social-platform-body">{twitter_clean}</div>
            </div>

            <div class="social-platform-card">
                <div class="social-platform-header sp-tiktok">
                    <span>🎵 TikTok ({len(tiktok_clean)} car.)</span>
                    <button class="copy-btn" onclick="navigator.clipboard.writeText(this.parentNode.parentNode.querySelector('.social-platform-body').innerText); alert('Copié !');">Copier</button>
                </div>
                <div class="social-platform-body">{tiktok_clean}</div>
            </div>

            <div class="social-platform-card">
                <div class="social-platform-header sp-instagram">
                    <span>📸 Instagram ({len(instagram_clean)} car.)</span>
                    <button class="copy-btn" onclick="navigator.clipboard.writeText(this.parentNode.parentNode.querySelector('.social-platform-body').innerText); alert('Copié !');">Copier</button>
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
    <title>Analyses & Tendances Météo - Tableau de Bord</title>
    <style>{style}</style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div style="font-size: 11px; font-weight: 800; letter-spacing: 2px; text-transform: uppercase; margin-bottom: 8px;">MONSIEUR MÉTÉO</div>
            <h1>📊 BULLETIN ÉVOLUTION & TENDANCES MÉTÉO</h1>
            <p>Tableau de bord de synthèse du {datetime.datetime.now().strftime('%d/%m/%Y')}</p>
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
