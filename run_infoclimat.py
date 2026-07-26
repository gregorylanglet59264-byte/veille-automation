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
import io
from email.utils import formatdate

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

socket.setdefaulttimeout(10)

INDEX_URL = "https://forums.infoclimat.fr/f/forum/20-evolution-%C3%A0-plus-long-terme/"
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'

# Table de correspondance déterministe pour 8 zones météorologiques
ZONE_TERRITORY_MAPPING = {
    "nord_ouest": ["bretagne", "normandie", "pays de la loire", "finistère", "morbihan", "ille-et-vilaine", "côtes-d'armor", "manche", "seine-maritime", "calvados", "eure", "orne", "mayenne", "sarthe", "loire-atlantique"],
    "nord": ["hauts-de-france", "île-de-france", "bassin parisien", "picardie", "pas-de-calais", "nord", "paris", "val-d'oise", "seine-et-marne", "yvelines", "essonne", "hauts-de-seine", "seine-saint-denis", "val-de-marne"],
    "nord_est": ["grand est", "ardennes", "lorraine", "alsace", "franche-comté", "marne", "haute-marne", "meuse", "meurthe-et-moselle", "vosges", "haut-rhin", "bas-rhin", "haute-saône", "doubs", "jura", "avesnois"],
    "ouest_atlantique": ["vendée", "charentes", "charente-maritime", "charente", "façade atlantique", "façade aquitaine", "littoral atlantique", "gironde littoral"],
    "centre": ["centre-val de loire", "berry", "limousin", "auvergne", "orléanais", "touraine", "sologne", "cher", "indre", "indre-et-loire", "loir-et-cher", "loiret", "allier", "puy-de-dôme", "creuse", "haute-vienne"],
    "sud_ouest": ["aquitaine", "nouvelle-aquitaine", "midi toulousain", "pyrénées", "gironde", "dordogne", "lot-et-garonne", "landes", "pyrénées-atlantiques", "hautes-pyrénées", "gers", "tarn", "tarn-et-garonne", "haute-garonne", "ariège"],
    "sud_est_rhone": ["paca", "vallée du rhône", "alpes du sud", "vaucluse", "bouches-du-rhône", "var", "alpes-maritimes", "hautes-alpes", "alpes-de-haute-provence", "drôme", "isère", "rhône"],
    "mediterranee_corse": ["languedoc", "roussillon", "provence littorale", "corse", "gard", "hérault", "aude", "pyrénées-orientales", "haute-corse", "corse-du-sud"]
}

def fetch_url(url, timeout=8):
    req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return response.read().decode('utf-8', errors='ignore')

def optimize_and_encode_image(img_path, max_width=900, quality=80):
    if not os.path.exists(img_path):
        return "", 800, 500
    if HAS_PIL:
        try:
            with Image.open(img_path) as img:
                img_format = img.format if img.format in ['JPEG', 'PNG', 'WEBP'] else 'JPEG'
                if img_format == 'JPEG' and img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')
                
                orig_w, orig_h = img.size
                if orig_w > max_width:
                    ratio = max_width / float(orig_w)
                    new_h = int(float(orig_h) * ratio)
                    img = img.resize((max_width, new_h), Image.Resampling.LANCZOS)
                else:
                    max_width, new_h = orig_w, orig_h
                
                buffer = io.BytesIO()
                if img_format == 'PNG':
                    img.save(buffer, format='PNG', optimize=True)
                    mime = 'image/png'
                else:
                    img.save(buffer, format='JPEG', quality=quality, optimize=True)
                    mime = 'image/jpeg'
                
                b64_str = base64.b64encode(buffer.getvalue()).decode('ascii')
                return f"data:{mime};base64,{b64_str}", max_width, new_h
        except Exception as e:
            print(f"Erreur d'optimisation de l'image {img_path} avec PIL : {e}")

    try:
        with open(img_path, "rb") as f_img:
            b64_str = base64.b64encode(f_img.read()).decode('ascii')
        ext = img_path.split('.')[-1].lower()
        mime = 'image/gif' if ext == 'gif' else ('image/png' if ext == 'png' else 'image/jpeg')
        return f"data:{mime};base64,{b64_str}", 800, 500
    except Exception as e:
        print(f"Erreur d'encodage direct de l'image {img_path} : {e}")
        return "", 800, 500

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
        "images": downloaded_images,
        "total_scraped_images": len(candidate_imgs)
    }

def extract_tag(text, tag):
    pattern = rf"\[{tag}\]\s*\n(.*?)(?=\n\s*\[|$)"
    match = re.search(pattern, text, re.DOTALL)
    return match.group(1).strip() if match else ""

def clean_text_typos(text):
    if not text: return ""
    text = text.replace("scenario", "scénario")
    text = text.replace("Scenario", "Scénario")
    text = text.replace("Sud-Eest", "Sud-Est")
    text = text.replace("Sud-eest", "sud-est")
    text = text.replace("vendudi", "vendredi")
    text = text.replace("un quart Nord-Est assoiffé", "un quart Nord-Est connaissant des précipitations très faibles")
    text = text.replace("GEM est perdu", "Scénario GEM peu soutenu")
    text = text.replace("sa crédibilité est remise en question", "scénario peu soutenu dans les messages analysés")
    text = text.replace("Aucun sensible", "Aucune période particulièrement sensible identifiée")
    text = text.replace("trace seulement", "traces possibles")
    text = re.sub(r'---+', '', text)
    text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
    return text.strip()

def clean_mentions_str(val):
    if not val:
        return "1 mention exploitable"
    val = val.strip()
    val = re.sub(r'\bmentions\s+mentions\b', 'mentions', val, flags=re.IGNORECASE)
    val = re.sub(r'\bmention\s+mentions\b', 'mentions', val, flags=re.IGNORECASE)
    val = re.sub(r'\bmentions\s+exploitable\s+mentions\b', 'mentions exploitables', val, flags=re.IGNORECASE)
    val = re.sub(r'\bmention\s+exploitable\s+mentions\b', 'mention exploitable', val, flags=re.IGNORECASE)
    return val

def format_run_string(run_val):
    if not run_val or run_val.strip().lower() in ["non précisé", "non precise", "non déterminable", "inconnu"]:
        return "Run du scénario : non déterminable"
    runs = re.findall(r'\b(00Z|06Z|12Z|18Z)\b', run_val, re.IGNORECASE)
    if len(runs) > 1:
        return f"Runs cités : {', '.join(set(runs))}"
    elif len(runs) == 1:
        return f"Run : {runs[0].upper()}"
    return f"Run : {run_val.strip()}"

def parse_models(week_text, prefix):
    blocks = re.findall(rf"\[{prefix}_MODEL_START\](.*?)\[{prefix}_MODEL_END\]", week_text, re.DOTALL)
    models = []
    for b in blocks:
        raw_conf = extract_tag(b, f"{prefix}_MODEL_EXTRACTION_CONF")
        model = {
            "name": clean_text_typos(extract_tag(b, f"{prefix}_MODEL_NAME")),
            "scenario": clean_text_typos(extract_tag(b, f"{prefix}_MODEL_SCENARIO")),
            "sensible_weather": clean_text_typos(extract_tag(b, f"{prefix}_MODEL_SENSIBLE_WEATHER")),
            "affected_zones": clean_text_typos(extract_tag(b, f"{prefix}_MODEL_AFFECTED_ZONES")),
            "extraction_conf": raw_conf if raw_conf else "Non estimable",
            "scenario_support": extract_tag(b, f"{prefix}_MODEL_SCENARIO_SUPPORT") or "Majoritaire",
            "status": extract_tag(b, f"{prefix}_MODEL_STATUS") or "Majoritaire",
            "mentions_count": clean_mentions_str(extract_tag(b, f"{prefix}_MODEL_MENTIONS_COUNT")),
            "run": format_run_string(extract_tag(b, f"{prefix}_MODEL_RUN")),
            "timing": extract_tag(b, f"{prefix}_MODEL_TIMING") or "Échéance non précisée",
            "details": clean_text_typos(extract_tag(b, f"{prefix}_MODEL_DETAILS")) or "Pas de détails complémentaires."
        }
        if model["name"]:
            models.append(model)
    return models

def parse_images_info(week_text, prefix):
    blocks = re.findall(rf"\[{prefix}_IMAGE_START\](.*?)\[{prefix}_IMAGE_END\]", week_text, re.DOTALL)
    imgs = []
    for b in blocks:
        img = {
            "type": clean_text_typos(extract_tag(b, f"{prefix}_IMAGE_TYPE")) or "Carte météo",
            "title": clean_text_typos(extract_tag(b, f"{prefix}_IMAGE_TITLE")) or "Carte d'analyse",
            "model": clean_text_typos(extract_tag(b, f"{prefix}_IMAGE_MODEL")) or "Modèle météo",
            "run": format_run_string(extract_tag(b, f"{prefix}_IMAGE_RUN")),
            "timing": extract_tag(b, f"{prefix}_IMAGE_TIMING") or "Échéance",
            "why_important": clean_text_typos(extract_tag(b, f"{prefix}_IMAGE_WHY_IMPORTANT")),
            "what_to_watch": clean_text_typos(extract_tag(b, f"{prefix}_IMAGE_WHAT_TO_WATCH")),
            "confidence": extract_tag(b, f"{prefix}_IMAGE_CONFIDENCE") or "Modérée",
            "limit": clean_text_typos(extract_tag(b, f"{prefix}_IMAGE_LIMIT"))
        }
        if img["title"]:
            imgs.append(img)
    return imgs

def parse_zones_json(text, prefix):
    match = re.search(rf'\[{prefix}_ZONES_JSON_START\](.*?)\[{prefix}_ZONES_JSON_END\]', text, re.DOTALL)
    if not match:
        return {}
    raw_json = match.group(1).strip()
    raw_json = re.sub(r'^```json\s*', '', raw_json)
    raw_json = re.sub(r'^```\s*', '', raw_json)
    raw_json = re.sub(r'\s*```$', '', raw_json)
    try:
        data = json.loads(raw_json)
        return data.get("zones", data)
    except Exception as e:
        print(f"Erreur parsing JSON zones {prefix} : {e}")
        return {}

