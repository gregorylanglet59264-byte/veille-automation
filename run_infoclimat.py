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

À partir exclusivement des discussions et analyses météorologiques fournies en entrée, tu dois produire une synthèse fiable, hiérarchisée et compréhensible des tendances prévues pour la semaine cible.

Le rapport doit permettre :
1. de comprendre la tendance générale en moins de 15 secondes ;
2. d’identifier les différences entre les grandes régions françaises ;
3. de connaître les principales incertitudes ;
4. d’obtenir trois scénarios météorologiques réalistes ;
5. de générer un post LinkedIn professionnel et accessible.

RÈGLES ABSOLUES

1. Ne mentionne jamais le forum Infoclimat, ses membres, leurs pseudonymes ou l’origine communautaire des discussions.
Utilise uniquement des formulations comme :
« le consensus des prévisionnistes » ;
« les dernières analyses disponibles » ;
« les modèles d’ensemble » ;
« notre analyse consolidée » ;
« les principaux scénarios envisagés ».

2. N’invente aucune information.
Tu ne dois jamais inventer : une température, une anomalie thermique, un cumul de précipitations, une rafale, une valeur à 850 hPa ou 500 hPa, le positionnement précis d’un centre d’action, le nom d’un modèle, une probabilité, un risque d’orage, de grêle ou de phénomène violent.
Toute valeur précise doit être explicitement présente ou clairement déductible des informations fournies.
Lorsqu’une donnée manque, utilise une formulation qualitative : « températures supérieures aux normales », « précipitations localement significatives », « risque orageux à préciser », « évolution encore incertaine ».

3. Ne transforme pas une hypothèse isolée en tendance générale. Distingue clairement le scénario majoritaire, les alternatives crédibles, les hypothèses très minoritaires et les éléments encore impossibles à trancher.

4. Rédige exclusivement en français.

5. Ton : professionnel, pédagogique, météorologiquement rigoureux, accessible au grand public, sans alarmisme ni sensationnalisme.

6. Utilise « degrés » dans le post LinkedIn destiné au public. Dans les parties techniques du rapport, « °C » peut être utilisé.

7. N’utilise jamais une comparaison historique spectaculaire si elle n’est pas explicitement justifiée (interdit : « comparable à 2003 », « scénario historique », « records absolus menacés »).

8. Les scénarios doivent être réellement différents. Chaque scénario doit reposer sur une différence météorologique structurante.

GESTION DES PROBABILITÉS
Les probabilités ne doivent pas être automatiquement fixées à 65 %, 30 % et 5 %. Évalue-les en fonction du degré de convergence observable :
- majoritaire : 50 à 75 % ;
- alternatif : 20 à 40 % ;
- minoritaire : 5 à 15 %.
La somme des trois probabilités doit être exactement égale à 100 %. Privilégie les valeurs arrondies (ex: 60%, 30%, 10%).

RÉSUMÉ MÉTÉO EXPRESS
Le rapport doit impérativement commencer par un résumé immédiatement compréhensible (tendance dominante, températures, précipitations, régions concernées, principal phénomène à surveiller, niveau de confiance).

DÉCOUPAGE GÉOGRAPHIQUE
Présente obligatoirement une synthèse pour : Hauts-de-France et moitié nord, façade atlantique, régions centrales, moitié sud, pourtour méditerranéen, reliefs.

INDICE DE CONFIANCE
Note globale entre 1/5 et 5/5 avec une explication courte.

CONTENU DES SCÉNARIOS
Chaque scénario doit faire entre 150 et 250 mots.
Présente dans cet ordre : 1. Mécanisme 2. Chronologie 3. Températures 4. Géographie 5. Précipitations/vent/orages 6. Principale incertitude 7. Confiance propre.

POST LINKEDIN
Texte brut de 220 à 320 mots, aucun markdown, pas de *, pas de # dans les titres, au maximum 5 hashtags à la fin.

FORMAT DE SORTIE OBLIGATOIRE - Utilise EXACTEMENT ces balises :

[SUBJECT_TITLE]
Titre avec la semaine, les dates et la tendance principale.

