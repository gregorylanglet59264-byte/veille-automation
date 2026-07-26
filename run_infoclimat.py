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
from email.utils import formatdate

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

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

def extract_comments_and_images(target_topic, topic_idx):
    decoded_topic = urllib.parse.unquote(target_topic)
    topic_title_slug = decoded_topic.rstrip('/').split('/')[-1]
    topic_title_slug = re.sub(r'^\d+-', '', topic_title_slug)
    topic_title_clean = topic_title_slug.replace('-', ' ').title()
    print(f"\n--- Scraping Sujet [{topic_idx+1}] : {topic_title_clean} ---")
    
    try:
        html_topic = fetch_url(target_topic)
    except Exception as e:
        print(f"Erreur sujet : {e}")
        return None
        
    pages = re.findall(r'\?page=(\d+)', html_topic)
    last_page = 1
    if pages:
        last_page = max(int(p) for p in pages)
    
    start_page = max(1, last_page - 2)
    all_comments = []
    all_authors = []
    
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
    
    # Extraire les images
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
        try:
            req = urllib.request.Request(img_url, headers={'User-Agent': USER_AGENT})
            with urllib.request.urlopen(req, timeout=6) as img_resp:
                with open(dest_file, 'wb') as f_out:
                    f_out.write(img_resp.read())
            downloaded_images.append(dest_file)
        except Exception as e:
            print(f"Erreur téléchargement graphique {idx+1} : {e}")

    return {
        "title_clean": topic_title_clean,
        "comments_text": recent_messages_text,
        "images": downloaded_images
    }

def extract_tag(text, tag):
    pattern = rf"\[{tag}\]\s*\n(.*?)(?=\n\s*\[|$)"
    match = re.search(pattern, text, re.DOTALL)
    return match.group(1).strip() if match else ""

def parse_models(week_text, prefix):
    blocks = re.findall(rf"\[{prefix}_MODEL_START\](.*?)\[{prefix}_MODEL_END\]", week_text, re.DOTALL)
    models = []
    for b in blocks:
        model = {
            "name": extract_tag(b, f"{prefix}_MODEL_NAME"),
            "scenario": extract_tag(b, f"{prefix}_MODEL_SCENARIO"),
            "sensible_weather": extract_tag(b, f"{prefix}_MODEL_SENSIBLE_WEATHER"),
            "temperatures": extract_tag(b, f"{prefix}_MODEL_TEMPERATURES"),
            "precipitations": extract_tag(b, f"{prefix}_MODEL_PRECIPITATIONS"),
            "affected_zones": extract_tag(b, f"{prefix}_MODEL_AFFECTED_ZONES"),
            "timing": extract_tag(b, f"{prefix}_MODEL_TIMING"),
            "mentions_count": extract_tag(b, f"{prefix}_MODEL_MENTIONS_COUNT"),
            "differences": extract_tag(b, f"{prefix}_MODEL_DIFFERENCES"),
            "confidence_reason": extract_tag(b, f"{prefix}_MODEL_CONFIDENCE_REASON"),
            "limits": extract_tag(b, f"{prefix}_MODEL_LIMITS"),
            "confidence": extract_tag(b, f"{prefix}_MODEL_CONFIDENCE")
        }
        if model["name"]:
            models.append(model)
    return models

def parse_images_info(week_text, prefix):
    blocks = re.findall(rf"\[{prefix}_IMAGE_START\](.*?)\[{prefix}_IMAGE_END\]", week_text, re.DOTALL)
    imgs = []
    for b in blocks:
        img = {
            "title": extract_tag(b, f"{prefix}_IMAGE_TITLE"),
            "model": extract_tag(b, f"{prefix}_IMAGE_MODEL"),
            "run": extract_tag(b, f"{prefix}_IMAGE_RUN"),
            "why_important": extract_tag(b, f"{prefix}_IMAGE_WHY_IMPORTANT"),
            "what_to_watch": extract_tag(b, f"{prefix}_IMAGE_WHAT_TO_WATCH"),
            "confidence": extract_tag(b, f"{prefix}_IMAGE_CONFIDENCE"),
            "attribution_uncertainty": extract_tag(b, f"{prefix}_IMAGE_ATTRIBUTION_UNCERTAINTY")
        }
        if img["title"]:
            imgs.append(img)
    return imgs

def generate_sparklines_html(history_dir="history"):
    if not os.path.exists(history_dir):
        return "", ""
        
    files = [f for f in os.listdir(history_dir) if f.endswith(".json")]
    if len(files) < 2:
        return "", ""
        
    files.sort()
    recent_files = files[-5:]
    
    sparkline_rows = []
    temp_rows = []
    
    for f in recent_files:
        path = os.path.join(history_dir, f)
        try:
            with open(path, "r", encoding="utf-8") as file_in:
                run_data = json.load(file_in)
                parts = f.replace(".json", "").split("_")[0].split("-")
                date_str = f"{parts[2]}/{parts[1]}" if len(parts) >= 3 else f
                
                conf = run_data.get("w1_confidence", 80)
                blocks = int(conf / 10)
                empty = 10 - blocks
                spark_bar = "█" * blocks + "░" * empty
                sparkline_rows.append(f'<div class="sparkline-row"><span>{date_str} :</span> <span>{spark_bar} {conf}%</span></div>')
                
                temp = run_data.get("w1_temp", "De saison")
                temp_rows.append(f'<div class="sparkline-row"><span>{date_str} :</span> <span>{temp}</span></div>')
        except Exception as e:
            print(f"Erreur lecture historique {f} : {e}")
            
    sparklines_html = "\n".join(sparkline_rows)
    temp_evolution_html = ""
    if len(recent_files) >= 2:
        try:
            with open(os.path.join(history_dir, recent_files[-2]), "r", encoding="utf-8") as f_prev:
                prev_data = json.load(f_prev)
            with open(os.path.join(history_dir, recent_files[-1]), "r", encoding="utf-8") as f_curr:
                curr_data = json.load(f_curr)
                
            t_prev = prev_data.get("w1_temp", "De saison")
            t_curr = curr_data.get("w1_temp", "De saison")
            
            trend = "➡️ Stable"
            if t_curr.lower() != t_prev.lower():
                if any(w in t_curr.lower() for w in ["chaud", "canicule", "hausse"]) and not any(w in t_prev.lower() for w in ["chaud", "canicule"]):
                    trend = "⬆ Renforcement"
                elif any(w in t_curr.lower() for w in ["frais", "baisse"]) and not any(w in t_prev.lower() for w in ["frais", "baisse"]):
                    trend = "⬇ Baisse"
                else:
                    trend = "➡️ Évolution"
                
            temp_evolution_html = f"""
            <div class="sparkline-row"><span>Précédent run :</span> <span>{t_prev}</span></div>
            <div class="sparkline-row"><span>Run actuel :</span> <span>{t_curr}</span></div>
            <div class="sparkline-row"><span>Évolution :</span> <span><span class="trend-pill trend-up">{trend}</span></span></div>
            """
        except Exception:
            temp_evolution_html = "\n".join(temp_rows[-2:])
    else:
        temp_evolution_html = "\n".join(temp_rows)
        
    return sparklines_html, temp_evolution_html

def build_model_cards(models):
    html_blocks = []
    for model in models:
        try:
            conf_val = int(re.search(r'\d+', model.get("confidence", "80")).group(0))
        except Exception:
            conf_val = 80
            
        color = "var(--green)"
        if conf_val < 60:
            color = "var(--red)"
        elif conf_val < 75:
            color = "var(--amber)"
            
        row_html = f"""
        <tr>
          <td>
            <div class="model-name">{model.get("name", "Modèle")}</div>
            <div class="chips">
              <span class="chip">{model.get("mentions_count", "0")} mentions</span>
              {f'<span class="chip">{model.get("timing", "")}</span>' if model.get("timing") else ''}
            </div>
          </td>
          <td>{model.get("scenario", "-")}</td>
          <td>{model.get("sensible_weather", "-")}</td>
          <td>{model.get("affected_zones", "-")}</td>
          <td>
            <div class="score">{conf_val} %</div>
            <div class="bar"><div class="fill" style="width:{conf_val}%; background:{color};"></div></div>
          </td>
        </tr>
        """
        html_blocks.append(row_html)
    return "\n".join(html_blocks) if html_blocks else "<tr><td colspan='5'>Aucun modèle spécifique n'est détaillé dans les sources.</td></tr>"