def log_zones_diagnostics(zones_dict, week_num):
    print(f"\n--- DIAGNOSTIC 8 ZONES SEMAINE {week_num} ---")
    fixed_keys = [
        ("nord_ouest", "Nord-Ouest"),
        ("nord", "Nord"),
        ("nord_est", "Nord-Est"),
        ("ouest_atlantique", "Ouest et Façade Atlantique"),
        ("centre", "Centre"),
        ("sud_ouest", "Sud-Ouest"),
        ("sud_est_rhone", "Sud-Est et Vallée du Rhône"),
        ("mediterranee_corse", "Méditerranée et Corse")
    ]
    for key, name in fixed_keys:
        zdata = zones_dict.get(key, {})
        status = zdata.get("status", "insufficient")
        conf = zdata.get("confidence_level", "non_estimable")
        sources = ", ".join(zdata.get("source_models", [])) if isinstance(zdata.get("source_models"), list) else "Aucun"
        print(f"[ZONE: {key}] Status: {status} | Confiance: {conf} | Modèles: {sources}")

def build_zone_card_from_dict(icon, zone_display_name, zone_data):
    if not zone_data or not isinstance(zone_data, dict):
        zone_data = {"status": "insufficient"}
        
    status = str(zone_data.get("status", "insufficient")).lower()
    weather = clean_text_typos(zone_data.get("weather", "")).strip()
    
    if status == "insufficient" or not weather or "temps non spécifié" in weather.lower() or "non précisé" in weather.lower():
        return f"""
        <div class="zone zone-insufficient">
          <div class="zone-head">
            <span class="zone-icon">{icon}</span>
            <h3>{zone_display_name}</h3>
          </div>
          <p class="zone-notice">Informations insuffisantes dans les messages analysés pour établir une tendance fiable sur cette zone.</p>
          <div class="zone-foot">
            <span class="chip-conf" style="background:#f1f5f9; color:#64748b;">Confiance : Non estimable</span>
            <span class="chip-uncert" style="background:#f1f5f9; color:#64748b;">Données insuffisantes</span>
          </div>
        </div>
        """
        
    temp = clean_text_typos(zone_data.get("temperatures", "")).strip()
    rain = clean_text_typos(zone_data.get("rain_storms", "")).strip()
    wind = clean_text_typos(zone_data.get("wind", "")).strip()
    timing = clean_text_typos(zone_data.get("sensitive_period", "")).strip()
    conf_level = str(zone_data.get("confidence_level", "moderee")).strip()
    uncert = clean_text_typos(zone_data.get("uncertainty", "")).strip()
    models = zone_data.get("source_models", [])
    scope = zone_data.get("spatial_scope", "regional")
    location = zone_data.get("location", "")
    
    conf_label = "Modérée"
    if "elev" in conf_level.lower() or "haut" in conf_level.lower(): conf_label = "Élevée"
    elif "faib" in conf_level.lower(): conf_label = "Faible"
    elif "non" in conf_level.lower(): conf_label = "Non estimable"
    
    badge_html = '<span class="badge" style="margin-bottom:6px; font-size:10px; background:#fef3c7; color:#92400e;">Informations partielles</span>' if status == "partial" else ""
    
    details_items = []
    if weather: details_items.append(f'<li><b>Temps dominant :</b> {weather}</li>')
    if temp and temp.lower() not in ["non documenté", "non précisé"]: details_items.append(f'<li><b>Températures :</b> {temp}</li>')
    
    if rain and rain.lower() not in ["non documenté", "non précisé"]:
        if scope == "local" and location:
            details_items.append(f'<li><b>Pluie / Orages :</b> Des cumuls de {rain} sont évoqués localement vers {location}, sans pouvoir être généralisés à l\'ensemble de la zone.</li>')
        else:
            details_items.append(f'<li><b>Pluie / Orages :</b> {rain}</li>')
            
    if wind and wind.lower() not in ["non documenté", "non précisé", "-", "vent non documenté"]:
        details_items.append(f'<li><b>Vent :</b> {wind}</li>')
        
    if timing and timing.lower() not in ["non documenté", "non précisé"]: details_items.append(f'<li><b>Période sensible :</b> {timing}</li>')
    
    evidence_count = zone_data.get("evidence_count", 0)
    sources_meta = []
    if models and isinstance(models, list) and len(models) > 0:
        sources_meta.append(f"Modèles : {', '.join(models)}")
    if location:
        sources_meta.append(f"Secteurs : {location}")
    if evidence_count > 0:
        sources_meta.append(f"{evidence_count} mentions")
        
    if sources_meta:
        details_items.append(f'<li style="margin-top:6px; font-size:11.5px; color:var(--muted); border-top:1px dashed var(--line); padding-top:4px;"><b>Sources :</b> {" • ".join(sources_meta)}</li>')

    details_html = "".join(details_items)
    uncert_html = f'<span class="chip-uncert">Incertitude : {uncert}</span>' if uncert else ''
    
    return f"""
    <details class="zone zone-accordion">
      <summary class="zone-summary">
        <div>
          {badge_html}
          <div class="zone-head" style="margin-bottom:2px;">
            <span class="zone-icon">{icon}</span>
            <h3>{zone_display_name}</h3>
          </div>
          <div class="zone-short-desc">{weather}</div>
        </div>
        <div style="display:flex; align-items:center; gap:6px;">
          <span class="chip-conf" style="font-size:10px;">{conf_label}</span>
          <span class="zone-chevron">▼</span>
        </div>
      </summary>
      <div class="zone-body">
        <ul class="zone-details">
          {details_html}
        </ul>
        <div class="zone-foot">
          <span class="chip-conf">Confiance : {conf_label}</span>
          {uncert_html}
        </div>
      </div>
    </details>
    """

