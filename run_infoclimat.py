import urllib.request
import urllib.error
import urllib.parse
import re
import sys
import os
import json
import base64
import uuid
import datetime
import smtplib
import socket
import time
import unicodedata
import concurrent.futures
from email.utils import formatdate
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

socket.setdefaulttimeout(10)

INDEX_URL = "https://forums.infoclimat.fr/f/forum/20-evolution-%C3%A0-plus-long-terme/"
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'

REGIONS_CONFIG = {
    "auvergne_rhone_alpes": ("Auvergne-Rhône-Alpes", "ARA.html"),
    "bourgogne_franche_comte": ("Bourgogne-Franche-Comté", "BFC.html"),
    "bretagne": ("Bretagne", "BRE.html"),
    "centre_val_de_loire": ("Centre-Val de Loire", "CVL.html"),
    "corse": ("Corse", "COR.html"),
    "grand_est": ("Grand Est", "GES.html"),
    "hauts_de_france": ("Hauts-de-France", "HDF.html"),
    "ile_de_france": ("Île-de-France", "IDF.html"),
    "normandie": ("Normandie", "NOR.html"),
    "nouvelle_aquitaine": ("Nouvelle-Aquitaine", "NAQ.html"),
    "occitanie": ("Occitanie", "OCC.html"),
    "pays_de_la_loire": ("Pays de la Loire", "PDL.html"),
    "provence_alpes_cote_azur": ("Provence-Alpes-Côte d'Azur", "PACA.html"),
}

REGIONS_MAP = {k: v[0] for k, v in REGIONS_CONFIG.items()}

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

def process_topic(target_topic, topic_idx, date_context_str):
    decoded_topic = urllib.parse.unquote(target_topic)
    topic_title_slug = decoded_topic.rstrip('/').split('/')[-1]
    topic_title_slug = re.sub(r'^\d+-', '', topic_title_slug)
    topic_title_clean = topic_title_slug.replace('-', ' ').title()
    print(f"\n--- Sujet [{topic_idx+1}] : {topic_title_clean} ({target_topic}) ---")
    
    print(f"[{topic_idx+1}] Analyse de la pagination...")
    try:
        html_topic = fetch_url(target_topic)
    except Exception as e:
        print(f"Erreur sujet : {e}")
        return None
        
    pages = re.findall(r'\?page=(\d+)', html_topic)
    last_page = 1
    if pages:
        last_page = max(int(p) for p in pages)
    print(f"[{topic_idx+1}] Pages détectées : {last_page}")
    
    start_page = max(1, last_page - 2)
    all_comments = []
    all_authors = []
    
    print(f"[{topic_idx+1}] Chargement des commentaires des pages {start_page} à {last_page}...")
    for page in range(start_page, last_page + 1):
        page_url = f"{target_topic}?page={page}"
        try:
            html_page = fetch_url(page_url)
            page_comments = re.findall(r'<div[^>]*data-role=["\']commentContent["\'][^>]*>(.*?)</div>\s*</div>', html_page, re.DOTALL)
            page_authors = re.findall(r'<strong>\s*<a href=[^>]*class=["\']ipsType_break["\'][^>]*>(.*?)</a>', html_page)
            all_comments.extend(page_comments)
            all_authors.extend(page_authors)
        except Exception as e:
            print(f"Erreur page {page} : {e}")
            
    cleaned_comments_data = []
    for idx, comment in enumerate(all_comments):
        clean_comment = re.sub(r'<br\s*/?>', '\n', comment)
        clean_comment = re.sub(r'<[^>]+>', '', clean_comment).strip()
        clean_comment = re.sub(r'\n\s*\n', '\n', clean_comment)
        author = all_authors[idx] if idx < len(all_authors) else "Membre"
        cleaned_comments_data.append(f"Auteur: {author}\nMessage:\n{clean_comment}")
        
    recent_messages_text = "\n\n=======================\n\n".join(cleaned_comments_data[-20:])
    
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

    print(f"[{topic_idx+1}] Appel de l'IA pour l'analyse des scénarios météo...")
    system_prompt = """Tu es Patrick Marlière, météorologue expert de renommée nationale pour Monsieur Météo.

MISSION
À partir EXCLUSIVEMENT des discussions et analyses météorologiques fournies en entrée, tu dois produire un bulletin d'analyse météorologique professionnel, grand public, hyper-visuel, pédagogique et directement exploitable sur le web et les réseaux sociaux sans aucune modification manuelle.

RÈGLE D'OR N°1 : DATES EXACTES ET JOURS NOMMÉS DANS 100% DES SECTIONS
Dans TOUTES les sections (Résumé, Chronologie, Régions, Scénarios, Incertitudes, À Retenir, Posts Sociaux), tu devez mentionner les jours précis associés à leurs dates exactes (ex: Lundi 20 juillet, Mardi 21 juillet, Mercredi 22 juillet, Jeudi 23 juillet, Vendredi 24 juillet, Samedi 25 juillet, Dimanche 26 juillet). Ne dis plus jamais "début de semaine" ou "week-end" sans les associer directement à leur date.

RÈGLE D'OR N°2 : INTÉGRATION DE LA DATE DE GÉNÉRATION & PÉRIODE PERTINENTE
- Analyse avec attention la "Date actuelle de génération" transmise dans l'invite.
- Si le sujet correspond à la "Semaine en cours" : toute journée précédant cette date est déjà passée. Les prévisions doivent se concentrer EXCLUSIVEMENT sur la période allant de la date de génération au dimanche de cette semaine. Ignore ou mentionne comme "déjà écoulées" les journées passées.
- Si le sujet correspond à la "Semaine suivante" (Semaine future) : c'est la véritable semaine de tendance à moyen terme. Rédige les prévisions complètes jour par jour, du lundi au dimanche.

RÈGLE D'OR N°3 : PÉDAGOGIE SYNOPTIQUE VULGARISÉE
Explique de manière simple et pédagogique le mécanisme synoptique sous-jacent (goutte froide, dorsale anticyclonique, talweg, marais barométrique, flux océanique) en une phrase fluide pour montrer notre expertise météorologique sans perdre le grand public.

RÈGLE D'OR N°4 : IMPACTS CONCRETS SUR LA VIE QUOTIDIENNE
Mentionne systématiquement les répercussions pratiques du temps prévu : confort/ressenti thermique (chaleur lourde, fraîcheur humide), vacances et activités extérieures, transports/déplacements, travaux agricoles/BTP, orages ou pluies bénéfiques.

RÈGLE D'OR N°5 : CALIBRAGE DES SCÉNARIOS & RAISON DU CHOIX
Indique précisément POURQUOI le Scénario Majoritaire est privilégié par rapport aux deux autres.
- Majoritaire : ~130 à 150 mots maximum.
- Alternatif & Minoritaire : 80 à 120 mots maximum chacun.

RÈGLE D'OR N°6 : PACK MULTI-RÉSEAUX SOCIAUX CONÇU POUR MOBILES
Rédige 5 publications distinctes, spécifiquement adaptées à l'audience, au style et aux limites de caractères de chaque plateforme :
- **LinkedIn** : Storytelling expert météo captivant, ton pro et pédagogique. Paragraphes courts, émojis et hashtags ciblés. (250-300 mots)
- **Facebook** : Message chaleureux, axé vie quotidienne et communauté. Paragraphes aérés, émojis.
- **X (Twitter)** : Post court, percutant et dynamique. Limite stricte de 280 caractères, hashtags inclus.
- **TikTok** : Description de vidéo dynamique, phrases courtes, appel à l'action visuel et hashtags tendance.
- **Instagram** : Légende soignée, esthétique, invitant à la contemplation ou à la préparation, avec un appel à l'action pour lire le rapport HTML complet en bio.

VÉRIFICATION QUALITÉ AUTOMATIQUE SILENCIEUSE (AVANT D'ÉMETTRE) :
1. Les probabilités des 3 scénarios totalisent-elles EXACTEMENT 100% ?
2. Les jours passés pour la semaine en cours ont-ils bien été exclus des prévisions à venir ?
3. Le post X (Twitter) fait-il moins de 280 caractères ?
4. Toutes les dates et jours correspondent-ils à la semaine analysée ?
5. Aucune donnée chiffrée n'a-t-elle été inventée ?
6. Le post LinkedIn est-il en paragraphes très courts sans aucun markdown ?

FORMAT DE SORTIE OBLIGATOIRE - Utilise EXACTEMENT ces balises :

[SUBJECT_TITLE_LINE1]
Semaine X - Du Lundi DD au Dimanche DD Mois AAAA

[SUBJECT_TITLE_LINE2]
Accroche météo courte résumant le temps de la semaine avec dates exactes

[EXPRESS_SUMMARY]
2 phrases ultra-concises allant à l'essentiel avec les jours et dates précis (ex: Du Lundi 20 au Mercredi 22 juillet, temps sec et chaud...).

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

[TIMELINE_EARLY_WEEK]
Jours exacts : Prévisions, mécanisme synoptique vulgarisé et impacts concrets.

[TIMELINE_MID_WEEK]
Jours exacts : Évolution chronologique, ressenti et activités.

[TIMELINE_LATE_WEEK]
Jours exacts : Tendance pour la fin de semaine et vigilance.

[TIMELINE_WEEKEND]
Jours exacts : Prévisions pour le week-end et loisirs extérieurs.

[REGIONAL_HDF_NORTH]
1-2 phrases pour Hauts-de-France & Nord.

[REGIONAL_ATLANTIC]
1-2 phrases pour Façade Atlantique.

[REGIONAL_CENTRAL]
1-2 phrases pour Régions Centrales.

[REGIONAL_SOUTH]
1-2 phrases pour Moitié Sud.

[REGIONAL_MEDITERRANEAN]
1-2 phrases pour Pourtour Méditerranéen.

[REGIONAL_MOUNTAINS]
1-2 phrases pour Reliefs.

[SCENARIO_MAJORITAIRE_PROB]
65%

[SCENARIO_MAJORITAIRE_TITLE]
Titre synoptique court

[SCENARIO_MAJORITAIRE_DESC]
Description concise (~130-150 mots)

[SCENARIO_MEDIAN_PROB]
25%

[SCENARIO_MEDIAN_TITLE]
Titre synoptique court

[SCENARIO_MEDIAN_DESC]
Description concise (80-120 mots)

[SCENARIO_MINORITAIRE_PROB]
10%

[SCENARIO_MINORITAIRE_TITLE]
Titre synoptique court

[SCENARIO_MINORITAIRE_DESC]
Description concise (80-120 mots)

[KEY_UNCERTAINTIES]
- Incertitude 1
- Incertitude 2

[MONITORING_POINTS]
- Point de vigilance 1
- Point de vigilance 2

[KEY_TAKEAWAYS]
- Puce essentielle 1 avec date
- Puce essentielle 2 avec date
- Puce essentielle 3 avec date
- Puce essentielle 4 avec impact concret

[SOCIAL_LINKEDIN]
Post LinkedIn réseaux sociaux captivant en texte brut (250-300 mots) aéré en paragraphes très courts pour smartphone avec dates exactes et question d'interaction finale.

[SOCIAL_FACEBOOK]
Post Facebook chaleureux et aéré pour grand public, avec émojis et dates exactes.

[SOCIAL_TWITTER]
Post X (Twitter) percutant et court (MAXIMUM 280 caractères, espaces compris) avec hashtags.

[SOCIAL_TIKTOK]
Description TikTok avec accroches, émojis et hashtags ciblés.

[SOCIAL_INSTAGRAM]
Légende Instagram soignée et esthétique avec appel à l'action pour bio.

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
                "express_summary": r"\[EXPRESS_SUMMARY\]\s*\n(.*?)(?=\n\s*\[|$)",
                "express_trend": r"\[EXPRESS_TREND\]\s*\n(.*?)(?=\n\s*\[|$)",
                "express_temperatures": r"\[EXPRESS_TEMPERATURES\]\s*\n(.*?)(?=\n\s*\[|$)",
                "express_precipitations": r"\[EXPRESS_PRECIPITATIONS\]\s*\n(.*?)(?=\n\s*\[|$)",
                "express_main_risk": r"\[EXPRESS_MAIN_RISK\]\s*\n(.*?)(?=\n\s*\[|$)",
                "global_confidence_score": r"\[GLOBAL_CONFIDENCE_SCORE\]\s*\n(.*?)(?=\n\s*\[|$)",
                "global_confidence_desc": r"\[GLOBAL_CONFIDENCE_DESC\]\s*\n(.*?)(?=\n\s*\[|$)",
                "timeline_early": r"\[TIMELINE_EARLY_WEEK\]\s*\n(.*?)(?=\n\s*\[|$)",
                "timeline_mid": r"\[TIMELINE_MID_WEEK\]\s*\n(.*?)(?=\n\s*\[|$)",
                "timeline_late": r"\[TIMELINE_LATE_WEEK\]\s*\n(.*?)(?=\n\s*\[|$)",
                "timeline_weekend": r"\[TIMELINE_WEEKEND\]\s*\n(.*?)(?=\n\s*\[|$)",
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
                    "timeline": {
                        "early": parsed["timeline_early"],
                        "mid": parsed["timeline_mid"],
                        "late": parsed["timeline_late"],
                        "weekend": parsed["timeline_weekend"],
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
            print(f"[{topic_idx+1}] Erreur parsing textuel : {e}")
            
    if not data:
        print(f"[{topic_idx+1}] ERREUR : Parsing échoué — vérifier les logs du LLM ci-dessus.")
        return None
    return {
        "data": data,
        "images": downloaded_images,
        "raw_comments": recent_messages_text  # conservé pour injection directe dans les bulletins régionaux
    }

def process_region_query(r_key, r_name, recent_messages_text, topic_title_clean, date_context_str, topic_idx):
    """Même prompt que le national, 2 semaines couverts, même richesse — focalisé sur r_name."""
    system_prompt = f"""Tu es Patrick Marlière, météorologue expert de renommée nationale pour Monsieur Météo.