def build_image_cards(images_info, downloaded_images):
    html_blocks = []
    paired_count = min(len(images_info), len(downloaded_images))
    for i in range(paired_count):
        img_info = images_info[i]
        img_path = downloaded_images[i]
        
        try:
            with open(img_path, "rb") as f_img:
                img_b64 = base64.b64encode(f_img.read()).decode('ascii')
            ext = img_path.split('.')[-1]
            img_html = f'<img src="data:image/{ext};base64,{img_b64}" style="width: 100%; height: 220px; object-fit: cover;" alt="Carte météo">'
        except Exception as e:
            print(f"Erreur encodage image {img_path} : {e}")
            img_html = f'<div class="image-demo">IMAGE {i+1}<br>Erreur de chargement</div>'
            
        card_html = f"""
        <div class="image-card">
            {img_html}
            <div class="image-caption">
                <h3>{img_info.get("title", "Carte météo")}</h3>
                <p>{img_info.get("why_important", "")} <br><b>À surveiller :</b> {img_info.get("what_to_watch", "")}</p>
                <div class="image-meta">
                    <span class="chip">{img_info.get("model", "-")}</span>
                    <span class="chip">Confiance : {img_info.get("confidence", "-")}</span>
                </div>
            </div>
        </div>
        """
        html_blocks.append(card_html)
    return "\n".join(html_blocks) if html_blocks else "<p>Aucun graphique météo associé n'a été trouvé.</p>"

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
    jours_restants_cours_str = semaine_cours_str

    current_iso_week = now.isocalendar()[1]

    def get_topic_week_num(url):
        match = re.search(r'semaine-(\d+)', url.lower())
        return int(match.group(1)) if match else 0

    # Sélection intelligente : on cherche d'abord la semaine courante et futures (>= current_iso_week)
    relevant_topics = [
        t for t in clean_topics
        if current_iso_week <= get_topic_week_num(t) <= current_iso_week + 4
    ]

    # Repli si moins de 2 sujets futurs (on ré-autorise la semaine précédente)
    if len(relevant_topics) < 2:
        relevant_topics = [
            t for t in clean_topics
            if current_iso_week - 1 <= get_topic_week_num(t) <= current_iso_week + 4
        ]

    # On prend les 2 plus futurs, triés par ordre croissant
    relevant_topics = sorted(relevant_topics, key=get_topic_week_num, reverse=True)[:2]
    relevant_topics.sort(key=get_topic_week_num)

    print(f"[INFO] Topics retenus (semaine ISO {current_iso_week}) : {[get_topic_week_num(t) for t in relevant_topics]} → {relevant_topics}")

    week1_data = extract_comments_and_images(relevant_topics[0], 0)
    week2_data = extract_comments_and_images(relevant_topics[1], 1)
    
    if not week1_data or not week2_data:
        print("Erreur de récupération des données du forum.")
        sys.exit(1)

    last_bulletin_path = "data/last_bulletin.json"
    last_bulletin_context = "Aucun bulletin précédent disponible."
    if os.path.exists(last_bulletin_path):
        try:
            with open(last_bulletin_path, "r", encoding="utf-8") as f_last:
                last_data = json.load(f_last)
                last_bulletin_context = (
                    f"Dernier bulletin généré le {last_data.get('date_generation', 'Inconnue')}.\n"
                    f"Résumé général précédent : {last_data.get('global_summary', 'Inconnu')}.\n"
                    f"Confiance précédente de la semaine 1 : {last_data.get('w1_confidence', 80)}%.\n"
                    f"Températures attendues précédemment : {last_data.get('w1_temp', 'De saison')}."
                )
        except Exception as e:
            print(f"Erreur lecture dernier bulletin : {e}")

    saison_actuelle = ["hiver", "printemps", "été", "automne"][(now.month % 12 // 3)]

    system_prompt = """Tu es Patrick Marlière, météorologue expert de renommée nationale pour Monsieur Météo.

MISSION
À partir des discussions et analyses météorologiques brutes de deux semaines distinctes (Semaine en cours et Semaine suivante), tu dois produire un bulletin d'analyse météorologique consolidé, professionnel, grand public, hyper-visuel et rigoureusement structuré par balises.

RÈGLE D'OR N°1 : DISCIPLINE SAISONNIÈRE & PRUDENCE MÉTÉOROLOGIQUE
- Nous sommes en ÉTÉ. Sauf mention explicite et justifiée en haute altitude (>1500m), toute référence à des conditions hivernales (neige en plaine, gel généralisé, températures négatives) est STRICTEMENT INTERDITE.
- Ne transforme jamais une simple conjecture en certitude. Si les prévisionnistes du forum hésitent, utilise des termes prudents ("probable", "incertain", "à confirmer").
- Ne cite jamais de pseudos ou d'utilisateurs du forum. Réfère-toi à "les prévisionnistes", "les modélisations" ou "le consensus".

RÈGLE D'OR N°2 : ANALYSE PAR MODÈLE & CALCUL D'INDICE DE CONFIANCE
- Pour chaque semaine, tu devez analyser la comparaison des modèles météo cités (ex: ECMWF, GFS, ICON, GEM, AIFS).
- Pour chaque modèle, calcule un Indice de Confiance d'Extraction (de 0 à 100%) selon ce barème logique :
  - Nombre de mentions positives ou convergentes du modèle : >=5 mentions = +30% | 2-4 mentions = +15% | 1 mention = +5%.
  - Concordance générale avec les autres modèles : Accord total = +30% | Accord partiel = +15% | Contradiction forte = +5%.
  - Précision des détails (zones, échéance) : Détails précis = +20% | Allusions générales = +10%.
  - Présence de cartes associées : Oui = +20% | Non = +0%.
  Si l'indice ne peut être estimé, écris "Non estimable". Cet indice mesure la fiabilité de la reconstitution du modèle depuis les messages et images du forum, pas une probabilité physique.

RÈGLE D'OR N°3 : DÉCOUPAGE PAR GRANDES ZONES MÉTÉO (7 ZONES FIXES)
Pour chaque semaine, tu devez évaluer le temps sensible pour ces 7 zones géographiques :
1. Ouest et façade atlantique
2. Nord et Nord-Ouest
3. Nord-Est
4. Centre
5. Sud-Ouest
6. Sud-Est et Méditerranée
7. Corse (uniquement si documentée, sinon écrire "Informations insuffisantes dans les sources")
Si les messages du forum ne parlent pas d'une zone, n'invente rien. Rédige explicitement "Informations insuffisantes dans les sources pour cette zone".

RÈGLE D'OR N°4 : SYNTHÈSE GLOBALE & POST LINKEDIN
- Produis une synthèse globale des 15 jours combinant l'évolution générale et le fait météo majeur.
- Rédige un Post LinkedIn professionnel, prêt à copier-coller (250-300 mots), aéré en paragraphes très courts pour smartphone, contenant un titre fort, une introduction courte, les dates précises, les tendances, les divergences et 4 à 8 hashtags pertinents. Aucun formatage markdown gras/italique dans le post LinkedIn.

RÈGLE D'OR N°5 : BULLETIN PRÉCÉDENT & COMPARAISON
Si un bulletin précédent (données clés) est fourni dans l'invite utilisateur, tu dois générer une section "Ce qui a changé depuis le précédent bulletin". Rédige cette section sous la balise suivante :
[WHAT_CHANGED_SINCE_LAST]
Description des évolutions importantes constatées (ex: renforcement d'un scénario, hausse des températures, décalage d'une perturbation).
Si aucun bulletin précédent n'est fourni, laisse cette section vide ou n'écris rien sous cette balise.

FORMAT DE SORTIE OBLIGATOIRE - Utilise EXACTEMENT ce balisage :

[WEEK_1_START]
[W1_DATES]
Période exacte de la semaine 1 (ex: Du Lundi 27 Juillet au Dimanche 2 Août 2026)

[W1_KEY_POINT_1]
Premier fait marquant très court (max 15 mots)

[W1_KEY_POINT_2]
Deuxième fait marquant très court (max 15 mots)

[W1_KEY_POINT_3]
Troisième fait marquant très court (max 15 mots)

[W1_KEY_POINT_4]
Quatrième fait marquant très court (max 15 mots)

[W1_KEY_POINT_5]
Cinquième fait marquant très court (max 15 mots) ou laisser vide

[W1_KEY_POINT_6]
Sixième fait marquant très court (max 15 mots) ou laisser vide

--- (Répéter le bloc ci-dessous pour chaque modèle météo cité) ---
[W1_MODEL_START]
[W1_MODEL_NAME]
Nom du modèle
[W1_MODEL_SCENARIO]
Scénario général du modèle
[W1_MODEL_SENSIBLE_WEATHER]
Temps sensible (soleil, orages, etc.)
[W1_MODEL_TEMPERATURES]
Tendances de températures
[W1_MODEL_PRECIPITATIONS]
Tendances de précipitations
[W1_MODEL_AFFECTED_ZONES]
Régions ou zones géographiques concernées
[W1_MODEL_TIMING]
Échéance ou période d'application
[W1_MODEL_MENTIONS_COUNT]
Nombre de mentions exploitables
[W1_MODEL_DIFFERENCES]
Différences notables avec les autres modèles
[W1_MODEL_CONFIDENCE_REASON]
Justification de l'indice de confiance d'extraction
[W1_MODEL_LIMITS]
Limites de l'analyse pour ce modèle
[W1_MODEL_CONFIDENCE]
Valeur en % ou Non estimable
[W1_MODEL_END]
-----------------------------------------------------------------

[W1_CONVERGENCES]
Points de convergence entre les modèles

[W1_DIVERGENCES]
Points de divergence et désaccords

[W1_ZONE_WEST]
Description météo pour Ouest et façade atlantique
[W1_ZONE_WEST_CONF]
Confiance et origine de l'incertitude

[W1_ZONE_NORTH]
Description météo pour Nord et Nord-Ouest
[W1_ZONE_NORTH_CONF]
Confiance et origine de l'incertitude

[W1_ZONE_NORTHEAST]
Description météo pour Nord-Est
[W1_ZONE_NORTHEAST_CONF]
Confiance et origine de l'incertitude

[W1_ZONE_CENTRAL]
Description météo pour Centre
[W1_ZONE_CENTRAL_CONF]
Confiance et origine de l'incertitude

[W1_ZONE_SOUTHWEST]
Description météo pour Sud-Ouest
[W1_ZONE_SOUTHWEST_CONF]
Confiance et origine de l'incertitude

[W1_ZONE_SOUTHEAST]
Description météo pour Sud-Est et Méditerranée
[W1_ZONE_SOUTHEAST_CONF]
Confiance et origine de l'incertitude

[W1_ZONE_CORSICA]
Description météo pour Corse
[W1_ZONE_CORSICA_CONF]
Confiance et origine de l'incertitude

[W1_SOLID_POINTS]
Points les mieux établis de la semaine

[W1_FRAGILE_POINTS]
Points les plus fragiles de la semaine

[W1_NEXT_RUNS_TO_WATCH]
Ce qu'il faut surveiller dans les prochains runs

[W1_PHASE_1_DATES]
Dates/Jours de la phase 1
[W1_PHASE_1]
Description de la phase 1
[W1_PHASE_2_DATES]
Dates/Jours de la phase 2
[W1_PHASE_2]
Description de la phase 2
[W1_PHASE_3_DATES]
Dates/Jours de la phase 3
[W1_PHASE_3]
Description de la phase 3
[W1_PHASE_4_DATES]
Dates/Jours de la phase 4
[W1_PHASE_4]
Description de la phase 4

--- (Répéter le bloc ci-dessous pour chaque image analysée, max 3) ---
[W1_IMAGE_START]
[W1_IMAGE_TITLE]
Titre de l'image
[W1_IMAGE_MODEL]
Modèle de l'image (ex: ECMWF)
[W1_IMAGE_RUN]
Échéance ou run
[W1_IMAGE_WHY_IMPORTANT]
Pourquoi cette carte est importante
[W1_IMAGE_WHAT_TO_WATCH]
Ce qu'il faut regarder
[W1_IMAGE_CONFIDENCE]
Confiance d'interprétation
[W1_IMAGE_ATTRIBUTION_UNCERTAINTY]
Incertitude d'attribution (laisser vide si aucune)
[W1_IMAGE_END]
---------------------------------------------------------------------

[WEEK_1_END]

[WEEK_2_START]
... (mêmes balises W2_ que pour W1_ ci-dessus) ...
[WEEK_2_END]

[GLOBAL_START]
[GLOBAL_15_DAY_TREND]
Tendance générale des 15 jours
[MOST_RELIABLE_WEEK]
Semaine la plus fiable des deux et pourquoi
[GLOBAL_SOLID_POINTS]
Points consolidés majeurs des deux semaines
[GLOBAL_RECURRING_PHENOMENA]
Phénomènes météo récurrents
[GLOBAL_AFFECTED_ZONES]
Régions les plus touchées/concernées
[GLOBAL_MAJOR_UNCERTAINTIES]
Incertitudes majeurs globales
[GLOBAL_CONSENSUS_KPI]
Pourcentage de consensus global (ex: 74 %)
[GLOBAL_CONSENSUS_NOTE]
Commentaire court sur le consensus (ex: Accord modéré à bon)
[GLOBAL_SCENARIO_KPI]
Nom court du scénario dominant (ex: Chaud)
[GLOBAL_SCENARIO_NOTE]
Commentaire court sur le scénario (ex: Puis plus instable)
[GLOBAL_CARDS_KPI]
Nombre de cartes analysées (ex: 6)
[GLOBAL_CARDS_NOTE]
Détail court (ex: 3 par semaine)
[GLOBAL_UNCERTAINTY_KPI]
Nom de l'incertitude majeure (ex: Timing)
[GLOBAL_UNCERTAINTY_NOTE]
Commentaire court sur l'incertitude (ex: Dégradation encore mobile)
[LINKEDIN_POST]
Post LinkedIn complet prêt à copier-coller
[GLOBAL_END]

[DOUBTS_START]
[DOUBTS_TIMING]
Incertitudes de calendrier (échéances)
[DOUBTS_LOCATION]
Incertitudes de localisation
[DOUBTS_INTENSITY]
Incertitudes d'intensité
[MISSING_INFORMATION]
Informations manquantes
[LOW_DOCUMENTED_MODELS]
Modèles trop peu commentés
[UNCERTAIN_IMAGES]
Images difficiles à interpréter
[DOUBTS_END]
"""

    user_prompt = f"""Date actuelle de génération : {today_str}
Saison en France : {saison_actuelle.upper()}

=== PRÉCÉDENT BULLETIN (POUR COMPARAISON) ===
{last_bulletin_context}
============================================

=== DISCUSSIONS SEMAINE 1 ({jours_restants_cours_str}) ===
{week1_data["comments_text"]}

=== DISCUSSIONS SEMAINE 2 ({semaine_suivante_str}) ===
{week2_data["comments_text"]}
"""

    response = call_llm(system_prompt, user_prompt)
    if not response:
        print("[LLM] ERREUR : Pas de réponse du LLM.")
        sys.exit(1)

    w1_text = re.search(r'\[WEEK_1_START\](.*?)\[WEEK_1_END\]', response, re.DOTALL)
    w2_text = re.search(r'\[WEEK_2_START\](.*?)\[WEEK_2_END\]', response, re.DOTALL)
    global_text = re.search(r'\[GLOBAL_START\](.*?)\[GLOBAL_END\]', response, re.DOTALL)
    doubts_text = re.search(r'\[DOUBTS_START\](.*?)\[DOUBTS_END\]', response, re.DOTALL)
    what_changed = extract_tag(response, "WHAT_CHANGED_SINCE_LAST")

    w1_content = w1_text.group(1) if w1_text else ""
    w2_content = w2_text.group(1) if w2_text else ""
    global_content = global_text.group(1) if global_text else ""
    doubts_content = doubts_text.group(1) if doubts_text else ""

    def format_key_point(key_str):
        if not key_str:
            return ""
        key_str = key_str.strip()
        emoji = "💡"
        
        # Détection d'emoji
        emoji_match = re.match(r'^([\U00010000-\U0010ffff]|\u2600-\u27bf)\s*', key_str)
        if emoji_match:
            emoji = emoji_match.group(1)
            key_str = key_str[emoji_match.end():].strip()
        else:
            lower = key_str.lower()
            if any(w in lower for w in ["temp", "chaud", "chaleur", "degré"]):
                emoji = "🌡️"
            elif any(w in lower for w in ["orage", "foudre"]):
                emoji = "⛈️"
            elif any(w in lower for w in ["pluie", "averse", "humide", "eau"]):
                emoji = "🌦️"
            elif any(w in lower for w in ["vent", "rafale"]):
                emoji = "💨"
            elif any(w in lower for w in ["soleil", "beau", "sec"]):
                emoji = "☀️"
            elif any(w in lower for w in ["nuage", "couvert", "gris"]):
                emoji = "☁️"
            elif any(w in lower for w in ["ouest", "atlantique", "manche"]):
                emoji = "🧭"
            elif any(w in lower for w in ["fiab", "confiance", "accord", "consensus"]):
                emoji = "🤝"
                
        parts = key_str.split(":", 1)
        if len(parts) == 2:
            title = parts[0].strip()
            desc = parts[1].strip()
        else:
            words = key_str.split()
            if len(words) > 3:
                title = " ".join(words[:2])
                desc = " ".join(words[2:])
            else:
                title = key_str
                desc = ""
        return f'<div class="key"><i>{emoji}</i><div><strong>{title}</strong>{desc}</div></div>'

    # Semaine 1
    w1_dates = extract_tag(w1_content, "W1_DATES") or jours_restants_cours_str
    w1_keys = [extract_tag(w1_content, f"W1_KEY_POINT_{i}") for i in range(1, 7)]
    w1_keys_html = "".join([format_key_point(k) for k in w1_keys if k])
    w1_models = parse_models(w1_content, "W1")
    w1_models_html = build_model_cards(w1_models)
    w1_images_info = parse_images_info(w1_content, "W1")
    w1_images_html = build_image_cards(w1_images_info, week1_data["images"])

    # Semaine 2
    w2_dates = extract_tag(w2_content, "W2_DATES") or semaine_suivante_str
    w2_keys = [extract_tag(w2_content, f"W2_KEY_POINT_{i}") for i in range(1, 7)]
    w2_keys_html = "".join([format_key_point(k) for k in w2_keys if k])
    w2_models = parse_models(w2_content, "W2")
    w2_models_html = build_model_cards(w2_models)
    w2_images_info = parse_images_info(w2_content, "W2")
    w2_images_html = build_image_cards(w2_images_info, week2_data["images"])

    # Extraction des KPIs globaux du header
    kpi_consensus_val = extract_tag(global_content, "GLOBAL_CONSENSUS_KPI") or "75 %"
    kpi_consensus_note = extract_tag(global_content, "GLOBAL_CONSENSUS_NOTE") or "Accord modéré"
    kpi_scenario_val = extract_tag(global_content, "GLOBAL_SCENARIO_KPI") or "Chaud"
    kpi_scenario_note = extract_tag(global_content, "GLOBAL_SCENARIO_NOTE") or "Puis plus instable"
    kpi_cards_val = extract_tag(global_content, "GLOBAL_CARDS_KPI") or str(len(week1_data["images"]) + len(week2_data["images"]))
    kpi_cards_note = extract_tag(global_content, "GLOBAL_CARDS_NOTE") or "Cartes clés"
    kpi_uncertainty_val = extract_tag(global_content, "GLOBAL_UNCERTAINTY_KPI") or "Timing"
    kpi_uncertainty_note = extract_tag(global_content, "GLOBAL_UNCERTAINTY_NOTE") or "Dégradation encore mobile"

    # Extraction des confiances et températures pour l'historique
    try:
        w1_conf_val = int(re.search(r'\d+', w1_models[0].get("confidence", "80")).group(0)) if w1_models else 80
    except Exception:
        w1_conf_val = 80
        
    w1_temp_val = w1_models[0].get("temperatures", "De saison") if w1_models else "De saison"

    try:
        w2_conf_val = int(re.search(r'\d+', w2_models[0].get("confidence", "70")).group(0)) if w2_models else 70
    except Exception:
        w2_conf_val = 70
        
    w2_temp_val = w2_models[0].get("temperatures", "De saison") if w2_models else "De saison"

    # Enregistrement
    run_record = {
        "date_generation": today_str,
        "w1_confidence": w1_conf_val,
        "w1_temp": w1_temp_val,
        "w2_confidence": w2_conf_val,
        "w2_temp": w2_temp_val,
        "global_summary": extract_tag(global_content, "GLOBAL_15_DAY_TREND")
    }
    
    os.makedirs("history", exist_ok=True)
    os.makedirs("data", exist_ok=True)
    
    date_fn = now.strftime('%Y-%m-%d_%H-%M')
    with open(f"history/{date_fn}.json", "w", encoding="utf-8") as f_hist:
        json.dump(run_record, f_hist, ensure_ascii=False, indent=2)
    with open(last_bulletin_path, "w", encoding="utf-8") as f_last:
        json.dump(run_record, f_last, ensure_ascii=False, indent=2)

    sparkline_conf_html, temp_evolution_html = generate_sparklines_html()

    # Section Ce qui a changé
    what_changed_box = ""
    if what_changed:
        what_changed_box = f"""
        <div class="section">
            <h2>📈 Ce qui a changé depuis le précédent bulletin</h2>
            <div class="notice" style="background:#eff6ff; color:#1e40af; border-color:#bfdbfe;">
                {what_changed}
            </div>
        </div>
        """

    linkedin_raw = extract_tag(global_content, "LINKEDIN_POST")
    linkedin_clean = linkedin_raw.replace('<br>', '\n').replace('<br/>', '\n')

    style = """
    :root{
      --bg:#eef4f8;
      --surface:#ffffff;
      --surface-2:#f8fbfd;
      --ink:#13273a;
      --muted:#64788c;
      --line:#dce6ee;
      --navy:#0d2f4f;
      --blue:#1565d8;
      --cyan:#1ea7c9;
      --green:#23936b;
      --amber:#df9d32;
      --red:#d85b58;
      --shadow:0 18px 50px rgba(18,55,88,.10);
      --r-xl:28px;
      --r-lg:20px;
      --r-md:14px;
    }
    *{box-sizing:border-box}
    html{scroll-behavior:smooth}
    body{
      margin:0;
      background:
        radial-gradient(circle at 12% 0%,rgba(30,167,201,.12),transparent 28%),
        radial-gradient(circle at 90% 0%,rgba(21,101,216,.11),transparent 30%),
        var(--bg);
      color:var(--ink);
      font-family:Inter,ui-sans-serif,-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif;
      line-height:1.5;
    }
    button{font:inherit}
    img{max-width:100%;display:block}
    .page{width:min(1180px,calc(100% - 24px));margin:20px auto 50px}
    .hero{
      position:relative;
      overflow:hidden;
      padding:40px;
      border-radius:32px;
      color:white;
      background:
        linear-gradient(135deg,rgba(8,38,67,.98),rgba(15,79,126,.96) 58%,rgba(26,150,177,.94)),
        radial-gradient(circle at 80% 20%,rgba(255,255,255,.08),transparent 30%);
      box-shadow:var(--shadow);
    }
    .hero:after{
      content:"";
      position:absolute;
      width:380px;height:380px;
      right:-120px;top:-140px;
      border-radius:50%;
      background:radial-gradient(circle,rgba(131,228,244,.35),transparent 68%);
    }
    .hero-inner{position:relative;z-index:2}
    .hero-top{display:flex;justify-content:space-between;gap:18px;align-items:flex-start}
    .brand{display:flex;gap:12px;align-items:center;font-weight:900;letter-spacing:.08em;text-transform:uppercase;font-size:13px}
    .brand-icon{width:42px;height:42px;display:grid;place-items:center;border-radius:14px;background:rgba(255,255,255,.12);border:1px solid rgba(255,255,255,.18);font-size:22px}
    .demo{padding:8px 12px;border-radius:999px;background:rgba(255,255,255,.12);border:1px solid rgba(255,255,255,.18);font-size:12px;font-weight:800}
    .hero h1{margin:32px 0 10px;font-size:clamp(32px,5vw,52px);line-height:1.1;letter-spacing:-.045em}
    .hero p{max-width:830px;margin:0;color:#e4f1f8;font-size:16px}
    .meta{display:flex;flex-wrap:wrap;gap:10px;margin-top:26px}
    .meta span{padding:9px 13px;border-radius:999px;background:rgba(255,255,255,.10);border:1px solid rgba(255,255,255,.16);font-size:12px;font-weight:800}
    .kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-top:18px}
    .kpi{
      padding:20px;
      border-radius:20px;
      background:rgba(255,255,255,.11);
      border:1px solid rgba(255,255,255,.16);
      backdrop-filter:blur(10px);
    }
    .kpi-label{font-size:11px;text-transform:uppercase;letter-spacing:.08em;color:#cfe5f1;font-weight:900}
    .kpi-value{font-size:30px;line-height:1.1;font-weight:900;margin-top:5px}
    .kpi-note{font-size:12px;color:#dcebf3;margin-top:5px}
    .tabs{
      display:grid;
      grid-template-columns:repeat(4,1fr);
      gap:10px;
      margin:20px 0 0;
      position:sticky;
      top:8px;
      z-index:20;
    }
    .tabs button{
      padding:14px 12px;
      border:1px solid var(--line);
      border-radius:14px;
      background:rgba(255,255,255,.96);
      color:#496176;
      font-weight:900;
      cursor:pointer;
      box-shadow:0 6px 18px rgba(18,55,88,.06);
      transition: all 0.2s ease;
    }
    .tabs button:hover{background:#f8fbfd;}
    .tabs button.active{background:var(--navy);color:#fff;border-color:var(--navy)}
    .panel{display:none}
    .panel.active{display:block}
    .section{
      margin-top:18px;
      padding:28px;
      border-radius:var(--r-xl);
      background:rgba(255,255,255,.96);
      border:1px solid rgba(215,227,237,.95);
      box-shadow:0 12px 34px rgba(18,55,88,.07);
    }
    .section-head{display:flex;justify-content:space-between;gap:18px;align-items:flex-end;margin-bottom:20px}
    .section h2{margin:0;font-size:clamp(22px,3vw,30px);line-height:1.1;letter-spacing:-.03em}
    .section .sub{margin:7px 0 0;color:var(--muted)}
    .badge{display:inline-flex;align-items:center;gap:6px;padding:7px 10px;border-radius:999px;background:#eaf3fb;color:#205d90;font-size:11px;font-weight:900;text-transform:uppercase;letter-spacing:.06em}
    .grid{display:grid;gap:14px}
    .grid-2{grid-template-columns:repeat(2,minmax(0,1fr))}
    .grid-3{grid-template-columns:repeat(3,minmax(0,1fr))}
    .grid-4{grid-template-columns:repeat(4,minmax(0,1fr))}
    .card{
      padding:20px;
      border-radius:18px;
      border:1px solid var(--line);
      background:var(--surface-2);
    }
    .card h3{margin:0 0 8px;font-size:18px}
    .card p{margin:0;color:var(--muted);font-size:14px}
    .key{
      display:flex;
      gap:12px;
      align-items:flex-start;
      padding:18px;
      border-radius:17px;
      background:#f3f8fc;
      border:1px solid var(--line);
    }
    .key i{
      width:36px;height:36px;display:grid;place-items:center;flex:0 0 auto;
      border-radius:12px;background:#e5f1fb;font-style:normal;font-size:20px
    }
    .key strong{display:block;margin-bottom:4px}
    .model-table{
      width:100%;
      border-collapse:separate;
      border-spacing:0 10px;
    }
    .model-table th{
      padding:0 12px 8px;
      text-align:left;
      color:var(--muted);
      font-size:11px;
      text-transform:uppercase;
      letter-spacing:.08em;
    }
    .model-table td{
      padding:16px 12px;
      background:#f8fbfd;
      border-top:1px solid var(--line);
      border-bottom:1px solid var(--line);
      vertical-align:top;
      font-size:14px;
    }
    .model-table td:first-child{border-left:1px solid var(--line);border-radius:14px 0 0 14px}
    .model-table td:last-child{border-right:1px solid var(--line);border-radius:0 14px 14px 0}
    .model-name{font-weight:900;color:var(--navy)}
    .score{font-size:22px;font-weight:900}
    .bar{height:8px;background:#e7eef4;border-radius:999px;overflow:hidden;margin-top:7px}
    .fill{height:100%;border-radius:999px;}
    .chips{display:flex;flex-wrap:wrap;gap:6px;margin-top:8px}
    .chip{padding:5px 8px;border-radius:999px;background:#eaf3fb;color:#315f83;font-size:10px;font-weight:800}
    .compare{
      display:grid;
      grid-template-columns:1fr 1fr;
      gap:14px;
    }
    .compare .card:first-child{border-top:5px solid var(--green)}
    .compare .card:last-child{border-top:5px solid var(--amber)}
    .zones{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}
    .zone{
      min-height:210px;
      padding:20px;
      border-radius:18px;
      border:1px solid var(--line);
      background:#fbfdff;
    }
    .zone-icon{font-size:28px}
    .zone h3{margin:8px 0 8px}
    .zone p{margin:0;color:var(--muted);font-size:14px}
    .zone-foot{display:flex;justify-content:space-between;gap:10px;margin-top:14px;padding-top:12px;border-top:1px solid var(--line);font-size:11px;font-weight:800;color:#526d82}
    .timeline{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}
    .phase{
      min-height:155px;
      padding:18px;
      border-radius:17px;
      border:1px solid var(--line);
      background:linear-gradient(180deg,#fbfdff,#f3f8fc);
    }
    .phase b{display:block;color:var(--blue);margin-bottom:8px}
    .phase p{margin:0;color:var(--muted);font-size:14px}
    .cards3{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}
    .image-card{overflow:hidden;border-radius:18px;border:1px solid var(--line);background:white}
    .image-demo{
      height:220px;
      display:grid;
      place-items:center;
      padding:20px;
      text-align:center;
      background:
        radial-gradient(circle at 20% 20%,rgba(21,101,216,.18),transparent 25%),
        radial-gradient(circle at 80% 30%,rgba(216,91,88,.15),transparent 24%),
        linear-gradient(135deg,#eef4f8,#dce8f1);
      color:#4e687d;
      font-weight:900;
    }
    .image-caption{padding:18px}
    .image-caption h3{margin:0 0 8px}
    .image-caption p{margin:0;color:var(--muted);font-size:13px}
    .image-meta{display:flex;gap:6px;flex-wrap:wrap;margin-top:10px}
    .alert{
      padding:18px;
      border-radius:17px;
      background:#fff8e7;
      border:1px solid #f2ddb0;
      color:#7a591d;
      font-weight:700;
    }
    .linkedin{
      padding:24px;
      border-radius:20px;
      background:#0d2f4f;
      color:white;
      white-space:pre-wrap;
      line-height:1.65;
      font-size:15px;
    }
    .copy{
      margin-top:12px;padding:11px 16px;border:0;border-radius:11px;
      background:var(--blue);color:white;font-weight:900;cursor:pointer;
      transition: background 0.15s ease;
    }
    .copy:hover{background:#114fa8}
    .footer{padding:24px 8px 0;text-align:center;color:#6a7d8f;font-size:12px}

    /* History Box and Sparklines */
    .evolution-card {
        background: var(--surface-2);
        border: 1px solid var(--line);
        border-radius: 18px;
        padding: 20px;
    }
    .sparkline {
        font-family: monospace;
        font-size: 13px;
        line-height: 1.5;
        color: var(--ink);
        background: #ffffff;
        border: 1px solid var(--line);
        border-radius: 10px;
        padding: 12px;
        margin-top: 8px;
    }
    .sparkline-row {
        display: flex;
        justify-content: space-between;
        margin-bottom: 4px;
    }
    .trend-pill {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 11px;
        font-weight: 700;
    }
    .trend-up { background: #dcfce7; color: #166534; }
    .trend-down { background: #fee2e2; color: #991b1b; }

    @media(max-width:950px){
      .kpis,.grid-4{grid-template-columns:repeat(2,1fr)}
      .grid-3,.zones,.cards3,.timeline{grid-template-columns:repeat(2,1fr)}
      .model-table{display:block;overflow-x:auto}
    }
    @media(max-width:650px){
      .page{width:min(100% - 14px,1180px);margin:7px auto 30px}
      .hero{padding:24px;border-radius:22px}
      .tabs{grid-template-columns:repeat(2,1fr);top:4px}
      .section{padding:20px;border-radius:22px}
      .section-head{align-items:flex-start;flex-direction:column}
    }
    @media print{
      body{background:white}
      .tabs{display:none}
      .panel{display:block!important}
      .section,.hero{box-shadow:none;break-inside:avoid}
    }
    """

    html_template = """<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Tendances météo France — Bulletin premium</title>
[STYLE_PLACEHOLDER]
</head>
<body>
<main class="page">

<header class="hero">
  <div class="hero-inner">
    <div class="hero-top">
      <div class="brand"><div class="brand-icon">🌦️</div>Tendances météo France</div>
      <div class="demo">Monsieur Météo</div>
    </div>
    <h1>Deux semaines de tendance, en un regard</h1>
    <p>Comparaison des modèles météo, temps sensible par grandes zones, niveau de confiance, cartes clés, points solides et incertitudes.</p>
    <div class="meta">
      <span>Semaine 1 : [W1_DATES_PLACEHOLDER]</span>
      <span>Semaine 2 : [W2_DATES_PLACEHOLDER]</span>
      <span>Génération : [TODAY_STR_PLACEHOLDER]</span>
    </div>
    <div class="kpis">
      <div class="kpi"><div class="kpi-label">Consensus général</div><div class="kpi-value">[GLOBAL_CONSENSUS_KPI_PLACEHOLDER]</div><div class="kpi-note">[GLOBAL_CONSENSUS_NOTE_PLACEHOLDER]</div></div>
      <div class="kpi"><div class="kpi-label">Scénario dominant</div><div class="kpi-value">[GLOBAL_SCENARIO_KPI_PLACEHOLDER]</div><div class="kpi-note">[GLOBAL_SCENARIO_NOTE_PLACEHOLDER]</div></div>
      <div class="kpi"><div class="kpi-label">Cartes retenues</div><div class="kpi-value">[GLOBAL_CARDS_KPI_PLACEHOLDER]</div><div class="kpi-note">[GLOBAL_CARDS_NOTE_PLACEHOLDER]</div></div>
      <div class="kpi"><div class="kpi-label">Incertitude majeure</div><div class="kpi-value">[GLOBAL_UNCERTAINTY_KPI_PLACEHOLDER]</div><div class="kpi-note">[GLOBAL_UNCERTAINTY_NOTE_PLACEHOLDER]</div></div>
    </div>
  </div>
</header>

<nav class="tabs">
  <button class="active" data-tab="week1">Semaine 1</button>
  <button data-tab="week2">Semaine 2</button>
  <button data-tab="summary">Synthèse 15 jours</button>
  <button data-tab="doubts">Doutes et limites</button>
</nav>

<section id="week1" class="panel active">
  <div class="section">
    <div class="section-head">
      <div><span class="badge">À retenir</span><h2>Semaine 1</h2><p class="sub">Les informations principales.</p></div>
    </div>
    <div class="grid grid-4">
      [W1_KEYS_HTML_PLACEHOLDER]
    </div>
  </div>

  <div class="section">
    <div class="section-head">
      <div><span class="badge">Comparateur</span><h2>Ce que disent les modèles</h2><p class="sub">Lecture synthétique, modèle par modèle.</p></div>
    </div>
    <table class="model-table">
      <thead><tr><th>Modèle</th><th>Scénario</th><th>Temps sensible</th><th>Zones</th><th>Confiance d’extraction</th></tr></thead>
      <tbody>
        [W1_MODELS_HTML_PLACEHOLDER]
      </tbody>
    </table>
  </div>

  <div class="section">
    <div class="section-head"><div><span class="badge">Analyse</span><h2>Convergences et divergences</h2></div></div>
    <div class="compare">
      <div class="card"><h3>Ce qui converge</h3><p>[W1_CONVERGENCES_PLACEHOLDER]</p></div>
      <div class="card"><h3>Ce qui diverge</h3><p>[W1_DIVERGENCES_PLACEHOLDER]</p></div>
    </div>
  </div>

  <div class="section">
    <div class="section-head">
      <div><span class="badge">Temps sensible</span><h2>Prévision par grandes zones</h2><p class="sub">Ce que le public doit comprendre immédiatement.</p></div>
    </div>
    <div class="zones">
      <div class="zone"><div class="zone-icon">🧭</div><h3>Ouest et Atlantique</h3><p>[W1_ZONE_WEST_PLACEHOLDER]</p><div class="zone-foot"><span>[W1_ZONE_WEST_CONF_PLACEHOLDER]</span></div></div>
      <div class="zone"><div class="zone-icon">☁️</div><h3>Nord et Nord-Ouest</h3><p>[W1_ZONE_NORTH_PLACEHOLDER]</p><div class="zone-foot"><span>[W1_ZONE_NORTH_CONF_PLACEHOLDER]</span></div></div>
      <div class="zone"><div class="zone-icon">🌤️</div><h3>Nord-Est</h3><p>[W1_ZONE_NORTHEAST_PLACEHOLDER]</p><div class="zone-foot"><span>[W1_ZONE_NORTHEAST_CONF_PLACEHOLDER]</span></div></div>
      <div class="zone"><div class="zone-icon">🌥️</div><h3>Centre</h3><p>[W1_ZONE_CENTRAL_PLACEHOLDER]</p><div class="zone-foot"><span>[W1_ZONE_CENTRAL_CONF_PLACEHOLDER]</span></div></div>
      <div class="zone"><div class="zone-icon">🌡️</div><h3>Sud-Ouest</h3><p>[W1_ZONE_SOUTHWEST_PLACEHOLDER]</p><div class="zone-foot"><span>[W1_ZONE_SOUTHWEST_CONF_PLACEHOLDER]</span></div></div>
      <div class="zone"><div class="zone-icon">☀️</div><h3>Sud-Est et Méditerranée</h3><p>[W1_ZONE_SOUTHEAST_PLACEHOLDER]</p><div class="zone-foot"><span>[W1_ZONE_SOUTHEAST_CONF_PLACEHOLDER]</span></div></div>
      <div class="zone"><div class="zone-icon">🏖️</div><h3>Corse</h3><p>[W1_ZONE_CORSICA_PLACEHOLDER]</p><div class="zone-foot"><span>[W1_ZONE_CORSICA_CONF_PLACEHOLDER]</span></div></div>
    </div>
  </div>

  <div class="section">
    <div class="section-head"><div><span class="badge">Chronologie</span><h2>Déroulé de la semaine</h2></div></div>
    <div class="timeline">
      <div class="phase"><b>[W1_PHASE_1_DATES_PLACEHOLDER]</b><p>[W1_PHASE_1_PLACEHOLDER]</p></div>
      <div class="phase"><b>[W1_PHASE_2_DATES_PLACEHOLDER]</b><p>[W1_PHASE_2_PLACEHOLDER]</p></div>
      <div class="phase"><b>[W1_PHASE_3_DATES_PLACEHOLDER]</b><p>[W1_PHASE_3_PLACEHOLDER]</p></div>
      <div class="phase"><b>[W1_PHASE_4_DATES_PLACEHOLDER]</b><p>[W1_PHASE_4_PLACEHOLDER]</p></div>
    </div>
  </div>

  <div class="section">
    <div class="section-head"><div><span class="badge">Fiabilité</span><h2>Points solides et points fragiles</h2></div></div>
    <div class="compare">
      <div class="card"><h3>Éléments solides</h3><p>[W1_SOLID_POINTS_PLACEHOLDER]</p></div>
      <div class="card"><h3>Éléments fragiles</h3><p>[W1_FRAGILE_POINTS_PLACEHOLDER]</p></div>
    </div>
    <div class="alert" style="margin-top:14px">À surveiller dans les prochains runs : [W1_NEXT_RUNS_TO_WATCH_PLACEHOLDER]</div>
  </div>

  <div class="section">
    <div class="section-head"><div><span class="badge">3 cartes clés</span><h2>Les images les plus intéressantes</h2><p class="sub">Les images réelles récoltées du forum.</p></div></div>
    <div class="cards3">
      [W1_IMAGES_HTML_PLACEHOLDER]
    </div>
  </div>
</section>

<section id="week2" class="panel">
  <div class="section">
    <div class="section-head">
      <div><span class="badge">À retenir</span><h2>Semaine 2</h2><p class="sub">Les informations principales.</p></div>
    </div>
    <div class="grid grid-4">
      [W2_KEYS_HTML_PLACEHOLDER]
    </div>
  </div>

  <div class="section">
    <div class="section-head">
      <div><span class="badge">Comparateur</span><h2>Ce que disent les modèles</h2><p class="sub">Lecture synthétique, modèle par modèle.</p></div>
    </div>
    <table class="model-table">
      <thead><tr><th>Modèle</th><th>Scénario</th><th>Temps sensible</th><th>Zones</th><th>Confiance d’extraction</th></tr></thead>
      <tbody>
        [W2_MODELS_HTML_PLACEHOLDER]
      </tbody>
    </table>
  </div>

  <div class="section">
    <div class="section-head"><div><span class="badge">Analyse</span><h2>Convergences et divergences</h2></div></div>
    <div class="compare">
      <div class="card"><h3>Ce qui converge</h3><p>[W2_CONVERGENCES_PLACEHOLDER]</p></div>
      <div class="card"><h3>Ce qui diverge</h3><p>[W2_DIVERGENCES_PLACEHOLDER]</p></div>
    </div>
  </div>

  <div class="section">
    <div class="section-head">
      <div><span class="badge">Temps sensible</span><h2>Prévision par grandes zones</h2><p class="sub">Ce que le public doit comprendre immédiatement.</p></div>
    </div>
    <div class="zones">
      <div class="zone"><div class="zone-icon">🧭</div><h3>Ouest et Atlantique</h3><p>[W2_ZONE_WEST_PLACEHOLDER]</p><div class="zone-foot"><span>[W2_ZONE_WEST_CONF_PLACEHOLDER]</span></div></div>
      <div class="zone"><div class="zone-icon">☁️</div><h3>Nord et Nord-Ouest</h3><p>[W2_ZONE_NORTH_PLACEHOLDER]</p><div class="zone-foot"><span>[W2_ZONE_NORTH_CONF_PLACEHOLDER]</span></div></div>
      <div class="zone"><div class="zone-icon">🌤️</div><h3>Nord-Est</h3><p>[W2_ZONE_NORTHEAST_PLACEHOLDER]</p><div class="zone-foot"><span>[W2_ZONE_NORTHEAST_CONF_PLACEHOLDER]</span></div></div>
      <div class="zone"><div class="zone-icon">🌥️</div><h3>Centre</h3><p>[W2_ZONE_CENTRAL_PLACEHOLDER]</p><div class="zone-foot"><span>[W2_ZONE_CENTRAL_CONF_PLACEHOLDER]</span></div></div>
      <div class="zone"><div class="zone-icon">🌡️</div><h3>Sud-Ouest</h3><p>[W2_ZONE_SOUTHWEST_PLACEHOLDER]</p><div class="zone-foot"><span>[W2_ZONE_SOUTHWEST_CONF_PLACEHOLDER]</span></div></div>
      <div class="zone"><div class="zone-icon">☀️</div><h3>Sud-Est et Méditerranée</h3><p>[W2_ZONE_SOUTHEAST_PLACEHOLDER]</p><div class="zone-foot"><span>[W2_ZONE_SOUTHEAST_CONF_PLACEHOLDER]</span></div></div>
      <div class="zone"><div class="zone-icon">🏖️</div><h3>Corse</h3><p>[W2_ZONE_CORSICA_PLACEHOLDER]</p><div class="zone-foot"><span>[W2_ZONE_CORSICA_CONF_PLACEHOLDER]</span></div></div>
    </div>
  </div>

  <div class="section">
    <div class="section-head"><div><span class="badge">Chronologie</span><h2>Déroulé de la semaine</h2></div></div>
    <div class="timeline">
      <div class="phase"><b>[W2_PHASE_1_DATES_PLACEHOLDER]</b><p>[W2_PHASE_1_PLACEHOLDER]</p></div>
      <div class="phase"><b>[W2_PHASE_2_DATES_PLACEHOLDER]</b><p>[W2_PHASE_2_PLACEHOLDER]</p></div>
      <div class="phase"><b>[W2_PHASE_3_DATES_PLACEHOLDER]</b><p>[W2_PHASE_3_PLACEHOLDER]</p></div>
      <div class="phase"><b>[W2_PHASE_4_DATES_PLACEHOLDER]</b><p>[W2_PHASE_4_PLACEHOLDER]</p></div>
    </div>
  </div>

  <div class="section">
    <div class="section-head"><div><span class="badge">Fiabilité</span><h2>Points solides et points fragiles</h2></div></div>
    <div class="compare">
      <div class="card"><h3>Éléments solides</h3><p>[W2_SOLID_POINTS_PLACEHOLDER]</p></div>
      <div class="card"><h3>Éléments fragiles</h3><p>[W2_FRAGILE_POINTS_PLACEHOLDER]</p></div>
    </div>
    <div class="alert" style="margin-top:14px">À surveiller dans les prochains runs : [W2_NEXT_RUNS_TO_WATCH_PLACEHOLDER]</div>
  </div>

  <div class="section">
    <div class="section-head"><div><span class="badge">3 cartes clés</span><h2>Les images les plus intéressantes</h2><p class="sub">Les images réelles récoltées du forum.</p></div></div>
    <div class="cards3">
      [W2_IMAGES_HTML_PLACEHOLDER]
    </div>
  </div>
</section>

<section id="summary" class="panel">
  [WHAT_CHANGED_BOX_PLACEHOLDER]

  <div class="section">
    <div class="section-head"><div><span class="badge">Synthèse</span><h2>À retenir sur les deux semaines</h2></div></div>
    
    <div id="history-box" class="grid grid-2" style="margin-bottom:20px;">
        <div class="evolution-card">
            <h3>📈 Évolution de la confiance (Scénario Principal)</h3>
            <div class="sparkline">
                [SPARKLINE_CONF_PLACEHOLDER]
            </div>
        </div>
        <div class="evolution-card">
            <h3>🌡️ Évolution des températures attendues</h3>
            <div class="sparkline">
                [TEMP_EVOLUTION_PLACEHOLDER]
            </div>
        </div>
    </div>

    <div class="grid grid-2">
      <div class="card"><h3>Évolution générale</h3><p>[GLOBAL_15_DAY_TREND_PLACEHOLDER]</p></div>
      <div class="card"><h3>Semaine la plus fiable</h3><p>[MOST_RELIABLE_WEEK_PLACEHOLDER]</p></div>
      <div class="card"><h3>Phénomènes récurrents</h3><p>[GLOBAL_RECURRING_PHENOMENA_PLACEHOLDER]</p></div>
      <div class="card"><h3>Incertitude majeure</h3><p>[GLOBAL_MAJOR_UNCERTAINTIES_PLACEHOLDER]</p></div>
    </div>
  </div>

  <div class="section">
    <div class="section-head"><div><span class="badge">Réseaux sociaux</span><h2>Post LinkedIn prêt à copier-coller</h2></div></div>
    <div id="linkedin" class="linkedin">[LINKEDIN_CLEAN_PLACEHOLDER]</div>
    <button class="copy" onclick="copyLinkedIn()">Copier le post LinkedIn</button>
  </div>
</section>

<section id="doubts" class="panel">
  <div class="section">
    <div class="section-head"><div><span class="badge">Transparence</span><h2>Doutes, imprécisions et limites</h2></div></div>
    <div class="grid grid-2">
      <div class="card"><h3>Calendrier</h3><p>[DOUBTS_TIMING_PLACEHOLDER]</p></div>
      <div class="card"><h3>Localisation</h3><p>[DOUBTS_LOCATION_PLACEHOLDER]</p></div>
      <div class="card"><h3>Intensité</h3><p>[DOUBTS_INTENSITY_PLACEHOLDER]</p></div>
      <div class="card"><h3>Données manquantes</h3><p>[MISSING_INFORMATION_PLACEHOLDER]</p></div>
      <div class="card"><h3>Modèles peu documentés</h3><p>[LOW_DOCUMENTED_MODELS_PLACEHOLDER]</p></div>
      <div class="card"><h3>Images incertaines</h3><p>[UNCERTAIN_IMAGES_PLACEHOLDER]</p></div>
    </div>
  </div>
</section>

<footer class="footer">
Bulletin généré automatiquement à partir des messages et images du forum Infoclimat.
</footer>

</main>

<script>
const buttons=document.querySelectorAll('.tabs button');
const panels=document.querySelectorAll('.panel');
buttons.forEach(btn=>{
  btn.addEventListener('click',()=>{
    buttons.forEach(b=>b.classList.remove('active'));
    panels.forEach(p=>p.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById(btn.dataset.tab).classList.add('active');
    window.scrollTo({top:document.querySelector('.tabs').offsetTop-8,behavior:'smooth'});
  });
});
function copyLinkedIn(){
  const text=document.getElementById('linkedin').innerText;
  navigator.clipboard.writeText(text).then(()=>{
    const btn=document.querySelector('.copy');
    const old=btn.textContent;
    btn.textContent='Post copié';
    setTimeout(()=>btn.textContent=old,1500);
  });
}
</script>
</body>
</html>
"""

    # Remplacement des variables dans le template
    html = html_template
    html = html.replace("[STYLE_PLACEHOLDER]", f"<style>\n{style}\n</style>")
    html = html.replace("[W1_DATES_PLACEHOLDER]", w1_dates)
    html = html.replace("[W2_DATES_PLACEHOLDER]", w2_dates)
    html = html.replace("[TODAY_STR_PLACEHOLDER]", today_str)
    
    html = html.replace("[W1_KEYS_HTML_PLACEHOLDER]", w1_keys_html)
    html = html.replace("[W1_MODELS_HTML_PLACEHOLDER]", w1_models_html)
    html = html.replace("[W1_IMAGES_HTML_PLACEHOLDER]", w1_images_html)
    
    html = html.replace("[W2_KEYS_HTML_PLACEHOLDER]", w2_keys_html)
    html = html.replace("[W2_MODELS_HTML_PLACEHOLDER]", w2_models_html)
    html = html.replace("[W2_IMAGES_HTML_PLACEHOLDER]", w2_images_html)
    
    html = html.replace("[W1_CONVERGENCES_PLACEHOLDER]", extract_tag(w1_content, "W1_CONVERGENCES") or "-")
    html = html.replace("[W1_DIVERGENCES_PLACEHOLDER]", extract_tag(w1_content, "W1_DIVERGENCES") or "-")
    
    html = html.replace("[W2_CONVERGENCES_PLACEHOLDER]", extract_tag(w2_content, "W2_CONVERGENCES") or "-")
    html = html.replace("[W2_DIVERGENCES_PLACEHOLDER]", extract_tag(w2_content, "W2_DIVERGENCES") or "-")

    # Zones Semaine 1
    html = html.replace("[W1_ZONE_WEST_PLACEHOLDER]", extract_tag(w1_content, "W1_ZONE_WEST") or "-")
    html = html.replace("[W1_ZONE_WEST_CONF_PLACEHOLDER]", extract_tag(w1_content, "W1_ZONE_WEST_CONF") or "-")
    html = html.replace("[W1_ZONE_NORTH_PLACEHOLDER]", extract_tag(w1_content, "W1_ZONE_NORTH") or "-")
    html = html.replace("[W1_ZONE_NORTH_CONF_PLACEHOLDER]", extract_tag(w1_content, "W1_ZONE_NORTH_CONF") or "-")
    html = html.replace("[W1_ZONE_NORTHEAST_PLACEHOLDER]", extract_tag(w1_content, "W1_ZONE_NORTHEAST") or "-")
    html = html.replace("[W1_ZONE_NORTHEAST_CONF_PLACEHOLDER]", extract_tag(w1_content, "W1_ZONE_NORTHEAST_CONF") or "-")
    html = html.replace("[W1_ZONE_CENTRAL_PLACEHOLDER]", extract_tag(w1_content, "W1_ZONE_CENTRAL") or "-")
    html = html.replace("[W1_ZONE_CENTRAL_CONF_PLACEHOLDER]", extract_tag(w1_content, "W1_ZONE_CENTRAL_CONF") or "-")
    html = html.replace("[W1_ZONE_SOUTHWEST_PLACEHOLDER]", extract_tag(w1_content, "W1_ZONE_SOUTHWEST") or "-")
    html = html.replace("[W1_ZONE_SOUTHWEST_CONF_PLACEHOLDER]", extract_tag(w1_content, "W1_ZONE_SOUTHWEST_CONF") or "-")
    html = html.replace("[W1_ZONE_SOUTHEAST_PLACEHOLDER]", extract_tag(w1_content, "W1_ZONE_SOUTHEAST") or "-")
    html = html.replace("[W1_ZONE_SOUTHEAST_CONF_PLACEHOLDER]", extract_tag(w1_content, "W1_ZONE_SOUTHEAST_CONF") or "-")
    html = html.replace("[W1_ZONE_CORSICA_PLACEHOLDER]", extract_tag(w1_content, "W1_ZONE_CORSICA") or "Informations insuffisantes dans les sources.")
    html = html.replace("[W1_ZONE_CORSICA_CONF_PLACEHOLDER]", extract_tag(w1_content, "W1_ZONE_CORSICA_CONF") or "-")

    # Zones Semaine 2
    html = html.replace("[W2_ZONE_WEST_PLACEHOLDER]", extract_tag(w2_content, "W2_ZONE_WEST") or "-")
    html = html.replace("[W2_ZONE_WEST_CONF_PLACEHOLDER]", extract_tag(w2_content, "W2_ZONE_WEST_CONF") or "-")
    html = html.replace("[W2_ZONE_NORTH_PLACEHOLDER]", extract_tag(w2_content, "W2_ZONE_NORTH") or "-")
    html = html.replace("[W2_ZONE_NORTH_CONF_PLACEHOLDER]", extract_tag(w2_content, "W2_ZONE_NORTH_CONF") or "-")
    html = html.replace("[W2_ZONE_NORTHEAST_PLACEHOLDER]", extract_tag(w2_content, "W2_ZONE_NORTHEAST") or "-")
    html = html.replace("[W2_ZONE_NORTHEAST_CONF_PLACEHOLDER]", extract_tag(w2_content, "W2_ZONE_NORTHEAST_CONF") or "-")
    html = html.replace("[W2_ZONE_CENTRAL_PLACEHOLDER]", extract_tag(w2_content, "W2_ZONE_CENTRAL") or "-")
    html = html.replace("[W2_ZONE_CENTRAL_CONF_PLACEHOLDER]", extract_tag(w2_content, "W2_ZONE_CENTRAL_CONF") or "-")
    html = html.replace("[W2_ZONE_SOUTHWEST_PLACEHOLDER]", extract_tag(w2_content, "W2_ZONE_SOUTHWEST") or "-")
    html = html.replace("[W2_ZONE_SOUTHWEST_CONF_PLACEHOLDER]", extract_tag(w2_content, "W2_ZONE_SOUTHWEST_CONF") or "-")
    html = html.replace("[W2_ZONE_SOUTHEAST_PLACEHOLDER]", extract_tag(w2_content, "W2_ZONE_SOUTHEAST") or "-")
    html = html.replace("[W2_ZONE_SOUTHEAST_CONF_PLACEHOLDER]", extract_tag(w2_content, "W2_ZONE_SOUTHEAST_CONF") or "-")
    html = html.replace("[W2_ZONE_CORSICA_PLACEHOLDER]", extract_tag(w2_content, "W2_ZONE_CORSICA") or "Informations insuffisantes dans les sources.")
    html = html.replace("[W2_ZONE_CORSICA_CONF_PLACEHOLDER]", extract_tag(w2_content, "W2_ZONE_CORSICA_CONF") or "-")

    # Chronologie Semaine 1
    html = html.replace("[W1_PHASE_1_DATES_PLACEHOLDER]", extract_tag(w1_content, "W1_PHASE_1_DATES") or "Phase 1")
    html = html.replace("[W1_PHASE_1_PLACEHOLDER]", extract_tag(w1_content, "W1_PHASE_1") or "-")
    html = html.replace("[W1_PHASE_2_DATES_PLACEHOLDER]", extract_tag(w1_content, "W1_PHASE_2_DATES") or "Phase 2")
    html = html.replace("[W1_PHASE_2_PLACEHOLDER]", extract_tag(w1_content, "W1_PHASE_2") or "-")
    html = html.replace("[W1_PHASE_3_DATES_PLACEHOLDER]", extract_tag(w1_content, "W1_PHASE_3_DATES") or "Phase 3")
    html = html.replace("[W1_PHASE_3_PLACEHOLDER]", extract_tag(w1_content, "W1_PHASE_3") or "-")
    html = html.replace("[W1_PHASE_4_DATES_PLACEHOLDER]", extract_tag(w1_content, "W1_PHASE_4_DATES") or "Phase 4")
    html = html.replace("[W1_PHASE_4_PLACEHOLDER]", extract_tag(w1_content, "W1_PHASE_4") or "-")

    # Chronologie Semaine 2
    html = html.replace("[W2_PHASE_1_DATES_PLACEHOLDER]", extract_tag(w2_content, "W2_PHASE_1_DATES") or "Phase 1")
    html = html.replace("[W2_PHASE_1_PLACEHOLDER]", extract_tag(w2_content, "W2_PHASE_1") or "-")
    html = html.replace("[W2_PHASE_2_DATES_PLACEHOLDER]", extract_tag(w2_content, "W2_PHASE_2_DATES") or "Phase 2")
    html = html.replace("[W2_PHASE_2_PLACEHOLDER]", extract_tag(w2_content, "W2_PHASE_2") or "-")
    html = html.replace("[W2_PHASE_3_DATES_PLACEHOLDER]", extract_tag(w2_content, "W2_PHASE_3_DATES") or "Phase 3")
    html = html.replace("[W2_PHASE_3_PLACEHOLDER]", extract_tag(w2_content, "W2_PHASE_3") or "-")
    html = html.replace("[W2_PHASE_4_DATES_PLACEHOLDER]", extract_tag(w2_content, "W2_PHASE_4_DATES") or "Phase 4")
    html = html.replace("[W2_PHASE_4_PLACEHOLDER]", extract_tag(w2_content, "W2_PHASE_4") or "-")

    # Solides / Fragiles
    html = html.replace("[W1_SOLID_POINTS_PLACEHOLDER]", extract_tag(w1_content, "W1_SOLID_POINTS") or "-")
    html = html.replace("[W1_FRAGILE_POINTS_PLACEHOLDER]", extract_tag(w1_content, "W1_FRAGILE_POINTS") or "-")
    html = html.replace("[W1_NEXT_RUNS_TO_WATCH_PLACEHOLDER]", extract_tag(w1_content, "W1_NEXT_RUNS_TO_WATCH") or "-")
    
    html = html.replace("[W2_SOLID_POINTS_PLACEHOLDER]", extract_tag(w2_content, "W2_SOLID_POINTS") or "-")
    html = html.replace("[W2_FRAGILE_POINTS_PLACEHOLDER]", extract_tag(w2_content, "W2_FRAGILE_POINTS") or "-")
    html = html.replace("[W2_NEXT_RUNS_TO_WATCH_PLACEHOLDER]", extract_tag(w2_content, "W2_NEXT_RUNS_TO_WATCH") or "-")

    # Synthèse globale et doutes
    html = html.replace("[GLOBAL_CONSENSUS_KPI_PLACEHOLDER]", kpi_consensus_val)
    html = html.replace("[GLOBAL_CONSENSUS_NOTE_PLACEHOLDER]", kpi_consensus_note)
    html = html.replace("[GLOBAL_SCENARIO_KPI_PLACEHOLDER]", kpi_scenario_val)
    html = html.replace("[GLOBAL_SCENARIO_NOTE_PLACEHOLDER]", kpi_scenario_note)
    html = html.replace("[GLOBAL_CARDS_KPI_PLACEHOLDER]", kpi_cards_val)
    html = html.replace("[GLOBAL_CARDS_NOTE_PLACEHOLDER]", kpi_cards_note)
    html = html.replace("[GLOBAL_UNCERTAINTY_KPI_PLACEHOLDER]", kpi_uncertainty_val)
    html = html.replace("[GLOBAL_UNCERTAINTY_NOTE_PLACEHOLDER]", kpi_uncertainty_note)

    html = html.replace("[GLOBAL_15_DAY_TREND_PLACEHOLDER]", extract_tag(global_content, "GLOBAL_15_DAY_TREND") or "-")
    html = html.replace("[MOST_RELIABLE_WEEK_PLACEHOLDER]", extract_tag(global_content, "MOST_RELIABLE_WEEK") or "-")
    html = html.replace("[GLOBAL_SOLID_POINTS_PLACEHOLDER]", extract_tag(global_content, "GLOBAL_SOLID_POINTS") or "-")
    html = html.replace("[GLOBAL_RECURRING_PHENOMENA_PLACEHOLDER]", extract_tag(global_content, "GLOBAL_RECURRING_PHENOMENA") or "-")
    html = html.replace("[GLOBAL_MAJOR_UNCERTAINTIES_PLACEHOLDER]", extract_tag(global_content, "GLOBAL_MAJOR_UNCERTAINTIES") or "-")
    
    html = html.replace("[DOUBTS_TIMING_PLACEHOLDER]", extract_tag(doubts_content, "DOUBTS_TIMING") or "-")
    html = html.replace("[DOUBTS_LOCATION_PLACEHOLDER]", extract_tag(doubts_content, "DOUBTS_LOCATION") or "-")
    html = html.replace("[DOUBTS_INTENSITY_PLACEHOLDER]", extract_tag(doubts_content, "DOUBTS_INTENSITY") or "-")
    html = html.replace("[MISSING_INFORMATION_PLACEHOLDER]", extract_tag(doubts_content, "MISSING_INFORMATION") or "-")
    html = html.replace("[LOW_DOCUMENTED_MODELS_PLACEHOLDER]", extract_tag(doubts_content, "LOW_DOCUMENTED_MODELS") or "-")
    html = html.replace("[UNCERTAIN_IMAGES_PLACEHOLDER]", extract_tag(doubts_content, "UNCERTAIN_IMAGES") or "-")

    html = html.replace("[LINKEDIN_CLEAN_PLACEHOLDER]", linkedin_clean)
    html = html.replace("[WHAT_CHANGED_BOX_PLACEHOLDER]", what_changed_box)
    html = html.replace("[SPARKLINE_CONF_PLACEHOLDER]", sparkline_conf_html)
    html = html.replace("[TEMP_EVOLUTION_PLACEHOLDER]", temp_evolution_html)

    html_path = "bulletin_infoclimat.html"
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"HTML généré avec succès : {html_path}")

    # Envoi email SMTP
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
    subject = f"Tendances de la semaine - {w1_dates.split('-')[0].strip()} & {w2_dates.split('-')[0].strip()}"
    clean_subj = unicodedata.normalize('NFKD', subject).encode('ASCII', 'ignore').decode('ASCII')
    subject = clean_subj
    
    filename = f"analyse_infoclimat_{datetime.datetime.now().strftime('%Y_%m_%d')}.html"
    
    # Version HTML pour le corps du mail (sans script, et avec tous les panneaux visibles)
    html_body = html
    # 1. Supprimer la balise script et son contenu
    html_body = re.sub(r'<script>.*?</script>', '', html_body, flags=re.DOTALL)
    # 2. Modifier le CSS pour afficher tous les panneaux et cacher la navigation par onglets
    html_body = html_body.replace('.panel{display:none}', '.panel{display:block !important;margin-bottom:30px}')
    html_body = html_body.replace('.tabs{', '.tabs{display:none !important;')

    html_b64 = base64.b64encode(html.encode('utf-8')).decode('ascii')
    html_body_b64 = base64.b64encode(html_body.encode('utf-8')).decode('ascii')
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
        f'Content-Type: text/html; charset=utf-8\r\n'
        f'Content-Transfer-Encoding: base64\r\n'
        f'\r\n'
        f'{html_body_b64}\r\n'
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