def render_zones_grid(zones_json_data):
    fixed_keys = [
        ("nord_ouest", "🧭", "Nord-Ouest"),
        ("nord", "☁️", "Nord"),
        ("nord_est", "🌤️", "Nord-Est"),
        ("ouest_atlantique", "🌊", "Ouest et Façade Atlantique"),
        ("centre", "🌥️", "Centre"),
        ("sud_ouest", "🌡️", "Sud-Ouest"),
        ("sud_est_rhone", "☀️", "Sud-Est et Vallée du Rhône"),
        ("mediterranee_corse", "🏖️", "Méditerranée et Corse")
    ]
    cards = []
    for key, icon, display_name in fixed_keys:
        zdata = zones_json_data.get(key, {})
        cards.append(build_zone_card_from_dict(icon, display_name, zdata))
    return "\n".join(cards)

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
                
                conf_val = run_data.get("w1_confidence", 70)
                if isinstance(conf_val, (int, float)):
                    conf_num = int(conf_val)
                    conf_disp = f"{conf_num}%"
                else:
                    conf_disp = str(conf_val)
                    conf_num = 80 if "elev" in conf_disp.lower() else (50 if "faib" in conf_disp.lower() else 70)
                blocks = int(conf_num / 10)
                empty = 10 - blocks
                spark_bar = "█" * blocks + "░" * empty
                sparkline_rows.append(f'<div class="sparkline-row"><span>{date_str} :</span> <span>{spark_bar} {conf_disp}</span></div>')
                
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
        raw_conf = model.get("extraction_conf", "Non estimable")
        conf_digits = re.search(r'\d+', str(raw_conf))
        
        if conf_digits and "non" not in str(raw_conf).lower():
            conf_num = int(conf_digits.group(0))
            color = "var(--green)"
            if conf_num < 60: color = "var(--red)"
            elif conf_num < 75: color = "var(--amber)"
            bar_html = f'<div class="bar"><div class="fill" style="width:{conf_num}%; background:{color};"></div></div>'
            score_text = f"{conf_num} %"
        else:
            score_text = "Non estimable"
            bar_html = '<div class="bar" style="background:#e2e8f0;"></div>'

        support_text = clean_text_typos(model.get("scenario_support", "Majoritaire"))
        support_text = re.sub(r'\d+\s*%', '', support_text).strip()
        if not support_text: support_text = "Majoritaire"

        status_class = "status-main"
        status_text = model.get("status", "Majoritaire")
        if "minor" in status_text.lower() or "isol" in status_text.lower():
            status_class = "status-minor"
        elif "interm" in status_text.lower():
            status_class = "status-inter"
            
        run_info = model.get("run", "Run du scénario : non déterminable")
        timing_info = model.get("timing", "-")
        mentions_info = model.get("mentions_count", "1 mention exploitable")
        
        row_html = f"""
        <tr class="model-row">
          <td data-label="Modèle">
            <div class="model-name-box">
              <div class="model-name">{model.get("name", "Modèle")}</div>
              <span class="status-badge {status_class}">{status_text}</span>
            </div>
            <div class="chips" style="margin-top:6px;">
              <span class="chip">{mentions_info}</span>
              <span class="chip">{run_info}</span>
              <span class="chip">{timing_info}</span>
            </div>
          </td>
          <td data-label="Scénario"><span class="m-label">Scénario :</span>{model.get("scenario", "-")}</td>
          <td data-label="Temps sensible"><span class="m-label">Temps sensible :</span>{model.get("sensible_weather", "-")}</td>
          <td data-label="Zones"><span class="m-label">Zones concernées :</span>{model.get("affected_zones", "-")}</td>
          <td data-label="Confiance & Soutien">
            <div class="score-box">
              <div class="score-label">Extraction : <strong>{score_text}</strong></div>
              {bar_html}
              <div class="score-label" style="margin-top:6px;">Soutien : <strong>{support_text}</strong></div>
            </div>
            <details class="model-details">
              <summary>Voir le détail d'analyse</summary>
              <div class="details-body">
                {model.get("details", "Pas de détails d'analyse disponibles.")}
              </div>
            </details>
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
        
        src_url, width, height = optimize_and_encode_image(img_path, max_width=900, quality=80)
        
        title_attr = img_info.get("title", "Carte d'analyse").replace('"', '&quot;')
        model_attr = img_info.get("model", "-").replace('"', '&quot;')
        run_attr = img_info.get("run", "Non précisé").replace('"', '&quot;')
        timing_attr = img_info.get("timing", "-").replace('"', '&quot;')
        
        if src_url:
            img_html = f'<img src="{src_url}" loading="lazy" width="{width}" height="{height}" class="lightbox-trigger" data-full="{src_url}" data-title="{title_attr}" data-meta="{model_attr} • {run_attr} • {timing_attr}" style="width: 100%; max-height: 240px; object-fit: contain; background: #0b1d2e; cursor: pointer;" alt="{title_attr}">'
        else:
            img_html = f'<div class="image-demo">IMAGE {i+1}<br>Erreur de chargement</div>'
            
        limit_html = f'<div class="image-limit">⚠️ <b>Limite :</b> {img_info.get("limit")}</div>' if img_info.get("limit") else ''
        
        card_html = f"""
        <div class="image-card">
            {img_html}
            <div class="image-caption">
                <div class="badge" style="margin-bottom:6px;">{img_info.get("type", "Carte météo")}</div>
                <h3>{img_info.get("title", "Carte d'analyse")}</h3>
                <p><b>Pourquoi retenue :</b> {img_info.get("why_important", "")}</p>
                <p style="margin-top:4px;"><b>À regarder :</b> {img_info.get("what_to_watch", "")}</p>
                {limit_html}
                <div class="image-meta">
                    <span class="chip">{img_info.get("model", "-")}</span>
                    <span class="chip">{img_info.get("run", "Run non précisé")}</span>
                    <span class="chip">Échéance : {img_info.get("timing", "-")}</span>
                    <span class="chip">Confiance : {img_info.get("confidence", "Modérée")}</span>
                </div>
            </div>
        </div>
        """
        html_blocks.append(card_html)
        
    if not html_blocks:
        return "<p class='notice'>1 seule carte ou aucun graphique exploitable n'a pu être extrait pour cette semaine.</p>"
    return "\n".join(html_blocks)

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
            return f"Du Lundi {d1.day} au Dimanche {d2.day} {m1} {d1.year}"
        else:
            return f"Du Lundi {d1.day} {m1} au Dimanche {d2.day} {m2} {d1.year}"
            
    lundi_actuel = now - datetime.timedelta(days=now.weekday())
    current_iso_week = now.isocalendar()[1]
    
    if now.weekday() >= 4:
        target_w1_iso = current_iso_week + 1
        target_w2_iso = current_iso_week + 2
        lundi_w1 = lundi_actuel + datetime.timedelta(days=7)
        lundi_w2 = lundi_actuel + datetime.timedelta(days=14)
    else:
        target_w1_iso = current_iso_week
        target_w2_iso = current_iso_week + 1
        lundi_w1 = lundi_actuel
        lundi_w2 = lundi_actuel + datetime.timedelta(days=7)

    dimanche_w1 = lundi_w1 + datetime.timedelta(days=6)
    dimanche_w2 = lundi_w2 + datetime.timedelta(days=6)

    today_str = get_french_date(now)
    w1_dates_calculated = fmt_date_range(lundi_w1, dimanche_w1)
    w2_dates_calculated = fmt_date_range(lundi_w2, dimanche_w2)

    def get_topic_week_num(url):
        match = re.search(r'semaine-(\d+)', url.lower())
        return int(match.group(1)) if match else 0

    relevant_topics = [
        t for t in clean_topics
        if target_w1_iso <= get_topic_week_num(t) <= target_w2_iso + 2
    ]
    relevant_topics.sort(key=get_topic_week_num)
    relevant_topics = relevant_topics[:2]

    if len(relevant_topics) < 2:
        relevant_topics = [
            t for t in clean_topics
            if target_w1_iso - 1 <= get_topic_week_num(t) <= target_w2_iso + 2
        ]
        relevant_topics.sort(key=get_topic_week_num)
        relevant_topics = relevant_topics[:2]

    print(f"[INFO] Topics retenus pour prévisions (Semaines cible ISO {target_w1_iso} et {target_w2_iso}) : {[get_topic_week_num(t) for t in relevant_topics]} → {relevant_topics}")

    week1_data = extract_comments_and_images(relevant_topics[0], 0)
    week2_data = extract_comments_and_images(relevant_topics[1], 1)
    
    if not week1_data or not week2_data:
        print("Erreur de récupération des données du forum.")
        sys.exit(1)

    total_scraped_cards = week1_data.get("total_scraped_images", 0) + week2_data.get("total_scraped_images", 0)
    downloaded_cards_count = len(week1_data["images"]) + len(week2_data["images"])

    last_bulletin_path = "data/last_bulletin.json"
    last_bulletin_context = "Aucun bulletin précédent disponible."
    has_last_bulletin = os.path.exists(last_bulletin_path)
    
    if has_last_bulletin:
        try:
            with open(last_bulletin_path, "r", encoding="utf-8") as f_last:
                last_data = json.load(f_last)
                last_bulletin_context = (
                    f"Dernier bulletin généré le {last_data.get('date_generation', 'Inconnue')}.\n"
                    f"Résumé général précédent : {last_data.get('global_summary', 'Inconnu')}.\n"
                    f"Confiance précédente de la semaine 1 : {last_data.get('w1_confidence', 'Modérée')}.\n"
                    f"Températures attendues précédemment : {last_data.get('w1_temp', 'De saison')}."
                )
        except Exception as e:
            print(f"Erreur lecture dernier bulletin : {e}")
            has_last_bulletin = False

    saison_actuelle = ["hiver", "printemps", "été", "automne"][(now.month % 12 // 3)]

    system_prompt = """Tu es Patrick Marlière, météorologue expert de renommée nationale pour Monsieur Météo.

MISSION
À partir des discussions et analyses météorologiques brutes de deux semaines distinctes de prévision, tu dois produire un bulletin d'analyse météorologique consolidé, professionnel, grand public, hyper-visuel et rigoureusement structuré par balises et par JSON.

RÈGLE D'OR N°1 : PRUDENCE MÉTÉOROLOGIQUE ET CONDITIONNEL OBLIGATOIRE
- Ne transforme JAMAIS une sortie isolée ou un scénario en certitude.
- Formulations affirmatives interdites pour les événements futurs incertains ! Utilise le conditionnel.
- Ne jamais utiliser le mot "canicule" sauf si les messages décrivent explicitement un épisode durable de températures très élevées de jour comme de nuit validé par le consensus.
- Ne pas inventer le vent : s'il n'est pas mentionné pour une zone, indiquer wind="Non documenté".

RÈGLE D'OR N°2 : SÉPARATION STRICTE DES SOUTIENS DE SCÉNARIOS ET DES RUNS
Pour chaque modèle météo cité :
1. Confiance d'extraction : Score 0-100% ou "Non estimable". Ne jamais forcer 80 % !
2. Soutien du scénario (QUALITATIF UNIQUEMENT) : Utiliser uniquement : Majoritaire | Intermédiaire | Minoritaire | Isolé | Non déterminable. AUCUN POURCENTAGE INVENTÉ !
3. Run : Si plusieurs runs sont cités, écrire "Runs cités : 00Z, 12Z". Si non précisé, écrire "Run du scénario : non déterminable".

RÈGLE D'OR N°3 : SYNTHÈSE DES 8 ZONES MÉTÉOROLOGIQUES EN JSON STRICT
Tu DOIS obligatoirement retourner un objet JSON sous les balises [W1_ZONES_JSON_START] et [W2_ZONES_JSON_START].
Utilise STRICTEMENT les 8 clés fixes suivantes :
1. "nord_ouest"
2. "nord"
3. "nord_est"
4. "ouest_atlantique"
5. "centre"
6. "sud_ouest"
7. "sud_est_rhone"
8. "mediterranee_corse"

Structure JSON exigée par zone :
{
  "status": "documented | partial | insufficient",
  "weather": "Temps dominant envisagé (max 15 mots sur mobile)",
  "temperatures": "Description des températures",
  "rain_storms": "Précipitations et orages",
  "spatial_scope": "local | regional | broad",
  "location": "Localisation précise si valeur locale",
  "wind": "Vent si documenté, sinon Non documenté",
  "sensitive_period": "Jours sensibles",
  "confidence_level": "elevee | moderee | faible | non_estimable",
  "uncertainty": "Principale incertitude",
  "evidence_count": 3,
  "source_models": ["GFS", "ECMWF"]
}

RÈGLE D'OR N°4 : POST LINKEDIN RÉVISÉ
Rédige un post LinkedIn prêt à copier-coller (250-300 mots) :
- Titre accrocheur et prudent (ex: 🌡️ 𝗣𝗿𝗲́𝘃𝗶𝘀𝗶𝗼𝗻𝘀 𝗺𝗲́𝘁𝗲́𝗼 : 𝗧𝗲𝗻𝗱𝗮𝗻𝗰𝗲𝘀 𝗲𝘁 𝗱𝗶𝘃𝗲𝗿𝗴𝗲𝗻𝗰𝗲𝘀 𝗺𝘂𝗹𝘁𝗶-𝗺𝗼𝗱𝗲̀𝗹𝗲𝘀).
- Aucun markdown ** visible dans le texte.

FORMAT DE SORTIE OBLIGATOIRE :

[WEEK_1_START]
[W1_DATES]
Période exacte semaine 1