MISSION
À partir EXCLUSIVEMENT des discussions et analyses météorologiques fournies en entrée, tu dois produire un bulletin d'analyse météorologique professionnel et complet pour la région : {r_name}
Le bulletin doit couvrir les DEUX semaines fournies en contexte : la semaine en cours ET la semaine suivante.

RÈGLE D'OR N°0 : RÉALITÉ SAISONNIÈRE & FOCUS GÉOGRAPHIQUE
- La date et la saison sont précisées dans le contexte. Respecte-les ABSOLUMENT.
- En été (juin/juillet/août), les mentions de neige en plaine, de gel, de températures négatives sont INTERDITES sauf en haute altitude (>1500m) si les sources le mentionnent EXPLICITEMENT.
- Toutes les analyses, températures, risques et impacts doivent concerner EXCLUSIVEMENT {r_name} (ses départements, villes, reliefs ou zones côtières). Si une information n'est pas précisée pour cette région, écris "Information non précisée dans les sources pour {r_name}". Ne déduis jamais depuis une autre région.

RÈGLE D'OR N°1 : DATES EXACTES ET JOURS NOMMÉS DANS 100% DES SECTIONS
Dans TOUTES les sections, tu dois mentionner les jours précis avec leurs dates exactes (ex: Lundi 27 Juillet, Mardi 28 Juillet).

RÈGLE D'OR N°2 : INTÉGRATION DE LA DATE DE GÉNÉRATION
Analyse la "Date actuelle de génération". Les journées déjà passées sont exclues des prévisions à venir.

RÈGLE D'OR N°3 : PÉDAGOGIE SYNOPTIQUE VULGARISÉE
Explique le mécanisme synoptique (dorsale, talweg, goutte froide, flux océanique) en une phrase simple et pédagogique.

RÈGLE D'OR N°4 : IMPACTS CONCRETS SUR LA VIE QUOTIDIENNE EN {r_name.upper()}
Mentionne les répercussions pratiques : confort thermique, vacances, transports, agriculture/BTP, orages locaux.

RÈGLE D'OR N°5 : CALIBRAGE DES SCÉNARIOS POUR {r_name.upper()}
3 scénarios calibrés pour cette région spécifique. Les probabilités totalisent EXACTEMENT 100%.
- Majoritaire : ~130 à 150 mots maximum.
- Alternatif & Minoritaire : 80 à 120 mots maximum chacun.

RÈGLE D'OR N°6 : PACK MULTI-RÉSEAUX SOCIAUX POUR {r_name.upper()}
5 publications distinctes adaptées à chaque plateforme, mentionnant la région {r_name} explicitement :
- LinkedIn (250-300 mots, storytelling expert)
- Facebook (message chaleureux, communauté locale)
- X/Twitter (MAXIMUM 280 caractères, hashtags)
- TikTok (description vidéo dynamique)
- Instagram (légende soignée, CTA bio)

VÉRIFICATION QUALITÉ AUTOMATIQUE SILENCIEUSE :
1. Probabilités des 3 scénarios = exactement 100% ?
2. Post Twitter < 280 caractères ?
3. Toutes les données concernent bien {r_name} ?
4. Aucune donnée chiffrée inventée ?

FORMAT DE SORTIE OBLIGATOIRE - Utilise EXACTEMENT ces balises :

[SUBJECT_TITLE_LINE1]
Semaine X - Du Lundi DD au Dimanche DD Mois AAAA — {r_name}

[SUBJECT_TITLE_LINE2]
Accroche météo courte résumant le temps de la semaine pour {r_name}

[EXPRESS_SUMMARY]
2 phrases ultra-concises avec jours et dates précis pour {r_name}.

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
Une phrase courte expliquant la raison du niveau de confiance pour {r_name}.