[EXPRESS_SUMMARY]
Résumé de 2 à 3 phrases maximum présentant la tendance générale.

[EXPRESS_TREND]
Une phrase très courte résumant la tendance dominante.

[EXPRESS_TEMPERATURES]
Une phrase sur le niveau général des températures et leur évolution.

[EXPRESS_PRECIPITATIONS]
Une phrase sur la répartition générale des pluies ou des orages.

[EXPRESS_MAIN_RISK]
Le phénomène météorologique principal à surveiller. Écrire « Aucun phénomène majeur identifié » si nécessaire.

[REGIONAL_HDF_NORTH]
Synthèse pour les Hauts-de-France et la moitié nord.

[REGIONAL_ATLANTIC]
Synthèse pour la façade atlantique.

[REGIONAL_CENTRAL]
Synthèse pour les régions centrales.

[REGIONAL_SOUTH]
Synthèse pour la moitié sud.

[REGIONAL_MEDITERRANEAN]
Synthèse pour le pourtour méditerranéen.

[REGIONAL_MOUNTAINS]
Synthèse pour les reliefs. Écrire « Pas de particularité notable » si aucune information spécifique n’est disponible.

[GLOBAL_CONFIDENCE_SCORE]
Note comprise entre 1/5 et 5/5.

[GLOBAL_CONFIDENCE_DESC]
Explication courte de la note de confiance.

[SCENARIO_MAJORITAIRE_PROB]
60%

[SCENARIO_MAJORITAIRE_TITLE]
Titre court et descriptif.

[SCENARIO_MAJORITAIRE_DESC]
Description du scénario majoritaire entre 150 et 250 mots.

[SCENARIO_MEDIAN_PROB]
30%

[SCENARIO_MEDIAN_TITLE]
Titre court et descriptif.

[SCENARIO_MEDIAN_DESC]
Description du scénario alternatif entre 150 et 250 mots.

[SCENARIO_MINORITAIRE_PROB]
10%

[SCENARIO_MINORITAIRE_TITLE]
Titre court et descriptif.

[SCENARIO_MINORITAIRE_DESC]
Description du scénario minoritaire entre 150 et 250 mots.

[KEY_UNCERTAINTIES]
- Incertitude 1
- Incertitude 2
- Incertitude 3

[MONITORING_POINTS]
- Point de vigilance 1
- Point de vigilance 2

[LINKEDIN_POST]
Post LinkedIn en texte brut de 220 à 320 mots.