[W1_KEY_POINT_1]
Titre court 2-5 mots : Explication courte d'une phrase (12-18 mots max).
[W1_KEY_POINT_2]
Titre court 2-5 mots : Explication courte.
[W1_KEY_POINT_3]
Titre court 2-5 mots : Explication courte.
[W1_KEY_POINT_4]
Titre court 2-5 mots : Explication courte.
[W1_KEY_POINT_5]
Titre court 2-5 mots : Explication courte.

[W1_MODEL_START]
[W1_MODEL_NAME] ...
[W1_MODEL_SCENARIO] ... (max 160 caractères)
[W1_MODEL_SENSIBLE_WEATHER] ... (max 120 caractères)
[W1_MODEL_AFFECTED_ZONES] ...
[W1_MODEL_EXTRACTION_CONF] ...
[W1_MODEL_SCENARIO_SUPPORT] ...
[W1_MODEL_STATUS] ...
[W1_MODEL_MENTIONS_COUNT] ...
[W1_MODEL_RUN] ...
[W1_MODEL_TIMING] ...
[W1_MODEL_DETAILS] ...
[W1_MODEL_END]

[W1_CONVERGENCES]
Points de convergence (max 3 points)
[W1_DIVERGENCES]
Points de divergence (max 3 points)

[W1_ZONES_JSON_START]
{ "zones": { ... 8 zones ... } }
[W1_ZONES_JSON_END]

[W1_SOLID_POINTS]
Points solides (max 3)
[W1_FRAGILE_POINTS]
Points fragiles (max 3)
[W1_NEXT_RUNS_TO_WATCH]
À surveiller

[W1_PHASE_1_DATES]
Dates phase 1
[W1_PHASE_1]
Une phrase courte
[W1_PHASE_2_DATES]
Dates phase 2
[W1_PHASE_2]
Une phrase courte
[W1_PHASE_3_DATES]
Dates phase 3
[W1_PHASE_3]
Une phrase courte
[W1_PHASE_4_DATES]
Dates phase 4
[W1_PHASE_4]
Une phrase courte

[W1_IMAGE_START] ... [W1_IMAGE_END]

[WEEK_1_END]

[WEEK_2_START] ... [WEEK_2_END]

[GLOBAL_START]
[GLOBAL_15_DAY_TREND] ...
[MOST_RELIABLE_WEEK] ...
[GLOBAL_SOLID_POINTS] ...
[GLOBAL_RECURRING_PHENOMENA] ...
[GLOBAL_AFFECTED_ZONES] ...
[GLOBAL_MAJOR_UNCERTAINTIES] ...
[GLOBAL_CONSENSUS_KPI] Modéré | Élevé | Faible
[GLOBAL_CONSENSUS_NOTE] Note très courte
[GLOBAL_SCENARIO_KPI] Scénario très court
[GLOBAL_SCENARIO_NOTE] Note très courte
[GLOBAL_UNCERTAINTY_KPI] Incertitude courte
[GLOBAL_UNCERTAINTY_NOTE] Note très courte
[LINKEDIN_POST] ...
[GLOBAL_END]

[DOUBTS_START] ... [DOUBTS_END]
"""

    user_prompt = f"""Date actuelle de génération : {today_str}
Saison en France : {saison_actuelle.upper()}

PÉRIODES EXACTES À RESPECTER IMPÉRATIVEMENT :
- SEMAINE 1 PREVISION : {w1_dates_calculated}
- SEMAINE 2 PREVISION : {w2_dates_calculated}

=== PRÉCÉDENT BULLETIN (POUR COMPARAISON) ===
{last_bulletin_context}
============================================

=== DISCUSSIONS SEMAINE 1 ({w1_dates_calculated}) ===
{week1_data["comments_text"]}