[TIMELINE_EARLY_WEEK]
Semaine en cours — début (Lundi/Mardi) : météo, mécanisme synoptique et impacts pour {r_name}.

[TIMELINE_MID_WEEK]
Semaine en cours — fin (Mercredi à Dimanche) : évolution chronologique pour {r_name}.

[TIMELINE_LATE_WEEK]
Semaine suivante — début (Lundi/Mardi) : premières tendances pour {r_name}.

[TIMELINE_WEEKEND]
Semaine suivante — fin (Mercredi à Dimanche) : tendances de fin de semaine pour {r_name}.

[REGIONAL_HDF_NORTH]
Sous-zone ou secteur nord / nord-ouest de {r_name} (si pertinent).

[REGIONAL_ATLANTIC]
Sous-zone ou secteur ouest / façade maritime de {r_name} (si pertinent).

[REGIONAL_CENTRAL]
Secteur central / intérieur de {r_name} (si pertinent).

[REGIONAL_SOUTH]
Sous-zone ou secteur sud de {r_name} (si pertinent).

[REGIONAL_MEDITERRANEAN]
Secteur méditerranéen / côtier de {r_name} (si pertinent, sinon "Non applicable").

[REGIONAL_MOUNTAINS]
Secteur montagneux / relief de {r_name} (si pertinent, sinon "Non applicable").

[SCENARIO_MAJORITAIRE_PROB]
65%

[SCENARIO_MAJORITAIRE_TITLE]
Titre synoptique court pour {r_name}

[SCENARIO_MAJORITAIRE_DESC]
Description concise (~130-150 mots) pour {r_name}

[SCENARIO_MEDIAN_PROB]
25%

[SCENARIO_MEDIAN_TITLE]
Titre synoptique court

[SCENARIO_MEDIAN_DESC]
Description concise (80-120 mots) pour {r_name}

[SCENARIO_MINORITAIRE_PROB]
10%

[SCENARIO_MINORITAIRE_TITLE]
Titre synoptique court

[SCENARIO_MINORITAIRE_DESC]
Description concise (80-120 mots) pour {r_name}

[KEY_UNCERTAINTIES]
- Incertitude 1 propre à {r_name}
- Incertitude 2 propre à {r_name}

[MONITORING_POINTS]
- Point de vigilance 1 pour {r_name}
- Point de vigilance 2 pour {r_name}

[KEY_TAKEAWAYS]
- Puce essentielle 1 avec date pour {r_name}
- Puce essentielle 2 avec date pour {r_name}
- Puce essentielle 3 avec date pour {r_name}
- Puce essentielle 4 avec impact concret pour {r_name}

[SOCIAL_LINKEDIN]
Post LinkedIn expert pour {r_name} (250-300 mots, paragraphes courts smartphone).

[SOCIAL_FACEBOOK]
Post Facebook chaleureux pour la communauté de {r_name}, avec émojis.

[SOCIAL_TWITTER]
Post X (MAXIMUM 280 caractères) pour {r_name} avec hashtags.

[SOCIAL_TIKTOK]
Description TikTok pour {r_name} avec accroches, émojis et hashtags.

[SOCIAL_INSTAGRAM]
Légende Instagram pour {r_name} avec CTA bio.

