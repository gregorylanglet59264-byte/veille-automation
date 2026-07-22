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

INDEX_URL = "https://forums.infoclimat.fr/f/forum/20-evolution-%C3%A0-plus-long-terme/"
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'

def fetch_url(url):
    req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
    with urllib.request.urlopen(req, timeout=15) as response:
        return response.read().decode('utf-8', errors='ignore')

def call_llm(system_prompt, user_prompt):
    openrouter_key = os.environ.get("OPENROUTER_API_KEY", "").replace('\ufeff', '').strip()
    if not openrouter_key:
        print("[LLM] ERREUR : OPENROUTER_API_KEY non configurée.")
        return None
    print("[LLM] Appel DeepSeek V4 Flash via OpenRouter...")
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
        print(f"[LLM] Erreur HTTP OpenRouter ({http_err.code})")
    except Exception as e:
        print(f"[LLM] Erreur OpenRouter: {e}")
    return None


def process_topic(target_topic, topic_idx):
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
            with urllib.request.urlopen(req, timeout=12) as img_resp:
                with open(dest_file, 'wb') as f_out:
                    f_out.write(img_resp.read())
            downloaded_images.append(dest_file)
        except Exception as e:
            print(f"Erreur téléchargement graphique {idx+1} : {e}")

    # Appeler l'IA pour l'analyse des scénarios et la rédaction du post LinkedIn
    print(f"[{topic_idx+1}] Appel de l'IA pour l'analyse des scénarios météo...")
    system_prompt = """Tu es Patrick Marlière, météorologue expert de renommée nationale pour Monsieur Météo.

MISSION
À partir EXCLUSIVEMENT des discussions et analyses météorologiques fournies en entrée, tu dois produire une synthèse météorologique de niveau professionnel, fluide, élégante et sans aucune redondance.

OBJECTIF CRITIQUE DE LECTURE EN 10 SECONDES
1. Compréhension instantanée en moins de 10 secondes grâce au Résumé Express et au badge de confiance coloré.
2. TITRE EN DEUX LIGNES OBLIGATOIRE :
   Ligne 1 : Les dates exactes de la semaine (ex: 📅 Semaine 30 - Du 20 au 26 Juillet 2026)
   Ligne 2 : Une accroche météo courte en sous-titre (ex: 🌤️ Temps mitigé et frais au Nord, chaleur constante au Sud)
3. ORDRE ET FLUX D'INFORMATION SANS REDONDANCE :
   - Résumé Express (temps dominant, températures, pluies, risque principal)
   - Synthèse Régionale (1 à 2 phrases spécifiques par zone, longueur harmonisée)
   - Indice de Confiance & Incertitudes (Note + explication d'une phrase + incertitudes)
   - Scénarios Atmosphériques (150 à 180 mots par scénario, réellement différenciés par un mécanisme synoptique structurant)
   - Post LinkedIn (250-300 mots, storytelling expert, très aéré avec émojis, puces, 1 question finale, hashtags).

RÈGLES ABSOLUES & PRUDENCE :
1. ANONYMAT : Ne mentionne JAMAIS Infoclimat ou ses membres. Utilise « le consensus des prévisionnistes », « les modèles d'ensemble », « notre analyse ».
2. ZERO INVENTION : Aucune température (°C), cumul (mm), rafale (km/h) ou modèle inventé. Utilise des termes qualitatifs prudents si manque (« températures de saison », « risque orageux à affiner »).
3. PROBABILITÉS DYNAMIQUES = EXACTEMENT 100% : Les probabilités doivent être cohérentes avec la note de confiance (ex: Confiance 4/5 ➔ 65% / 25% / 10% ; Confiance 3/5 ➔ 50% / 35% / 15%).
4. SCÉNARIOS CONCIS (150 à 180 mots) : Axés sur le mécanisme physique et l'évolution chronologique, sans répéter ce qui est déjà dit dans le résumé express ou les régions. Formulations prudentes pour les échéances lointaines.
5. POST LINKEDIN OPTIMISÉ (250 à 300 mots) :
   - Raconte la tendance météo avec un storytelling fluide et captivant d'expert.
   - Utilise des émojis pertinents et des puces pour aérer et rythmer.
   - Ne fais pas une liste rébarbative des scénarios, mais donne la clé de lecture et le conseil pro.
   - Texte brut uniquement (0 markdown, pas de *, pas de # dans les titres).
   - Termine par une question engageante + 3-5 hashtags.

FORMAT DE SORTIE OBLIGATOIRE - Utilise EXACTEMENT ces balises :

[SUBJECT_TITLE_LINE1]
Semaine 30 - Du 20 au 26 Juillet 2026

[SUBJECT_TITLE_LINE2]
Accroche météo courte résumant le temps de la semaine

[EXPRESS_SUMMARY]
Résumé ultra-concis en 1 à 2 phrases maximum lisible en 10 secondes.

[EXPRESS_TREND]
Tendance dominante en 4-7 mots.

[EXPRESS_TEMPERATURES]
Niveau général des températures en 4-7 mots.

[EXPRESS_PRECIPITATIONS]
Précipitations et orages en 4-7 mots.

[EXPRESS_MAIN_RISK]
Risque principal à surveiller (ou « Aucun risque majeur »).

[GLOBAL_CONFIDENCE_SCORE]
Ex: 4/5 (ou 3/5, 5/5)

[GLOBAL_CONFIDENCE_DESC]
Une phrase courte expliquant directement le niveau de confiance (ex: Bonne convergence sur la tendance générale, mais incertitude sur l'intensité des orages).

[REGIONAL_HDF_NORTH]
1-2 phrases harmonisées pour Hauts-de-France & Nord.

[REGIONAL_ATLANTIC]
1-2 phrases harmonisées pour la Façade Atlantique.

[REGIONAL_CENTRAL]
1-2 phrases harmonisées pour les Régions Centrales.

[REGIONAL_SOUTH]
1-2 phrases harmonisées pour la Moitié Sud.

[REGIONAL_MEDITERRANEAN]
1-2 phrases harmonisées pour le Pourtour Méditerranéen.

[REGIONAL_MOUNTAINS]
1-2 phrases harmonisées pour les Reliefs (ou « Pas de particularité remarquable »).

[SCENARIO_MAJORITAIRE_PROB]
65%

[SCENARIO_MAJORITAIRE_TITLE]
Titre synoptique court.

[SCENARIO_MAJORITAIRE_DESC]
Description concise et structurée de 150 à 180 mots.

[SCENARIO_MEDIAN_PROB]
25%

[SCENARIO_MEDIAN_TITLE]
Titre synoptique court.

[SCENARIO_MEDIAN_DESC]
Description concise et structurée de 150 à 180 mots.

[SCENARIO_MINORITAIRE_PROB]
10%

[SCENARIO_MINORITAIRE_TITLE]
Titre synoptique court.

[SCENARIO_MINORITAIRE_DESC]
Description concise et structurée de 150 à 180 mots.

[KEY_UNCERTAINTIES]
- Incertitude 1
- Incertitude 2

[MONITORING_POINTS]
- Point de vigilance 1
- Point de vigilance 2

[LINKEDIN_POST]
Post LinkedIn expert storytelling en texte brut de 250 à 300 mots.

[LINKEDIN_HASHTAGS]
#Meteo #Previsions #France #Climat #MonsieurMeteo"""

    user_prompt = f"""Voici les 20 derniers messages des prévisionnistes pour le sujet : {topic_title_clean}

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
                
                "linkedin_post": r"\[LINKEDIN_POST\]\s*\n(.*?)(?=\n\s*\[|$)",
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
                    "regional": {
                        "hdf_north": parsed["regional_hdf_north"],
                        "atlantic": parsed["regional_atlantic"],
                        "central": parsed["regional_central"],
                        "south": parsed["regional_south"],
                        "mediterranean": parsed["regional_mediterranean"],
                        "mountains": parsed["regional_mountains"],
                    },
                    "scenarios": {
                        "majoritaire": {"prob": parsed["majoritaire_prob"] or "60%", "title": parsed["majoritaire_title"] or "Scénario Majoritaire", "desc": parsed["majoritaire_desc"]},
                        "median": {"prob": parsed["median_prob"] or "30%", "title": parsed["median_title"] or "Scénario Alternatif", "desc": parsed["median_desc"]},
                        "minoritaire": {"prob": parsed["minoritaire_prob"] or "10%", "title": parsed["minoritaire_title"] or "Scénario Minoritaire", "desc": parsed["minoritaire_desc"]}
                    },
                    "key_uncertainties": parsed["key_uncertainties"],
                    "monitoring_points": parsed["monitoring_points"],
                    "linkedin_post": parsed["linkedin_post"],
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
        
    # Extraire les deux semaines : clean_topics[1] (cours) et clean_topics[0] (suivante)
    # On les trie par ordre chronologique pour l'affichage (semaine en cours d'abord, puis semaine suivante)
    topics_to_process = []
    if len(clean_topics) >= 2:
        topics_to_process = [clean_topics[1], clean_topics[0]]
    else:
        topics_to_process = [clean_topics[0]]
        
    results = []
    for idx, topic in enumerate(topics_to_process):
        res = process_topic(topic, idx)
        if res:
            results.append(res)
            
    if not results:
        print("Aucun sujet n'a pu être traité.")
        sys.exit(1)
        
    # Génération du HTML combiné pour les deux semaines avec hiérarchie visuelle premium
    style = """
    body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #0f172a; background-color: #f1f5f9; margin: 0; padding: 25px 15px; }
    .container { max-width: 880px; background-color: #ffffff; margin: 0 auto; border-radius: 20px; overflow: hidden; box-shadow: 0 20px 35px -10px rgba(0, 0, 0, 0.09); border: 1px solid #cbd5e1; }
    .header { background: linear-gradient(135deg, #0284c7 0%, #1e3a8a 60%, #0f172a 100%); color: #ffffff; padding: 40px 30px; text-align: center; }
    .header-badge { display: inline-block; background: rgba(255, 255, 255, 0.18); backdrop-filter: blur(10px); padding: 4px 14px; border-radius: 30px; font-size: 11px; font-weight: 800; letter-spacing: 2px; text-transform: uppercase; margin-bottom: 12px; }
    .header h1 { margin: 0; font-size: 28px; font-weight: 800; letter-spacing: -0.5px; }
    .header p { margin: 10px 0 0 0; font-size: 14px; opacity: 0.92; }
    .content { padding: 35px 30px; }
    .week-divider { border-top: 3px dashed #94a3b8; margin: 55px 0; }
    
    /* Titre de semaine 2 Lignes */
    .week-title-box { margin-bottom: 25px; padding-left: 16px; border-left: 6px solid #0284c7; }
    .week-title-line1 { font-size: 22px; font-weight: 800; color: #1e3a8a; text-transform: uppercase; letter-spacing: 0.5px; margin: 0; }
    .week-title-line2 { font-size: 15px; font-weight: 600; color: #0284c7; margin-top: 4px; }

    .section-title { font-size: 13px; font-weight: 800; text-transform: uppercase; letter-spacing: 1.2px; color: #475569; margin-top: 35px; margin-bottom: 16px; border-bottom: 2px solid #e2e8f0; padding-bottom: 6px; }
    
    /* 1. HERO RESUME EXPRESS */
    .hero-express { background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 100%); color: #ffffff; border-radius: 18px; padding: 28px; margin-bottom: 30px; box-shadow: 0 12px 25px -5px rgba(30, 58, 138, 0.3); }
    .hero-top-bar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
    .hero-label { font-size: 12px; font-weight: 800; text-transform: uppercase; letter-spacing: 1.5px; color: #38bdf8; }
    
    /* Badge Confiance Dynamique */
    .conf-badge-green { background: #10b981; color: #ffffff; font-size: 13px; font-weight: 800; padding: 5px 14px; border-radius: 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.2); }
    .conf-badge-orange { background: #f59e0b; color: #ffffff; font-size: 13px; font-weight: 800; padding: 5px 14px; border-radius: 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.2); }
    .conf-badge-red { background: #ef4444; color: #ffffff; font-size: 13px; font-weight: 800; padding: 5px 14px; border-radius: 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.2); }

    .hero-summary { font-size: 17px; font-weight: 700; line-height: 1.55; margin-bottom: 14px; color: #ffffff; }
    .hero-conf-explanation { font-size: 13px; font-style: italic; color: #93c5fd; margin-bottom: 20px; background: rgba(255,255,255,0.08); padding: 8px 14px; border-radius: 8px; border-left: 3px solid #38bdf8; }

    .hero-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
    .hero-card { background: rgba(255, 255, 255, 0.1); backdrop-filter: blur(10px); border-radius: 10px; padding: 12px 14px; border: 1px solid rgba(255, 255, 255, 0.15); }
    .hero-card label { display: block; font-size: 10px; font-weight: 800; text-transform: uppercase; letter-spacing: 0.8px; color: #93c5fd; margin-bottom: 3px; }
    .hero-card span { font-size: 13px; font-weight: 600; color: #ffffff; }
    
    /* 2. REGIONS */
    .regional-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; margin-bottom: 30px; }
    .regional-card { background: #ffffff; border-radius: 12px; padding: 16px; border: 1px solid #e2e8f0; box-shadow: 0 2px 5px rgba(0,0,0,0.02); }
    .regional-card strong { color: #0f172a; font-size: 13px; display: block; margin-bottom: 6px; }
    .regional-card p { margin: 0; font-size: 13px; color: #475569; line-height: 1.55; }
    
    /* 3. CONFIANCE & INCERTITUDES */
    .confidence-panel { background: #f8fafc; border-radius: 14px; padding: 20px; border: 1px solid #e2e8f0; margin-bottom: 30px; }
    .confidence-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
    .confidence-head strong { font-size: 14px; color: #0f172a; }
    .uncertainties-box { background: #ffffff; border-radius: 10px; padding: 14px; border-left: 4px solid #f59e0b; border: 1px solid #fef3c7; border-left-width: 4px; font-size: 13px; color: #334155; line-height: 1.55; }
    
    /* 4. SCENARIOS */
    .scenario-card { border-radius: 14px; padding: 20px; margin-bottom: 18px; border: 1px solid #e2e8f0; background: #ffffff; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.03); }
    .sc-major { border-left: 6px solid #10b981; }
    .sc-median { border-left: 6px solid #f59e0b; }
    .sc-minor { border-left: 6px solid #ef4444; }
    .sc-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
    .sc-header h3 { margin: 0; font-size: 15px; font-weight: 800; color: #0f172a; }
    .sc-prob { font-size: 12px; padding: 3px 10px; border-radius: 20px; color: #ffffff; font-weight: 800; }
    .bg-major { background-color: #10b981; }
    .bg-median { background-color: #f59e0b; }
    .bg-minor { background-color: #ef4444; }
    .sc-text { margin: 0; font-size: 13px; line-height: 1.6; color: #334155; text-align: justify; }
    
    /* 5. LINKEDIN */
    .linkedin-box { background-color: #ffffff; border: 2px dashed #0284c7; padding: 22px; border-radius: 14px; font-family: 'Segoe UI', Tahoma, Geneva, sans-serif; font-size: 13px; white-space: pre-wrap; color: #0f172a; margin-bottom: 25px; line-height: 1.65; border-left: 6px solid #0284c7; }
    .hashtags { font-size: 13px; font-weight: 700; color: #0284c7; margin-top: 12px; }
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
                <div style="background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 12px; text-align: center; display: inline-block; width: 45%; margin-right: 3%; margin-bottom: 15px; vertical-align: top; box-shadow: 0 2px 5px rgba(0,0,0,0.03);">
                    <span style="font-weight: 800; font-size: 11px; color: #475569; display: block; margin-bottom: 8px; text-transform: uppercase; letter-spacing: 0.5px;">📈 Modélisation Candidate {idx+1}</span>
                    <img src="data:image/{ext};base64,{img_b64}" style="width: 100%; border-radius: 6px;" alt="Graphique Météo {idx+1}">
                </div>
                """
            except Exception as e:
                print(f"Erreur encodage base64 pour {img_path} : {e}")
        
        if html_images_block:
            html_images_block = f"""
            <div class="section-title">📊 MODÉLISATIONS & GRAPHIQUES DE TENDANCE</div>
            <div style="text-align: left;">{html_images_block}</div>
            """

        linkedin_post_clean = data["linkedin_post"].replace('<br>', '\n').replace('<br/>', '\n')
        hashtags_clean = data.get("linkedin_hashtags", "")
        
        express = data.get("express", {})
        regional = data.get("regional", {})
        conf = data.get("confidence", {})
        scenarios = data.get("scenarios", {})

        # Couleur dynamique du badge de confiance
        conf_score_raw = conf.get('score', '4/5')
        conf_class = "conf-badge-green"
        if "3/" in conf_score_raw:
            conf_class = "conf-badge-orange"
        elif "1/" in conf_score_raw or "2/" in conf_score_raw:
            conf_class = "conf-badge-red"

        divider = '<div class="week-divider"></div>' if w_idx > 0 else ""
        weeks_html += f"""
        {divider}
        
        <!-- TITRE DE SEMAINE EN 2 LIGNES -->
        <div class="week-title-box">
            <h2 class="week-title-line1">📅 {data.get('title_line1', 'SEMAINE')}</h2>
            <div class="week-title-line2">{data.get('title_line2', 'Synthèse des prévisions')}</div>
        </div>
        
        <!-- 1. HERO RESUME EXPRESS (10 SECONDES) -->
        <div class="hero-express">
            <div class="hero-top-bar">
                <span class="hero-label">⚡ RÉSUMÉ EXPRESS EN 10 SECONDES</span>
                <span class="{conf_class}">Indice Confiance : {conf_score_raw}</span>
            </div>
            <div class="hero-summary">{express.get('summary', '')}</div>
            <div class="hero-conf-explanation">🎯 <strong>Raison du niveau de confiance ({conf_score_raw}) :</strong> {conf.get('desc', '')}</div>
            <div class="hero-grid">
                <div class="hero-card"><label>🌤️ Temps Dominant</label><span>{express.get('trend', '-')}</span></div>
                <div class="hero-card"><label>🌡️ Températures</label><span>{express.get('temperatures', '-')}</span></div>
                <div class="hero-card"><label>🌧️ Précipitations</label><span>{express.get('precipitations', '-')}</span></div>
                <div class="hero-card"><label>⚠️ Risque Principal</label><span>{express.get('main_risk', 'Aucun risque majeur')}</span></div>
            </div>
        </div>

        <!-- 2. SYNTHESE PAR REGIONS -->
        <div class="section-title">🗺️ SYNTHÈSE PAR GRANDES RÉGIONS</div>
        <div class="regional-grid">
            <div class="regional-card"><strong>📍 Hauts-de-France & Nord</strong><p>{regional.get('hdf_north', '-')}</p></div>
            <div class="regional-card"><strong>🌊 Façade Atlantique</strong><p>{regional.get('atlantic', '-')}</p></div>
            <div class="regional-card"><strong>🏙️ Régions Centrales</strong><p>{regional.get('central', '-')}</p></div>
            <div class="regional-card"><strong>☀️ Moitié Sud</strong><p>{regional.get('south', '-')}</p></div>
            <div class="regional-card"><strong>🏖️ Pourtour Méditerranéen</strong><p>{regional.get('mediterranean', '-')}</p></div>
            <div class="regional-card"><strong>⛰️ Reliefs & Montagnes</strong><p>{regional.get('mountains', 'Pas de particularité remarquable')}</p></div>
        </div>

        <!-- 3. CONFIANCE & INCERTITUDES -->
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

        <!-- 4. GRAPHIQUES METEO -->
        {html_images_block}

        <!-- 5. LES 3 SCENARIOS (150-180 MOTS) -->
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

        <!-- 6. LINKEDIN STORYTELLING -->
        <div class="section-title">📰 POST LINKEDIN PROFESSIONNEL OPTIMISÉ (STORYTELLING EXPERT - 250-300 MOTS)</div>
        <div class="linkedin-box">
{linkedin_post_clean}

<div class="hashtags">{hashtags_clean}</div>
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
    subject_week_names = " & ".join([r["data"]["subject_title"].split("-")[0].strip() for r in results])
    subject = f"Tendances de la semaine - {subject_week_names}"
    
    # Nettoyage ASCII du sujet pour éviter les rejets SMTP
    import unicodedata
    clean_subj = unicodedata.normalize('NFKD', subject).encode('ASCII', 'ignore').decode('ASCII')
    subject = clean_subj
    
    filename = f"analyse_infoclimat_{datetime.datetime.now().strftime('%Y_%m_%d')}.html"
    
    html_b64 = base64.b64encode(html.encode('utf-8')).decode('ascii')
    text_body = f"Bonjour,\n\nVeuillez trouver ci-joint l'analyse consolidée des tendances météo pour la semaine en cours et la semaine suivante.\n\nLe rapport HTML contenant les scénarios synthétisés, les posts LinkedIn associés et les graphiques de modélisation est joint à ce message.\n\nCordialement,\nMonsieur Météo"
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