=== DISCUSSIONS SEMAINE 2 ({w2_dates_calculated}) ===
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

    w1_zones_dict = parse_zones_json(w1_content, "W1")
    w2_zones_dict = parse_zones_json(w2_content, "W2")

    log_zones_diagnostics(w1_zones_dict, 1)
    log_zones_diagnostics(w2_zones_dict, 2)

    def format_key_point(key_str):
        if not key_str:
            return ""
        key_str = clean_text_typos(key_str).strip()
        emoji = "💡"
        
        emoji_match = re.match(r'^([\U00010000-\U0010ffff]|\u2600-\u27bf)\s*', key_str)
        if emoji_match:
            emoji = emoji_match.group(1)
            key_str = key_str[emoji_match.end():].strip()
        else:
            lower = key_str.lower()
            if any(w in lower for w in ["temp", "chaud", "chaleur", "degré", "canicule"]): emoji = "🌡️"
            elif any(w in lower for w in ["orage", "foudre", "tonnerre"]): emoji = "⛈️"
            elif any(w in lower for w in ["pluie", "averse", "humide", "eau", "front"]): emoji = "🌦️"
            elif any(w in lower for w in ["vent", "rafale", "mistral"]): emoji = "💨"
            elif any(w in lower for w in ["soleil", "beau", "sec", "anticyclone"]): emoji = "☀️"
            elif any(w in lower for w in ["nuage", "couvert", "gris"]): emoji = "☁️"
            elif any(w in lower for w in ["ouest", "atlantique", "manche"]): emoji = "🧭"
            elif any(w in lower for w in ["fiab", "confiance", "accord", "consensus"]): emoji = "🤝"
            elif any(w in lower for w in ["incertain", "doute", "surveiller", "risq"]): emoji = "⚠️"
                
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
    w1_dates = extract_tag(w1_content, "W1_DATES") or w1_dates_calculated
    w1_keys = [extract_tag(w1_content, f"W1_KEY_POINT_{i}") for i in range(1, 6)]
    w1_keys_html = "".join([format_key_point(k) for k in w1_keys if k])
    w1_models = parse_models(w1_content, "W1")
    w1_models_html = build_model_cards(w1_models)
    w1_images_info = parse_images_info(w1_content, "W1")
    w1_images_html = build_image_cards(w1_images_info, week1_data["images"])
    w1_zones_html = render_zones_grid(w1_zones_dict)

    # Semaine 2
    w2_dates = extract_tag(w2_content, "W2_DATES") or w2_dates_calculated
    w2_keys = [extract_tag(w2_content, f"W2_KEY_POINT_{i}") for i in range(1, 6)]
    w2_keys_html = "".join([format_key_point(k) for k in w2_keys if k])
    w2_models = parse_models(w2_content, "W2")
    w2_models_html = build_model_cards(w2_models)
    w2_images_info = parse_images_info(w2_content, "W2")
    w2_images_html = build_image_cards(w2_images_info, week2_data["images"])
    w2_zones_html = render_zones_grid(w2_zones_dict)

    # KPIs globaux du header
    kpi_consensus_val = extract_tag(global_content, "GLOBAL_CONSENSUS_KPI") or "Modéré"
    kpi_consensus_note = extract_tag(global_content, "GLOBAL_CONSENSUS_NOTE") or "Accord sur la chaleur, intensité débattue"
    kpi_scenario_val = extract_tag(global_content, "GLOBAL_SCENARIO_KPI") or "Forte chaleur possible"
    kpi_scenario_note = extract_tag(global_content, "GLOBAL_SCENARIO_NOTE") or "Intensité débattue en semaine 2"
    
    kpi_cards_val = f"{downloaded_cards_count} / {total_scraped_cards}" if total_scraped_cards > 0 else f"{downloaded_cards_count} retenues"
    kpi_cards_note = f"{downloaded_cards_count} cartes sur {total_scraped_cards} analysées"
    
    kpi_uncertainty_val = extract_tag(global_content, "GLOBAL_UNCERTAINTY_KPI") or "Intensité"
    kpi_uncertainty_note = extract_tag(global_content, "GLOBAL_UNCERTAINTY_NOTE") or "Écart GFS et ECMWF"

    w1_conf_val = "Modérée"
    w1_temp_val = w1_models[0].get("sensible_weather", "De saison") if w1_models else "De saison"
    w2_conf_val = "Modérée"
    w2_temp_val = w2_models[0].get("sensible_weather", "De saison") if w2_models else "De saison"

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

    what_changed_box = ""
    if has_last_bulletin and what_changed:
        what_changed_box = f"""
        <div class="section">
            <div class="section-head"><div><span class="badge">Comparatif</span><h2>📈 Ce qui a changé depuis le précédent bulletin</h2></div></div>
            <div class="alert" style="background:#eff6ff; color:#1e40af; border-color:#bfdbfe;">
                {clean_text_typos(what_changed)}
            </div>
        </div>
        """

    linkedin_raw = extract_tag(global_content, "LINKEDIN_POST")
    linkedin_clean = clean_text_typos(linkedin_raw).replace('<br>', '\n').replace('<br/>', '\n')

    # CSS RESPONSIVE MOBILE MOBILE-FIRST COMPLET (< 650px)
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
      font-size:15px;
    }
    button{font:inherit; min-height:44px;}
    button:focus-visible, a:focus-visible { outline: 3px solid var(--cyan); outline-offset: 2px; }
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
    .hero-inner{position:relative;z-index:2}
    .hero-top{display:flex;justify-content:space-between;gap:18px;align-items:flex-start}
    .brand{display:flex;gap:12px;align-items:center;font-weight:900;letter-spacing:.08em;text-transform:uppercase;font-size:13px}
    .brand-icon{width:42px;height:42px;display:grid;place-items:center;border-radius:14px;background:rgba(255,255,255,.12);border:1px solid rgba(255,255,255,.18);font-size:22px}
    .demo{padding:8px 12px;border-radius:999px;background:rgba(255,255,255,.12);border:1px solid rgba(255,255,255,.18);font-size:12px;font-weight:800}
    .hero h1{margin:24px 0 6px;font-size:clamp(26px,4vw,42px);line-height:1.15;letter-spacing:-.03em;text-transform:uppercase;}
    .hero-sub{font-size:15px;color:#dcebf3;font-weight:700;margin-bottom:16px;}
    .hero p{max-width:830px;margin:0;color:#e4f1f8;font-size:15px}
    .meta-cards{display:flex;flex-wrap:wrap;gap:10px;margin-top:22px}
    .meta-card{padding:8px 14px;border-radius:12px;background:rgba(255,255,255,.10);border:1px solid rgba(255,255,255,.16);font-size:12.5px;font-weight:800}
    .generation-date{font-size:11.5px;color:#cfe5f1;margin-top:8px;}
    
    .kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-top:18px}
    .kpi{
      padding:18px;
      border-radius:20px;
      background:rgba(255,255,255,.11);
      border:1px solid rgba(255,255,255,.16);
    }
    .kpi-label{font-size:11px;text-transform:uppercase;letter-spacing:.08em;color:#cfe5f1;font-weight:900}
    .kpi-value{font-size:24px;line-height:1.1;font-weight:900;margin-top:4px}
    .kpi-note{font-size:12px;color:#dcebf3;margin-top:4px}

    /* Tabs Navigation */
    .tabs-wrapper { position:sticky; top:0; z-index:20; background:var(--bg); padding:10px 0 4px; }
    .tabs{
      display:grid;
      grid-template-columns:repeat(4,1fr);
      gap:10px;
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
      white-space:nowrap;
    }
    .tabs button:hover{background:#f8fbfd;}
    .tabs button.active{background:var(--navy);color:#fff;border-color:var(--navy)}
    
    /* Sub-navigation mobile */
    .sub-nav { display:none; gap:6px; overflow-x:auto; padding:6px 0; margin-top:6px; scrollbar-width:none; }
    .sub-nav a { flex:0 0 auto; padding:6px 12px; border-radius:999px; background:rgba(255,255,255,.8); border:1px solid var(--line); color:var(--navy); font-size:12px; font-weight:800; text-decoration:none; }

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
    .section h2{margin:0;font-size:clamp(20px,3vw,28px);line-height:1.15;letter-spacing:-.03em}
    .section .sub{margin:7px 0 0;color:var(--muted);font-size:14px;}
    .badge{display:inline-flex;align-items:center;gap:6px;padding:6px 10px;border-radius:999px;background:#eaf3fb;color:#205d90;font-size:11px;font-weight:900;text-transform:uppercase;letter-spacing:.06em}
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
    .card h3{margin:0 0 8px;font-size:17px;color:var(--navy)}
    .card p{margin:0;color:var(--muted);font-size:14px}
    .key{
      display:flex;
      gap:14px;
      align-items:flex-start;
      padding:18px;
      border-radius:17px;
      background:#f3f8fc;
      border:1px solid var(--line);
    }
    .key i{
      width:38px;height:38px;display:grid;place-items:center;flex:0 0 auto;
      border-radius:12px;background:#e5f1fb;font-style:normal;font-size:20px
    }
    .key strong{display:block;margin-bottom:4px;color:var(--navy);font-size:15px}
    
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
    .model-name-box{display:flex;align-items:center;gap:8px;flex-wrap:wrap;}
    .model-name{font-weight:900;color:var(--navy);font-size:16px}
    .status-badge { display:inline-block; padding:3px 8px; border-radius:6px; font-size:10.5px; font-weight:800; text-transform:uppercase; }
    .status-main { background:#dcfce7; color:#166534; }
    .status-inter { background:#fef3c7; color:#92400e; }
    .status-minor { background:#fee2e2; color:#991b1b; }
    .score-box { background:#ffffff; border:1px solid var(--line); padding:8px 10px; border-radius:10px; }
    .score-label { font-size:11.5px; color:var(--muted); }
    .bar{height:7px;background:#e7eef4;border-radius:999px;overflow:hidden;margin-top:4px}
    .fill{height:100%;border-radius:999px;}
    .chips{display:flex;flex-wrap:wrap;gap:5px;margin-top:6px}
    .chip{padding:4px 8px;border-radius:999px;background:#eaf3fb;color:#315f83;font-size:10.5px;font-weight:800}
    .model-details { margin-top:10px; border-top:1px dashed var(--line); padding-top:8px; font-size:13px; color:var(--ink); }
    .model-details summary { font-weight:800; color:var(--blue); cursor:pointer; font-size:12px; }
    .details-body { margin-top:6px; padding:10px; background:#f1f5f9; border-radius:10px; line-height:1.45; }
    .m-label { display:none; font-weight:800; color:var(--navy); margin-bottom:4px; font-size:12px; text-transform:uppercase; }

    .table-footnote { margin-top:12px; font-size:12px; color:var(--muted); font-style:italic; }
    .compare{
      display:grid;
      grid-template-columns:1fr 1fr;
      gap:14px;
    }
    .compare .card:first-child{border-top:5px solid var(--green)}
    .compare .card:last-child{border-top:5px solid var(--amber)}
    
    /* Zones Grid */
    .zones{display:grid;grid-template-columns:repeat(4,1fr);gap:14px}
    .zone{
      padding:20px;
      border-radius:18px;
      border:1px solid var(--line);
      background:#fbfdff;
    }
    .zone-summary { display:block; cursor:default; }
    .zone-short-desc { display:none; }
    .zone-chevron { display:none; }
    .zone-insufficient { background: #f8fafc; border-style: dashed; }
    .zone-notice { font-size: 13.5px; color: var(--muted); line-height: 1.5; margin: 10px 0; }
    .zone-head{display:flex;align-items:center;gap:10px;margin-bottom:10px}
    .zone-icon{font-size:24px}
    .zone h3{margin:0;font-size:16px;color:var(--navy)}
    .zone-details{list-style:none;padding:0;margin:0;font-size:13.5px;color:var(--ink)}
    .zone-details li{margin-bottom:5px;line-height:1.4}
    .zone-foot{display:flex;justify-content:space-between;gap:6px;flex-wrap:wrap;margin-top:12px;padding-top:10px;border-top:1px solid var(--line);font-size:11px;font-weight:800}
    .chip-conf { color:var(--green); background:#e6f4ea; padding:3px 8px; border-radius:6px; }
    .chip-uncert { color:var(--amber); background:#fef3c7; padding:3px 8px; border-radius:6px; }

    /* Timeline */
    .timeline{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}
    .phase{
      min-height:140px;
      padding:18px;
      border-radius:17px;
      border:1px solid var(--line);
      background:linear-gradient(180deg,#fbfdff,#f3f8fc);
    }
    .phase b{display:block;color:var(--blue);margin-bottom:8px}
    .phase p{margin:0;color:var(--muted);font-size:13.5px}

    /* Images */
    .cards3{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}
    .image-card{overflow:hidden;border-radius:18px;border:1px solid var(--line);background:white}
    .image-demo{
      height:200px;
      display:grid;
      place-items:center;
      padding:20px;
      text-align:center;
      background:linear-gradient(135deg,#eef4f8,#dce8f1);
      color:#4e687d;
      font-weight:900;
    }
    .image-caption{padding:16px}
    .image-caption h3{margin:0 0 8px;font-size:16px;color:var(--navy)}
    .image-caption p{margin:0;color:var(--muted);font-size:13px}
    .image-limit { margin-top:6px; padding:6px 10px; border-radius:8px; background:#fff3cd; color:#856404; font-size:12px; }
    .image-meta{display:flex;gap:6px;flex-wrap:wrap;margin-top:10px}

    /* Alert & LinkedIn */
    .alert{
      padding:18px;
      border-radius:17px;
      background:#fff8e7;
      border:1px solid #f2ddb0;
      color:#7a591d;
      font-weight:700;
    }
    .linkedin-box { position:relative; }
    .linkedin{
      padding:20px;
      border-radius:20px;
      background:#0d2f4f;
      color:white;
      white-space:pre-wrap;
      line-height:1.65;
      font-size:14.5px;
    }
    .linkedin-toggle-btn { display:none; margin-top:8px; width:100%; padding:10px; border-radius:10px; background:rgba(255,255,255,.15); color:white; border:none; font-weight:800; cursor:pointer; }
    .linkedin-toolbar { display:flex; justify-content:space-between; align-items:center; margin-top:12px; gap:10px; }
    .char-counter { font-size:12px; color:var(--muted); font-weight:700; }
    .copy{
      padding:12px 20px;border:0;border-radius:12px;
      background:var(--blue);color:white;font-weight:900;cursor:pointer;
      transition: background 0.15s ease;
      min-height:48px;
    }
    .copy:hover{background:#114fa8}
    .footer{padding:28px 8px 0;text-align:center;color:#6a7d8f;font-size:12px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px}
    .back-to-top { background:var(--surface); border:1px solid var(--line); padding:10px 16px; border-radius:10px; color:var(--navy); font-weight:800; cursor:pointer; min-height:44px; }
    .fab-top { display:none; position:fixed; bottom:20px; right:20px; z-index:99; width:48px; height:48px; border-radius:50%; background:var(--navy); color:white; border:2px solid white; box-shadow:0 6px 20px rgba(0,0,0,.25); font-size:20px; place-items:center; cursor:pointer; }

    /* Lightbox Modal */
    .lightbox-modal {
      display:none;
      position:fixed;
      inset:0;
      z-index:9999;
      background:rgba(0,0,0,0.92);
      flex-direction:column;
      justify-content:center;
      align-items:center;
      padding:16px;
    }
    .lightbox-modal.active { display:flex; }
    .lightbox-content { max-width:100%; max-height:80vh; object-fit:contain; border-radius:8px; }
    .lightbox-caption { color:white; text-align:center; margin-top:12px; max-width:600px; font-size:14px; }
    .lightbox-close { position:absolute; top:20px; right:20px; background:rgba(255,255,255,.2); color:white; border:none; width:44px; height:44px; border-radius:50%; font-size:22px; cursor:pointer; display:grid; place-items:center; }

    /* Evolution Box */
    .evolution-card { background: var(--surface-2); border: 1px solid var(--line); border-radius: 18px; padding: 20px; }
    .sparkline { font-family: monospace; font-size: 13px; line-height: 1.5; color: var(--ink); background: #ffffff; border: 1px solid var(--line); border-radius: 10px; padding: 12px; margin-top: 8px; }
    .sparkline-row { display: flex; justify-content: space-between; margin-bottom: 4px; }
    .trend-pill { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 700; }
    .trend-up { background: #dcfce7; color: #166534; }
    .trend-down { background: #fee2e2; color: #991b1b; }

    /* ==========================================================================
       RÈGLES RESPONSIVE MOBILE-FIRST STRICITES (< 650PX)
       ========================================================================== */
    @media(max-width:1100px){
      .zones{grid-template-columns:repeat(2,1fr)}
    }
    @media(max-width:950px){
      .kpis,.grid-4{grid-template-columns:repeat(2,1fr)}
      .grid-3,.cards3,.timeline{grid-template-columns:repeat(2,1fr)}
    }
    @media(max-width:650px){
      body { font-size:15px; }
      .page{width:min(100% - 14px,1180px);margin:6px auto 30px}
      
      /* En-tête mobile compact */
      .hero{padding:20px 16px;border-radius:22px;}
      .hero-top{flex-direction:column; gap:8px;}
      .hero h1{font-size:clamp(24px, 6vw, 30px); margin:12px 0 4px; line-height:1.2;}
      .hero-sub{font-size:13.5px; margin-bottom:12px; line-height:1.4;}
      .hero p{font-size:14px; line-height:1.45;}
      .meta-cards{display:grid; grid-template-columns:1fr 1fr; gap:6px; margin-top:14px;}
      .meta-card{padding:6px 10px; font-size:11.5px; text-align:center;}
      .generation-date{text-align:center; font-size:11px; margin-top:6px;}

      /* KPIs Mobile */
      .kpis { grid-template-columns: 1fr 1fr !important; gap:8px !important; margin-top:14px !important; }
      @media(max-width:400px){ .kpis { grid-template-columns: 1fr !important; } }
      .kpi { padding:12px !important; border-radius:14px !important; }
      .kpi-value { font-size:19px !important; }
      .kpi-note { font-size:11px !important; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }

      /* Tabs Mobile horizontaux avec scroll-snap */
      .tabs-wrapper { top:0; padding:6px 0; background:var(--bg); }
      .tabs {
        display: flex !important;
        overflow-x: auto !important;
        gap: 8px !important;
        scrollbar-width: none !important;
        scroll-snap-type: x mandatory !important;
        padding-bottom: 2px !important;
        -webkit-overflow-scrolling: touch;
      }
      .tabs::-webkit-scrollbar { display: none; }
      .tabs button {
        flex: 0 0 auto !important;
        min-width: 105px !important;
        scroll-snap-align: start !important;
        padding: 10px 14px !important;
        font-size: 13px !important;
        border-radius: 12px !important;
      }
      .sub-nav { display: flex !important; }

      /* Grilles et sections mobile */
      .grid-2,.grid-3,.grid-4,.zones,.cards3,.compare {
        grid-template-columns: 1fr !important;
        gap:10px !important;
      }
      .section{padding:16px !important; border-radius:20px !important; margin-top:14px !important;}
      .section-head{align-items:flex-start; flex-direction:column; margin-bottom:14px; gap:8px;}

      /* Cartes modèles véritables sur mobile */
      .model-table, .model-table tbody, .model-table tr, .model-table td {
        display: block !important;
        width: 100% !important;
      }
      .model-table thead { display: none !important; }
      .model-table tr {
        margin-bottom: 14px;
        border: 1px solid var(--line);
        border-radius: 16px;
        background: #f8fbfd;
        padding: 14px;
      }
      .model-table td {
        border: none !important;
        padding: 6px 0 !important;
      }
      .m-label { display: block !important; }

      /* Accordéons pour les 8 zones sur mobile */
      .zone-accordion {
        padding:0 !important;
        border-radius:14px !important;
        overflow:hidden;
        background:white !important;
      }
      .zone-summary {
        display:flex !important;
        justify-content:space-between !important;
        align-items:center !important;
        padding:14px !important;
        background:#f8fbfd !important;
        cursor:pointer !important;
        list-style:none !important;
      }
      .zone-summary::-webkit-details-marker { display:none; }
      .zone-short-desc { display:block !important; font-size:12.5px; color:var(--muted); margin-top:2px; max-width:210px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
      .zone-chevron { display:inline-block !important; font-size:11px; color:var(--muted); transition:transform 0.2s; }
      details[open] .zone-chevron { transform:rotate(180deg); }
      .zone-body { padding:14px !important; border-top:1px solid var(--line); }

      /* Chronologie verticale mobile */
      .timeline {
        display: flex !important;
        flex-direction: column !important;
        position: relative !important;
        padding-left: 20px !important;
        border-left: 2.5px solid var(--blue) !important;
        gap: 12px !important;
      }
      .phase {
        position: relative !important;
        min-height: auto !important;
        padding: 12px 14px !important;
        border-radius: 12px !important;
      }
      .phase::before {
        content: "" !important;
        position: absolute !important;
        left: -27px !important;
        top: 16px !important;
        width: 11px !important;
        height: 11px !important;
        border-radius: 50% !important;
        background: var(--blue) !important;
        border: 2px solid white !important;
      }

      /* LinkedIn mobile */
      .linkedin {
        max-height: 220px;
        overflow: hidden;
        position: relative;
        font-size:14px;
        padding:16px;
      }
      .linkedin.expanded { max-height: none; }
      .linkedin-toggle-btn { display: block !important; }
      .linkedin-toolbar { flex-direction: column; align-items: stretch; }
      .copy { width: 100%; text-align: center; }
      .fab-top { display: grid !important; }
    }

    @media (prefers-reduced-motion: reduce) {
      * { animation: none !important; transition: none !important; }
    }
    """

    html_template = """<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>PRÉVISIONS À MOYEN ET LONG TERME — Bulletin premium</title>
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
    <h1>PRÉVISIONS À MOYEN ET LONG TERME</h1>
    <div class="hero-sub">Analyse nationale • Comparaison multi-modèles • Consensus • Incertitudes • Deux prochaines semaines</div>
    <p>Analyse comparative multi-modèles, temps sensible par grandes zones, niveau de confiance et incertitudes.</p>
    
    <div class="meta-cards">
      <div class="meta-card">Semaine 1 : [W1_DATES_PLACEHOLDER]</div>
      <div class="meta-card">Semaine 2 : [W2_DATES_PLACEHOLDER]</div>
    </div>
    <div class="generation-date">Génération : [TODAY_STR_PLACEHOLDER]</div>

    <div class="kpis">
      <div class="kpi"><div class="kpi-label">Consensus</div><div class="kpi-value">[GLOBAL_CONSENSUS_KPI_PLACEHOLDER]</div><div class="kpi-note">[GLOBAL_CONSENSUS_NOTE_PLACEHOLDER]</div></div>
      <div class="kpi"><div class="kpi-label">Scénario</div><div class="kpi-value">[GLOBAL_SCENARIO_KPI_PLACEHOLDER]</div><div class="kpi-note">[GLOBAL_SCENARIO_NOTE_PLACEHOLDER]</div></div>
      <div class="kpi"><div class="kpi-label">Cartes</div><div class="kpi-value">[GLOBAL_CARDS_KPI_PLACEHOLDER]</div><div class="kpi-note">[GLOBAL_CARDS_NOTE_PLACEHOLDER]</div></div>
      <div class="kpi"><div class="kpi-label">Incertitude</div><div class="kpi-value">[GLOBAL_UNCERTAINTY_KPI_PLACEHOLDER]</div><div class="kpi-note">[GLOBAL_UNCERTAINTY_NOTE_PLACEHOLDER]</div></div>
    </div>
  </div>
</header>

<div class="tabs-wrapper">
  <nav class="tabs" role="tablist" aria-label="Navigation du bulletin">
    <button class="active" id="tab-week1" role="tab" aria-selected="true" aria-controls="week1" data-tab="week1">Semaine 1</button>
    <button id="tab-week2" role="tab" aria-selected="false" aria-controls="week2" data-tab="week2">Semaine 2</button>
    <button id="tab-summary" role="tab" aria-selected="false" aria-controls="summary" data-tab="summary">Synthèse</button>
    <button id="tab-doubts" role="tab" aria-selected="false" aria-controls="doubts" data-tab="doubts">Incertitudes</button>
  </nav>
  <div class="sub-nav">
    <a href="#sec-w1-keys">À retenir</a>
    <a href="#sec-w1-models">Modèles</a>
    <a href="#sec-w1-zones">Zones</a>
    <a href="#sec-w1-timeline">Chronologie</a>
    <a href="#sec-w1-images">Graphiques</a>
  </div>
</div>

<section id="week1" class="panel active" role="tabpanel" aria-labelledby="tab-week1">
  <div id="sec-w1-keys" class="section">
    <div class="section-head">
      <div><span class="badge">À retenir</span><h2>Semaine 1 — [W1_DATES_PLACEHOLDER]</h2><p class="sub">Les 4 à 5 informations principales par ordre d'importance.</p></div>
    </div>
    <div class="grid grid-2">
      [W1_KEYS_HTML_PLACEHOLDER]
    </div>
  </div>

  <div id="sec-w1-models" class="section">
    <div class="section-head">
      <div><span class="badge">Comparateur</span><h2>Ce que disent les modèles</h2><p class="sub">Lecture synthétique et deux niveaux d'analyse.</p></div>
    </div>
    <table class="model-table">
      <thead><tr><th>Modèle</th><th>Scénario</th><th>Temps sensible</th><th>Zones</th><th>Confiance & Soutien</th></tr></thead>
      <tbody>
        [W1_MODELS_HTML_PLACEHOLDER]
      </tbody>
    </table>
    <div class="table-footnote">
      📌 La confiance d'extraction mesure la clarté des informations. Le soutien du scénario qualifie son niveau de convergence (Majoritaire, Intermédiaire, Minoritaire, Isolé).
    </div>
  </div>

  <div class="section">
    <div class="section-head"><div><span class="badge">Analyse</span><h2>Convergences et divergences</h2></div></div>
    <div class="compare">
      <div class="card"><h3>Ce qui converge</h3><p>[W1_CONVERGENCES_PLACEHOLDER]</p></div>
      <div class="card"><h3>Ce qui diverge</h3><p>[W1_DIVERGENCES_PLACEHOLDER]</p></div>
    </div>
  </div>

  <div id="sec-w1-zones" class="section">
    <div class="section-head">
      <div><span class="badge">Temps sensible</span><h2>Prévision par 8 grandes zones géographiques</h2><p class="sub">Toucher une zone pour déplier les détails complets.</p></div>
    </div>
    <div class="zones">
      [W1_ZONES_HTML_PLACEHOLDER]
    </div>
  </div>

  <div id="sec-w1-timeline" class="section">
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

  <div id="sec-w1-images" class="section">
    <div class="section-head"><div><span class="badge">Graphiques clés</span><h2>Les images les plus pertinentes</h2><p class="sub">Images optimisées, touchez une carte pour l'agrandir.</p></div></div>
    <div class="cards3">
      [W1_IMAGES_HTML_PLACEHOLDER]
    </div>
  </div>
</section>

<section id="week2" class="panel" role="tabpanel" aria-labelledby="tab-week2">
  <div class="section">
    <div class="section-head">
      <div><span class="badge">À retenir</span><h2>Semaine 2 — [W2_DATES_PLACEHOLDER]</h2><p class="sub">Les 4 à 5 informations principales par ordre d'importance.</p></div>
    </div>
    <div class="grid grid-2">
      [W2_KEYS_HTML_PLACEHOLDER]
    </div>
  </div>

  <div class="section">
    <div class="section-head">
      <div><span class="badge">Comparateur</span><h2>Ce que disent les modèles</h2><p class="sub">Lecture synthétique et deux niveaux d'analyse.</p></div>
    </div>
    <table class="model-table">
      <thead><tr><th>Modèle</th><th>Scénario</th><th>Temps sensible</th><th>Zones</th><th>Confiance & Soutien</th></tr></thead>
      <tbody>
        [W2_MODELS_HTML_PLACEHOLDER]
      </tbody>
    </table>
    <div class="table-footnote">
      📌 La confiance d'extraction mesure la clarté des informations. Le soutien du scénario qualifie son niveau de convergence (Majoritaire, Intermédiaire, Minoritaire, Isolé).
    </div>
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
      <div><span class="badge">Temps sensible</span><h2>Prévision par 8 grandes zones géographiques</h2><p class="sub">Toucher une zone pour déplier les détails complets.</p></div>
    </div>
    <div class="zones">
      [W2_ZONES_HTML_PLACEHOLDER]
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
    <div class="section-head"><div><span class="badge">Graphiques clés</span><h2>Les images les plus pertinentes</h2><p class="sub">Images optimisées, touchez une carte pour l'agrandir.</p></div></div>
    <div class="cards3">
      [W2_IMAGES_HTML_PLACEHOLDER]
    </div>
  </div>
</section>

<section id="summary" class="panel" role="tabpanel" aria-labelledby="tab-summary">
  [WHAT_CHANGED_BOX_PLACEHOLDER]

  <div class="section">
    <div class="section-head"><div><span class="badge">Synthèse</span><h2>À retenir sur les deux semaines</h2></div></div>
    
    <div id="history-box" class="grid grid-2" style="margin-bottom:20px;">
        <div class="evolution-card">
            <h3>📈 Évolution de la confiance</h3>
            <div class="sparkline">
                [SPARKLINE_CONF_PLACEHOLDER]
            </div>
        </div>
        <div class="evolution-card">
            <h3>🌡️ Évolution des températures</h3>
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
    <div class="linkedin-box">
      <div id="linkedin" class="linkedin">[LINKEDIN_CLEAN_PLACEHOLDER]</div>
      <button id="linkedin-toggle" class="linkedin-toggle-btn" onclick="toggleLinkedIn()">Afficher le post complet</button>
    </div>
    <div class="linkedin-toolbar">
      <span id="char-count" class="char-counter">0 caractères</span>
      <button class="copy" onclick="copyLinkedIn()">Copier le post LinkedIn</button>
    </div>
    <div id="copy-status" aria-live="polite" style="margin-top:6px; font-weight:800; color:var(--green); text-align:center;"></div>
  </div>
</section>

<section id="doubts" class="panel" role="tabpanel" aria-labelledby="tab-doubts">
  <div class="section">
    <div class="section-head"><div><span class="badge">Transparence</span><h2>Méthodologie des scores & doutes</h2></div></div>
    <div class="alert" style="margin-bottom:16px;">
      💡 <b>Calcul des scores :</b> La <i>confiance d'extraction</i> évalue la clarté des informations. Le <i>soutien du scénario</i> qualifie le niveau d'accord entre les modélisations sans chiffre artificiel.
    </div>
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
<span>Bulletin généré automatiquement à partir des discussions et images du forum Infoclimat.</span>
<button class="back-to-top" onclick="window.scrollTo({top:0,behavior:'smooth'})">↑ Haut de page</button>
</footer>

</main>

<button id="fab-top" class="fab-top" onclick="window.scrollTo({top:0,behavior:'smooth'})" title="Retour en haut" aria-label="Retour en haut">↑</button>

<!-- Lightbox Visionneuse Plein Écran Mobile & Desktop -->
<div id="lightbox" class="lightbox-modal" onclick="closeLightbox(event)">
  <button class="lightbox-close" onclick="closeLightbox(event)">✕</button>
  <img id="lightbox-img" class="lightbox-content" src="" alt="Agrandissement carte météo">
  <div id="lightbox-caption" class="lightbox-caption"></div>
</div>

<script>
const buttons = document.querySelectorAll('.tabs button');
const panels = document.querySelectorAll('.panel');

function activateTab(tabId) {
  buttons.forEach(b => {
    const active = b.dataset.tab === tabId;
    b.classList.toggle('active', active);
    b.setAttribute('aria-selected', active ? 'true' : 'false');
  });
  panels.forEach(p => {
    p.classList.toggle('active', p.id === tabId);
  });
  try { localStorage.setItem('infoclimat_active_tab', tabId); } catch(e){}
}

buttons.forEach(btn => {
  btn.addEventListener('click', () => {
    activateTab(btn.dataset.tab);
    window.scrollTo({top: document.querySelector('.tabs-wrapper').offsetTop - 4, behavior: 'smooth'});
  });
});

const hash = window.location.hash.replace('#', '');
const savedTab = localStorage.getItem('infoclimat_active_tab');
if (['week1', 'week2', 'summary', 'doubts'].includes(hash)) {
  activateTab(hash);
} else if (savedTab && ['week1', 'week2', 'summary', 'doubts'].includes(savedTab)) {
  activateTab(savedTab);
}

// Mobile FAB Top button
const fabTop = document.getElementById('fab-top');
window.addEventListener('scroll', () => {
  if (window.scrollY > 400) {
    fabTop.style.display = 'grid';
  } else {
    fabTop.style.display = 'none';
  }
});

// Visionneuse Lightbox Modal
const lightbox = document.getElementById('lightbox');
const lightboxImg = document.getElementById('lightbox-img');
const lightboxCaption = document.getElementById('lightbox-caption');

document.querySelectorAll('.lightbox-trigger').forEach(img => {
  img.addEventListener('click', (e) => {
    e.preventDefault();
    const fullUrl = img.dataset.full || img.src;
    const title = img.dataset.title || '';
    const meta = img.dataset.meta || '';
    lightboxImg.src = fullUrl;
    lightboxCaption.innerHTML = '<strong>' + title + '</strong><br><small style="color:#cbd5e1;">' + meta + '</small>';
    lightbox.classList.add('active');
  });
});

function closeLightbox(e) {
  if (e.target === lightbox || e.target.classList.contains('lightbox-close')) {
    lightbox.classList.remove('active');
    lightboxImg.src = '';
  }
}

// Toggle LinkedIn text on mobile
function toggleLinkedIn() {
  const el = document.getElementById('linkedin');
  const btn = document.getElementById('linkedin-toggle');
  if (el.classList.contains('expanded')) {
    el.classList.remove('expanded');
    btn.textContent = 'Afficher le post complet';
  } else {
    el.classList.add('expanded');
    btn.textContent = 'Réduire le post';
  }
}

function copyLinkedIn() {
  const text = document.getElementById('linkedin').innerText;
  const statusEl = document.getElementById('copy-status');
  
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(text).then(() => {
      statusEl.textContent = '✓ Post LinkedIn copié dans le presse-papiers !';
      setTimeout(() => statusEl.textContent = '', 3000);
    }).catch(fallbackCopy);
  } else {
    fallbackCopy();
  }

  function fallbackCopy() {
    const ta = document.createElement('textarea');
    ta.value = text;
    document.body.appendChild(ta);
    ta.select();
    try {
      document.execCommand('copy');
      statusEl.textContent = '✓ Post LinkedIn copié dans le presse-papiers !';
      setTimeout(() => statusEl.textContent = '', 3000);
    } catch(e) {
      alert('Veuillez sélectionner et copier manuellement le texte du post.');
    }
    document.body.removeChild(ta);
  }
}

const linkText = document.getElementById('linkedin') ? document.getElementById('linkedin').innerText : '';
if(document.getElementById('char-count')) {
  document.getElementById('char-count').textContent = linkText.length + ' caractères';
}
</script>
</body>
</html>"""

    # Remplacement des variables dans le template
    html = html_template
    html = html.replace("[STYLE_PLACEHOLDER]", f"<style>\n{style}\n</style>")
    html = html.replace("[W1_DATES_PLACEHOLDER]", w1_dates)
    html = html.replace("[W2_DATES_PLACEHOLDER]", w2_dates)
    html = html.replace("[TODAY_STR_PLACEHOLDER]", today_str)
    
    html = html.replace("[W1_KEYS_HTML_PLACEHOLDER]", w1_keys_html)
    html = html.replace("[W1_MODELS_HTML_PLACEHOLDER]", w1_models_html)
    html = html.replace("[W1_ZONES_HTML_PLACEHOLDER]", w1_zones_html)
    html = html.replace("[W1_IMAGES_HTML_PLACEHOLDER]", w1_images_html)
    
    html = html.replace("[W2_KEYS_HTML_PLACEHOLDER]", w2_keys_html)
    html = html.replace("[W2_MODELS_HTML_PLACEHOLDER]", w2_models_html)
    html = html.replace("[W2_ZONES_HTML_PLACEHOLDER]", w2_zones_html)
    html = html.replace("[W2_IMAGES_HTML_PLACEHOLDER]", w2_images_html)
    
    html = html.replace("[W1_CONVERGENCES_PLACEHOLDER]", clean_text_typos(extract_tag(w1_content, "W1_CONVERGENCES")) or "-")
    html = html.replace("[W1_DIVERGENCES_PLACEHOLDER]", clean_text_typos(extract_tag(w1_content, "W1_DIVERGENCES")) or "-")
    
    html = html.replace("[W2_CONVERGENCES_PLACEHOLDER]", clean_text_typos(extract_tag(w2_content, "W2_CONVERGENCES")) or "-")
    html = html.replace("[W2_DIVERGENCES_PLACEHOLDER]", clean_text_typos(extract_tag(w2_content, "W2_DIVERGENCES")) or "-")

    # Chronologie Semaine 1
    html = html.replace("[W1_PHASE_1_DATES_PLACEHOLDER]", clean_text_typos(extract_tag(w1_content, "W1_PHASE_1_DATES")) or "Phase 1")
    html = html.replace("[W1_PHASE_1_PLACEHOLDER]", clean_text_typos(extract_tag(w1_content, "W1_PHASE_1")) or "-")
    html = html.replace("[W1_PHASE_2_DATES_PLACEHOLDER]", clean_text_typos(extract_tag(w1_content, "W1_PHASE_2_DATES")) or "Phase 2")
    html = html.replace("[W1_PHASE_2_PLACEHOLDER]", clean_text_typos(extract_tag(w1_content, "W1_PHASE_2")) or "-")
    html = html.replace("[W1_PHASE_3_DATES_PLACEHOLDER]", clean_text_typos(extract_tag(w1_content, "W1_PHASE_3_DATES")) or "Phase 3")
    html = html.replace("[W1_PHASE_3_PLACEHOLDER]", clean_text_typos(extract_tag(w1_content, "W1_PHASE_3")) or "-")
    html = html.replace("[W1_PHASE_4_DATES_PLACEHOLDER]", clean_text_typos(extract_tag(w1_content, "W1_PHASE_4_DATES")) or "Phase 4")
    html = html.replace("[W1_PHASE_4_PLACEHOLDER]", clean_text_typos(extract_tag(w1_content, "W1_PHASE_4")) or "-")

    # Chronologie Semaine 2
    html = html.replace("[W2_PHASE_1_DATES_PLACEHOLDER]", clean_text_typos(extract_tag(w2_content, "W2_PHASE_1_DATES")) or "Phase 1")
    html = html.replace("[W2_PHASE_1_PLACEHOLDER]", clean_text_typos(extract_tag(w2_content, "W2_PHASE_1")) or "-")
    html = html.replace("[W2_PHASE_2_DATES_PLACEHOLDER]", clean_text_typos(extract_tag(w2_content, "W2_PHASE_2_DATES")) or "Phase 2")
    html = html.replace("[W2_PHASE_2_PLACEHOLDER]", clean_text_typos(extract_tag(w2_content, "W2_PHASE_2")) or "-")
    html = html.replace("[W2_PHASE_3_DATES_PLACEHOLDER]", clean_text_typos(extract_tag(w2_content, "W2_PHASE_3_DATES")) or "Phase 3")
    html = html.replace("[W2_PHASE_3_PLACEHOLDER]", clean_text_typos(extract_tag(w2_content, "W2_PHASE_3")) or "-")
    html = html.replace("[W2_PHASE_4_DATES_PLACEHOLDER]", clean_text_typos(extract_tag(w2_content, "W2_PHASE_4_DATES")) or "Phase 4")
    html = html.replace("[W2_PHASE_4_PLACEHOLDER]", clean_text_typos(extract_tag(w2_content, "W2_PHASE_4")) or "-")

    # Solides / Fragiles
    html = html.replace("[W1_SOLID_POINTS_PLACEHOLDER]", clean_text_typos(extract_tag(w1_content, "W1_SOLID_POINTS")) or "-")
    html = html.replace("[W1_FRAGILE_POINTS_PLACEHOLDER]", clean_text_typos(extract_tag(w1_content, "W1_FRAGILE_POINTS")) or "-")
    html = html.replace("[W1_NEXT_RUNS_TO_WATCH_PLACEHOLDER]", clean_text_typos(extract_tag(w1_content, "W1_NEXT_RUNS_TO_WATCH")) or "-")
    
    html = html.replace("[W2_SOLID_POINTS_PLACEHOLDER]", clean_text_typos(extract_tag(w2_content, "W2_SOLID_POINTS")) or "-")
    html = html.replace("[W2_FRAGILE_POINTS_PLACEHOLDER]", clean_text_typos(extract_tag(w2_content, "W2_FRAGILE_POINTS")) or "-")
    html = html.replace("[W2_NEXT_RUNS_TO_WATCH_PLACEHOLDER]", clean_text_typos(extract_tag(w2_content, "W2_NEXT_RUNS_TO_WATCH")) or "-")

    # Synthèse globale et doutes
    html = html.replace("[GLOBAL_CONSENSUS_KPI_PLACEHOLDER]", clean_text_typos(kpi_consensus_val))
    html = html.replace("[GLOBAL_CONSENSUS_NOTE_PLACEHOLDER]", clean_text_typos(kpi_consensus_note))
    html = html.replace("[GLOBAL_SCENARIO_KPI_PLACEHOLDER]", clean_text_typos(kpi_scenario_val))
    html = html.replace("[GLOBAL_SCENARIO_NOTE_PLACEHOLDER]", clean_text_typos(kpi_scenario_note))
    html = html.replace("[GLOBAL_CARDS_KPI_PLACEHOLDER]", kpi_cards_val)
    html = html.replace("[GLOBAL_CARDS_NOTE_PLACEHOLDER]", kpi_cards_note)
    html = html.replace("[GLOBAL_UNCERTAINTY_KPI_PLACEHOLDER]", clean_text_typos(kpi_uncertainty_val))
    html = html.replace("[GLOBAL_UNCERTAINTY_NOTE_PLACEHOLDER]", clean_text_typos(kpi_uncertainty_note))

    html = html.replace("[GLOBAL_15_DAY_TREND_PLACEHOLDER]", clean_text_typos(extract_tag(global_content, "GLOBAL_15_DAY_TREND")) or "-")
    html = html.replace("[MOST_RELIABLE_WEEK_PLACEHOLDER]", clean_text_typos(extract_tag(global_content, "MOST_RELIABLE_WEEK")) or "-")
    html = html.replace("[GLOBAL_SOLID_POINTS_PLACEHOLDER]", clean_text_typos(extract_tag(global_content, "GLOBAL_SOLID_POINTS")) or "-")
    html = html.replace("[GLOBAL_RECURRING_PHENOMENA_PLACEHOLDER]", clean_text_typos(extract_tag(global_content, "GLOBAL_RECURRING_PHENOMENA")) or "-")
    html = html.replace("[GLOBAL_MAJOR_UNCERTAINTIES_PLACEHOLDER]", clean_text_typos(extract_tag(global_content, "GLOBAL_MAJOR_UNCERTAINTIES")) or "-")
    
    html = html.replace("[DOUBTS_TIMING_PLACEHOLDER]", clean_text_typos(extract_tag(doubts_content, "DOUBTS_TIMING")) or "-")
    html = html.replace("[DOUBTS_LOCATION_PLACEHOLDER]", clean_text_typos(extract_tag(doubts_content, "DOUBTS_LOCATION")) or "-")
    html = html.replace("[DOUBTS_INTENSITY_PLACEHOLDER]", clean_text_typos(extract_tag(doubts_content, "DOUBTS_INTENSITY")) or "-")
    html = html.replace("[MISSING_INFORMATION_PLACEHOLDER]", clean_text_typos(extract_tag(doubts_content, "MISSING_INFORMATION")) or "-")
    html = html.replace("[LOW_DOCUMENTED_MODELS_PLACEHOLDER]", clean_text_typos(extract_tag(doubts_content, "LOW_DOCUMENTED_MODELS")) or "-")
    html = html.replace("[UNCERTAIN_IMAGES_PLACEHOLDER]", clean_text_typos(extract_tag(doubts_content, "UNCERTAIN_IMAGES")) or "-")

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
    subject = f"PRÉVISIONS À MOYEN ET LONG TERME - {w1_dates.split('-')[0].strip()} & {w2_dates.split('-')[0].strip()}"
    clean_subj = unicodedata.normalize('NFKD', subject).encode('ASCII', 'ignore').decode('ASCII')
    subject = clean_subj
    
    filename = f"analyse_infoclimat_{datetime.datetime.now().strftime('%Y_%m_%d')}.html"
    
    html_body = html
    html_body = re.sub(r'<script>.*?</script>', '', html_body, flags=re.DOTALL)
    html_body = html_body.replace('.panel{display:none}', '.panel{display:block !important;margin-bottom:30px}')
    html_body = html_body.replace('.tabs-wrapper{', '.tabs-wrapper{display:none !important;')

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