[LINKEDIN_HASHTAGS]
#Meteo #Previsions #France #Climat #MonsieurMeteo"""

    user_prompt = f"""Voici les 20 derniers messages des prévisionnistes à analyser :

{recent_messages_text}

Analyse ces discussions en profondeur selon tes règles absolues et génère le rapport complet et le post LinkedIn."""

    response = call_llm(system_prompt, user_prompt)
    
    data = None
    if response:
        try:
            print(f"[{topic_idx+1}] Parsing de la réponse de l'IA...")
            blocks = {
                "subject_title": r"\[SUBJECT_TITLE\]\s*\n(.*?)(?=\n\s*\[|$)",
                "express_summary": r"\[EXPRESS_SUMMARY\]\s*\n(.*?)(?=\n\s*\[|$)",
                "express_trend": r"\[EXPRESS_TREND\]\s*\n(.*?)(?=\n\s*\[|$)",
                "express_temperatures": r"\[EXPRESS_TEMPERATURES\]\s*\n(.*?)(?=\n\s*\[|$)",
                "express_precipitations": r"\[EXPRESS_PRECIPITATIONS\]\s*\n(.*?)(?=\n\s*\[|$)",
                "express_main_risk": r"\[EXPRESS_MAIN_RISK\]\s*\n(.*?)(?=\n\s*\[|$)",
                
                "regional_hdf_north": r"\[REGIONAL_HDF_NORTH\]\s*\n(.*?)(?=\n\s*\[|$)",
                "regional_atlantic": r"\[REGIONAL_ATLANTIC\]\s*\n(.*?)(?=\n\s*\[|$)",
                "regional_central": r"\[REGIONAL_CENTRAL\]\s*\n(.*?)(?=\n\s*\[|$)",
                "regional_south": r"\[REGIONAL_SOUTH\]\s*\n(.*?)(?=\n\s*\[|$)",
                "regional_mediterranean": r"\[REGIONAL_MEDITERRANEAN\]\s*\n(.*?)(?=\n\s*\[|$)",
                "regional_mountains": r"\[REGIONAL_MOUNTAINS\]\s*\n(.*?)(?=\n\s*\[|$)",
                
                "global_confidence_score": r"\[GLOBAL_CONFIDENCE_SCORE\]\s*\n(.*?)(?=\n\s*\[|$)",
                "global_confidence_desc": r"\[GLOBAL_CONFIDENCE_DESC\]\s*\n(.*?)(?=\n\s*\[|$)",
                
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
            
            if parsed["subject_title"] and (parsed["express_summary"] or parsed["majoritaire_desc"]):
                data = {
                    "subject_title": parsed["subject_title"],
                    "express": {
                        "summary": parsed["express_summary"],
                        "trend": parsed["express_trend"],
                        "temperatures": parsed["express_temperatures"],
                        "precipitations": parsed["express_precipitations"],
                        "main_risk": parsed["express_main_risk"],
                    },
                    "regional": {
                        "hdf_north": parsed["regional_hdf_north"],
                        "atlantic": parsed["regional_atlantic"],
                        "central": parsed["regional_central"],
                        "south": parsed["regional_south"],
                        "mediterranean": parsed["regional_mediterranean"],
                        "mountains": parsed["regional_mountains"],
                    },
                    "confidence": {
                        "score": parsed["global_confidence_score"] or "4/5",
                        "desc": parsed["global_confidence_desc"],
                    },
                    "scenarios": {
                        "majoritaire": {"prob": parsed["majoritaire_prob"] or "60%", "title": parsed["majoritaire_title"] or "Scénario Principal", "desc": parsed["majoritaire_desc"]},
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
        
    # Génération du HTML combiné pour les deux semaines
    style = """
    body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #1e293b; background-color: #f8fafc; margin: 0; padding: 20px; }
    .container { max-width: 850px; background-color: #ffffff; margin: 0 auto; border-radius: 16px; overflow: hidden; box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.08); border: 1px solid #e2e8f0; }
    .header { background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 50%, #2563eb 100%); color: #ffffff; padding: 35px; text-align: center; }
    .header h1 { margin: 0; font-size: 26px; font-weight: 800; letter-spacing: 0.5px; }
    .header p { margin: 8px 0 0 0; font-size: 14px; opacity: 0.9; }
    .content { padding: 35px; }
    .week-divider { border-top: 3px dashed #cbd5e1; margin: 50px 0; }
    .week-header { font-size: 22px; font-weight: 800; color: #1e3a8a; margin-bottom: 25px; padding-left: 12px; border-left: 6px solid #2563eb; text-transform: uppercase; }
    .section-title { font-size: 14px; font-weight: 800; text-transform: uppercase; letter-spacing: 1px; color: #475569; margin-top: 30px; margin-bottom: 14px; border-bottom: 2px solid #e2e8f0; padding-bottom: 6px; }
    
    /* Résumé Express */
    .express-box { background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%); border-radius: 14px; padding: 22px; margin-bottom: 25px; border: 1px solid #bfdbfe; }
    .express-summary-text { font-size: 15px; font-weight: 600; color: #1e40af; margin-bottom: 15px; line-height: 1.6; }
    .express-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
    .express-item { background: #ffffff; border-radius: 8px; padding: 10px 14px; font-size: 13px; border: 1px solid #dbeafe; }
    .express-item strong { color: #1e3a8a; display: block; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 2px; }
    
    /* Régions */
    .regional-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; margin-bottom: 25px; }
    .regional-card { background: #f8fafc; border-radius: 10px; padding: 14px; border: 1px solid #e2e8f0; }
    .regional-card strong { color: #0f172a; font-size: 13px; display: block; margin-bottom: 4px; }
    .regional-card p { margin: 0; font-size: 13px; color: #475569; line-height: 1.5; }
    
    /* Confiance & Incertitudes */
    .confidence-box { background: #f0fdf4; border-radius: 10px; padding: 16px; border: 1px solid #bbf7d0; margin-bottom: 20px; display: flex; align-items: center; justify-content: space-between; }
    .confidence-score { font-size: 22px; font-weight: 800; color: #166534; background: #dcfce7; padding: 4px 14px; border-radius: 20px; }
    
    /* Scénarios */
    .scenario-card { border-radius: 12px; padding: 20px; margin-bottom: 16px; border: 1px solid #e2e8f0; }
    .sc-major { background-color: #ecfdf5; border-left: 6px solid #10b981; }
    .sc-median { background-color: #fffbeb; border-left: 6px solid #f59e0b; }
    .sc-minor { background-color: #fef2f2; border-left: 6px solid #ef4444; }
    .sc-title { font-size: 16px; font-weight: 700; color: #1e293b; display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
    .sc-prob { font-size: 13px; padding: 3px 10px; border-radius: 20px; color: #ffffff; font-weight: 700; }
    .bg-major { background-color: #10b981; }
    .bg-median { background-color: #f59e0b; }
    .bg-minor { background-color: #ef4444; }
    
    /* Social Box */
    .social-box { background-color: #f8fafc; border: 1px dashed #2563eb; padding: 20px; border-radius: 12px; font-family: monospace; font-size: 13px; white-space: pre-wrap; color: #1e293b; margin-bottom: 25px; line-height: 1.6; border-left: 5px solid #2563eb; }
    .hashtags { font-size: 13px; font-weight: 700; color: #2563eb; margin-top: 10px; }
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
                <div style="background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 12px; text-align: center; display: inline-block; width: 45%; margin-right: 3%; margin-bottom: 15px; vertical-align: top; box-shadow: 0 2px 4px rgba(0,0,0,0.04);">
                    <span style="font-weight: bold; font-size: 11px; color: #475569; display: block; margin-bottom: 8px; text-transform: uppercase; letter-spacing: 0.5px;">📈 Graphique Candidat {idx+1}</span>
                    <img src="data:image/{ext};base64,{img_b64}" style="width: 100%; border-radius: 6px;" alt="Graphique Météo {idx+1}">
                </div>
                """
            except Exception as e:
                print(f"Erreur encodage base64 pour {img_path} : {e}")
        
        if html_images_block:
            html_images_block = f"""
            <div class="section-title">📊 GRAPHIQUES METEO ASSOCIES</div>
            <div style="text-align: left;">{html_images_block}</div>
            """

        linkedin_post_clean = data["linkedin_post"].replace('<br>', '\n').replace('<br/>', '\n')
        hashtags_clean = data.get("linkedin_hashtags", "")
        
        express = data.get("express", {})
        regional = data.get("regional", {})
        conf = data.get("confidence", {})
        scenarios = data.get("scenarios", {})

        divider = '<div class="week-divider"></div>' if w_idx > 0 else ""
        weeks_html += f"""
        {divider}
        <div class="week-header">📅 {data['subject_title']}</div>
        
        <!-- 1. RESUME EXPRESS (15 SECONDES) -->
        <div class="express-box">
            <div class="express-summary-text">⚡ EN 15 SECONDES : {express.get('summary', '')}</div>
            <div class="express-grid">
                <div class="express-item"><strong>🌤️ Tendance Dominante</strong>{express.get('trend', '')}</div>
                <div class="express-item"><strong>🌡️ Températures</strong>{express.get('temperatures', '')}</div>
                <div class="express-item"><strong>🌧️ Précipitations</strong>{express.get('precipitations', '')}</div>
                <div class="express-item"><strong>⚠️ Risque Principal</strong>{express.get('main_risk', 'Aucun phénomène majeur')}</div>
            </div>
        </div>

        <!-- 2. GRAPHIQUES METEO -->
        {html_images_block}

        <!-- 3. SYNTHESE REGIONALE -->
        <div class="section-title">🗺️ SYNTHÈSE PAR GRANDES RÉGIONS</div>
        <div class="regional-grid">
            <div class="regional-card"><strong>📍 Hauts-de-France & Nord</strong><p>{regional.get('hdf_north', '-')}</p></div>
            <div class="regional-card"><strong>🌊 Façade Atlantique</strong><p>{regional.get('atlantic', '-')}</p></div>
            <div class="regional-card"><strong>🏙️ Régions Centrales</strong><p>{regional.get('central', '-')}</p></div>
            <div class="regional-card"><strong>☀️ Moitié Sud</strong><p>{regional.get('south', '-')}</p></div>
            <div class="regional-card"><strong>🏖️ Pourtour Méditerranéen</strong><p>{regional.get('mediterranean', '-')}</p></div>
            <div class="regional-card"><strong>⛰️ Reliefs & Montagnes</strong><p>{regional.get('mountains', 'Pas de particularité notable')}</p></div>
        </div>

        <!-- 4. INDICE DE CONFIANCE & INCERTITUDES -->
        <div class="section-title">🎯 CONFIANCE & INCERTITUDES</div>
        <div class="confidence-box">
            <div>
                <strong style="color: #166534; font-size: 14px; display: block;">Indice de Confiance Global</strong>
                <span style="font-size: 13px; color: #374151;">{conf.get('desc', '')}</span>
            </div>
            <div class="confidence-score">{conf.get('score', '4/5')}</div>
        </div>
        
        <div style="background: #f8fafc; border-radius: 10px; padding: 16px; border: 1px solid #e2e8f0; margin-bottom: 25px;">
            <strong style="color: #334155; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px; display: block; margin-bottom: 6px;">❓ Principales Incertitudes & Points à Surveiller :</strong>
            <div style="font-size: 13px; color: #475569; line-height: 1.5; white-space: pre-wrap;">{data.get('key_uncertainties', '')}\n\n<strong>Points de vigilance :</strong>\n{data.get('monitoring_points', '')}</div>
        </div>

        <!-- 5. LES 3 SCENARIOS -->
        <div class="section-title">🔮 LES 3 SCÉNARIOS MÉTÉOROLOGIQUES</div>
        
        <div class="scenario-card sc-major">
            <div class="sc-title">
                <span>🟢 {scenarios.get('majoritaire', {}).get('title', 'Scénario Majoritaire')}</span>
                <span class="sc-prob bg-major">{scenarios.get('majoritaire', {}).get('prob', '60%')}</span>
            </div>
            <p style="margin: 0; font-size: 13px; line-height: 1.6; text-align: justify; color: #334155;">{scenarios.get('majoritaire', {}).get('desc', '')}</p>
        </div>
        
        <div class="scenario-card sc-median">
            <div class="sc-title">
                <span>🟡 {scenarios.get('median', {}).get('title', 'Scénario Alternatif')}</span>
                <span class="sc-prob bg-median">{scenarios.get('median', {}).get('prob', '30%')}</span>
            </div>
            <p style="margin: 0; font-size: 13px; line-height: 1.6; text-align: justify; color: #334155;">{scenarios.get('median', {}).get('desc', '')}</p>
        </div>
        
        <div class="scenario-card sc-minor">
            <div class="sc-title">
                <span>🔴 {scenarios.get('minoritaire', {}).get('title', 'Scénario Minoritaire')}</span>
                <span class="sc-prob bg-minor">{scenarios.get('minoritaire', {}).get('prob', '10%')}</span>
            </div>
            <p style="margin: 0; font-size: 13px; line-height: 1.6; text-align: justify; color: #334155;">{scenarios.get('minoritaire', {}).get('desc', '')}</p>
        </div>

        <!-- 6. POST LINKEDIN -->
        <div class="section-title">📰 POST LINKEDIN PROFESSIONNEL (PRÊT À PUBLIER)</div>
        <div class="social-box">
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
