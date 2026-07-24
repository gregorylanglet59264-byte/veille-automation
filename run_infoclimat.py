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


def process_topic(target_topic, topic_idx, date_context_str):
    # Extraire et décoder un titre propre du sujet à partir de l'URL
    import urllib.parse
    decoded_topic = urllib.parse.unquote(target_topic)
    topic_title_slug = decoded_topic.rstrip('/').split('/')[-1]
    topic_title_slug = re.sub(r'^\d+-', '', topic_title_slug)  # Enlever l'ID du sujet au début
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
Effectue un contrôle qualité automatique et silencieux :
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
        "images": downloaded_images
    }


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

    # Semaine future (clean_topics[0]) en premier, Semaine en cours (clean_topics[1]) en second
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
        
    # Style CSS Premium & Responsive
    style = """
    body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #0f172a; background-color: #f1f5f9; margin: 0; padding: 25px 15px; }
    .container { max-width: 880px; background-color: #ffffff; margin: 0 auto; border-radius: 20px; overflow: hidden; box-shadow: 0 20px 35px -10px rgba(0, 0, 0, 0.09); border: 1px solid #cbd5e1; }
    .header { background: linear-gradient(135deg, #0284c7 0%, #1e3a8a 60%, #0f172a 100%); color: #ffffff; padding: 40px 30px; text-align: center; }
    .header h1 { margin: 0; font-size: 28px; font-weight: 800; letter-spacing: -0.5px; }
    .header p { margin: 10px 0 0 0; font-size: 14px; opacity: 0.92; }
    .content { padding: 35px 30px; }
    .week-divider { border-top: 3px dashed #94a3b8; margin: 55px 0; }
    
    .week-title-box { margin-bottom: 25px; padding-left: 16px; border-left: 6px solid #0284c7; }
    .week-title-line1 { font-size: 22px; font-weight: 800; color: #1e3a8a; text-transform: uppercase; letter-spacing: 0.5px; margin: 0; }
    .week-title-line2 { font-size: 15px; font-weight: 600; color: #0284c7; margin-top: 4px; }

    .section-title { font-size: 13px; font-weight: 800; text-transform: uppercase; letter-spacing: 1.2px; color: #475569; margin-top: 35px; margin-bottom: 16px; border-bottom: 2px solid #e2e8f0; padding-bottom: 6px; }
    
    .hero-express { background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 100%); color: #ffffff; border-radius: 18px; padding: 26px; margin-bottom: 30px; box-shadow: 0 12px 25px -5px rgba(30, 58, 138, 0.3); }
    .hero-top-bar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
    .hero-label { font-size: 12px; font-weight: 800; text-transform: uppercase; letter-spacing: 1.5px; color: #38bdf8; }
    
    .conf-badge-green { background: #10b981; color: #ffffff; font-size: 13px; font-weight: 800; padding: 5px 14px; border-radius: 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.2); }
    .conf-badge-orange { background: #f59e0b; color: #ffffff; font-size: 13px; font-weight: 800; padding: 5px 14px; border-radius: 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.2); }
    .conf-badge-red { background: #ef4444; color: #ffffff; font-size: 13px; font-weight: 800; padding: 5px 14px; border-radius: 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.2); }

    .hero-summary { font-size: 16px; font-weight: 700; line-height: 1.5; margin-bottom: 14px; color: #ffffff; }
    .hero-conf-explanation { font-size: 12.5px; font-style: italic; color: #93c5fd; margin-bottom: 18px; background: rgba(255,255,255,0.08); padding: 8px 12px; border-radius: 8px; border-left: 3px solid #38bdf8; }

    .hero-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; }
    .hero-card { background: rgba(255, 255, 255, 0.1); backdrop-filter: blur(10px); border-radius: 10px; padding: 10px 8px; border: 1px solid rgba(255, 255, 255, 0.15); text-align: center; }
    .hero-card label { display: block; font-size: 9.5px; font-weight: 800; text-transform: uppercase; letter-spacing: 0.5px; color: #93c5fd; margin-bottom: 4px; }
    .hero-card span { font-size: 13px; font-weight: 800; color: #ffffff; text-transform: capitalize; }
    
    .timeline-container { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-bottom: 30px; }
    .timeline-step { background: #f8fafc; border-radius: 12px; padding: 14px 12px; border: 1px solid #e2e8f0; border-top: 4px solid #0284c7; }
    .timeline-step strong { display: block; font-size: 11px; text-transform: uppercase; letter-spacing: 0.6px; color: #0284c7; margin-bottom: 6px; }
    .timeline-step p { margin: 0; font-size: 12.5px; color: #334155; line-height: 1.45; }

    .regional-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 30px; }
    .regional-card { background: #ffffff; border-radius: 12px; padding: 14px 16px; border: 1px solid #e2e8f0; box-shadow: 0 2px 5px rgba(0,0,0,0.02); }
    .regional-card strong { color: #0f172a; font-size: 12.5px; display: block; margin-bottom: 5px; }
    .regional-card p { margin: 0; font-size: 12.5px; color: #475569; line-height: 1.5; }
    
    .confidence-panel { background: #f8fafc; border-radius: 14px; padding: 18px; border: 1px solid #e2e8f0; margin-bottom: 30px; }
    .confidence-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
    .confidence-head strong { font-size: 13.5px; color: #0f172a; }
    .uncertainties-box { background: #ffffff; border-radius: 10px; padding: 12px 14px; border-left: 4px solid #f59e0b; border: 1px solid #fef3c7; border-left-width: 4px; font-size: 12.5px; color: #334155; line-height: 1.5; }
    
    .scenario-card { border-radius: 14px; padding: 18px; margin-bottom: 16px; border: 1px solid #e2e8f0; background: #ffffff; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.03); }
    .sc-major { border-left: 6px solid #10b981; }
    .sc-median { border-left: 6px solid #f59e0b; }
    .sc-minor { border-left: 6px solid #ef4444; }
    .sc-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
    .sc-header h3 { margin: 0; font-size: 14.5px; font-weight: 800; color: #0f172a; }
    .sc-prob { font-size: 11.5px; padding: 3px 10px; border-radius: 20px; color: #ffffff; font-weight: 800; }
    .bg-major { background-color: #10b981; }
    .bg-median { background-color: #f59e0b; }
    .bg-minor { background-color: #ef4444; }
    .sc-text { margin: 0; font-size: 12.5px; line-height: 1.55; color: #334155; text-align: justify; }

    .takeaways-panel { background: #f0fdf4; border: 1px solid #bbf7d0; border-left: 6px solid #10b981; border-radius: 14px; padding: 18px; margin-bottom: 30px; }
    .takeaways-panel h3 { margin: 0 0 10px 0; font-size: 13.5px; font-weight: 800; color: #166534; text-transform: uppercase; letter-spacing: 0.5px; }
    .takeaways-panel ul { margin: 0; padding-left: 18px; color: #15803d; font-size: 12.5px; line-height: 1.6; }
    .takeaways-panel li { margin-bottom: 4px; }
    
    /* Graphiques Météo */
    .meteo-images-container { display: flex; flex-wrap: wrap; gap: 15px; margin-bottom: 30px; justify-content: space-between; }
    .meteo-image-card { flex: 1 1 45%; min-width: 280px; background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 14px; padding: 14px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.03); text-align: center; }
    .meteo-image-card span { font-weight: 800; font-size: 11px; color: #475569; display: block; margin-bottom: 10px; text-transform: uppercase; letter-spacing: 0.5px; }
    .meteo-image-card img { width: 100%; height: auto; border-radius: 8px; border: 1px solid #f1f5f9; }

    /* Pack Réseaux Sociaux */
    .social-pack-container { display: flex; flex-direction: column; gap: 16px; margin-bottom: 30px; }
    .social-platform-card { background: #ffffff; border: 1px solid #e2e8f0; border-radius: 14px; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.03); }
    .social-platform-header { display: flex; align-items: center; justify-content: space-between; padding: 12px 18px; font-weight: 800; font-size: 13px; color: #ffffff; text-transform: uppercase; letter-spacing: 0.5px; }
    .sp-linkedin { background: #0077b5; }
    .sp-facebook { background: #1877f2; }
    .sp-twitter { background: #0f1419; }
    .sp-tiktok { background: #fe2c55; }
    .sp-instagram { background: linear-gradient(45deg, #f09433 0%, #e6683c 25%, #dc2743 50%, #cc2366 75%, #bc1888 100%); }
    .social-platform-body { padding: 18px; font-size: 12.5px; white-space: pre-wrap; color: #334155; line-height: 1.6; font-family: 'Segoe UI', Tahoma, Geneva, sans-serif; }
    .copy-btn { background: rgba(255, 255, 255, 0.25); border: none; color: #ffffff; font-size: 10px; font-weight: bold; padding: 4px 10px; border-radius: 6px; cursor: pointer; text-transform: uppercase; letter-spacing: 0.5px; transition: background 0.2s; }
    .copy-btn:hover { background: rgba(255, 255, 255, 0.4); }
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
        scenarios = data.get("scenarios", {})
        social = data.get("social_pack", {}) or {}

        # Nettoyage des posts sociaux pour éviter les backslashes dans le f-string (SyntaxError en Python <3.12)
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

        divider = '<div class="week-divider"></div>' if w_idx > 0 else ""
        weeks_html += f"""
        {divider}
        
        <!-- TITRE DE SEMAINE EN 2 LIGNES -->
        <div class="week-title-box">
            <h2 class="week-title-line1">📅 {data.get('title_line1', 'SEMAINE')}</h2>
            <div class="week-title-line2">{data.get('title_line2', 'Synthèse des prévisions')}</div>
        </div>
        
        <!-- 1. HERO RESUME EXPRESS (<10 SECONDES) -->
        <div class="hero-express">
            <div class="hero-top-bar">
                <span class="hero-label">⚡ LECTURE < 10s : RÉSUMÉ EXPRESS</span>
                <span class="{conf_class}">Confiance : {conf_score_raw}</span>
            </div>
            <div class="hero-summary">{express.get('summary', '')}</div>
            <div class="hero-conf-explanation">🎯 <strong>Raison de la note ({conf_score_raw}) :</strong> {conf.get('desc', '')}</div>
            <div class="hero-grid">
                <div class="hero-card"><label>🌤️ Temps</label><span>{express.get('trend', '-')}</span></div>
                <div class="hero-card"><label>🌡️ Températures</label><span>{express.get('temperatures', '-')}</span></div>
                <div class="hero-card"><label>🌧️ Pluies</label><span>{express.get('precipitations', '-')}</span></div>
                <div class="hero-card"><label>⚠️ Risque</label><span>{express.get('main_risk', 'Aucun')}</span></div>
            </div>
        </div>

        <!-- 2. CHRONOLOGIE DE LA SEMAINE -->
        <div class="section-title">🗓️ CHRONOLOGIE DE LA SEMAINE</div>
        <div class="timeline-container">
            <div class="timeline-step"><strong>Début de semaine</strong><p>{timeline.get('early', '-')}</p></div>
            <div class="timeline-step"><strong>Milieu de semaine</strong><p>{timeline.get('mid', '-')}</p></div>
            <div class="timeline-step"><strong>Fin de semaine</strong><p>{timeline.get('late', '-')}</p></div>
            <div class="timeline-step"><strong>Week-end</strong><p>{timeline.get('weekend', '-')}</p></div>
        </div>

        <!-- 3. SYNTHESE PAR REGIONS HARMONISEES -->
        <div class="section-title">🗺️ SYNTHÈSE PAR GRANDES RÉGIONS</div>
        <div class="regional-grid">
            <div class="regional-card"><strong>📍 Hauts-de-France & Nord</strong><p>{regional.get('hdf_north', '-')}</p></div>
            <div class="regional-card"><strong>🌊 Façade Atlantique</strong><p>{regional.get('atlantic', '-')}</p></div>
            <div class="regional-card"><strong>🏙️ Régions Centrales</strong><p>{regional.get('central', '-')}</p></div>
            <div class="regional-card"><strong>☀️ Moitié Sud</strong><p>{regional.get('south', '-')}</p></div>
            <div class="regional-card"><strong>🏖️ Pourtour Méditerranéen</strong><p>{regional.get('mediterranean', '-')}</p></div>
            <div class="regional-card"><strong>⛰️ Reliefs & Montagnes</strong><p>{regional.get('mountains', 'Pas de particularité remarquable')}</p></div>
        </div>

        <!-- 4. CONFIANCE & INCERTITUDES -->
        <div class="section-title">🎯 CONFIANCE ET INCERTITUDES RESTANTES</div>
        <div class="confidence-panel">
            <div class="confidence-head">
                <strong>Fiabilité du Consensus des Modèles</strong>
                <span class="{conf_class}">Note : {conf_score_raw}</span>
            </div>
            <div class="uncertainties-box">
                <strong style="display: block; margin-bottom: 4px; color: #d97706; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px;">❓ Incertitudes Majeures & Points à Surveiller :</strong>
                {data.get('key_uncertainties', '')}\n{data.get('monitoring_points', '')}
            </div>
        </div>

        <!-- 5. GRAPHIQUES METEO -->
        {html_images_block}

        <!-- 6. LES 3 SCENARIOS CALIBRES -->
        <div class="section-title">🔮 LES 3 SCÉNARIOS ATMOSPHÉRIQUES DÉTAILLÉS</div>
        
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

        <!-- 7. A RETENIR (KEY TAKEAWAYS) -->
        <div class="takeaways-panel">
            <h3>📌 À Retenir — L'Essentiel en 4 Puces</h3>
            <ul>
                {takeaways_li_html}
            </ul>
        </div>

        <!-- 8. PACK RÉSEAUX SOCIAUX PRÊT À PUBLIER -->
        <div class="section-title">📢 PACK RÉSEAUX SOCIAUX (PRÊT À DIFFUSER)</div>
        <div class="social-pack-container">
            <!-- LinkedIn -->
            <div class="social-platform-card">
                <div class="social-platform-header sp-linkedin">
                    <span>🔗 LinkedIn (Storytelling Expert Météo)</span>
                    <button class="copy-btn" onclick="navigator.clipboard.writeText(this.parentNode.parentNode.querySelector('.social-platform-body').innerText); alert('Copié dans le presse-papiers !');">Copier</button>
                </div>
                <div class="social-platform-body">{linkedin_clean}</div>
            </div>

            <!-- Facebook -->
            <div class="social-platform-card">
                <div class="social-platform-header sp-facebook">
                    <span>👥 Facebook (Communautaire & Grand Public)</span>
                    <button class="copy-btn" onclick="navigator.clipboard.writeText(this.parentNode.parentNode.querySelector('.social-platform-body').innerText); alert('Copié dans le presse-papiers !');">Copier</button>
                </div>
                <div class="social-platform-body">{facebook_clean}</div>
            </div>

            <!-- X (Twitter) -->
            <div class="social-platform-card">
                <div class="social-platform-header sp-twitter">
                    <span>🐦 X (Twitter - 280 Caractères max)</span>
                    <button class="copy-btn" onclick="navigator.clipboard.writeText(this.parentNode.parentNode.querySelector('.social-platform-body').innerText); alert('Copié dans le presse-papiers !');">Copier</button>
                </div>
                <div class="social-platform-body">{twitter_clean}</div>
            </div>

            <!-- TikTok -->
            <div class="social-platform-card">
                <div class="social-platform-header sp-tiktok">
                    <span>🎵 TikTok (Description vidéo)</span>
                    <button class="copy-btn" onclick="navigator.clipboard.writeText(this.parentNode.parentNode.querySelector('.social-platform-body').innerText); alert('Copié dans le presse-papiers !');">Copier</button>
                </div>
                <div class="social-platform-body">{tiktok_clean}</div>
            </div>

            <!-- Instagram -->
            <div class="social-platform-card">
                <div class="social-platform-header sp-instagram">
                    <span>📸 Instagram (Légende & CTA Bio)</span>
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