[LINKEDIN_HASHTAGS]
#Meteo #{r_name.replace('-', '').replace(' ', '').replace("'", '')} #Previsions #France #MonsieurMeteo"""

    user_prompt = f"""Contexte de date : {date_context_str}
Région analysée : {r_name}

Voici les analyses des prévisionnistes pour : {topic_title_clean}

{recent_messages_text}

Analyse ces discussions EXCLUSIVEMENT pour la région {r_name} et génère le rapport complet au format spécifié."""

    response = None
    for attempt in range(1, 4):
        print(f"[Région {r_name}] Tentative {attempt}/3...")
        r = call_llm(system_prompt, user_prompt)
        if r:
            response = r
            break

    if not response:
        print(f"[Région {r_name}] ERREUR : Pas de réponse LLM")
        return r_key, None

    blocks = {
        "title_line1": r"\[SUBJECT_TITLE_LINE1\]\s*\n(.*?)(?=\n\s*\[|$)",
        "title_line2": r"\[SUBJECT_TITLE_LINE2\]\s*\n(.*?)(?=\n\s*\[|$)",
        "express_summary": r"\[EXPRESS_SUMMARY\]\s*\n(.*?)(?=\n\s*\[|$)",
        "express_trend": r"\[EXPRESS_TREND\]\s*\n(.*?)(?=\n\s*\[|$)",
        "express_temperatures": r"\[EXPRESS_TEMPERATURES\]\s*\n(.*?)(?=\n\s*\[|$)",
        "express_precipitations": r"\[EXPRESS_PRECIPITATIONS\]\s*\n(.*?)(?=\n\s*\[|$)",
        "express_main_risk": r"\[EXPRESS_MAIN_RISK\]\s*\n(.*?)(?=\n\s*\[|$)",
        "global_confidence_score": r"\[GLOBAL_CONFIDENCE_SCORE\]\s*\n(.*?)(?=\n\s*\[|$)",
        "global_confidence_desc": r"\[GLOBAL_CONFIDENCE_DESC\]\s*\n(.*?)(?=\n\s*\[|$)",
        "timeline_early": r"\[TIMELINE_EARLY_WEEK\]\s*\n(.*?)(?=\n\s*\[|$)",
        "timeline_mid": r"\[TIMELINE_MID_WEEK\]\s*\n(.*?)(?=\n\s*\[|$)",
        "timeline_late": r"\[TIMELINE_LATE_WEEK\]\s*\n(.*?)(?=\n\s*\[|$)",
        "timeline_weekend": r"\[TIMELINE_WEEKEND\]\s*\n(.*?)(?=\n\s*\[|$)",
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
        parsed[key] = match.group(1).strip() if match else ""

    data = {
        "title_line1": parsed["title_line1"] or f"Semaine — {r_name}",
        "title_line2": parsed["title_line2"] or f"Tendances pour {r_name}",
        "region_name": r_name,
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
        "timeline": {
            "early": parsed["timeline_early"],
            "mid": parsed["timeline_mid"],
            "late": parsed["timeline_late"],
            "weekend": parsed["timeline_weekend"],
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
            "majoritaire": {"prob": parsed["majoritaire_prob"] or "65%", "title": parsed["majoritaire_title"], "desc": parsed["majoritaire_desc"]},
            "median": {"prob": parsed["median_prob"] or "25%", "title": parsed["median_title"], "desc": parsed["median_desc"]},
            "minoritaire": {"prob": parsed["minoritaire_prob"] or "10%", "title": parsed["minoritaire_title"], "desc": parsed["minoritaire_desc"]},
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

    print(f"[Région {r_name}] Bulletin parsé avec succès !")
    return r_key, data

def clean_html_for_email(html_content):
    # Enlever les boutons de copie, les scripts/onclick et les images base64 (trop lourdes pour SFR/Gmail inline)
    cleaned = re.sub(r'<div class="copy-note">.*?</div>', '', html_content, flags=re.DOTALL)
    cleaned = re.sub(r'\s*onclick="[^"]*"', '', cleaned)
    # Supprimer les blocs img base64 (src="data:image/...") qui gonflent le corps et le font rejeter
    cleaned = re.sub(r'<div class="meteo-image-card".*?</div>\s*</div>', '', cleaned, flags=re.DOTALL)
    cleaned = re.sub(r'<div class="meteo-images-container".*?</div>\s*</div>', '', cleaned, flags=re.DOTALL)
    return cleaned

def main():
    print(f"1. Chargement de l'index du forum : {INDEX_URL}")
    try:
        html_index = fetch_url(INDEX_URL)
    except Exception as e:
        print(f"Erreur index : {e}")
        sys.exit(1)
        
    topic_links = re.findall(r'href=["\'](https://forums.infoclimat.fr/f/topic/\d+-[^"\']+)["\']', html_index)
    clean_topics = []
    seen = set()
    for link in topic_links:
        base_link = link.split('?')[0].split('#')[0]
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

    # Extraction et tri robuste des numéros de semaine pour l'ordre chronologique
    current_iso_week = now.isocalendar()[1]

    def get_topic_week_num(url):
        match = re.search(r'semaine-(\d+)', url.lower())
        return int(match.group(1)) if match else 0

    # Filtrer : garder uniquement les sujets dont le n° de semaine est dans la fenêtre
    # [semaine_courante - 1 .. semaine_courante + 4] pour éviter les anciens fils hiver/printemps
    # La tolérance -1 couvre le cas du lundi matin où le sujet "semaine en cours" n'est pas encore créé.
    relevant_topics = [
        t for t in clean_topics
        if current_iso_week - 1 <= get_topic_week_num(t) <= current_iso_week + 4
    ]

    if not relevant_topics:
        # Fallback : prendre les 2 topics avec le plus grand numéro de semaine
        print(f"[WARN] Aucun topic dans la fenêtre semaine {current_iso_week}. Fallback sur les 2 plus récents.")
        relevant_topics = sorted(clean_topics, key=get_topic_week_num, reverse=True)[:2]

    # Trier par numéro de semaine croissant : semaine en cours d'abord, suivante ensuite
    relevant_topics.sort(key=get_topic_week_num)
    print(f"[INFO] Topics retenus (semaine ISO {current_iso_week}) : {[get_topic_week_num(t) for t in relevant_topics]} → {relevant_topics}")

    # Construire la liste des topics à traiter (toujours 2 semaines si disponibles)
    topics_to_process = []
    if len(relevant_topics) >= 2:
        topics_to_process = [
            (relevant_topics[0], "cours", f"Date actuelle de génération : {today_str}\nType de semaine : Semaine en cours\nPériode à analyser : {jours_restants_cours_str} (jours restants uniquement). Les journées antérieures au {today_str} sont déjà passées, concentre-toi sur la fin de semaine."),
            (relevant_topics[1], "future", f"Date actuelle de génération : {today_str}\nType de semaine : Semaine suivante (Tendance à moyen terme)\nPériode à analyser : {semaine_suivante_str} (semaine complète).")
        ]
    else:
        topics_to_process = [
            (relevant_topics[0], "cours", f"Date actuelle de génération : {today_str}\nSemaine en cours : {semaine_cours_str} (jours restants : {jours_restants_cours_str})\nSemaine suivante : {semaine_suivante_str}.")
        ]

    results = []
    for idx, (topic, sem_type, date_context) in enumerate(topics_to_process):
        res = process_topic(topic, idx, date_context)
        if res:
            results.append(res)
            
    if not results:
        print("Aucun sujet n'a pu être traité.")
        sys.exit(1)
        
    # Style CSS Premium & Responsive (Stripe-inspired)
    style = """
    body { margin: 0; background: #eef3f8; font-family: Arial, Helvetica, sans-serif; color: #172033; font-size: 16px; line-height: 1.6; }
    .wrap { max-width: 920px; margin: 22px auto; background: #fff; border: 1px solid #dce4ee; border-radius: 22px; overflow: hidden; box-shadow: 0 16px 42px rgba(28,48,75,.10); }
    .pad { padding: 30px; }
    .header { padding: 34px 30px; background: #102a43; color: #fff; }
    .kicker { font-size: 13px; letter-spacing: 2px; text-transform: uppercase; font-weight: 800; color: #7dd3fc; }
    .hero-title { font-size: 33px; line-height: 1.15; margin: 8px 0; font-weight: 850; letter-spacing: .2px; }
    .sub { font-size: 15px; line-height: 1.55; color: #d7e5f2; }
    .section { margin-top: 34px; }
    .section-title { font-size: 16px; letter-spacing: .7px; text-transform: uppercase; color: #102a43; font-weight: 850; border-bottom: 2px solid #e8eef5; padding-bottom: 9px; margin-bottom: 15px; }
    .week { border: 1px solid #d8e3ef; border-radius: 18px; overflow: hidden; margin-top: 22px; }
    .week-head { padding: 22px 22px 18px; background: #f4f8fc; border-bottom: 1px solid #d8e3ef; }
    .week-head h2 { font-size: 24px; line-height: 1.25; margin: 0 0 7px; color: #14395b; }
    .week-head p { margin: 0; font-size: 15px; line-height: 1.55; color: #40556b; }
    .alert { padding: 20px; border-radius: 15px; background: #102a43; color: #fff; margin-top: 18px; }
    .alert.orange { background: #7c3f00; }
    .alert.blue { background: #153e75; }
    .alert.green { background: #065f46; }
    .alert .eyebrow { font-size: 12px; text-transform: uppercase; letter-spacing: 1.5px; color: #bae6fd; font-weight: 800; }
    .alert h3 { font-size: 21px; line-height: 1.35; margin: 7px 0 8px; }
    .alert p { font-size: 14px; line-height: 1.55; margin: 0; color: #eaf4fb; }
    .grid2, .grid3, .grid4 { display: table; width: 100%; table-layout: fixed; border-spacing: 10px; }
    .cell { display: table-cell; vertical-align: top; }
    .metric { border: 1px solid #dce6f0; background: #fff; border-radius: 14px; padding: 14px; text-align: center; height: 82px; }
    .metric .big { font-size: 30px; font-weight: 900; color: #14395b; line-height: 1; }
    .metric .label { margin-top: 7px; font-size: 12px; line-height: 1.45; text-transform: uppercase; letter-spacing: .7px; color: #60758a; font-weight: 800; }
    .metric.hot .big { color: #b45309; }
    .metric.risk .big { color: #b91c1c; }
    .metric.good .big { color: #047857; }
    .chips { margin: 12px 0 -4px; }
    .chip { display: inline-block; padding: 6px 9px; margin: 0 5px 6px 0; border-radius: 999px; background: #e9f2f9; color: #173b5d; font-size: 12px; font-weight: 750; }
    .chip.warn { background: #fff2dc; color: #914b00; }
    .chip.red { background: #fee8e8; color: #991b1b; }
    .chip.green { background: #e7f8ef; color: #087443; }
    .timeline-table { width: 100%; border-collapse: separate; border-spacing: 8px; }
    .timeline-table td { width: 25%; vertical-align: top; background: #f7fafc; border: 1px solid #dce6f0; border-top: 4px solid #1d78a8; border-radius: 12px; padding: 13px; }
    .timeline-table strong { font-size: 12px; text-transform: uppercase; color: #14658d; letter-spacing: .5px; }
    .timeline-table .dates { font-size: 14px; font-weight: 850; color: #172033; margin: 5px 0; }
    .timeline-table .keys { font-size: 13px; line-height: 1.55; color: #304a62; }
    .barbox { border: 1px solid #dce6f0; border-radius: 14px; padding: 16px; background: #fff; }
    .barrow { margin: 11px 0; }
    .barlabel { display: table; width: 100%; font-size: 12px; font-weight: 750; color: #3f556a; margin-bottom: 5px; }
    .barlabel span { display: table-cell; }
    .barlabel .right { text-align: right; }
    .track { height: 12px; background: #e9eff5; border-radius: 999px; overflow: hidden; }
    .fill { height: 12px; border-radius: 999px; background: #247ba0; }
    .fill.orange { background: #d97706; }
    .fill.red { background: #c2413a; }
    .fill.green { background: #15936b; }
    .fill.gray { background: #718096; }
    .caption { font-size: 11px; color: #718096; line-height: 1.45; margin-top: 10px; }
    .region { border: 1px solid #dce6f0; border-radius: 14px; padding: 15px; background: #fff; }
    .region h4 { margin: 0 0 8px; font-size: 14px; color: #14395b; }
    .region .numbers { font-size: 20px; color: #b45309; font-weight: 900; margin-bottom: 7px; }
    .region p { margin: 0; font-size: 13.5px; line-height: 1.58; color: #40586e; }
    .conf { display: table; width: 100%; border: 1px solid #dce6f0; border-radius: 14px; overflow: hidden; }
    .conf > div { display: table-cell; padding: 16px; vertical-align: middle; }
    .conf-score { width: 110px; text-align: center; background: #e8f7ef; }
    .conf-score.conf-badge-orange { background: #fff3dd; }
    .conf-score.conf-badge-red { background: #fee8e8; }
    .conf-score .big { font-size: 34px; font-weight: 900; color: #087443; }
    .conf-score .big.conf-text-orange { color: #a95c00; }
    .conf-score .big.conf-text-red { color: #991b1b; }
    .conf-text { font-size: 13.5px; line-height: 1.55; color: #40586e; }
    .listbox { border-left: 5px solid #d97706; background: #fff8ec; border-radius: 12px; padding: 15px 17px; }
    .listbox ul { margin: 0; padding-left: 18px; }
    .listbox li { font-size: 13.5px; line-height: 1.55; color: #55452d; margin: 4px 0; }
    .scenario { border: 1px solid #dce6f0; border-radius: 14px; padding: 16px; margin: 10px 0; background: #fff; }
    .scenario.major { border-left: 6px solid #15936b; }
    .scenario.medium { border-left: 6px solid #d97706; }
    .scenario.minor { border-left: 6px solid #c2413a; }
    .scenario-head { display: table; width: 100%; }
    .scenario-head h4 { display: table-cell; margin: 0; font-size: 14px; color: #173b5d; }
    .pct { display: table-cell; width: 60px; text-align: right; font-size: 18px; font-weight: 900; }
    .scenario p { font-size: 13.5px; line-height: 1.5; color: #40586e; margin: 9px 0 0; }
    .takeaway { background: #edf9f3; border: 1px solid #c3ead4; border-left: 6px solid #15936b; border-radius: 14px; padding: 17px; }
    .takeaway b { font-size: 15px; color: #166534; display: block; margin-bottom: 8px; }
    .takeaway li { font-size: 13.5px; line-height: 1.55; color: #215b43; margin: 5px 0; }
    .detail { margin-top: 12px; border: 1px solid #dce6f0; border-radius: 13px; background: #fbfdff; padding: 14px; }
    .detail-title { font-size: 12px; text-transform: uppercase; letter-spacing: .8px; font-weight: 850; color: #60758a; margin-bottom: 7px; }
    .detail p { font-size: 13.5px; line-height: 1.57; color: #435970; margin: 0; }
    .social { border: 1px solid #cfdce8; border-radius: 16px; overflow: hidden; background: #fff; margin-bottom: 18px; }
    .social-head { background: #0a66c2; color: #fff; padding: 14px 17px; font-size: 14px; font-weight: 850; }
    .social-body { padding: 19px; font-size: 14.5px; line-height: 1.64; color: #24384b; white-space: pre-wrap; font-family: Arial, sans-serif; }
    .social-body strong { font-weight: 850; }
    .copy-note { font-size: 11.5px; color: #718096; background: #f5f8fb; padding: 9px 17px; border-top: 1px solid #e1e9f1; }
    .copy-btn-modern { background: #102a43; border: none; color: #ffffff; font-size: 11px; font-weight: bold; padding: 5px 12px; border-radius: 6px; cursor: pointer; text-transform: uppercase; letter-spacing: 0.5px; transition: background 0.2s; }
    .copy-btn-modern:hover { background: #1d4ed8; }
    .footer { padding: 20px 30px; background: #f2f6fa; color: #65798d; font-size: 11.5px; line-height: 1.5; text-align: center; }
    .source-note { font-size: 11.5px; color: #718096; line-height: 1.45; margin-top: 15px; }

    @media only screen and (max-width:700px) {
      body { padding: 0!important; background: #eef3f8!important; }
      .wrap { width: 100%!important; max-width: 100%!important; margin: 0!important; border-radius: 0!important; border-left: 0!important; border-right: 0!important; box-shadow: none!important; }
      .header { padding: 24px 16px!important; text-align: left!important; }
      .hero-title { font-size: 29px!important; line-height: 1.18!important; }
      .sub { font-size: 14px!important; }
      .pad { padding: 18px 12px!important; }
      .week { margin-top: 16px!important; border-radius: 14px!important; }
      .week-head { padding: 17px 14px 15px!important; }
      .week-head h2 { font-size: 21px!important; line-height: 1.25!important; }
      .week-head p { font-size: 14px!important; }
      .section { margin-top: 25px!important; }
      .section-title { font-size: 15px!important; }
      .grid2, .grid3, .grid4 { display: block!important; width: 100%!important; border-spacing: 0!important; }
      .cell { display: block!important; width: 100%!important; margin: 0 0 10px 0!important; }
      .metric { height: auto!important; min-height: 74px!important; padding: 13px 10px!important; }
      .metric .label { font-size: 12px!important; }
      .alert { padding: 17px 14px!important; border-radius: 13px!important; }
      .alert h3 { font-size: 19px!important; }
      .alert p { font-size: 14px!important; }
      .timeline-table, .timeline-table tbody, .timeline-table tr { display: block!important; width: 100%!important; }
      .timeline-table td { display: block!important; width: auto!important; margin-bottom: 9px!important; padding: 13px!important; }
      .timeline-table .keys { font-size: 13px!important; }
      .region p, .detail p, .scenario p, .conf-text, .listbox li, .takeaway li { font-size: 14px!important; }
      .social-body { font-size: 14px!important; }
      .caption, .copy-note, .footer, .source-note { font-size: 11px!important; }
    }
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
                <div class="meteo-image-card" style="margin-top: 15px; text-align: center;">
                    <span style="font-size: 12px; font-weight: bold; color: #60758a; display: block; margin-bottom: 5px;">📈 Modélisation Météo {idx+1}</span>
                    <img src="data:image/{ext};base64,{img_b64}" alt="Graphique Météo {idx+1}" style="max-width: 100%; border-radius: 12px; border: 1px solid #dce6f0;">
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
        scenarios = data.get("scenarios", {})
        social = data.get("social_pack", {})

        # Pré-calculer les valeurs social (évite les backslash dans f-string, interdit en Python <3.12)
        nl = "\n"
        social_linkedin = social.get('linkedin', '').replace('<br>', nl).replace('<br/>', nl)
        social_facebook = social.get('facebook', '').replace('<br>', nl).replace('<br/>', nl)
        social_twitter = social.get('twitter', '').replace('<br>', nl).replace('<br/>', nl)
        social_tiktok = social.get('tiktok', '').replace('<br>', nl).replace('<br/>', nl)
        social_instagram = social.get('instagram', '').replace('<br>', nl).replace('<br/>', nl)

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

        # Ajustement dynamique des classes de confiance
        conf_bg_class = ""
        conf_text_class = ""
        conf_color_hex = "#087443"
        if "3/" in conf_score_raw:
            conf_bg_class = "conf-badge-orange"
            conf_text_class = "conf-text-orange"
            conf_color_hex = "#a95c00"
        elif "1/" in conf_score_raw or "2/" in conf_score_raw:
            conf_bg_class = "conf-badge-red"
            conf_text_class = "conf-text-red"
            conf_color_hex = "#991b1b"

        # Traitement des incertitudes
        uncertainties_raw = data.get("key_uncertainties", "") + "\n" + data.get("monitoring_points", "")
        uncertainties_items = [u.strip("-* ").strip() for u in uncertainties_raw.split("\n") if u.strip()]
        uncertainties_li_html = "".join([f"<li>{u}</li>" for u in uncertainties_items if u])
        if not uncertainties_li_html:
            uncertainties_li_html = "<li>Aucun élément d'incertitude particulier signalé.</li>"

        # Couleur d'alerte pour le résumé express (basé sur la confiance ou la sévérité)
        alert_cls = "blue"
        if "canicule" in express.get('summary', '').lower() or "extreme" in express.get('summary', '').lower():
            alert_cls = "orange"
        if "4/" in conf_score_raw or "5/" in conf_score_raw:
            if "canicule" in express.get('summary', '').lower():
                alert_cls = "orange"
            else:
                alert_cls = "green"

        divider = '<div style="margin: 40px 0; border-top: 2px dashed #cfdce8;"></div>' if w_idx > 0 else ""
        weeks_html += f"""
        {divider}
        
        <div class="week">
            <div class="week-head">
                <h2>📅 {data.get('title_line1', 'SEMAINE')}</h2>
                <p>{data.get('title_line2', 'Synthèse des prévisions')}</p>
            </div>
            
            <div class="pad">
                <!-- 1. Lecture immédiate -->
                <div class="alert {alert_cls}">
                    <div class="eyebrow">Lecture immédiate · moins de 10 secondes</div>
                    <h3>{express.get('summary', '')}</h3>
                    <p>🎯 Confiance globale : {conf_score_raw} — {conf.get('desc', '')}</p>
                </div>

                <!-- 2. Les Chiffres Clés (KPI) -->
                <div class="section-title">Chiffres clés de la période</div>
                <div class="grid4">
                    <div class="cell"><div class="metric"><div class="big" style="font-size: 22px; padding-top: 4px;">{express.get('trend', '-')}</div><div class="label">Temps</div></div></div>
                    <div class="cell"><div class="metric"><div class="big" style="font-size: 22px; padding-top: 4px;">{express.get('temperatures', '-')}</div><div class="label">Températures</div></div></div>
                    <div class="cell"><div class="metric"><div class="big" style="font-size: 22px; padding-top: 4px;">{express.get('precipitations', '-')}</div><div class="label">Pluies</div></div></div>
                    <div class="cell"><div class="metric risk"><div class="big" style="font-size: 22px; padding-top: 4px; color:#b91c1c;">{express.get('main_risk', 'Aucun')}</div><div class="label">Risque principal</div></div></div>
                </div>

                <!-- 3. Chronologie visuelle -->
                <div class="section">
                    <div class="section-title">Chronologie visuelle</div>
                    <table class="timeline-table" role="presentation">
                        <tr>
                            <td><strong>Début de semaine</strong><div class="keys">{timeline.get('early', '-')}</div></td>
                            <td><strong>Milieu de semaine</strong><div class="keys">{timeline.get('mid', '-')}</div></td>
                            <td><strong>Fin de semaine</strong><div class="keys">{timeline.get('late', '-')}</div></td>
                            <td><strong>Week-end</strong><div class="keys">{timeline.get('weekend', '-')}</div></td>
                        </tr>
                    </table>
                </div>

                <!-- 4. Synthèse Régionale -->
                <div class="section">
                    <div class="section-title">Synthèse régionale · zones clés</div>
                    <div class="grid3">
                        <div class="cell"><div class="region"><h4>📍 Hauts-de-France & Nord</h4><p>{regional.get('hdf_north', '-')}</p></div></div>
                        <div class="cell"><div class="region"><h4>🌊 Façade Atlantique</h4><p>{regional.get('atlantic', '-')}</p></div></div>
                        <div class="cell"><div class="region"><h4>🏙️ Régions Centrales</h4><p>{regional.get('central', '-')}</p></div></div>
                    </div>
                    <div class="grid3" style="margin-top: 10px;">
                        <div class="cell"><div class="region"><h4>☀️ Moitié Sud</h4><p>{regional.get('south', '-')}</p></div></div>
                        <div class="cell"><div class="region"><h4>🏖️ Pourtour Méditerranéen</h4><p>{regional.get('mediterranean', '-')}</p></div></div>
                        <div class="cell"><div class="region"><h4>⛰️ Reliefs & Montagnes</h4><p>{regional.get('mountains', '-')}</p></div></div>
                    </div>
                </div>

                <!-- 5. Confiance & Incertitudes -->
                <div class="section">
                    <div class="section-title">Confiance et incertitudes</div>
                    <div class="conf">
                        <div class="conf-score {conf_bg_class}"><div class="big {conf_text_class}">{conf_score_raw}</div><div style="font-size:10px;font-weight:800;color:{conf_color_hex}">CONFIANCE</div></div>
                        <div class="conf-text"><b>Consensus des modèles :</b> {conf.get('desc', '')}</div>
                    </div>
                    <div class="listbox" style="margin-top:12px">
                        <ul>
                            {uncertainties_li_html}
                        </ul>
                    </div>
                </div>

                <!-- 6. Les 3 Scénarios -->
                <div class="section">
                    <div class="section-title">Trois scénarios atmosphériques</div>
                    <div class="scenario major">
                        <div class="scenario-head"><h4>🟢 {scenarios.get('majoritaire', {}).get('title', 'Scénario Majoritaire')}</h4><div class="pct">{scenarios.get('majoritaire', {}).get('prob', '65%')}</div></div>
                        <div class="track" style="margin: 6px 0;"><div class="fill green" style="width:{scenarios.get('majoritaire', {}).get('prob', '65%')}"></div></div>
                        <p>{scenarios.get('majoritaire', {}).get('desc', '')}</p>
                    </div>
                    <div class="scenario medium">
                        <div class="scenario-head"><h4>🟡 {scenarios.get('median', {}).get('title', 'Scénario Alternatif')}</h4><div class="pct">{scenarios.get('median', {}).get('prob', '25%')}</div></div>
                        <div class="track" style="margin: 6px 0;"><div class="fill orange" style="width:{scenarios.get('median', {}).get('prob', '25%')}"></div></div>
                        <p>{scenarios.get('median', {}).get('desc', '')}</p>
                    </div>
                    <div class="scenario minor">
                        <div class="scenario-head"><h4>🔴 {scenarios.get('minoritaire', {}).get('title', 'Scénario Minoritaire')}</h4><div class="pct">{scenarios.get('minoritaire', {}).get('prob', '10%')}</div></div>
                        <div class="track" style="margin: 6px 0;"><div class="fill red" style="width:{scenarios.get('minoritaire', {}).get('prob', '10%')}"></div></div>
                        <p>{scenarios.get('minoritaire', {}).get('desc', '')}</p>
                    </div>
                </div>

                <!-- 7. À retenir -->
                <div class="section">
                    <div class="takeaway">
                        <b>À retenir en 20 secondes</b>
                        <ul>
                            {takeaways_li_html}
                        </ul>
                    </div>
                </div>

                <!-- 8. Modélisations (images) -->
                {html_images_block}

                <!-- 9. Pack Réseaux Sociaux -->
                <div class="section">
                    <div class="section-title">📢 Pack réseaux sociaux (prêt à diffuser)</div>
                    <div class="social">
                        <div class="social-head" style="background:#0a66c2;">🔗 LinkedIn · Storytelling Expert Météo</div>
                        <div class="social-body">{social_linkedin}</div>
                        <div class="copy-note">
                            <button class="copy-btn-modern" onclick="navigator.clipboard.writeText(this.parentNode.parentNode.querySelector('.social-body').innerText); alert('Copié dans le presse-papiers !');">Copier le post LinkedIn</button>
                        </div>
                    </div>
                    <div class="social">
                        <div class="social-head" style="background:#1877f2;">👥 Facebook · Communautaire & Grand Public</div>
                        <div class="social-body">{social_facebook}</div>
                        <div class="copy-note">
                            <button class="copy-btn-modern" onclick="navigator.clipboard.writeText(this.parentNode.parentNode.querySelector('.social-body').innerText); alert('Copié dans le presse-papiers !');">Copier le post Facebook</button>
                        </div>
                    </div>
                    <div class="social">
                        <div class="social-head" style="background:#0f1419;">🐦 X (Twitter) · 280 Caractères max</div>
                        <div class="social-body">{social_twitter}</div>
                        <div class="copy-note">
                            <button class="copy-btn-modern" onclick="navigator.clipboard.writeText(this.parentNode.parentNode.querySelector('.social-body').innerText); alert('Copié dans le presse-papiers !');">Copier le post X</button>
                        </div>
                    </div>
                    <div class="social">
                        <div class="social-head" style="background:linear-gradient(45deg, #f09433, #e6683c, #dc2743, #cc2366, #bc1888);">📸 Instagram · Légende & CTA Bio</div>
                        <div class="social-body">{social_instagram}</div>
                        <div class="copy-note">
                            <button class="copy-btn-modern" onclick="navigator.clipboard.writeText(this.parentNode.parentNode.querySelector('.social-body').innerText); alert('Copié dans le presse-papiers !');">Copier le post Instagram</button>
                        </div>
                    </div>
                    <div class="social">
                        <div class="social-head" style="background:#fe2c55;">🎵 TikTok · Description vidéo</div>
                        <div class="social-body">{social_tiktok}</div>
                        <div class="copy-note">
                            <button class="copy-btn-modern" onclick="navigator.clipboard.writeText(this.parentNode.parentNode.querySelector('.social-body').innerText); alert('Copié la description TikTok !');">Copier la description TikTok</button>
                        </div>
                    </div>
                </div>

            </div>
        </div>
        """

    html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Tendances Moyen Terme</title>
    <style>{style}</style>
</head>
<body>
<div class="wrap">
    <div class="header">
        <div class="kicker">MONSIEUR MÉTÉO</div>
        <div class="hero-title">BULLETIN ÉVOLUTION & TENDANCES MÉTÉO</div>
        <div class="sub">Analyse consolidée du {datetime.datetime.now().strftime('%d/%m/%Y')} · France · Prévisions à 2 semaines</div>
    </div>
    <div class="pad">
        {weeks_html}
    </div>
</div>
</body>
</html>
"""

    output_dir = "bulletins"
    os.makedirs(output_dir, exist_ok=True)

    html_path = "bulletins/FR.html"
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"HTML généré avec succès : {html_path}")

    date_suffix = datetime.datetime.now().strftime('%Y_%m_%d')

    # --- GÉNÉRATION PARALLÈLE DES 13 BULLETINS RÉGIONAUX ---
    # Utiliser les commentaires BRUTS du forum (pas le résumé LLM) pour maximiser la fidélité régionale
    raw_parts = []
    for res in results:
        d = res.get("data", {})
        raw_text = res.get("raw_comments", "")
        week_title = d.get("title_line1", "Prévisions")
        raw_parts.append(f"=== {week_title} — DISCUSSIONS BRUTES DU FORUM ===\n{raw_text}")

    # all_raw_context = les vraies discussions des prévisionnistes, source directe
    all_raw_context = "\n\n".join(raw_parts)
    topic_title_for_regions = " & ".join([r["data"].get("title_line1", "Prévisions") for r in results])
    # Bug fix: passer le contexte des DEUX semaines aux régions, pas seulement la semaine en cours
    # Aussi injecter la date ISO et la saison pour éviter les hallucinations (neige en été, etc.)
    saison_actuelle = ["hiver", "printemps", "été", "automne"][(now.month % 12 // 3)]
    date_context_for_regions = (
        f"Date actuelle de génération : {today_str} ({now.strftime('%Y-%m-%d')}) — Saison : {saison_actuelle.upper()} EN FRANCE.\n"
        f"ATTENTION ABSOLUE : Nous sommes en {saison_actuelle.upper()}. Toute mention de neige en plaine, de gel sévère ou de conditions hivernales est STRICTEMENT INTERDITE sauf en altitude (>1500m) si les sources le mentionnent explicitement.\n"
        f"Semaine en cours : {semaine_cours_str} (jours restants à prévoir : {jours_restants_cours_str}).\n"
        f"Semaine suivante : {semaine_suivante_str} (semaine complète à prévoir)."
    )

    def gen_region(r_key, r_info):
        r_name, r_abbr = r_info
        # Injection des commentaires bruts du forum directement au LLM régional
        return process_region_query(r_key, r_name, all_raw_context, topic_title_for_regions, date_context_for_regions, 0)

    print("\n--- Génération parallèle des 13 bulletins régionaux ---")
    regions_data = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=13) as executor:
        futures = {executor.submit(gen_region, k, v): k for k, v in REGIONS_CONFIG.items()}
        for future in concurrent.futures.as_completed(futures):
            k, r_data = future.result()
            regions_data[k] = r_data

    # Générer le HTML régional dans le dossier bulletins/ sous le nom abrégé de la région
    for r_key, (r_name, r_abbr) in REGIONS_CONFIG.items():
        r_data = regions_data.get(r_key)
        filename_region = f"bulletins/{r_abbr}"

        if not r_data:
            print(f"[{r_name}] Bulletin manquant — fichier minimal généré.")
            r_data = {
                "title_line1": f"Semaine — {r_name}",
                "title_line2": "Information non précisée dans les sources.",
                "region_name": r_name,
                "express": {"summary": "Information non précisée.", "trend": "-", "temperatures": "-", "precipitations": "-", "main_risk": "-"},
                "confidence": {"score": "3/5", "desc": "Données insuffisantes pour cette région."},
                "timeline": {"early": "-", "mid": "-", "late": "-", "weekend": "-"},
                "regional": {"hdf_north": "-", "atlantic": "-", "central": "-", "south": "-", "mediterranean": "-", "mountains": "-"},
                "scenarios": {
                    "majoritaire": {"prob": "65%", "title": "Scénario Majoritaire", "desc": "Information non précisée dans les sources."},
                    "median": {"prob": "25%", "title": "Scénario Alternatif", "desc": "Information non précisée dans les sources."},
                    "minoritaire": {"prob": "10%", "title": "Scénario Minoritaire", "desc": "Information non précisée dans les sources."},
                },
                "key_uncertainties": "- Information non précisée.",
                "monitoring_points": "- Information non précisée.",
                "key_takeaways": "- Information non précisée dans les sources.",
                "social_pack": {"linkedin": "", "facebook": "", "twitter": "", "tiktok": "", "instagram": ""},
                "linkedin_hashtags": f"#Meteo #{r_name.replace(' ', '').replace('-', '')} #France #MonsieurMeteo",
            }

        # Même CSS que le national
        express_r = r_data.get("express", {})
        timeline_r = r_data.get("timeline", {})
        regional_r = r_data.get("regional", {})
        conf_r = r_data.get("confidence", {})
        scenarios_r = r_data.get("scenarios", {})
        social_r = r_data.get("social_pack", {})

        conf_score_r = conf_r.get('score', '4/5')
        conf_class_r = "conf-badge-green"
        if "3/" in conf_score_r:
            conf_class_r = "conf-badge-orange"
        elif "1/" in conf_score_r or "2/" in conf_score_r:
            conf_class_r = "conf-badge-red"

        takeaways_r_raw = r_data.get("key_takeaways", "")
        takeaways_r_items = [t.strip("-* ").strip() for t in takeaways_r_raw.split("\n") if t.strip()]
        takeaways_r_li = "".join([f"<li>{t}</li>" for t in takeaways_r_items if t])
        if not takeaways_r_li:
            takeaways_r_li = "<li>Information non précisée dans les sources pour cette région.</li>"

        # Ajustement des classes régionales
        conf_bg_class_r = ""
        conf_text_class_r = ""
        conf_color_hex_r = "#087443"
        if "3/" in conf_score_r:
            conf_bg_class_r = "conf-badge-orange"
            conf_text_class_r = "conf-text-orange"
            conf_color_hex_r = "#a95c00"
        elif "1/" in conf_score_r or "2/" in conf_score_r:
            conf_bg_class_r = "conf-badge-red"
            conf_text_class_r = "conf-text-red"
            conf_color_hex_r = "#991b1b"

        uncertainties_r_raw = r_data.get("key_uncertainties", "") + "\n" + r_data.get("monitoring_points", "")
        uncertainties_r_items = [u.strip("-* ").strip() for u in uncertainties_r_raw.split("\n") if u.strip()]
        uncertainties_r_li_html = "".join([f"<li>{u}</li>" for u in uncertainties_r_items if u])
        if not uncertainties_r_li_html:
            uncertainties_r_li_html = "<li>Aucun élément d'incertitude particulier signalé.</li>"

        alert_cls_r = "blue"
        if "canicule" in express_r.get('summary', '').lower() or "extreme" in express_r.get('summary', '').lower():
            alert_cls_r = "orange"
        if "4/" in conf_score_r or "5/" in conf_score_r:
            if "canicule" in express_r.get('summary', '').lower():
                alert_cls_r = "orange"
            else:
                alert_cls_r = "green"

        # Pré-calculer les réseaux sociaux régionaux (pour éviter backslash dans f-string)
        nl = "\n"
        social_r_linkedin = social_r.get('linkedin', '').replace('<br>', nl).replace('<br/>', nl)
        social_r_facebook = social_r.get('facebook', '').replace('<br>', nl).replace('<br/>', nl)
        social_r_twitter = social_r.get('twitter', '').replace('<br>', nl).replace('<br/>', nl)
        social_r_tiktok = social_r.get('tiktok', '').replace('<br>', nl).replace('<br/>', nl)
        social_r_instagram = social_r.get('instagram', '').replace('<br>', nl).replace('<br/>', nl)

        region_html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bulletin Météo — {r_name}</title>
    <style>{style}</style>
</head>
<body>
<div class="wrap">
    <div class="header">
        <div class="kicker">MONSIEUR MÉTÉO — BULLETIN RÉGIONAL</div>
        <div class="hero-title">📍 {r_name}</div>
        <div class="sub">Analyse consolidée du {datetime.datetime.now().strftime('%d/%m/%Y')} · Prévisions à 2 semaines</div>
    </div>
    
    <div class="pad">
        <div class="week">
            <div class="week-head">
                <h2>📅 {r_data.get('title_line1', r_name)}</h2>
                <p>{r_data.get('title_line2', '')}</p>
            </div>
            
            <div class="pad">
                <!-- 1. Lecture immédiate -->
                <div class="alert {alert_cls_r}">
                    <div class="eyebrow">Lecture immédiate · moins de 10 secondes</div>
                    <h3>{express_r.get('summary', '')}</h3>
                    <p>🎯 Confiance globale : {conf_score_r} — {conf_r.get('desc', '')}</p>
                </div>
 
                <!-- 2. KPIs -->
                <div class="section-title">Chiffres clés de la période</div>
                <div class="grid4">
                    <div class="cell"><div class="metric"><div class="big" style="font-size: 22px; padding-top: 4px;">{express_r.get('trend', '-')}</div><div class="label">Temps</div></div></div>
                    <div class="cell"><div class="metric"><div class="big" style="font-size: 22px; padding-top: 4px;">{express_r.get('temperatures', '-')}</div><div class="label">Températures</div></div></div>
                    <div class="cell"><div class="metric"><div class="big" style="font-size: 22px; padding-top: 4px;">{express_r.get('precipitations', '-')}</div><div class="label">Pluies</div></div></div>
                    <div class="cell"><div class="metric risk"><div class="big" style="font-size: 22px; padding-top: 4px; color:#b91c1c;">{express_r.get('main_risk', 'Aucun')}</div><div class="label">Risque principal</div></div></div>
                </div>

                <div class="section">
                    <div class="section-title">Chronologie — 2 semaines</div>
                    <table class="timeline-table" role="presentation">
                        <tr>
                            <td><strong>Sem. en cours · Début</strong><div class="keys">{timeline_r.get('early', '-')}</div></td>
                            <td><strong>Sem. en cours · Fin</strong><div class="keys">{timeline_r.get('mid', '-')}</div></td>
                            <td><strong>Sem. suivante · Début</strong><div class="keys">{timeline_r.get('late', '-')}</div></td>
                            <td><strong>Sem. suivante · Fin</strong><div class="keys">{timeline_r.get('weekend', '-')}</div></td>
                        </tr>
                    </table>
                </div>

                <!-- 4. Découpage par secteurs -->
                <div class="section">
                    <div class="section-title">🗺️ Secteurs de {r_name.upper()}</div>
                    <div class="grid3">
                        <div class="cell"><div class="region"><h4>🔹 Secteur Nord / NW</h4><p>{regional_r.get('hdf_north', '-')}</p></div></div>
                        <div class="cell"><div class="region"><h4>🌊 Façade Ouest</h4><p>{regional_r.get('atlantic', '-')}</p></div></div>
                        <div class="cell"><div class="region"><h4>🏙️ Intérieur / Centre</h4><p>{regional_r.get('central', '-')}</p></div></div>
                    </div>
                    <div class="grid3" style="margin-top: 10px;">
                        <div class="cell"><div class="region"><h4>☀️ Secteur Sud</h4><p>{regional_r.get('south', '-')}</p></div></div>
                        <div class="cell"><div class="region"><h4>🏖️ Côtes / Méditerranée</h4><p>{regional_r.get('mediterranean', 'Non applicable')}</p></div></div>
                        <div class="cell"><div class="region"><h4>⛰️ Reliefs / Montagnes</h4><p>{regional_r.get('mountains', 'Non applicable')}</p></div></div>
                    </div>
                </div>

                <!-- 5. Confiance & Incertitudes -->
                <div class="section">
                    <div class="section-title">Confiance et incertitudes</div>
                    <div class="conf">
                        <div class="conf-score {conf_bg_class_r}"><div class="big {conf_text_class_r}">{conf_score_r}</div><div style="font-size:10px;font-weight:800;color:{conf_color_hex_r}">CONFIANCE</div></div>
                        <div class="conf-text"><b>Consensus des modèles :</b> {conf_r.get('desc', '')}</div>
                    </div>
                    <div class="listbox" style="margin-top:12px">
                        <ul>
                            {uncertainties_r_li_html}
                        </ul>
                    </div>
                </div>

                <!-- 6. Les 3 Scénarios -->
                <div class="section">
                    <div class="section-title">Trois scénarios atmosphériques</div>
                    <div class="scenario major">
                        <div class="scenario-head"><h4>🟢 {scenarios_r.get('majoritaire', {}).get('title', 'Scénario Majoritaire')}</h4><div class="pct">{scenarios_r.get('majoritaire', {}).get('prob', '65%')}</div></div>
                        <div class="track" style="margin: 6px 0;"><div class="fill green" style="width:{scenarios_r.get('majoritaire', {}).get('prob', '65%')}"></div></div>
                        <p>{scenarios_r.get('majoritaire', {}).get('desc', '')}</p>
                    </div>
                    <div class="scenario medium">
                        <div class="scenario-head"><h4>🟡 {scenarios_r.get('median', {}).get('title', 'Scénario Alternatif')}</h4><div class="pct">{scenarios_r.get('median', {}).get('prob', '25%')}</div></div>
                        <div class="track" style="margin: 6px 0;"><div class="fill orange" style="width:{scenarios_r.get('median', {}).get('prob', '25%')}"></div></div>
                        <p>{scenarios_r.get('median', {}).get('desc', '')}</p>
                    </div>
                    <div class="scenario minor">
                        <div class="scenario-head"><h4>🔴 {scenarios_r.get('minoritaire', {}).get('title', 'Scénario Minoritaire')}</h4><div class="pct">{scenarios_r.get('minoritaire', {}).get('prob', '10%')}</div></div>
                        <div class="track" style="margin: 6px 0;"><div class="fill red" style="width:{scenarios_r.get('minoritaire', {}).get('prob', '10%')}"></div></div>
                        <p>{scenarios_r.get('minoritaire', {}).get('desc', '')}</p>
                    </div>
                </div>

                <!-- 7. À retenir -->
                <div class="section">
                    <div class="takeaway">
                        <b>À retenir en 20 secondes</b>
                        <ul>
                            {takeaways_r_li}
                        </ul>
                    </div>
                </div>

                <!-- 9. Pack Réseaux Sociaux -->
                <div class="section">
                    <div class="section-title">📢 Pack réseaux sociaux — {r_name}</div>
                    <div class="social">
                        <div class="social-head" style="background:#0a66c2;">🔗 LinkedIn · Storytelling Expert Météo</div>
                        <div class="social-body">{social_r_linkedin}</div>
                        <div class="copy-note">
                            <button class="copy-btn-modern" onclick="navigator.clipboard.writeText(this.parentNode.parentNode.querySelector('.social-body').innerText); alert('Copié dans le presse-papiers !');">Copier le post LinkedIn</button>
                        </div>
                    </div>
                    <div class="social">
                        <div class="social-head" style="background:#1877f2;">👥 Facebook · Communautaire & Grand Public</div>
                        <div class="social-body">{social_r_facebook}</div>
                        <div class="copy-note">
                            <button class="copy-btn-modern" onclick="navigator.clipboard.writeText(this.parentNode.parentNode.querySelector('.social-body').innerText); alert('Copié dans le presse-papiers !');">Copier le post Facebook</button>
                        </div>
                    </div>
                    <div class="social">
                        <div class="social-head" style="background:#0f1419;">🐦 X (Twitter) · 280 Caractères max</div>
                        <div class="social-body">{social_r_twitter}</div>
                        <div class="copy-note">
                            <button class="copy-btn-modern" onclick="navigator.clipboard.writeText(this.parentNode.parentNode.querySelector('.social-body').innerText); alert('Copié dans le presse-papiers !');">Copier le post X</button>
                        </div>
                    </div>
                    <div class="social">
                        <div class="social-head" style="background:linear-gradient(45deg, #f09433, #e6683c, #dc2743, #cc2366, #bc1888);">📸 Instagram · Légende & CTA Bio</div>
                        <div class="social-body">{social_r_instagram}</div>
                        <div class="copy-note">
                            <button class="copy-btn-modern" onclick="navigator.clipboard.writeText(this.parentNode.parentNode.querySelector('.social-body').innerText); alert('Copié dans le presse-papiers !');">Copier le post Instagram</button>
                        </div>
                    </div>
                    <div class="social">
                        <div class="social-head" style="background:#fe2c55;">🎵 TikTok · Description vidéo</div>
                        <div class="social-body">{social_r_tiktok}</div>
                        <div class="copy-note">
                            <button class="copy-btn-modern" onclick="navigator.clipboard.writeText(this.parentNode.parentNode.querySelector('.social-body').innerText); alert('Copié la description TikTok !');">Copier la description TikTok</button>
                        </div>
                    </div>
                </div>

            </div>
        </div>
    </div>
</div>
</body>
</html>"""

        with open(filename_region, "w", encoding="utf-8") as f_r:
            f_r.write(region_html)
        print(f"Bulletin régional généré : {filename_region}")

    # --- ENVOI EMAIL SMTP (National inline + 14 pièces jointes abrégées) ---
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
    subject_week_names = " & ".join([r["data"].get("title_line1", "Semaine").split("-")[0].strip() for r in results])
    subject = f"Tendances de la semaine - {subject_week_names}"
    subject = unicodedata.normalize('NFKD', subject).encode('ASCII', 'ignore').decode('ASCII')

    msg = MIMEMultipart('mixed')
    msg['From'] = f"Meteo Climat Pro <{sender}>"
    msg['To'] = ", ".join(recipients)
    msg['Subject'] = subject
    msg['Date'] = formatdate(localtime=True)
    msg['Reply-To'] = "gregory.langlet@sfr.fr"

    msg_alt = MIMEMultipart('alternative')
    msg.attach(msg_alt)

    text_body = "Bonjour,\n\nVeuillez trouver le bulletin national France en ligne ci-dessous, et les 13 bulletins régionaux en pièces jointes (FR.html, HDF.html, IDF.html, PACA.html...).\n\nCordialement,\nMonsieur Météo"
    msg_alt.attach(MIMEText(text_body, 'plain', 'utf-8'))
    # Clean the HTML specifically for the email body (remove JavaScript onclick buttons)
    msg_alt.attach(MIMEText(clean_html_for_email(html), 'html', 'utf-8'))

    # Bulletin national FR.html en pièce jointe (contient tous les boutons interactifs intacts)
    part_fr = MIMEBase('text', 'html', charset='utf-8')
    part_fr.set_payload(html.encode('utf-8'))
    encoders.encode_base64(part_fr)
    part_fr.add_header('Content-Disposition', 'attachment', filename="FR.html")
    msg.attach(part_fr)

    # 13 bulletins régionaux en pièces jointes sous leurs noms d'abréviations directes
    for r_key, (r_name, r_abbr) in REGIONS_CONFIG.items():
        fn = f"bulletins/{r_abbr}"
        try:
            with open(fn, "r", encoding="utf-8") as f_r:
                r_html_content = f_r.read()
            part_r = MIMEBase('text', 'html', charset='utf-8')
            part_r.set_payload(r_html_content.encode('utf-8'))
            encoders.encode_base64(part_r)
            part_r.add_header('Content-Disposition', 'attachment', filename=r_abbr)
            msg.attach(part_r)
        except Exception as e:
            print(f"Erreur attachement {r_abbr} : {e}")

    print(f"[SMTP] Envoi via Gmail à {', '.join(recipients)}...")
    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=45) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(gmail_email, gmail_password)
            server.sendmail(gmail_email, recipients, msg.as_bytes())
        print("[SMTP] E-mail envoyé avec succès !")
    except Exception as e:
        print(f"[SMTP] Erreur d'envoi : {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
