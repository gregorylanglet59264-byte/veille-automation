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
            
        color = "#16a34a"
        if conf_val < 60:
            color = "#dc2626"
        elif conf_val < 75:
            color = "#d97706"
            
        card_html = f"""
        <article class="card accent">
            <div class="model-head">
                <div>
                    <h3>{model.get("name", "Modèle")}</h3>
                    <p>{model.get("timing", "-")}</p>
                </div>
                <div class="score" style="color: {color};">{conf_val}%</div>
            </div>
            <div class="bar"><div class="fill" style="width:{conf_val}%; background:{color};"></div></div>
            <p style="margin-top:14px"><b>Scénario :</b> {model.get("scenario", "-")}</p>
            <p><b>Temps sensible :</b> {model.get("sensible_weather", "-")}</p>
            <p><b>Zones :</b> {model.get("affected_zones", "-")}</p>
            <div class="tags">
                <span class="tag">{model.get("mentions_count", "0")} mentions</span>
            </div>
        </article>
        <article class="card">
            <h3>Différences et limites ({model.get("name", "Modèle")})</h3>
            <p><b>Écart avec les autres modèles :</b> {model.get("differences", "-")}</p>
            <p><b>Pourquoi cette confiance :</b> {model.get("confidence_reason", "-")}</p>
            <p><b>Limites :</b> {model.get("limits", "-")}</p>
        </article>
        """
        html_blocks.append(card_html)
    return "\n".join(html_blocks) if html_blocks else "<p>Aucun modèle spécifique n'est détaillé dans les sources.</p>"

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
            img_html = f'<img src="data:image/{ext};base64,{img_b64}" style="width: 100%; border-bottom: 1px solid var(--line);" alt="Carte météo">'
        except Exception as e:
            print(f"Erreur encodage image {img_path} : {e}")
            img_html = '<div class="ph">Erreur de chargement de l\'image</div>'
            
        card_html = f"""
        <div class="imagebox">
            {img_html}
            <div class="caption">
                <h3>{img_info.get("title", "Carte météo")}</h3>
                <p><b>Modèle :</b> {img_info.get("model", "-")} | <b>Run :</b> {img_info.get("run", "-")}</p>
                <p style="margin-top:8px;">{img_info.get("why_important", "")}</p>
                <p style="margin-top:4px;"><b>À regarder :</b> {img_info.get("what_to_watch", "")}</p>
                <small style="display:block; margin-top:8px; font-weight:700;">Confiance d'interprétation : {img_info.get("confidence", "-")}</small>
                {f'<small style="color:var(--red); display:block; margin-top:4px;">⚠️ {img_info.get("attribution_uncertainty")}</small>' if img_info.get("attribution_uncertainty") else ''}
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
    jours_restants_cours_str = f"du {DAYS_FR[now.weekday()]} {now.day} {MONTHS_FR[now.month-1]} au Dimanche {dimanche_cours.day} {MONTHS_FR[dimanche_cours.month-1]} {dimanche_cours.year}"

    current_iso_week = now.isocalendar()[1]

    def get_topic_week_num(url):
        match = re.search(r'semaine-(\d+)', url.lower())
        return int(match.group(1)) if match else 0

    relevant_topics = [
        t for t in clean_topics
        if current_iso_week - 1 <= get_topic_week_num(t) <= current_iso_week + 4
    ]

    if not relevant_topics:
        relevant_topics = sorted(clean_topics, key=get_topic_week_num, reverse=True)[:2]

    relevant_topics.sort(key=get_topic_week_num)
    
    if len(relevant_topics) < 2:
        relevant_topics = sorted(clean_topics, key=get_topic_week_num, reverse=True)[:2]
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

    # Semaine 1
    w1_dates = extract_tag(w1_content, "W1_DATES") or jours_restants_cours_str
    w1_keys = [extract_tag(w1_content, f"W1_KEY_POINT_{i}") for i in range(1, 7)]
    w1_keys_html = "".join([f'<div class="key">{k}</div>' for k in w1_keys if k])
    w1_models = parse_models(w1_content, "W1")
    w1_models_html = build_model_cards(w1_models)
    w1_images_info = parse_images_info(w1_content, "W1")
    w1_images_html = build_image_cards(w1_images_info, week1_data["images"])

    # Semaine 2
    w2_dates = extract_tag(w2_content, "W2_DATES") or semaine_suivante_str
    w2_keys = [extract_tag(w2_content, f"W2_KEY_POINT_{i}") for i in range(1, 7)]
    w2_keys_html = "".join([f'<div class="key">{k}</div>' for k in w2_keys if k])
    w2_models = parse_models(w2_content, "W2")
    w2_models_html = build_model_cards(w2_models)
    w2_images_info = parse_images_info(w2_content, "W2")
    w2_images_html = build_image_cards(w2_images_info, week2_data["images"])

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

    # CSS
    style = """
    :root {
        --bg: #f8fafc;
        --card: #ffffff;
        --ink: #0f172a;
        --muted: #64748b;
        --line: #e2e8f0;
        --navy: #0f172a;
        --blue: #2563eb;
        --cyan: #06b6d4;
        --green: #16a34a;
        --amber: #d97706;
        --red: #dc2626;
        --shadow: 0 10px 25px -5px rgb(0 0 0 / 0.05), 0 8px 10px -6px rgb(0 0 0 / 0.05);
        --radius-lg: 24px;
        --radius-md: 16px;
        --radius-sm: 8px;
    }
    * { box-sizing: border-box; }
    body {
        margin: 0;
        background: var(--bg);
        font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
        color: var(--ink);
        line-height: 1.5;
        -webkit-font-smoothing: antialiased;
    }
    .wrap {
        width: min(1180px, calc(100% - 24px));
        margin: 24px auto 60px;
    }
    .hero {
        padding: 40px;
        border-radius: var(--radius-lg);
        color: #ffffff;
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        box-shadow: var(--shadow);
        position: relative;
        overflow: hidden;
    }
    .eyebrow {
        font-size: 11px;
        font-weight: 800;
        letter-spacing: 0.15em;
        text-transform: uppercase;
        color: #60a5fa;
        margin-bottom: 8px;
    }
    .hero h1 {
        margin: 0 0 12px;
        font-size: clamp(28px, 5vw, 44px);
        line-height: 1.1;
        font-weight: 800;
        letter-spacing: -0.02em;
    }
    .hero p {
        max-width: 800px;
        margin: 0;
        color: #cbd5e1;
        font-size: 16px;
        line-height: 1.6;
    }
    .meta {
        display: flex;
        gap: 8px;
        flex-wrap: wrap;
        margin-top: 24px;
    }
    .chip {
        padding: 6px 12px;
        border-radius: 999px;
        background: rgba(255, 255, 255, 0.08);
        border: 1px solid rgba(255, 255, 255, 0.12);
        font-size: 12px;
        font-weight: 700;
        color: #e2e8f0;
    }
    .tabs {
        display: flex;
        gap: 8px;
        flex-wrap: wrap;
        margin: 24px 0 16px;
    }
    .tabs button {
        border: 1px solid var(--line);
        padding: 12px 20px;
        border-radius: var(--radius-md);
        background: var(--card);
        color: #475569;
        font-weight: 700;
        cursor: pointer;
        box-shadow: 0 1px 2px 0 rgb(0 0 0 / 0.02);
        transition: all 0.2s ease;
    }
    .tabs button:hover {
        background: #f8fafc;
        border-color: #cbd5e1;
    }
    .tabs button.active {
        background: var(--navy);
        border-color: var(--navy);
        color: #ffffff;
        box-shadow: var(--shadow);
    }
    .panel {
        display: none;
    }
    .panel.active {
        display: block;
    }
    .section {
        background: var(--card);
        border: 1px solid var(--line);
        border-radius: var(--radius-lg);
        padding: 30px;
        margin-top: 20px;
        box-shadow: var(--shadow);
    }
    .section h2 {
        margin: 0 0 8px;
        font-size: 24px;
        font-weight: 800;
        letter-spacing: -0.015em;
        color: var(--navy);
    }
    .sub {
        margin: 0 0 24px;
        color: var(--muted);
        font-size: 14px;
    }
    .grid {
        display: grid;
        gap: 16px;
    }
    .grid-2 { grid-template-columns: repeat(2, minmax(0, 1fr)); }
    .grid-3 { grid-template-columns: repeat(3, minmax(0, 1fr)); }
    .grid-4 { grid-template-columns: repeat(4, minmax(0, 1fr)); }

    .card {
        border: 1px solid var(--line);
        border-radius: var(--radius-md);
        padding: 20px;
        background: #ffffff;
        position: relative;
    }
    .card h3 {
        margin: 0 0 10px;
        font-size: 16px;
        font-weight: 800;
        color: var(--navy);
    }
    .card p {
        margin: 0;
        color: #475569;
        font-size: 14px;
        line-height: 1.5;
    }
    .accent {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        color: #ffffff;
        border: none;
    }
    .accent h3 { color: #ffffff; }
    .accent p { color: #e2e8f0; }
    
    .key {
        padding: 16px 20px;
        border-radius: var(--radius-md);
        background: #f1f5f9;
        border-left: 4px solid var(--blue);
        font-weight: 600;
        font-size: 14px;
        color: var(--navy);
    }
    .model-head {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 12px;
    }
    .score {
        font-size: 26px;
        font-weight: 850;
    }
    .bar {
        height: 8px;
        background: #e2e8f0;
        border-radius: 999px;
        overflow: hidden;
        margin-top: 12px;
    }
    .accent .bar { background: rgba(255, 255, 255, 0.15); }
    .fill { height: 100%; border-radius: 999px; }
    .tags {
        display: flex;
        gap: 6px;
        flex-wrap: wrap;
        margin-top: 14px;
    }
    .tag {
        font-size: 10.5px;
        font-weight: 700;
        padding: 4px 8px;
        border-radius: 999px;
        background: #f1f5f9;
        color: #475569;
    }
    .accent .tag { background: rgba(255, 255, 255, 0.1); color: #f1f5f9; }
    .zone h3 { margin: 4px 0 8px; }
    .zone small {
        display: block;
        margin-top: 12px;
        color: var(--muted);
        font-weight: 700;
        font-size: 11px;
        text-transform: uppercase;
    }
    .splitline {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 20px;
    }
    .solid { border-top: 4px solid var(--green); }
    .fragile { border-top: 4px solid var(--amber); }
    
    .timeline {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 12px;
    }
    .phase {
        padding: 16px;
        border-radius: var(--radius-md);
        background: #f8fafc;
        border: 1px solid var(--line);
    }
    .phase b {
        display: block;
        color: var(--blue);
        margin-bottom: 6px;
        font-weight: 800;
        font-size: 14px;
    }
    .phase p { margin: 0; font-size: 13.5px; color: #475569; }
    
    .images {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 16px;
    }
    .imagebox {
        overflow: hidden;
        border-radius: var(--radius-md);
        border: 1px solid var(--line);
        background: #ffffff;
    }
    .ph {
        height: 180px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        background: repeating-linear-gradient(45deg, #f8fafc, #f8fafc 10px, #f1f5f9 10px, #f1f5f9 20px);
        color: var(--muted);
        font-weight: 700;
        text-align: center;
        padding: 20px;
        border-bottom: 1px solid var(--line);
    }
    .caption { padding: 16px; }
    .caption h3 { margin: 0 0 6px; font-size: 15px; font-weight: 800; color: var(--navy); }
    .caption p { margin: 0; color: var(--muted); font-size: 13px; line-height: 1.4; }
    
    .linkedin {
        white-space: pre-wrap;
        background: #0f172a;
        color: #f8fafc;
        border-radius: var(--radius-md);
        padding: 24px;
        font-size: 14.5px;
        line-height: 1.6;
        border: 1px solid var(--line);
    }
    .copy {
        margin-top: 14px;
        border: none;
        border-radius: var(--radius-sm);
        padding: 10px 18px;
        font-weight: 700;
        cursor: pointer;
        background: var(--blue);
        color: #ffffff;
    }
    .notice {
        padding: 16px 20px;
        border-radius: var(--radius-md);
        background: #fffbeb;
        color: #78350f;
        border: 1px solid #fef3c7;
        font-weight: 600;
        font-size: 14px;
    }
    .evolution-card {
        background: #f8fafc;
        border: 1px solid var(--line);
        border-radius: var(--radius-md);
        padding: 20px;
    }
    .sparkline {
        font-family: monospace;
        font-size: 13px;
        line-height: 1.5;
        color: var(--navy);
        background: #ffffff;
        border: 1px solid var(--line);
        border-radius: var(--radius-sm);
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

    @media (max-width: 900px) {
        .grid-3, .grid-4, .images, .timeline { grid-template-columns: repeat(2, 1fr); }
        .splitline { grid-template-columns: 1fr; }
    }
    @media (max-width: 620px) {
        .hero { padding: 24px; }
        .grid-2, .grid-3, .grid-4, .images, .timeline { grid-template-columns: 1fr; }
        .section { padding: 20px; }
        .tabs button { flex: 1 1 46%; padding: 10px; }
    }
    @media print {
        .tabs { display: none; }
        .panel { display: block !important; }
        .section, .hero { box-shadow: none; margin-top: 15px; }
    }
    """

    # Template HTML de base avec des tags de remplacement
    html_template = """<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Bulletin de Tendances Météo Forum</title>
[STYLE_PLACEHOLDER]
</head>
<body>
<div class="wrap">
<header class="hero">
    <div class="eyebrow">MONSIEUR MÉTÉO</div>
    <h1>BULLETIN ÉVOLUTION & TENDANCES</h1>
    <p>Analyse comparative multi-modèles basée sur les discussions des prévisionnistes du forum Infoclimat.</p>
    <div class="meta">
        <span class="chip">Semaine 1 : [W1_DATES_PLACEHOLDER]</span>
        <span class="chip">Semaine 2 : [W2_DATES_PLACEHOLDER]</span>
        <span class="chip">Génération : [TODAY_STR_PLACEHOLDER]</span>
    </div>
</header>

<nav class="tabs">
    <button class="active" data-tab="w1">Semaine 1</button>
    <button data-tab="w2">Semaine 2</button>
    <button data-tab="summary">Synthèse 15 jours</button>
    <button data-tab="doubts">Doutes et limites</button>
</nav>

<!-- SEMAINE 1 -->
<section id="w1" class="panel active">
    <div class="section">
        <h2>À retenir — Semaine 1</h2>
        <div class="grid grid-2">
            [W1_KEYS_HTML_PLACEHOLDER]
        </div>
    </div>
    
    <div class="section">
        <h2>Comparaison des modèles</h2>
        <p class="sub">Modèles météo identifiés dans les échanges.</p>
        <div class="grid grid-2">
            [W1_MODELS_HTML_PLACEHOLDER]
        </div>
    </div>

    <div class="section">
        <h2>Convergences et divergences</h2>
        <div class="splitline">
            <div class="card solid">
                <h3>Ce qui converge</h3>
                <p>[W1_CONVERGENCES_PLACEHOLDER]</p>
            </div>
            <div class="card fragile">
                <h3>Ce qui diverge</h3>
                <p>[W1_DIVERGENCES_PLACEHOLDER]</p>
            </div>
        </div>
    </div>

    <div class="section">
        <h2>Temps sensible par grandes zones</h2>
        <div class="grid grid-3">
            <div class="card zone">
                <h3>Ouest et façade atlantique</h3>
                <p>[W1_ZONE_WEST_PLACEHOLDER]</p>
                <small>[W1_ZONE_WEST_CONF_PLACEHOLDER]</small>
            </div>
            <div class="card zone">
                <h3>Nord et Nord-Ouest</h3>
                <p>[W1_ZONE_NORTH_PLACEHOLDER]</p>
                <small>[W1_ZONE_NORTH_CONF_PLACEHOLDER]</small>
            </div>
            <div class="card zone">
                <h3>Nord-Est</h3>
                <p>[W1_ZONE_NORTHEAST_PLACEHOLDER]</p>
                <small>[W1_ZONE_NORTHEAST_CONF_PLACEHOLDER]</small>
            </div>
            <div class="card zone">
                <h3>Centre</h3>
                <p>[W1_ZONE_CENTRAL_PLACEHOLDER]</p>
                <small>[W1_ZONE_CENTRAL_CONF_PLACEHOLDER]</small>
            </div>
            <div class="card zone">
                <h3>Sud-Ouest</h3>
                <p>[W1_ZONE_SOUTHWEST_PLACEHOLDER]</p>
                <small>[W1_ZONE_SOUTHWEST_CONF_PLACEHOLDER]</small>
            </div>
            <div class="card zone">
                <h3>Sud-Est et Méditerranée</h3>
                <p>[W1_ZONE_SOUTHEAST_PLACEHOLDER]</p>
                <small>[W1_ZONE_SOUTHEAST_CONF_PLACEHOLDER]</small>
            </div>
            <div class="card zone">
                <h3>Corse</h3>
                <p>[W1_ZONE_CORSICA_PLACEHOLDER]</p>
                <small>[W1_ZONE_CORSICA_CONF_PLACEHOLDER]</small>
            </div>
        </div>
    </div>

    <div class="section">
        <h2>Chronologie de la semaine</h2>
        <div class="timeline">
            <div class="phase"><b>[W1_PHASE_1_DATES_PLACEHOLDER]</b><p>[W1_PHASE_1_PLACEHOLDER]</p></div>
            <div class="phase"><b>[W1_PHASE_2_DATES_PLACEHOLDER]</b><p>[W1_PHASE_2_PLACEHOLDER]</p></div>
            <div class="phase"><b>[W1_PHASE_3_DATES_PLACEHOLDER]</b><p>[W1_PHASE_3_PLACEHOLDER]</p></div>
            <div class="phase"><b>[W1_PHASE_4_DATES_PLACEHOLDER]</b><p>[W1_PHASE_4_PLACEHOLDER]</p></div>
        </div>
    </div>

    <div class="section">
        <h2>Éléments solides et fragiles</h2>
        <div class="splitline">
            <div class="card solid">
                <h3>Éléments solides</h3>
                <p>[W1_SOLID_POINTS_PLACEHOLDER]</p>
            </div>
            <div class="card fragile">
                <h3>Éléments fragiles</h3>
                <p>[W1_FRAGILE_POINTS_PLACEHOLDER]</p>
            </div>
        </div>
        <div class="notice" style="margin-top:14px;">⚠️ À surveiller dans les prochains runs : [W1_NEXT_RUNS_TO_WATCH_PLACEHOLDER]</div>
    </div>

    <div class="section">
        <h2>Sélection de cartes météo analysées</h2>
        <div class="images">
            [W1_IMAGES_HTML_PLACEHOLDER]
        </div>
    </div>
</section>

<!-- SEMAINE 2 -->
<section id="w2" class="panel">
    <div class="section">
        <h2>À retenir — Semaine 2</h2>
        <div class="grid grid-2">
            [W2_KEYS_HTML_PLACEHOLDER]
        </div>
    </div>

    <div class="section">
        <h2>Comparaison des modèles — Semaine 2</h2>
        <div class="grid grid-2">
            [W2_MODELS_HTML_PLACEHOLDER]
        </div>
    </div>

    <div class="section">
        <h2>Convergences et divergences — Semaine 2</h2>
        <div class="splitline">
            <div class="card solid">
                <h3>Ce qui converge</h3>
                <p>[W2_CONVERGENCES_PLACEHOLDER]</p>
            </div>
            <div class="card fragile">
                <h3>Ce qui diverge</h3>
                <p>[W2_DIVERGENCES_PLACEHOLDER]</p>
            </div>
        </div>
    </div>

    <div class="section">
        <h2>Temps sensible par grandes zones — Semaine 2</h2>
        <div class="grid grid-3">
            <div class="card zone">
                <h3>Ouest et façade atlantique</h3>
                <p>[W2_ZONE_WEST_PLACEHOLDER]</p>
                <small>[W2_ZONE_WEST_CONF_PLACEHOLDER]</small>
            </div>
            <div class="card zone">
                <h3>Nord et Nord-Ouest</h3>
                <p>[W2_ZONE_NORTH_PLACEHOLDER]</p>
                <small>[W2_ZONE_NORTH_CONF_PLACEHOLDER]</small>
            </div>
            <div class="card zone">
                <h3>Nord-Est</h3>
                <p>[W2_ZONE_NORTHEAST_PLACEHOLDER]</p>
                <small>[W2_ZONE_NORTHEAST_CONF_PLACEHOLDER]</small>
            </div>
            <div class="card zone">
                <h3>Centre</h3>
                <p>[W2_ZONE_CENTRAL_PLACEHOLDER]</p>
                <small>[W2_ZONE_CENTRAL_CONF_PLACEHOLDER]</small>
            </div>
            <div class="card zone">
                <h3>Sud-Ouest</h3>
                <p>[W2_ZONE_SOUTHWEST_PLACEHOLDER]</p>
                <small>[W2_ZONE_SOUTHWEST_CONF_PLACEHOLDER]</small>
            </div>
            <div class="card zone">
                <h3>Sud-Est et Méditerranée</h3>
                <p>[W2_ZONE_SOUTHEAST_PLACEHOLDER]</p>
                <small>[W2_ZONE_SOUTHEAST_CONF_PLACEHOLDER]</small>
            </div>
            <div class="card zone">
                <h3>Corse</h3>
                <p>[W2_ZONE_CORSICA_PLACEHOLDER]</p>
                <small>[W2_ZONE_CORSICA_CONF_PLACEHOLDER]</small>
            </div>
        </div>
    </div>

    <div class="section">
        <h2>Chronologie de la semaine — Semaine 2</h2>
        <div class="timeline">
            <div class="phase"><b>[W2_PHASE_1_DATES_PLACEHOLDER]</b><p>[W2_PHASE_1_PLACEHOLDER]</p></div>
            <div class="phase"><b>[W2_PHASE_2_DATES_PLACEHOLDER]</b><p>[W2_PHASE_2_PLACEHOLDER]</p></div>
            <div class="phase"><b>[W2_PHASE_3_DATES_PLACEHOLDER]</b><p>[W2_PHASE_3_PLACEHOLDER]</p></div>
            <div class="phase"><b>[W2_PHASE_4_DATES_PLACEHOLDER]</b><p>[W2_PHASE_4_PLACEHOLDER]</p></div>
        </div>
    </div>

    <div class="section">
        <h2>Éléments solides et fragiles — Semaine 2</h2>
        <div class="splitline">
            <div class="card solid">
                <h3>Éléments solides</h3>
                <p>[W2_SOLID_POINTS_PLACEHOLDER]</p>
            </div>
            <div class="card fragile">
                <h3>Éléments fragiles</h3>
                <p>[W2_FRAGILE_POINTS_PLACEHOLDER]</p>
            </div>
        </div>
        <div class="notice" style="margin-top:14px;">⚠️ À surveiller dans les prochains runs : [W2_NEXT_RUNS_TO_WATCH_PLACEHOLDER]</div>
    </div>

    <div class="section">
        <h2>Sélection de cartes météo — Semaine 2</h2>
        <div class="images">
            [W2_IMAGES_HTML_PLACEHOLDER]
        </div>
    </div>
</section>

<!-- SYNTHÈSE 15 JOURS -->
<section id="summary" class="panel">
    [WHAT_CHANGED_BOX_PLACEHOLDER]

    <div class="section">
        <h2>Synthèse des deux semaines</h2>
        
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
            <div class="card accent">
                <h3>Évolution générale</h3>
                <p>[GLOBAL_15_DAY_TREND_PLACEHOLDER]</p>
            </div>
            <div class="card">
                <h3>Semaine la plus fiable</h3>
                <p>[MOST_RELIABLE_WEEK_PLACEHOLDER]</p>
            </div>
            <div class="card solid">
                <h3>Points les plus solides</h3>
                <p>[GLOBAL_SOLID_POINTS_PLACEHOLDER]</p>
            </div>
            <div class="card fragile">
                <h3>Incertitudes majeures</h3>
                <p>[GLOBAL_MAJOR_UNCERTAINTIES_PLACEHOLDER]</p>
            </div>
        </div>
    </div>

    <div class="section">
        <h2>📢 Post LinkedIn prêt à copier-coller</h2>
        <div id="linkedin" class="linkedin">[LINKEDIN_CLEAN_PLACEHOLDER]</div>
        <button class="copy" onclick="copyLinkedIn()">Copier le post LinkedIn</button>
    </div>
</section>

<!-- DOUBT & LIMITS -->
<section id="doubts" class="panel">
    <div class="section">
        <h2>Doutes, imprécisions et limites</h2>
        <div class="grid grid-2">
            <div class="card">
                <h3>Calendrier</h3>
                <p>[DOUBTS_TIMING_PLACEHOLDER]</p>
            </div>
            <div class="card">
                <h3>Localisation</h3>
                <p>[DOUBTS_LOCATION_PLACEHOLDER]</p>
            </div>
            <div class="card">
                <h3>Intensité</h3>
                <p>[DOUBTS_INTENSITY_PLACEHOLDER]</p>
            </div>
            <div class="card">
                <h3>Données manquantes</h3>
                <p>[MISSING_INFORMATION_PLACEHOLDER]</p>
            </div>
            <div class="card">
                <h3>Modèles peu documentés</h3>
                <p>[LOW_DOCUMENTED_MODELS_PLACEHOLDER]</p>
            </div>
            <div class="card">
                <h3>Images difficiles à interpréter</h3>
                <p>[UNCERTAIN_IMAGES_PLACEHOLDER]</p>
            </div>
        </div>
    </div>
</section>
</div>

<script>
document.querySelectorAll('.tabs button').forEach(btn => btn.addEventListener('click', () => {
    document.querySelectorAll('.tabs button').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById(btn.dataset.tab).classList.add('active');
}));

function copyLinkedIn() {
    navigator.clipboard.writeText(document.getElementById('linkedin').innerText).then(() => {
        alert('Le post LinkedIn a été copié dans votre presse-papiers !');
    });
}
</script>
</body>
</html>
"""

    # Remplacement des variables dans le template
    html = html_template
    html = html.replace("[STYLE_PLACEHOLDER]", style)
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
    html = html.replace("[GLOBAL_15_DAY_TREND_PLACEHOLDER]", extract_tag(global_content, "GLOBAL_15_DAY_TREND") or "-")
    html = html.replace("[MOST_RELIABLE_WEEK_PLACEHOLDER]", extract_tag(global_content, "MOST_RELIABLE_WEEK") or "-")
    html = html.replace("[GLOBAL_SOLID_POINTS_PLACEHOLDER]", extract_tag(global_content, "GLOBAL_SOLID_POINTS") or "-")
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
    
    html_b64 = base64.b64encode(html.encode('utf-8')).decode('ascii')
    text_body = (
        f"Bonjour,\n\n"
        f"Veuillez trouver ci-joint l'analyse consolidée des tendances météo pour les 2 prochaines semaines.\n\n"
        f"Le rapport HTML interactif premium contenant le comparateur de modèles (ECMWF, GFS...), le découpage géographique complet, le post LinkedIn prêt à publier et l'évolution historique des runs est joint à ce message.\n\n"
        f"Cordialement,\n"
        f"Monsieur Météo"
    )
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
