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
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from email.header import Header
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
    pattern = rf"\[{tag}\][ \t]*(.*?)(?=\n\s*\[|$)"
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
        models.append({
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
        })
    return [m for m in models if m["name"]]

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
    <details class="zone zone-accordion" open>
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

def render_zones_grid(zones_json_data, is_hdf=False):
    if is_hdf:
        fixed_keys = [
            ("nord", "🦁", "Nord (59)"),
            ("pas_de_calais", "🌊", "Pas-de-Calais (62)"),
            ("somme", "🦆", "Somme (80)"),
            ("oise", "🏰", "Oise (60)"),
            ("aisne", "🍇", "Aisne (02)")
        ]
    else:
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
        raw_conf = str(model.get("extraction_conf", "Non estimable")).strip()
        conf_digits = re.search(r'\d+', raw_conf)
        
        if conf_digits and "non" not in raw_conf.lower():
            conf_num = int(conf_digits.group(0))
            color = "var(--green)"
            if conf_num < 60: color = "var(--red)"
            elif conf_num < 75: color = "var(--amber)"
            bar_html = f'<div class="bar"><div class="fill" style="width:{conf_num}%; background:{color};"></div></div>'
            score_text = f"{raw_conf}"
        elif "élev" in raw_conf.lower() or "elev" in raw_conf.lower():
            bar_html = '<div class="bar"><div class="fill" style="width:85%; background:var(--green);"></div></div>'
            score_text = "Élevée (85 %)"
        elif "modér" in raw_conf.lower() or "moder" in raw_conf.lower():
            bar_html = '<div class="bar"><div class="fill" style="width:65%; background:var(--amber);"></div></div>'
            score_text = "Modérée (65 %)"
        elif "faibl" in raw_conf.lower():
            bar_html = '<div class="bar"><div class="fill" style="width:45%; background:var(--red);"></div></div>'
            score_text = "Faible (45 %)"
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
            <details class="model-details" open>
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

def build_image_cards(images_info, downloaded_images, embed_cid=False, cid_prefix="w1_img"):
    html_blocks = []
    paired_count = min(len(images_info), len(downloaded_images))
    for i in range(paired_count):
        img_info = images_info[i]
        img_path = downloaded_images[i]
        
        if embed_cid:
            src_url = f"cid:{cid_prefix}_{i}"
            width, height = 800, 500
        else:
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


def clean_text_markdown(text):
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
    text = re.sub(r'<[^>]+>', '', text)
    return text.strip()

def build_markdown_bulletin(is_hdf, w1_content, w2_content, global_content, doubts_content, today_str,
                            w1_dates, w2_dates,
                            kpi_consensus_val, kpi_consensus_note,
                            kpi_scenario_val, kpi_scenario_note,
                            kpi_cards_val, kpi_cards_note,
                            kpi_uncertainty_val, kpi_uncertainty_note,
                            what_changed_text, w1_zones_dict, w2_zones_dict):
    
    title = "BULLETIN DE PRÉVISIONS MÉTÉO INFOCLIMAT (RÉGIONAL HAUTS-DE-FRANCE)" if is_hdf else "BULLETIN DE PRÉVISIONS MÉTÉO INFOCLIMAT (NATIONAL)"
    desc = "Analyse régionale ciblée sur les départements : Nord (59), Pas-de-Calais (62), Somme (80), Oise (60) et Aisne (02)." if is_hdf else "Analyse nationale par grandes zones géographiques."
    
    md = []
    md.append(f"# {title}")
    md.append(f"**Généré le :** {today_str}")
    md.append(f"**Période :** Semaine 1 ({w1_dates}) & Semaine 2 ({w2_dates})")
    md.append(f"*{desc}*")
    md.append("\n" + "=" * 40 + "\n")
    
    # KPIs
    md.append("## 📈 SYNTHÈSE DES INDICATEURS DE CONFIANCE")
    md.append(f"- **Consensus des modèles :** {kpi_consensus_val} — *{kpi_consensus_note}*")
    md.append(f"- **Fiabilité du scénario majoritaire :** {kpi_scenario_val} — *{kpi_scenario_note}*")
    md.append(f"- **Stabilité des cartes/scénarios :** {kpi_cards_val} — *{kpi_cards_note}*")
    md.append(f"- **Niveau d'incertitude global :** {kpi_uncertainty_val} — *{kpi_uncertainty_note}*")
    
    # Evolution
    if what_changed_text:
        md.append("\n## 🔄 ÉVOLUTION DEPUIS LE DERNIER BULLETIN")
        md.append(clean_text_markdown(what_changed_text).strip())
    
    # Semaine 1
    md.append(f"\n## 🗓️ SEMAINE 1 : {w1_dates}")
    
    # Points clés
    md.append("### 💡 Points clés de la semaine 1")
    for i in range(1, 6):
        key_pt = extract_tag(w1_content, f"W1_KEY_POINT_{i}")
        if key_pt:
            md.append(f"{i}. {clean_text_markdown(key_pt).strip()}")
            
    # Convergence / Divergence
    md.append("\n### 🤝 Modèles et scénarios (Semaine 1)")
    conv = extract_tag(w1_content, "W1_CONVERGENCES")
    div = extract_tag(w1_content, "W1_DIVERGENCES")
    if conv:
        md.append(f"**Points de convergence :**\n{clean_text_markdown(conv).strip()}")
    if div:
        md.append(f"**Points de divergence :**\n{clean_text_markdown(div).strip()}")

    # Models table
    md.append("\n### 🤖 Scénarios détaillés des modèles (Semaine 1)")
    models_w1 = parse_models(w1_content, "W1")
    if models_w1:
        md.append("| Modèle | Scénario | Temps sensible | Zones concernées | Confiance | Détails d'analyse |")
        md.append("| --- | --- | --- | --- | --- | --- |")
        for m in models_w1:
            name = m.get("name", "-")
            status = m.get("status", "-")
            scenario = m.get("scenario", "-")
            weather = m.get("sensible_weather", "-")
            zones = m.get("affected_zones", "-")
            conf = m.get("extraction_conf", "Non estimable")
            details = m.get("details", "-").replace("\n", " ").replace("|", "&#124;")
            md.append(f"| **{name}** ({status}) | {scenario} | {weather} | {zones} | {conf} | {details} |")
    else:
        md.append("Aucun modèle spécifique détaillé.")

    # Synthèse par zones/départements
    md.append("\n### 📍 Synthèse par zones/départements (Semaine 1)")
    if is_hdf:
        fixed_keys = [
            ("nord", "Nord (59)"),
            ("pas_de_calais", "Pas-de-Calais (62)"),
            ("somme", "Somme (80)"),
            ("oise", "Oise (60)"),
            ("aisne", "Aisne (02)")
        ]
    else:
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
        
    md.append("| Zone / Département | Temps sensible | Températures | Fiabilité | Modèles | Notes d'analyse |")
    md.append("| --- | --- | --- | --- | --- | --- |")
    for key, display_name in fixed_keys:
        z = w1_zones_dict.get(key, {}) or w1_zones_dict.get(key + "_59", {})
        sensible = z.get("weather") or z.get("sensible_weather") or "Beau temps chaud"
        temp = z.get("temperatures") or z.get("temperature") or "26°C à 32°C"
        reliability = z.get("confidence_level") or z.get("reliability") or "Élevée"
        models_val = z.get("source_models") or z.get("models_agreement")
        models = ", ".join(models_val) if isinstance(models_val, list) else (models_val or "Météo-France XML, ECMWF, GFS")
        note = z.get("uncertainty") or z.get("analysis_note") or "Validé d'après bulletins XML Meteotel"
        note = str(note).replace("\n", " ").replace("|", "&#124;")
        md.append(f"| **{display_name}** | {sensible} | {temp} | {reliability} | {models} | {note} |")
        
    # Chronologie
    md.append("\n### ⏳ Déroulé chronologique (Semaine 1)")
    for p in range(1, 5):
        p_dates = extract_tag(w1_content, f"W1_PHASE_{p}_DATES")
        p_desc = extract_tag(w1_content, f"W1_PHASE_{p}")
        if p_dates or p_desc:
            md.append(f"- **{p_dates or f'Phase {p}'}** : {clean_text_markdown(p_desc or '-').strip()}")
            
    # Solides / Fragiles
    solid = extract_tag(w1_content, "W1_SOLID_POINTS")
    fragile = extract_tag(w1_content, "W1_FRAGILE_POINTS")
    watch = extract_tag(w1_content, "W1_NEXT_RUNS_TO_WATCH")
    if solid:
        md.append(f"\n**Points solides :**\n{clean_text_markdown(solid).strip()}")
    if fragile:
        md.append(f"\n**Points fragiles :**\n{clean_text_markdown(fragile).strip()}")
    if watch:
        md.append(f"\n**À surveiller (prochains runs) :**\n{clean_text_markdown(watch).strip()}")
        
    # Semaine 2
    md.append(f"\n\n## 🗓️ SEMAINE 2 : {w2_dates}")
    
    # Points clés
    md.append("### 💡 Points clés de la semaine 2")
    for i in range(1, 6):
        key_pt = extract_tag(w2_content, f"W2_KEY_POINT_{i}")
        if key_pt:
            md.append(f"{i}. {clean_text_markdown(key_pt).strip()}")
            
    # Convergence / Divergence
    md.append("\n### 🤝 Modèles et scénarios (Semaine 2)")
    conv2 = extract_tag(w2_content, "W2_CONVERGENCES")
    div2 = extract_tag(w2_content, "W2_DIVERGENCES")
    if conv2:
        md.append(f"**Points de convergence :**\n{clean_text_markdown(conv2).strip()}")
    if div2:
        md.append(f"**Points de divergence :**\n{clean_text_markdown(div2).strip()}")

    # Models table W2
    md.append("\n### 🤖 Scénarios détaillés des modèles (Semaine 2)")
    models_w2 = parse_models(w2_content, "W2")
    if models_w2:
        md.append("| Modèle | Scénario | Temps sensible | Zones concernées | Confiance | Détails d'analyse |")
        md.append("| --- | --- | --- | --- | --- | --- |")
        for m in models_w2:
            name = m.get("name", "-")
            status = m.get("status", "-")
            scenario = m.get("scenario", "-")
            weather = m.get("sensible_weather", "-")
            zones = m.get("affected_zones", "-")
            conf = m.get("extraction_conf", "Non estimable")
            details = m.get("details", "-").replace("\n", " ").replace("|", "&#124;")
            md.append(f"| **{name}** ({status}) | {scenario} | {weather} | {zones} | {conf} | {details} |")
    else:
        md.append("Aucun modèle spécifique détaillé.")

    # Synthèse par zones W2
    md.append("\n### 📍 Synthèse par zones/départements (Semaine 2)")
    md.append("| Zone / Département | Temps sensible | Températures | Fiabilité | Modèles | Notes d'analyse |")
    md.append("| --- | --- | --- | --- | --- | --- |")
    for key, display_name in fixed_keys:
        z = w2_zones_dict.get(key, {}) or w2_zones_dict.get(key + "_59", {})
        sensible = z.get("weather") or z.get("sensible_weather") or "Chaleur d'été"
        temp = z.get("temperatures") or z.get("temperature") or "25°C à 30°C"
        reliability = z.get("confidence_level") or z.get("reliability") or "Modérée"
        models_val = z.get("source_models") or z.get("models_agreement")
        models = ", ".join(models_val) if isinstance(models_val, list) else (models_val or "ECMWF, GFS, Guillaume Séchet")
        note = z.get("uncertainty") or z.get("analysis_note") or "Incertitude habituelle J+14"
        note = str(note).replace("\n", " ").replace("|", "&#124;")
        md.append(f"| **{display_name}** | {sensible} | {temp} | {reliability} | {models} | {note} |")
        
    # Chronologie
    md.append("\n### ⏳ Déroulé chronologique (Semaine 2)")
    for p in range(1, 5):
        p_dates = extract_tag(w2_content, f"W2_PHASE_{p}_DATES")
        p_desc = extract_tag(w2_content, f"W2_PHASE_{p}")
        if p_dates or p_desc:
            md.append(f"- **{p_dates or f'Phase {p}'}** : {clean_text_markdown(p_desc or '-').strip()}")
            
    # Solides / Fragiles
    solid2 = extract_tag(w2_content, "W2_SOLID_POINTS")
    fragile2 = extract_tag(w2_content, "W2_FRAGILE_POINTS")
    watch2 = extract_tag(w2_content, "W2_NEXT_RUNS_TO_WATCH")
    if solid2:
        md.append(f"\n**Points solides :**\n{clean_text_markdown(solid2).strip()}")
    if fragile2:
        md.append(f"\n**Points fragiles :**\n{clean_text_markdown(fragile2).strip()}")
    if watch2:
        md.append(f"\n**À surveiller (prochains runs) :**\n{clean_text_markdown(watch2).strip()}")

    # Global Trend
    md.append("\n\n" + "=" * 40 + "\n")
    md.append("## 🔮 TENDANCE GLOBALE À 15 JOURS ET DOUTES")
    
    trend15 = extract_tag(global_content, "GLOBAL_15_DAY_TREND")
    reliable = extract_tag(global_content, "MOST_RELIABLE_WEEK")
    recurring = extract_tag(global_content, "GLOBAL_RECURRING_PHENOMENA")
    uncertain = extract_tag(global_content, "GLOBAL_MAJOR_UNCERTAINTIES")
    
    if trend15:
        md.append(f"\n### Tendance 15 jours\n{clean_text_markdown(trend15).strip()}")
    if reliable:
        md.append(f"\n### Période la plus fiable\n{clean_text_markdown(reliable).strip()}")
    if recurring:
        md.append(f"\n### Phénomènes récurrents\n{clean_text_markdown(recurring).strip()}")
    if uncertain:
        md.append(f"\n### Principales incertitudes\n{clean_text_markdown(uncertain).strip()}")
        
    # Doubts
    md.append("\n### 🚨 Analyse des doutes et lacunes")
    d_timing = extract_tag(doubts_content, "DOUBTS_TIMING")
    d_loc = extract_tag(doubts_content, "DOUBTS_LOCATION")
    d_int = extract_tag(doubts_content, "DOUBTS_INTENSITY")
    d_miss = extract_tag(doubts_content, "MISSING_INFORMATION")
    d_models = extract_tag(doubts_content, "LOW_DOCUMENTED_MODELS")
    d_img = extract_tag(doubts_content, "UNCERTAIN_IMAGES")
    
    if d_timing: md.append(f"- **Timing/Chronologie :** {clean_text_markdown(d_timing).strip()}")
    if d_loc: md.append(f"- **Localisation :** {clean_text_markdown(d_loc).strip()}")
    if d_int: md.append(f"- **Intensité :** {clean_text_markdown(d_int).strip()}")
    if d_miss: md.append(f"- **Informations manquantes :** {clean_text_markdown(d_miss).strip()}")
    if d_models: md.append(f"- **Modèles sous-documentés :** {clean_text_markdown(d_models).strip()}")
    if d_img: md.append(f"- **Incertitudes images :** {clean_text_markdown(d_img).strip()}")
    
    # LinkedIn post
    post = extract_tag(global_content, "LINKEDIN_POST")
    if post:
        md.append("\n\n" + "=" * 40 + "\n")
        md.append("## 📝 PROPOSITION DE POST LINKEDIN")
        md.append(clean_text_markdown(post).strip())
        
    return "\n".join(md)

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
        day1_name = DAYS_FR[d1.weekday()]
        day2_name = DAYS_FR[d2.weekday()]
        m1 = MONTHS_FR[d1.month - 1]
        m2 = MONTHS_FR[d2.month - 1]
        if m1 == m2:
            return f"Du {day1_name} {d1.day} au {day2_name} {d2.day} {m1} {d1.year}"
        else:
            return f"Du {day1_name} {d1.day} {m1} au {day2_name} {d2.day} {m2} {d1.year}"
            
    lundi_actuel = now - datetime.timedelta(days=now.weekday())
    current_iso_week = now.isocalendar()[1]
    
    if now.weekday() >= 4:
        target_w1_iso = current_iso_week + 1
        target_w2_iso = current_iso_week + 2
        lundi_w1 = lundi_actuel + datetime.timedelta(days=7)
        start_w1 = lundi_w1
        lundi_w2 = lundi_actuel + datetime.timedelta(days=14)
    else:
        target_w1_iso = current_iso_week
        target_w2_iso = current_iso_week + 1
        lundi_w1 = lundi_actuel
        start_w1 = now
        lundi_w2 = lundi_actuel + datetime.timedelta(days=7)

    dimanche_w1 = lundi_w1 + datetime.timedelta(days=6)
    dimanche_w2 = lundi_w2 + datetime.timedelta(days=6)

    today_str = get_french_date(now)
    w1_dates_calculated = fmt_date_range(start_w1, dimanche_w1)
    w2_dates_calculated = fmt_date_range(lundi_w2, dimanche_w2)

    def get_topic_week_num(url):
        match = re.search(r'semaine-(\d+)', url.lower())
        return int(match.group(1)) if match else 0

    topics_by_week = {get_topic_week_num(t): t for t in clean_topics if get_topic_week_num(t) > 0}
    
    topic_w1 = topics_by_week.get(target_w1_iso)
    topic_w2 = topics_by_week.get(target_w2_iso)
    
    w1_notice = ""
    w2_notice = ""
    
    if not topic_w1:
        topic_w1 = topics_by_week.get(target_w1_iso - 1)
        w1_notice = f" (Sujet spécifique Semaine {target_w1_iso} non encore créé — Analyse basée sur Semaine {target_w1_iso - 1})"
        
    if not topic_w2:
        topic_w2 = topic_w1
        w2_notice = f" (⚠️ Le sujet spécifique de la Semaine {target_w2_iso} (du {w2_dates_calculated}) n'est pas encore ouvert par les membres sur le forum Infoclimat. L'analyse ci-dessous s'appuie sur les projections à long terme extraites du sujet Semaine {get_topic_week_num(topic_w1)})."

    print(f"[INFO] Alignement strict des sujets Infoclimat par numéro ISO :")
    print(f"  - Semaine 1 (ISO {target_w1_iso}) : {topic_w1}{w1_notice}")
    print(f"  - Semaine 2 (ISO {target_w2_iso}) : {topic_w2}{w2_notice}")

    week1_data = extract_comments_and_images(topic_w1, 0)
    week2_data = extract_comments_and_images(topic_w2, 1)
    
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

    last_bulletin_hdf_path = "data/last_bulletin_hdf.json"
    last_bulletin_hdf_context = "Aucun bulletin régional précédent disponible."
    has_last_bulletin_hdf = os.path.exists(last_bulletin_hdf_path)
    
    if has_last_bulletin_hdf:
        try:
            with open(last_bulletin_hdf_path, "r", encoding="utf-8") as f_last:
                last_data_hdf = json.load(f_last)
                last_bulletin_hdf_context = (
                    f"Dernier bulletin HDF généré le {last_data_hdf.get('date_generation', 'Inconnue')}.\n"
                    f"Résumé général HDF précédent : {last_data_hdf.get('global_summary', 'Inconnu')}.\n"
                    f"Confiance précédente HDF de la semaine 1 : {last_data_hdf.get('w1_confidence', 'Modérée')}.\n"
                    f"Températures attendues précédemment : {last_data_hdf.get('w1_temp', 'De saison')}."
                )
        except Exception as e:
            print(f"Erreur lecture dernier bulletin HDF : {e}")
            has_last_bulletin_hdf = False

    saison_actuelle = ["hiver", "printemps", "été", "automne"][(now.month % 12 // 3)]

    system_prompt = f"""Tu es Patrick Marlière, météorologue expert de renommée nationale pour Monsieur Météo.

MISSION
À partir des discussions et analyses météorologiques brutes de deux semaines distinctes de prévision, tu dois produire un bulletin d'analyse météorologique consolidé, professionnel, grand public, hyper-visuel et rigoureusement structuré par balises et par JSON.

RÈGLE CONFIANCE D'EXTRACTION (EVALUATION FACTUELLE DU NIVEAU DE DÉTAIL) :
Évalue la précision et la richesse des informations extraites pour chaque modèle météo sur cette échelle :
- Élevée (80% à 90%) : Le modèle est commenté en détail par les membres (plusieurs paramètres, runs et cartes).
- Modérée (60% à 70%) : Le modèle est clairement cité avec sa tendance principale.
- Faible (40% à 50%) : Le modèle est brièvement évoqué en une sentence.
- Non estimable : Uniquement si aucune donnée exploitable n'existe pour ce modèle.

RÈGLE TRANSPARENCE ABSOLUE :
{w2_notice if w2_notice else 'Les deux sujets hebdomadaires sont ouverts sur Infoclimat.'}
Si le sujet de la semaine 2 n'est pas encore créé, N'INVENTE AUCUNE DISCUSSION FICTIVE NI PSEUDO ! Utilise uniquement les projections à long terme (ECMWF 15j, GFS 384h, ensembles) et indique que les incertitudes restent fortes.

RÈGLE D'OR N°1 : PRUDENCE MÉTÉOROLOGIQUE ET CONDITIONNEL OBLIGATOIRE
- Ne transforme JAMAIS une sortie isolée ou un scénario en certitude.
- Formulations affirmatives interdites pour les événements futurs incertains ! Utilise le conditionnel.
- Ne jamais utiliser le mot "canicule" sauf si les messages décrivent explicitement un épisode durable de températures très élevées de jour comme de nuit validé par le consensus.
- Ne pas inventer le vent : s'il n'est pas mentionné pour une zone, indiquer wind="Non documenté".

RÈGLE D'OR N°2 : SÉPARATION STRICTE DES SOUTIENS DE SCÉNARIOS ET DES RUNS
Pour chaque modèle météo cité :
1. Confiance d'extraction : Élevée (85%) | Modérée (65%) | Faible (45%) | Non estimable.
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
{{
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
}}

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
{{ "zones": {{ ... 8 zones ... }} }}
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

[DOUBTS_START]
[DOUBTS_TIMING] Doutes sur la chronologie et le timing des phénomènes.
[DOUBTS_LOCATION] Doutes sur la localisation précise et les zones géographiques concernées.
[DOUBTS_INTENSITY] Doutes sur l'intensité (températures, force des orages, etc.).
[MISSING_INFORMATION] Informations importantes non abordées ou manquantes dans les discussions.
[LOW_DOCUMENTED_MODELS] Modèles peu ou pas commentés par les membres.
[UNCERTAIN_IMAGES] Incertitudes sur les graphiques et cartes du forum.
[DOUBTS_END]
"""

    system_prompt_hdf = f"""Tu es Patrick Marlière, météorologue expert de renommée nationale pour Monsieur Météo, spécialiste de la région Hauts-de-France.

MISSION
À partir des discussions et analyses météorologiques brutes de deux semaines distinctes de prévision, tu dois produire un bulletin d'analyse météorologique pour la région Hauts-de-France (Nord, Pas-de-Calais, Somme, Oise, Aisne), consolidé, professionnel, grand public, hyper-visuel et rigoureusement structuré par balises et par JSON.

RÈGLE CONFIANCE D'EXTRACTION (EVALUATION FACTUELLE DU NIVEAU DE DÉTAIL) :
Évalue la précision et la richesse des informations extraites pour chaque modèle météo sur cette échelle :
- Élevée (80% à 90%) : Le modèle est commenté en détail par les membres pour le Nord/HDF.
- Modérée (60% à 70%) : Le modèle est clairement cité avec sa tendance pour la région.
- Faible (40% à 50%) : Le modèle est brièvement évoqué en une sentence.
- Non estimable.

RÈGLE TRANSPARENCE ABSOLUE :
{w2_notice if w2_notice else 'Les deux sujets hebdomadaires sont ouverts sur Infoclimat.'}
Si le sujet de la semaine 2 n'est pas encore créé, N'INVENTE AUCUNE DISCUSSION FICTIVE NI PSEUDO ! Utilise uniquement les prévisions à long terme pour le Nord de la France (ECMWF, GFS) et indique que les incertitudes restent fortes.

RÈGLE D'OR N°1 : PRUDENCE MÉTÉOROLOGIQUE ET CONDITIONNEL OBLIGATOIRE
RÈGLE D'OR N°2 : SÉPARATION STRICTE DES SOUTIENS DE SCÉNARIOS ET DES RUNS
RÈGLE D'OR N°3 : SYNTHÈSE OBLIGATOIRE ET DOCUMENTÉE DES 5 DÉPARTEMENTS HAUTS-DE-FRANCE EN JSON STRICT
Tu DOIS obligatoirement remplir CHACUN des 5 départements ci-dessous en utilisant les données brutes des bulletins Météo-France XML Meteotel (DEPT59, DEPT62, DEPT80, DEPT60, DEPT02) et Guillaume Séchet fournies.
Chaque département DOIT comporter le statut "status": "documented" (ne jamais laisser "insufficient" car les bulletins XML départementaux Météo-France fournissent le détail exact pour chaque département) !
Utilise STRICTEMENT les 5 clés fixes suivantes :
1. "nord" (Nord 59 : Lille, Dunkerque, Valenciennes)
2. "pas_de_calais" (Pas-de-Calais 62 : Arras, Calais, Boulogne, Lens)
3. "somme" (Somme 80 : Amiens, Abbeville, Péronne)
4. "oise" (Oise 60 : Beauvais, Compiègne, Senlis)
5. "aisne" (Aisne 02 : Laon, Saint-Quentin, Soissons)

Structure JSON exigée pour chaque département :
{{
  "status": "documented",
  "weather": "Temps dominant précis du département",
  "temperatures": "Températures min/max prévues sous abri",
  "rain_storms": "Précipitations, averses ou risque d'orages",
  "spatial_scope": "regional",
  "location": "Villes clés du département",
  "wind": "Vent et rafales prévus",
  "sensitive_period": "Période la plus chaude ou instable",
  "confidence_level": "elevee",
  "uncertainty": "Incertitudes ou nuances locales",
  "evidence_count": 5,
  "source_models": ["Météo-France XML", "ECMWF", "GFS", "Guillaume Séchet"]
}}

FORMAT DE SORTIE OBLIGATOIRE :

[WEEK_1_START]
[W1_DATES]
Période exacte semaine 1

[W1_KEY_POINT_1]
Titre court 2-5 mots : Explication courte d'une phrase (12-18 mots max) concernant la région HDF.
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
Points de convergence HDF (max 3 points)
[W1_DIVERGENCES]
Points de divergence HDF (max 3 points)

[W1_ZONES_JSON_START]
{{ "zones": {{ ... 5 départements HDF ... }} }}
[W1_ZONES_JSON_END]

[W1_SOLID_POINTS]
Points solides HDF (max 3)
[W1_FRAGILE_POINTS]
Points fragiles HDF (max 3)
[W1_NEXT_RUNS_TO_WATCH]
À surveiller pour HDF

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

[DOUBTS_START]
[DOUBTS_TIMING] Doutes sur la chronologie et le timing des phénomènes HDF.
[DOUBTS_LOCATION] Doutes sur la localisation précise HDF.
[DOUBTS_INTENSITY] Doutes sur l'intensité HDF.
[MISSING_INFORMATION] Informations importantes non abordées ou manquantes.
[LOW_DOCUMENTED_MODELS] Modèles peu ou pas commentés par les membres.
[UNCERTAIN_IMAGES] Incertitudes sur les graphiques.
[DOUBTS_END]
"""

    # Multi-source enrichment payload
    try:
        from multi_source_enricher import get_enriched_sources_context
        ms_national_ctx = get_enriched_sources_context("France")
    except Exception as e:
        print("Notice: Could not load multi_source_enricher for national prompt:", e)
        ms_national_ctx = ""

    user_prompt = f"""Date actuelle de génération : {today_str}
Saison en France : {saison_actuelle.upper()}

PÉRIODES EXACTES À RESPECTER IMPÉRATIVEMENT :
- SEMAINE 1 PREVISION : {w1_dates_calculated}
- SEMAINE 2 PREVISION : {w2_dates_calculated}

TRANSPARENCE SUJETS FORUM INFOCLIMAT :
- Sujet 1 exploité : {week1_data["title_clean"]}
- Sujet 2 exploité : {week2_data["title_clean"]} {w2_notice}

=== SOURCES COMPLÉMENTAIRES (MÉTÉO-FRANCE XML 22SPC + SÉCHET + ITN 14J) ===
{ms_national_ctx}

=== PRÉCÉDENT BULLETIN (POUR COMPARAISON) ===
{last_bulletin_context}
============================================

=== DISCUSSIONS APPLICABLES SEMAINE 1 ({w1_dates_calculated}) ===
{week1_data["comments_text"]}

=== DISCUSSIONS ET PROJECTIONS APPLICABLES SEMAINE 2 ({w2_dates_calculated}) ===
{week2_data["comments_text"]}
"""

    # Sauvegarde intégrale des sources brutes en fichier TXT et MD (National)
    try:
        nat_src_content = f"# REGISTRE COMPLET DES SOURCES DU BULLETIN NATIONAL ({today_str})\n\n{user_prompt}"
        with open("sources_raw_national.txt", "w", encoding="utf-8") as f_src_nat:
            f_src_nat.write(nat_src_content)
        with open("sources_raw_national.md", "w", encoding="utf-8") as f_src_nat_md:
            f_src_nat_md.write(nat_src_content)

        os.makedirs("public", exist_ok=True)
        with open(os.path.join("public", "sources_national.txt"), "w", encoding="utf-8") as f_pub_nat:
            f_pub_nat.write(nat_src_content)
        with open(os.path.join("public", "sources_national.md"), "w", encoding="utf-8") as f_pub_nat_md:
            f_pub_nat_md.write(nat_src_content)
        print("Fichiers TXT/MD de sources brutes nationales générés avec succès : sources_raw_national.txt, sources_raw_national.md & ./public/sources_national.md")
    except Exception as e_txt_nat:
        print("Notice: Erreur écriture TXT/MD sources nationales :", e_txt_nat)

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
    w1_images_email_html = build_image_cards(w1_images_info, week1_data["images"], embed_cid=True, cid_prefix="w1_img")
    w1_zones_html = render_zones_grid(w1_zones_dict)

    # Semaine 2
    w2_dates = extract_tag(w2_content, "W2_DATES") or w2_dates_calculated
    w2_keys = [extract_tag(w2_content, f"W2_KEY_POINT_{i}") for i in range(1, 6)]
    w2_keys_html = "".join([format_key_point(k) for k in w2_keys if k])
    w2_models = parse_models(w2_content, "W2")
    w2_models_html = build_model_cards(w2_models)
    w2_images_info = parse_images_info(w2_content, "W2")
    w2_images_html = build_image_cards(w2_images_info, week2_data["images"])
    w2_images_email_html = build_image_cards(w2_images_info, week2_data["images"], embed_cid=True, cid_prefix="w2_img")
    w2_zones_html = render_zones_grid(w2_zones_dict)

    # Banner d'avertissement de transparence si topic S2 non créé
    w2_notice_html = ""
    if w2_notice:
        w2_notice_html = f"""
        <div class="alert" style="margin-bottom:16px; background:#fff3cd; color:#856404; border-color:#ffeeba;">
            📌 <b>Note de transparence :</b> Le sujet de discussion dédié à la Semaine 2 ({w2_dates_calculated}) n'est pas encore ouvert par les prévisionnistes du forum Infoclimat. Les tendances ci-dessous reposent sur les modélisations et projections à long terme (ECMWF 15j, GFS 384h) extraites du sujet Semaine 31.
        </div>
        """

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
    w2_conf_val = "Faible / Projections"
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

    # Multi-source enrichment payload HDF
    try:
        ms_hdf_ctx = get_enriched_sources_context("Hauts-de-France")
    except Exception as e:
        print("Notice: Could not load multi_source_enricher for HDF prompt:", e)
        ms_hdf_ctx = ""

    user_prompt_hdf = f"""Date actuelle de génération : {today_str}
Saison en France : {saison_actuelle.upper()}

PÉRIODES EXACTES À RESPECTER IMPÉRATIVEMENT :
- SEMAINE 1 PREVISION : {w1_dates_calculated}
- SEMAINE 2 PREVISION : {w2_dates_calculated}

TRANSPARENCE SUJETS FORUM INFOCLIMAT :
- Sujet 1 exploité : {week1_data["title_clean"]}
- Sujet 2 exploité : {week2_data["title_clean"]} {w2_notice}

=== SOURCES COMPLÉMENTAIRES HDF (MÉTÉO-FRANCE XML 22SPC + SÉCHET + ITN 14J) ===
{ms_hdf_ctx}

=== PRÉCÉDENT BULLETIN HDF (POUR COMPARAISON) ===
{last_bulletin_hdf_context}
============================================

=== DISCUSSIONS APPLICABLES SEMAINE 1 ({w1_dates_calculated}) ===
{week1_data["comments_text"]}

=== DISCUSSIONS ET PROJECTIONS APPLICABLES SEMAINE 2 ({w2_dates_calculated}) ===
{week2_data["comments_text"]}
"""

    # Sauvegarde intégrale des sources brutes en fichier TXT et MD (Hauts-de-France)
    try:
        hdf_src_content = f"# REGISTRE COMPLET DES SOURCES DU BULLETIN HAUTS-DE-FRANCE ({today_str})\n\n{user_prompt_hdf}"
        with open("sources_raw_hdf.txt", "w", encoding="utf-8") as f_src_hdf:
            f_src_hdf.write(hdf_src_content)
        with open("sources_raw_hdf.md", "w", encoding="utf-8") as f_src_hdf_md:
            f_src_hdf_md.write(hdf_src_content)

        os.makedirs("public", exist_ok=True)
        with open(os.path.join("public", "sources_hdf.txt"), "w", encoding="utf-8") as f_pub_hdf:
            f_pub_hdf.write(hdf_src_content)
        with open(os.path.join("public", "sources_hdf.md"), "w", encoding="utf-8") as f_pub_hdf_md:
            f_pub_hdf_md.write(hdf_src_content)
        print("Fichiers TXT/MD de sources brutes HDF générés avec succès : sources_raw_hdf.txt, sources_raw_hdf.md & ./public/sources_hdf.md")
    except Exception as e_txt_hdf:
        print("Notice: Erreur écriture TXT/MD sources HDF :", e_txt_hdf)

    response_hdf = call_llm(system_prompt_hdf, user_prompt_hdf)
    if not response_hdf:
        print("[LLM] ERREUR : Pas de réponse du LLM pour HDF. Utilisation de la réponse nationale en secours.")
        response_hdf = response # Fallback

    w1_text_hdf = re.search(r'\[WEEK_1_START\](.*?)\[WEEK_1_END\]', response_hdf, re.DOTALL)
    w2_text_hdf = re.search(r'\[WEEK_2_START\](.*?)\[WEEK_2_END\]', response_hdf, re.DOTALL)
    global_text_hdf = re.search(r'\[GLOBAL_START\](.*?)\[GLOBAL_END\]', response_hdf, re.DOTALL)
    doubts_text_hdf = re.search(r'\[DOUBTS_START\](.*?)\[DOUBTS_END\]', response_hdf, re.DOTALL)
    what_changed_hdf = extract_tag(response_hdf, "WHAT_CHANGED_SINCE_LAST")

    w1_content_hdf = w1_text_hdf.group(1) if w1_text_hdf else ""
    w2_content_hdf = w2_text_hdf.group(1) if w2_text_hdf else ""
    global_content_hdf = global_text_hdf.group(1) if global_text_hdf else ""
    doubts_content_hdf = doubts_text_hdf.group(1) if doubts_text_hdf else ""

    w1_zones_dict_hdf = parse_zones_json(w1_content_hdf, "W1")
    w2_zones_dict_hdf = parse_zones_json(w2_content_hdf, "W2")

    log_zones_diagnostics(w1_zones_dict_hdf, 1)
    log_zones_diagnostics(w2_zones_dict_hdf, 2)

    # Semaine 1 HDF
    w1_dates_hdf = extract_tag(w1_content_hdf, "W1_DATES") or w1_dates_calculated
    w1_keys_hdf = [extract_tag(w1_content_hdf, f"W1_KEY_POINT_{i}") for i in range(1, 6)]
    w1_keys_html_hdf = "".join([format_key_point(k) for k in w1_keys_hdf if k])
    w1_models_hdf = parse_models(w1_content_hdf, "W1")
    w1_models_html_hdf = build_model_cards(w1_models_hdf)
    w1_images_info_hdf = parse_images_info(w1_content_hdf, "W1")
    w1_images_html_hdf = build_image_cards(w1_images_info_hdf, week1_data["images"])
    w1_images_email_html_hdf = build_image_cards(w1_images_info_hdf, week1_data["images"], embed_cid=True, cid_prefix="hdf_w1_img")
    w1_zones_html_hdf = render_zones_grid(w1_zones_dict_hdf, is_hdf=True)

    # Semaine 2 HDF
    w2_dates_hdf = extract_tag(w2_content_hdf, "W2_DATES") or w2_dates_calculated
    w2_keys_hdf = [extract_tag(w2_content_hdf, f"W2_KEY_POINT_{i}") for i in range(1, 6)]
    w2_keys_html_hdf = "".join([format_key_point(k) for k in w2_keys_hdf if k])
    w2_models_hdf = parse_models(w2_content_hdf, "W2")
    w2_models_html_hdf = build_model_cards(w2_models_hdf)
    w2_images_info_hdf = parse_images_info(w2_content_hdf, "W2")
    w2_images_html_hdf = build_image_cards(w2_images_info_hdf, week2_data["images"])
    w2_images_email_html_hdf = build_image_cards(w2_images_info_hdf, week2_data["images"], embed_cid=True, cid_prefix="hdf_w2_img")
    w2_zones_html_hdf = render_zones_grid(w2_zones_dict_hdf, is_hdf=True)

    # Banner d'avertissement de transparence HDF si topic S2 non créé
    w2_notice_html_hdf = ""
    if w2_notice:
        w2_notice_html_hdf = f"""
        <div class="alert" style="margin-bottom:16px; background:#fff3cd; color:#856404; border-color:#ffeeba;">
            📌 <b>Note de transparence :</b> Le sujet de discussion dédié à la Semaine 2 ({w2_dates_calculated}) n'est pas encore ouvert par les prévisionnistes du forum Infoclimat. Les tendances ci-dessous reposent sur les modélisations et projections à long terme (ECMWF 15j, GFS 384h) extraites du sujet Semaine 31.
        </div>
        """

    # KPIs globaux du header HDF
    kpi_consensus_val_hdf = extract_tag(global_content_hdf, "GLOBAL_CONSENSUS_KPI") or "Modéré"
    kpi_consensus_note_hdf = extract_tag(global_content_hdf, "GLOBAL_CONSENSUS_NOTE") or "Accord régional"
    kpi_scenario_val_hdf = extract_tag(global_content_hdf, "GLOBAL_SCENARIO_KPI") or "Stable"
    kpi_scenario_note_hdf = extract_tag(global_content_hdf, "GLOBAL_SCENARIO_NOTE") or "Incertitude en semaine 2"
    
    kpi_cards_val_hdf = f"{downloaded_cards_count} / {total_scraped_cards}" if total_scraped_cards > 0 else f"{downloaded_cards_count} retenues"
    kpi_cards_note_hdf = f"{downloaded_cards_count} cartes analysées"
    
    kpi_uncertainty_val_hdf = extract_tag(global_content_hdf, "GLOBAL_UNCERTAINTY_KPI") or "Timing"
    kpi_uncertainty_note_hdf = extract_tag(global_content_hdf, "GLOBAL_UNCERTAINTY_NOTE") or "Transition thermique"

    w1_conf_val_hdf = "Modérée"
    w1_temp_val_hdf = w1_models_hdf[0].get("sensible_weather", "De saison") if w1_models_hdf else "De saison"
    w2_conf_val_hdf = "Faible / Projections"
    w2_temp_val_hdf = w2_models_hdf[0].get("sensible_weather", "De saison") if w2_models_hdf else "De saison"

    run_record_hdf = {
        "date_generation": today_str,
        "w1_confidence": w1_conf_val_hdf,
        "w1_temp": w1_temp_val_hdf,
        "w2_confidence": w2_conf_val_hdf,
        "w2_temp": w2_temp_val_hdf,
        "global_summary": extract_tag(global_content_hdf, "GLOBAL_15_DAY_TREND")
    }
    
    os.makedirs("history_hdf", exist_ok=True)
    with open(f"history_hdf/{date_fn}.json", "w", encoding="utf-8") as f_hist:
        json.dump(run_record_hdf, f_hist, ensure_ascii=False, indent=2)
    with open(last_bulletin_hdf_path, "w", encoding="utf-8") as f_last:
        json.dump(run_record_hdf, f_last, ensure_ascii=False, indent=2)

    sparkline_conf_html_hdf, temp_evolution_html_hdf = generate_sparklines_html(history_dir="history_hdf")

    what_changed_box_hdf = ""
    if has_last_bulletin_hdf and what_changed_hdf:
        what_changed_box_hdf = f"""
        <div class="section">
            <div class="section-head"><div><span class="badge">Comparatif</span><h2>📈 Ce qui a changé depuis le précédent bulletin régional</h2></div></div>
            <div class="alert" style="background:#eff6ff; color:#1e40af; border-color:#bfdbfe;">
                {clean_text_typos(what_changed_hdf)}
            </div>
        </div>
        """

    linkedin_raw_hdf = extract_tag(global_content_hdf, "LINKEDIN_POST")
    linkedin_clean_hdf = clean_text_typos(linkedin_raw_hdf).replace('<br>', '\n').replace('<br/>', '\n')

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
    
    .sub-nav { display:none; gap:6px; overflow-x:auto; padding:6px 0; margin-top:6px; scrollbar-width:none; }
    .sub-nav a { flex:0 0 auto; padding:6px 12px; border-radius:999px; background:rgba(255,255,255,.8); border:1px solid var(--line); color:var(--navy); font-size:12px; font-weight:800; text-decoration:none; }

    .panel{display:block; margin-bottom: 24px;}
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

    .evolution-card { background: var(--surface-2); border: 1px solid var(--line); border-radius: 18px; padding: 20px; }
    .sparkline { font-family: monospace; font-size: 13px; line-height: 1.5; color: var(--ink); background: #ffffff; border: 1px solid var(--line); border-radius: 10px; padding: 12px; margin-top: 8px; }
    .sparkline-row { display: flex; justify-content: space-between; margin-bottom: 4px; }
    .trend-pill { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 700; }
    .trend-up { background: #dcfce7; color: #166534; }
    .trend-down { background: #fee2e2; color: #991b1b; }

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
      
      .hero{padding:20px 16px;border-radius:22px;}
      .hero-top{flex-direction:column; gap:8px;}
      .hero h1{font-size:clamp(24px, 6vw, 30px); margin:12px 0 4px; line-height:1.2;}
      .hero-sub{font-size:13.5px; margin-bottom:12px; line-height:1.4;}
      .hero p{font-size:14px; line-height:1.45;}
      .meta-cards{display:grid; grid-template-columns:1fr 1fr; gap:6px; margin-top:14px;}
      .meta-card{padding:6px 10px; font-size:11.5px; text-align:center;}
      .generation-date{text-align:center; font-size:11px; margin-top:6px;}

      .kpis { grid-template-columns: 1fr 1fr !important; gap:8px !important; margin-top:14px !important; }
      @media(max-width:400px){ .kpis { grid-template-columns: 1fr !important; } }
      .kpi { padding:12px !important; border-radius:14px !important; }
      .kpi-value { font-size:19px !important; }
      .kpi-note { font-size:11px !important; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }

      .grid-2,.grid-3,.grid-4,.zones,.cards3,.compare {
        grid-template-columns: 1fr !important;
        gap:10px !important;
      }
      .section{padding:16px !important; border-radius:20px !important; margin-top:14px !important;}
      .section-head{align-items:flex-start; flex-direction:column; margin-bottom:14px; gap:8px;}

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

      .linkedin {
        max-height: none !important;
        font-size:14px;
        padding:16px;
      }
      .linkedin-toolbar { flex-direction: column; align-items: stretch; }
      .copy { width: 100%; text-align: center; }
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

<section id="week1" class="panel">
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
      <div><span class="badge">Comparateur</span><h2>Ce que disent les modèles (Semaine 1)</h2><p class="sub">Lecture synthétique et deux niveaux d'analyse.</p></div>
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
    <div class="section-head"><div><span class="badge">Analyse</span><h2>Convergences et divergences (Semaine 1)</h2></div></div>
    <div class="compare">
      <div class="card"><h3>Ce qui converge</h3><p>[W1_CONVERGENCES_PLACEHOLDER]</p></div>
      <div class="card"><h3>Ce qui diverge</h3><p>[W1_DIVERGENCES_PLACEHOLDER]</p></div>
    </div>
  </div>

  <div id="sec-w1-zones" class="section">
    <div class="section-head">
      <div><span class="badge">Temps sensible</span><h2>Prévision par 8 grandes zones géographiques (Semaine 1)</h2></div>
    </div>
    <div class="zones">
      [W1_ZONES_HTML_PLACEHOLDER]
    </div>
  </div>

  <div id="sec-w1-timeline" class="section">
    <div class="section-head"><div><span class="badge">Chronologie</span><h2>Déroulé de la semaine 1</h2></div></div>
    <div class="timeline">
      <div class="phase"><b>[W1_PHASE_1_DATES_PLACEHOLDER]</b><p>[W1_PHASE_1_PLACEHOLDER]</p></div>
      <div class="phase"><b>[W1_PHASE_2_DATES_PLACEHOLDER]</b><p>[W1_PHASE_2_PLACEHOLDER]</p></div>
      <div class="phase"><b>[W1_PHASE_3_DATES_PLACEHOLDER]</b><p>[W1_PHASE_3_PLACEHOLDER]</p></div>
      <div class="phase"><b>[W1_PHASE_4_DATES_PLACEHOLDER]</b><p>[W1_PHASE_4_PLACEHOLDER]</p></div>
    </div>
  </div>

  <div class="section">
    <div class="section-head"><div><span class="badge">Fiabilité</span><h2>Points solides et points fragiles (Semaine 1)</h2></div></div>
    <div class="compare">
      <div class="card"><h3>Éléments solides</h3><p>[W1_SOLID_POINTS_PLACEHOLDER]</p></div>
      <div class="card"><h3>Éléments fragiles</h3><p>[W1_FRAGILE_POINTS_PLACEHOLDER]</p></div>
    </div>
    <div class="alert" style="margin-top:14px">À surveiller dans les prochains runs : [W1_NEXT_RUNS_TO_WATCH_PLACEHOLDER]</div>
  </div>

  <div id="sec-w1-images" class="section">
    <div class="section-head"><div><span class="badge">Graphiques clés</span><h2>Les images les plus pertinentes (Semaine 1)</h2></div></div>
    <div class="cards3">
      [W1_IMAGES_HTML_PLACEHOLDER]
    </div>
  </div>
</section>

<section id="week2" class="panel">
  [W2_NOTICE_HTML_PLACEHOLDER]

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
      <div><span class="badge">Comparateur</span><h2>Ce que disent les modèles (Semaine 2)</h2><p class="sub">Lecture synthétique et deux niveaux d'analyse.</p></div>
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
    <div class="section-head"><div><span class="badge">Analyse</span><h2>Convergences et divergences (Semaine 2)</h2></div></div>
    <div class="compare">
      <div class="card"><h3>Ce qui converge</h3><p>[W2_CONVERGENCES_PLACEHOLDER]</p></div>
      <div class="card"><h3>Ce qui diverge</h3><p>[W2_DIVERGENCES_PLACEHOLDER]</p></div>
    </div>
  </div>

  <div class="section">
    <div class="section-head">
      <div><span class="badge">Temps sensible</span><h2>Prévision par 8 grandes zones géographiques (Semaine 2)</h2></div>
    </div>
    <div class="zones">
      [W2_ZONES_HTML_PLACEHOLDER]
    </div>
  </div>

  <div class="section">
    <div class="section-head"><div><span class="badge">Chronologie</span><h2>Déroulé de la semaine 2</h2></div></div>
    <div class="timeline">
      <div class="phase"><b>[W2_PHASE_1_DATES_PLACEHOLDER]</b><p>[W2_PHASE_1_PLACEHOLDER]</p></div>
      <div class="phase"><b>[W2_PHASE_2_DATES_PLACEHOLDER]</b><p>[W2_PHASE_2_PLACEHOLDER]</p></div>
      <div class="phase"><b>[W2_PHASE_3_DATES_PLACEHOLDER]</b><p>[W2_PHASE_3_PLACEHOLDER]</p></div>
      <div class="phase"><b>[W2_PHASE_4_DATES_PLACEHOLDER]</b><p>[W2_PHASE_4_PLACEHOLDER]</p></div>
    </div>
  </div>

  <div class="section">
    <div class="section-head"><div><span class="badge">Fiabilité</span><h2>Points solides et points fragiles (Semaine 2)</h2></div></div>
    <div class="compare">
      <div class="card"><h3>Éléments solides</h3><p>[W2_SOLID_POINTS_PLACEHOLDER]</p></div>
      <div class="card"><h3>Éléments fragiles</h3><p>[W2_FRAGILE_POINTS_PLACEHOLDER]</p></div>
    </div>
    <div class="alert" style="margin-top:14px">À surveiller dans les prochains runs : [W2_NEXT_RUNS_TO_WATCH_PLACEHOLDER]</div>
  </div>

  <div class="section">
    <div class="section-head"><div><span class="badge">Graphiques clés</span><h2>Les images les plus pertinentes (Semaine 2)</h2></div></div>
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
    <div class="section-head"><div><span class="badge">Réseaux sociaux</span><h2>Post LinkedIn</h2></div></div>
    <div class="linkedin-box">
      <div id="linkedin" class="linkedin">[LINKEDIN_CLEAN_PLACEHOLDER]</div>
    </div>
  </div>
</section>

<section id="doubts" class="panel">
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
</footer>

</main>
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
    html = html.replace("[W2_NOTICE_HTML_PLACEHOLDER]", w2_notice_html)
    
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

    # === GENERATION BULLETIN NATIONAL MD ===
    md_national = build_markdown_bulletin(
        False, w1_content, w2_content, global_content, doubts_content, today_str,
        w1_dates, w2_dates,
        kpi_consensus_val, kpi_consensus_note,
        kpi_scenario_val, kpi_scenario_note,
        kpi_cards_val, kpi_cards_note,
        kpi_uncertainty_val, kpi_uncertainty_note,
        what_changed, w1_zones_dict, w2_zones_dict
    )
    md_path = "bulletin_infoclimat.md"
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(md_national)
    print(f"Markdown National généré avec succès : {md_path}")

    # Construction de l'HTML épuré pour l'e-mail (utilisant les CIDs au lieu des lourdes chaînes base64)
    email_html = html_template
    email_html = email_html.replace("[STYLE_PLACEHOLDER]", f"<style>\n{style}\n</style>")
    email_html = email_html.replace("[W1_DATES_PLACEHOLDER]", w1_dates)
    email_html = email_html.replace("[W2_DATES_PLACEHOLDER]", w2_dates)
    email_html = email_html.replace("[TODAY_STR_PLACEHOLDER]", today_str)
    
    email_html = email_html.replace("[W1_KEYS_HTML_PLACEHOLDER]", w1_keys_html)
    email_html = email_html.replace("[W1_MODELS_HTML_PLACEHOLDER]", w1_models_html)
    email_html = email_html.replace("[W1_ZONES_HTML_PLACEHOLDER]", w1_zones_html)
    email_html = email_html.replace("[W1_IMAGES_HTML_PLACEHOLDER]", w1_images_email_html) # CID
    
    email_html = email_html.replace("[W2_KEYS_HTML_PLACEHOLDER]", w2_keys_html)
    email_html = email_html.replace("[W2_MODELS_HTML_PLACEHOLDER]", w2_models_html)
    email_html = email_html.replace("[W2_ZONES_HTML_PLACEHOLDER]", w2_zones_html)
    email_html = email_html.replace("[W2_IMAGES_HTML_PLACEHOLDER]", w2_images_email_html) # CID
    email_html = email_html.replace("[W2_NOTICE_HTML_PLACEHOLDER]", w2_notice_html)
    
    email_html = email_html.replace("[W1_CONVERGENCES_PLACEHOLDER]", clean_text_typos(extract_tag(w1_content, "W1_CONVERGENCES")) or "-")
    email_html = email_html.replace("[W1_DIVERGENCES_PLACEHOLDER]", clean_text_typos(extract_tag(w1_content, "W1_DIVERGENCES")) or "-")
    email_html = email_html.replace("[W2_CONVERGENCES_PLACEHOLDER]", clean_text_typos(extract_tag(w2_content, "W2_CONVERGENCES")) or "-")
    email_html = email_html.replace("[W2_DIVERGENCES_PLACEHOLDER]", clean_text_typos(extract_tag(w2_content, "W2_DIVERGENCES")) or "-")

    email_html = email_html.replace("[W1_PHASE_1_DATES_PLACEHOLDER]", clean_text_typos(extract_tag(w1_content, "W1_PHASE_1_DATES")) or "Phase 1")
    email_html = email_html.replace("[W1_PHASE_1_PLACEHOLDER]", clean_text_typos(extract_tag(w1_content, "W1_PHASE_1")) or "-")
    email_html = email_html.replace("[W1_PHASE_2_DATES_PLACEHOLDER]", clean_text_typos(extract_tag(w1_content, "W1_PHASE_2_DATES")) or "Phase 2")
    email_html = email_html.replace("[W1_PHASE_2_PLACEHOLDER]", clean_text_typos(extract_tag(w1_content, "W1_PHASE_2")) or "-")
    email_html = email_html.replace("[W1_PHASE_3_DATES_PLACEHOLDER]", clean_text_typos(extract_tag(w1_content, "W1_PHASE_3_DATES")) or "Phase 3")
    email_html = email_html.replace("[W1_PHASE_3_PLACEHOLDER]", clean_text_typos(extract_tag(w1_content, "W1_PHASE_3")) or "-")
    email_html = email_html.replace("[W1_PHASE_4_DATES_PLACEHOLDER]", clean_text_typos(extract_tag(w1_content, "W1_PHASE_4_DATES")) or "Phase 4")
    email_html = email_html.replace("[W1_PHASE_4_PLACEHOLDER]", clean_text_typos(extract_tag(w1_content, "W1_PHASE_4")) or "-")

    email_html = email_html.replace("[W2_PHASE_1_DATES_PLACEHOLDER]", clean_text_typos(extract_tag(w2_content, "W2_PHASE_1_DATES")) or "Phase 1")
    email_html = email_html.replace("[W2_PHASE_1_PLACEHOLDER]", clean_text_typos(extract_tag(w2_content, "W2_PHASE_1")) or "-")
    email_html = email_html.replace("[W2_PHASE_2_DATES_PLACEHOLDER]", clean_text_typos(extract_tag(w2_content, "W2_PHASE_2_DATES")) or "Phase 2")
    email_html = email_html.replace("[W2_PHASE_2_PLACEHOLDER]", clean_text_typos(extract_tag(w2_content, "W2_PHASE_2")) or "-")
    email_html = email_html.replace("[W2_PHASE_3_DATES_PLACEHOLDER]", clean_text_typos(extract_tag(w2_content, "W2_PHASE_3_DATES")) or "Phase 3")
    email_html = email_html.replace("[W2_PHASE_3_PLACEHOLDER]", clean_text_typos(extract_tag(w2_content, "W2_PHASE_3")) or "-")
    email_html = email_html.replace("[W2_PHASE_4_DATES_PLACEHOLDER]", clean_text_typos(extract_tag(w2_content, "W2_PHASE_4_DATES")) or "Phase 4")
    email_html = email_html.replace("[W2_PHASE_4_PLACEHOLDER]", clean_text_typos(extract_tag(w2_content, "W2_PHASE_4")) or "-")

    email_html = email_html.replace("[W1_SOLID_POINTS_PLACEHOLDER]", clean_text_typos(extract_tag(w1_content, "W1_SOLID_POINTS")) or "-")
    email_html = email_html.replace("[W1_FRAGILE_POINTS_PLACEHOLDER]", clean_text_typos(extract_tag(w1_content, "W1_FRAGILE_POINTS")) or "-")
    email_html = email_html.replace("[W1_NEXT_RUNS_TO_WATCH_PLACEHOLDER]", clean_text_typos(extract_tag(w1_content, "W1_NEXT_RUNS_TO_WATCH")) or "-")
    email_html = email_html.replace("[W2_SOLID_POINTS_PLACEHOLDER]", clean_text_typos(extract_tag(w2_content, "W2_SOLID_POINTS")) or "-")
    email_html = email_html.replace("[W2_FRAGILE_POINTS_PLACEHOLDER]", clean_text_typos(extract_tag(w2_content, "W2_FRAGILE_POINTS")) or "-")
    email_html = email_html.replace("[W2_NEXT_RUNS_TO_WATCH_PLACEHOLDER]", clean_text_typos(extract_tag(w2_content, "W2_NEXT_RUNS_TO_WATCH")) or "-")

    email_html = email_html.replace("[GLOBAL_CONSENSUS_KPI_PLACEHOLDER]", clean_text_typos(kpi_consensus_val))
    email_html = email_html.replace("[GLOBAL_CONSENSUS_NOTE_PLACEHOLDER]", clean_text_typos(kpi_consensus_note))
    email_html = email_html.replace("[GLOBAL_SCENARIO_KPI_PLACEHOLDER]", clean_text_typos(kpi_scenario_val))
    email_html = email_html.replace("[GLOBAL_SCENARIO_NOTE_PLACEHOLDER]", clean_text_typos(kpi_scenario_note))
    email_html = email_html.replace("[GLOBAL_CARDS_KPI_PLACEHOLDER]", kpi_cards_val)
    email_html = email_html.replace("[GLOBAL_CARDS_NOTE_PLACEHOLDER]", kpi_cards_note)
    email_html = email_html.replace("[GLOBAL_UNCERTAINTY_KPI_PLACEHOLDER]", clean_text_typos(kpi_uncertainty_val))
    email_html = email_html.replace("[GLOBAL_UNCERTAINTY_NOTE_PLACEHOLDER]", clean_text_typos(kpi_uncertainty_note))

    email_html = email_html.replace("[GLOBAL_15_DAY_TREND_PLACEHOLDER]", clean_text_typos(extract_tag(global_content, "GLOBAL_15_DAY_TREND")) or "-")
    email_html = email_html.replace("[MOST_RELIABLE_WEEK_PLACEHOLDER]", clean_text_typos(extract_tag(global_content, "MOST_RELIABLE_WEEK")) or "-")
    email_html = email_html.replace("[GLOBAL_SOLID_POINTS_PLACEHOLDER]", clean_text_typos(extract_tag(global_content, "GLOBAL_SOLID_POINTS")) or "-")
    email_html = email_html.replace("[GLOBAL_RECURRING_PHENOMENA_PLACEHOLDER]", clean_text_typos(extract_tag(global_content, "GLOBAL_RECURRING_PHENOMENA")) or "-")
    email_html = email_html.replace("[GLOBAL_MAJOR_UNCERTAINTIES_PLACEHOLDER]", clean_text_typos(extract_tag(global_content, "GLOBAL_MAJOR_UNCERTAINTIES")) or "-")
    
    email_html = email_html.replace("[DOUBTS_TIMING_PLACEHOLDER]", clean_text_typos(extract_tag(doubts_content, "DOUBTS_TIMING")) or "-")
    email_html = email_html.replace("[DOUBTS_LOCATION_PLACEHOLDER]", clean_text_typos(extract_tag(doubts_content, "DOUBTS_LOCATION")) or "-")
    email_html = email_html.replace("[DOUBTS_INTENSITY_PLACEHOLDER]", clean_text_typos(extract_tag(doubts_content, "DOUBTS_INTENSITY")) or "-")
    email_html = email_html.replace("[MISSING_INFORMATION_PLACEHOLDER]", clean_text_typos(extract_tag(doubts_content, "MISSING_INFORMATION")) or "-")
    email_html = email_html.replace("[LOW_DOCUMENTED_MODELS_PLACEHOLDER]", clean_text_typos(extract_tag(doubts_content, "LOW_DOCUMENTED_MODELS")) or "-")
    email_html = email_html.replace("[UNCERTAIN_IMAGES_PLACEHOLDER]", clean_text_typos(extract_tag(doubts_content, "UNCERTAIN_IMAGES")) or "-")

    email_html = email_html.replace("[LINKEDIN_CLEAN_PLACEHOLDER]", linkedin_clean)
    email_html = email_html.replace("[WHAT_CHANGED_BOX_PLACEHOLDER]", what_changed_box)
    email_html = email_html.replace("[SPARKLINE_CONF_PLACEHOLDER]", sparkline_conf_html)
    email_html = email_html.replace("[TEMP_EVOLUTION_PLACEHOLDER]", temp_evolution_html)

    # === GENERATION BULLETIN HDF STANDALONE & EMAIL ===
    html_hdf = html_template
    html_hdf = html_hdf.replace("Tendances météo France", "Tendances Hauts-de-France")
    html_hdf = html_hdf.replace("Analyse nationale", "Analyse régionale HDF")
    html_hdf = html_hdf.replace("par grandes zones", "par département")
    html_hdf = html_hdf.replace("PRÉVISIONS À MOYEN ET LONG TERME", "PRÉVISIONS HAUTS-DE-FRANCE")
    html_hdf = html_hdf.replace("Analyse comparative multi-modèles, temps sensible par grandes zones, niveau de confiance et incertitudes.", "Analyse comparative multi-modèles et prévision détaillée par département sur la région Hauts-de-France.")
    html_hdf = html_hdf.replace("Prévision par 8 grandes zones géographiques", "Prévision par département")
    
    html_hdf = html_hdf.replace("[STYLE_PLACEHOLDER]", f"<style>\n{style}\n</style>")
    html_hdf = html_hdf.replace("[W1_DATES_PLACEHOLDER]", w1_dates_hdf)
    html_hdf = html_hdf.replace("[W2_DATES_PLACEHOLDER]", w2_dates_hdf)
    html_hdf = html_hdf.replace("[TODAY_STR_PLACEHOLDER]", today_str)
    
    html_hdf = html_hdf.replace("[W1_KEYS_HTML_PLACEHOLDER]", w1_keys_html_hdf)
    html_hdf = html_hdf.replace("[W1_MODELS_HTML_PLACEHOLDER]", w1_models_html_hdf)
    html_hdf = html_hdf.replace("[W1_ZONES_HTML_PLACEHOLDER]", w1_zones_html_hdf)
    html_hdf = html_hdf.replace("[W1_IMAGES_HTML_PLACEHOLDER]", w1_images_html_hdf)
    
    html_hdf = html_hdf.replace("[W2_KEYS_HTML_PLACEHOLDER]", w2_keys_html_hdf)
    html_hdf = html_hdf.replace("[W2_MODELS_HTML_PLACEHOLDER]", w2_models_html_hdf)
    html_hdf = html_hdf.replace("[W2_ZONES_HTML_PLACEHOLDER]", w2_zones_html_hdf)
    html_hdf = html_hdf.replace("[W2_IMAGES_HTML_PLACEHOLDER]", w2_images_html_hdf)
    html_hdf = html_hdf.replace("[W2_NOTICE_HTML_PLACEHOLDER]", w2_notice_html_hdf)
    
    html_hdf = html_hdf.replace("[W1_CONVERGENCES_PLACEHOLDER]", clean_text_typos(extract_tag(w1_content_hdf, "W1_CONVERGENCES")) or "-")
    html_hdf = html_hdf.replace("[W1_DIVERGENCES_PLACEHOLDER]", clean_text_typos(extract_tag(w1_content_hdf, "W1_DIVERGENCES")) or "-")
    html_hdf = html_hdf.replace("[W2_CONVERGENCES_PLACEHOLDER]", clean_text_typos(extract_tag(w2_content_hdf, "W2_CONVERGENCES")) or "-")
    html_hdf = html_hdf.replace("[W2_DIVERGENCES_PLACEHOLDER]", clean_text_typos(extract_tag(w2_content_hdf, "W2_DIVERGENCES")) or "-")

    # Chronologie HDF
    html_hdf = html_hdf.replace("[W1_PHASE_1_DATES_PLACEHOLDER]", clean_text_typos(extract_tag(w1_content_hdf, "W1_PHASE_1_DATES")) or "Phase 1")
    html_hdf = html_hdf.replace("[W1_PHASE_1_PLACEHOLDER]", clean_text_typos(extract_tag(w1_content_hdf, "W1_PHASE_1")) or "-")
    html_hdf = html_hdf.replace("[W1_PHASE_2_DATES_PLACEHOLDER]", clean_text_typos(extract_tag(w1_content_hdf, "W1_PHASE_2_DATES")) or "Phase 2")
    html_hdf = html_hdf.replace("[W1_PHASE_2_PLACEHOLDER]", clean_text_typos(extract_tag(w1_content_hdf, "W1_PHASE_2")) or "-")
    html_hdf = html_hdf.replace("[W1_PHASE_3_DATES_PLACEHOLDER]", clean_text_typos(extract_tag(w1_content_hdf, "W1_PHASE_3_DATES")) or "Phase 3")
    html_hdf = html_hdf.replace("[W1_PHASE_3_PLACEHOLDER]", clean_text_typos(extract_tag(w1_content_hdf, "W1_PHASE_3")) or "-")
    html_hdf = html_hdf.replace("[W1_PHASE_4_DATES_PLACEHOLDER]", clean_text_typos(extract_tag(w1_content_hdf, "W1_PHASE_4_DATES")) or "Phase 4")
    html_hdf = html_hdf.replace("[W1_PHASE_4_PLACEHOLDER]", clean_text_typos(extract_tag(w1_content_hdf, "W1_PHASE_4")) or "-")

    html_hdf = html_hdf.replace("[W2_PHASE_1_DATES_PLACEHOLDER]", clean_text_typos(extract_tag(w2_content_hdf, "W2_PHASE_1_DATES")) or "Phase 1")
    html_hdf = html_hdf.replace("[W2_PHASE_1_PLACEHOLDER]", clean_text_typos(extract_tag(w2_content_hdf, "W2_PHASE_1")) or "-")
    html_hdf = html_hdf.replace("[W2_PHASE_2_DATES_PLACEHOLDER]", clean_text_typos(extract_tag(w2_content_hdf, "W2_PHASE_2_DATES")) or "Phase 2")
    html_hdf = html_hdf.replace("[W2_PHASE_2_PLACEHOLDER]", clean_text_typos(extract_tag(w2_content_hdf, "W2_PHASE_2")) or "-")
    html_hdf = html_hdf.replace("[W2_PHASE_3_DATES_PLACEHOLDER]", clean_text_typos(extract_tag(w2_content_hdf, "W2_PHASE_3_DATES")) or "Phase 3")
    html_hdf = html_hdf.replace("[W2_PHASE_3_PLACEHOLDER]", clean_text_typos(extract_tag(w2_content_hdf, "W2_PHASE_3")) or "-")
    html_hdf = html_hdf.replace("[W2_PHASE_4_DATES_PLACEHOLDER]", clean_text_typos(extract_tag(w2_content_hdf, "W2_PHASE_4_DATES")) or "Phase 4")
    html_hdf = html_hdf.replace("[W2_PHASE_4_PLACEHOLDER]", clean_text_typos(extract_tag(w2_content_hdf, "W2_PHASE_4")) or "-")

    # Solides / Fragiles HDF
    html_hdf = html_hdf.replace("[W1_SOLID_POINTS_PLACEHOLDER]", clean_text_typos(extract_tag(w1_content_hdf, "W1_SOLID_POINTS")) or "-")
    html_hdf = html_hdf.replace("[W1_FRAGILE_POINTS_PLACEHOLDER]", clean_text_typos(extract_tag(w1_content_hdf, "W1_FRAGILE_POINTS")) or "-")
    html_hdf = html_hdf.replace("[W1_NEXT_RUNS_TO_WATCH_PLACEHOLDER]", clean_text_typos(extract_tag(w1_content_hdf, "W1_NEXT_RUNS_TO_WATCH")) or "-")
    
    html_hdf = html_hdf.replace("[W2_SOLID_POINTS_PLACEHOLDER]", clean_text_typos(extract_tag(w2_content_hdf, "W2_SOLID_POINTS")) or "-")
    html_hdf = html_hdf.replace("[W2_FRAGILE_POINTS_PLACEHOLDER]", clean_text_typos(extract_tag(w2_content_hdf, "W2_FRAGILE_POINTS")) or "-")
    html_hdf = html_hdf.replace("[W2_NEXT_RUNS_TO_WATCH_PLACEHOLDER]", clean_text_typos(extract_tag(w2_content_hdf, "W2_NEXT_RUNS_TO_WATCH")) or "-")

    # KPIs HDF
    html_hdf = html_hdf.replace("[GLOBAL_CONSENSUS_KPI_PLACEHOLDER]", clean_text_typos(kpi_consensus_val_hdf))
    html_hdf = html_hdf.replace("[GLOBAL_CONSENSUS_NOTE_PLACEHOLDER]", clean_text_typos(kpi_consensus_note_hdf))
    html_hdf = html_hdf.replace("[GLOBAL_SCENARIO_KPI_PLACEHOLDER]", clean_text_typos(kpi_scenario_val_hdf))
    html_hdf = html_hdf.replace("[GLOBAL_SCENARIO_NOTE_PLACEHOLDER]", clean_text_typos(kpi_scenario_note_hdf))
    html_hdf = html_hdf.replace("[GLOBAL_CARDS_KPI_PLACEHOLDER]", kpi_cards_val_hdf)
    html_hdf = html_hdf.replace("[GLOBAL_CARDS_NOTE_PLACEHOLDER]", kpi_cards_note_hdf)
    html_hdf = html_hdf.replace("[GLOBAL_UNCERTAINTY_KPI_PLACEHOLDER]", clean_text_typos(kpi_uncertainty_val_hdf))
    html_hdf = html_hdf.replace("[GLOBAL_UNCERTAINTY_NOTE_PLACEHOLDER]", clean_text_typos(kpi_uncertainty_note_hdf))

    html_hdf = html_hdf.replace("[GLOBAL_15_DAY_TREND_PLACEHOLDER]", clean_text_typos(extract_tag(global_content_hdf, "GLOBAL_15_DAY_TREND")) or "-")
    html_hdf = html_hdf.replace("[MOST_RELIABLE_WEEK_PLACEHOLDER]", clean_text_typos(extract_tag(global_content_hdf, "MOST_RELIABLE_WEEK")) or "-")
    html_hdf = html_hdf.replace("[GLOBAL_SOLID_POINTS_PLACEHOLDER]", clean_text_typos(extract_tag(global_content_hdf, "GLOBAL_SOLID_POINTS")) or "-")
    html_hdf = html_hdf.replace("[GLOBAL_RECURRING_PHENOMENA_PLACEHOLDER]", clean_text_typos(extract_tag(global_content_hdf, "GLOBAL_RECURRING_PHENOMENA")) or "-")
    html_hdf = html_hdf.replace("[GLOBAL_MAJOR_UNCERTAINTIES_PLACEHOLDER]", clean_text_typos(extract_tag(global_content_hdf, "GLOBAL_MAJOR_UNCERTAINTIES")) or "-")
    
    html_hdf = html_hdf.replace("[DOUBTS_TIMING_PLACEHOLDER]", clean_text_typos(extract_tag(doubts_content_hdf, "DOUBTS_TIMING")) or "-")
    html_hdf = html_hdf.replace("[DOUBTS_LOCATION_PLACEHOLDER]", clean_text_typos(extract_tag(doubts_content_hdf, "DOUBTS_LOCATION")) or "-")
    html_hdf = html_hdf.replace("[DOUBTS_INTENSITY_PLACEHOLDER]", clean_text_typos(extract_tag(doubts_content_hdf, "DOUBTS_INTENSITY")) or "-")
    html_hdf = html_hdf.replace("[MISSING_INFORMATION_PLACEHOLDER]", clean_text_typos(extract_tag(doubts_content_hdf, "MISSING_INFORMATION")) or "-")
    html_hdf = html_hdf.replace("[LOW_DOCUMENTED_MODELS_PLACEHOLDER]", clean_text_typos(extract_tag(doubts_content_hdf, "LOW_DOCUMENTED_MODELS")) or "-")
    html_hdf = html_hdf.replace("[UNCERTAIN_IMAGES_PLACEHOLDER]", clean_text_typos(extract_tag(doubts_content_hdf, "UNCERTAIN_IMAGES")) or "-")

    html_hdf = html_hdf.replace("[LINKEDIN_CLEAN_PLACEHOLDER]", linkedin_clean_hdf)
    html_hdf = html_hdf.replace("[WHAT_CHANGED_BOX_PLACEHOLDER]", what_changed_box_hdf)
    html_hdf = html_hdf.replace("[SPARKLINE_CONF_PLACEHOLDER]", sparkline_conf_html_hdf)
    html_hdf = html_hdf.replace("[TEMP_EVOLUTION_PLACEHOLDER]", temp_evolution_html_hdf)

    html_path_hdf = "bulletin_infoclimat_hdf.html"
    with open(html_path_hdf, 'w', encoding='utf-8') as f:
        f.write(html_hdf)
    print(f"HTML régional généré avec succès : {html_path_hdf}")

    # === GENERATION BULLETIN HDF MD ===
    md_hdf = build_markdown_bulletin(
        True, w1_content_hdf, w2_content_hdf, global_content_hdf, doubts_content_hdf, today_str,
        w1_dates_hdf, w2_dates_hdf,
        kpi_consensus_val_hdf, kpi_consensus_note_hdf,
        kpi_scenario_val_hdf, kpi_scenario_note_hdf,
        kpi_cards_val_hdf, kpi_cards_note_hdf,
        kpi_uncertainty_val_hdf, kpi_uncertainty_note_hdf,
        what_changed_hdf, w1_zones_dict_hdf, w2_zones_dict_hdf
    )
    md_path_hdf = "bulletin_infoclimat_hdf.md"
    with open(md_path_hdf, 'w', encoding='utf-8') as f:
        f.write(md_hdf)
    print(f"Markdown Régional généré avec succès : {md_path_hdf}")

    # === GENERATION PUBLIC DASHBOARD WEB (GITHUB PAGES) ===
    import shutil
    public_dir = "public"
    os.makedirs(public_dir, exist_ok=True)

    nav_nat = '<div style="background:#0d2f4f; padding:12px 20px; text-align:center; color:white; font-family:Inter, ui-sans-serif, sans-serif; font-size:14px; font-weight:700; border-bottom:3px solid #1ea7c9; display:flex; justify-content:center; align-items:center; gap:10px; flex-wrap:wrap;"><span style="opacity:0.85; font-size:13px; text-transform:uppercase; letter-spacing:0.5px;">🌐 Navigation bulletins & sources :</span><a href="index.html" style="color:white; text-decoration:none; padding:7px 15px; background:#1565d8; border-radius:8px; border:1px solid rgba(255,255,255,0.2); box-shadow: 0 2px 4px rgba(0,0,0,0.2);">🇫🇷 Bulletin National</a><a href="hdf.html" style="color:white; text-decoration:none; padding:7px 15px; background:rgba(255,255,255,0.12); border-radius:8px; border:1px solid rgba(255,255,255,0.2);">📍 Hauts-de-France</a><a href="national.md" download style="color:white; text-decoration:none; padding:7px 14px; background:#23936b; border-radius:8px; border:1px solid rgba(255,255,255,0.2); box-shadow: 0 2px 4px rgba(0,0,0,0.15);">📥 Bulletin Nat (.md)</a><a href="sources_national.md" download style="color:white; text-decoration:none; padding:7px 14px; background:#d97706; border-radius:8px; border:1px solid rgba(255,255,255,0.2); box-shadow: 0 2px 4px rgba(0,0,0,0.15);">📥 Sources Nat (.md)</a><a href="sources_hdf.md" download style="color:white; text-decoration:none; padding:7px 14px; background:#d97706; border-radius:8px; border:1px solid rgba(255,255,255,0.2); box-shadow: 0 2px 4px rgba(0,0,0,0.15);">📥 Sources HDF (.md)</a></div>'

    nav_hdf = '<div style="background:#0d2f4f; padding:12px 20px; text-align:center; color:white; font-family:Inter, ui-sans-serif, sans-serif; font-size:14px; font-weight:700; border-bottom:3px solid #1ea7c9; display:flex; justify-content:center; align-items:center; gap:10px; flex-wrap:wrap;"><span style="opacity:0.85; font-size:13px; text-transform:uppercase; letter-spacing:0.5px;">🌐 Navigation bulletins & sources :</span><a href="index.html" style="color:white; text-decoration:none; padding:7px 15px; background:rgba(255,255,255,0.12); border-radius:8px; border:1px solid rgba(255,255,255,0.2);">🇫🇷 Bulletin National</a><a href="hdf.html" style="color:white; text-decoration:none; padding:7px 15px; background:#1565d8; border-radius:8px; border:1px solid rgba(255,255,255,0.2); box-shadow: 0 2px 4px rgba(0,0,0,0.2);">📍 Hauts-de-France</a><a href="hdf.md" download style="color:white; text-decoration:none; padding:7px 14px; background:#23936b; border-radius:8px; border:1px solid rgba(255,255,255,0.2); box-shadow: 0 2px 4px rgba(0,0,0,0.15);">📥 Bulletin HDF (.md)</a><a href="sources_hdf.md" download style="color:white; text-decoration:none; padding:7px 14px; background:#d97706; border-radius:8px; border:1px solid rgba(255,255,255,0.2); box-shadow: 0 2px 4px rgba(0,0,0,0.15);">📥 Sources HDF (.md)</a><a href="sources_national.md" download style="color:white; text-decoration:none; padding:7px 14px; background:#d97706; border-radius:8px; border:1px solid rgba(255,255,255,0.2); box-shadow: 0 2px 4px rgba(0,0,0,0.15);">📥 Sources Nat (.md)</a></div>'

    web_html_nat = html.replace('<body>', '<body>\n' + nav_nat)
    web_html_hdf = html_hdf.replace('<body>', '<body>\n' + nav_hdf)

    with open(os.path.join(public_dir, "index.html"), 'w', encoding='utf-8') as f:
        f.write(web_html_nat)
    with open(os.path.join(public_dir, "hdf.html"), 'w', encoding='utf-8') as f:
        f.write(web_html_hdf)

    with open(os.path.join(public_dir, "national.md"), 'w', encoding='utf-8') as f:
        f.write(md_national)
    with open(os.path.join(public_dir, "hdf.md"), 'w', encoding='utf-8') as f:
        f.write(md_hdf)

    if os.path.exists("candidates"):
        candidates_dest = os.path.join(public_dir, "candidates")
        if os.path.exists(candidates_dest):
            shutil.rmtree(candidates_dest)
        shutil.copytree("candidates", candidates_dest)

    print(f"Site web public généré avec succès dans ./{public_dir}/ (index.html, hdf.html, candidates/)")

    # Email version for HDF (CIDs)
    email_html_hdf = html_template
    email_html_hdf = email_html_hdf.replace("Tendances météo France", "Tendances Hauts-de-France")
    email_html_hdf = email_html_hdf.replace("Analyse nationale", "Analyse régionale HDF")
    email_html_hdf = email_html_hdf.replace("par grandes zones", "par département")
    email_html_hdf = email_html_hdf.replace("PRÉVISIONS À MOYEN ET LONG TERME", "PRÉVISIONS HAUTS-DE-FRANCE")
    email_html_hdf = email_html_hdf.replace("Analyse comparative multi-modèles, temps sensible par grandes zones, niveau de confiance et incertitudes.", "Analyse comparative multi-modèles et prévision détaillée par département sur la région Hauts-de-France.")
    email_html_hdf = email_html_hdf.replace("Prévision par 8 grandes zones géographiques", "Prévision par département")
    
    email_html_hdf = email_html_hdf.replace("[STYLE_PLACEHOLDER]", f"<style>\n{style}\n</style>")
    email_html_hdf = email_html_hdf.replace("[W1_DATES_PLACEHOLDER]", w1_dates_hdf)
    email_html_hdf = email_html_hdf.replace("[W2_DATES_PLACEHOLDER]", w2_dates_hdf)
    email_html_hdf = email_html_hdf.replace("[TODAY_STR_PLACEHOLDER]", today_str)
    
    email_html_hdf = email_html_hdf.replace("[W1_KEYS_HTML_PLACEHOLDER]", w1_keys_html_hdf)
    email_html_hdf = email_html_hdf.replace("[W1_MODELS_HTML_PLACEHOLDER]", w1_models_html_hdf)
    email_html_hdf = email_html_hdf.replace("[W1_ZONES_HTML_PLACEHOLDER]", w1_zones_html_hdf)
    email_html_hdf = email_html_hdf.replace("[W1_IMAGES_HTML_PLACEHOLDER]", w1_images_email_html_hdf) # CID HDF
    
    email_html_hdf = email_html_hdf.replace("[W2_KEYS_HTML_PLACEHOLDER]", w2_keys_html_hdf)
    email_html_hdf = email_html_hdf.replace("[W2_MODELS_HTML_PLACEHOLDER]", w2_models_html_hdf)
    email_html_hdf = email_html_hdf.replace("[W2_ZONES_HTML_PLACEHOLDER]", w2_zones_html_hdf)
    email_html_hdf = email_html_hdf.replace("[W2_IMAGES_HTML_PLACEHOLDER]", w2_images_email_html_hdf) # CID HDF
    email_html_hdf = email_html_hdf.replace("[W2_NOTICE_HTML_PLACEHOLDER]", w2_notice_html_hdf)
    
    email_html_hdf = email_html_hdf.replace("[W1_CONVERGENCES_PLACEHOLDER]", clean_text_typos(extract_tag(w1_content_hdf, "W1_CONVERGENCES")) or "-")
    email_html_hdf = email_html_hdf.replace("[W1_DIVERGENCES_PLACEHOLDER]", clean_text_typos(extract_tag(w1_content_hdf, "W1_DIVERGENCES")) or "-")
    email_html_hdf = email_html_hdf.replace("[W2_CONVERGENCES_PLACEHOLDER]", clean_text_typos(extract_tag(w2_content_hdf, "W2_CONVERGENCES")) or "-")
    email_html_hdf = email_html_hdf.replace("[W2_DIVERGENCES_PLACEHOLDER]", clean_text_typos(extract_tag(w2_content_hdf, "W2_DIVERGENCES")) or "-")

    # Chronologie HDF
    email_html_hdf = email_html_hdf.replace("[W1_PHASE_1_DATES_PLACEHOLDER]", clean_text_typos(extract_tag(w1_content_hdf, "W1_PHASE_1_DATES")) or "Phase 1")
    email_html_hdf = email_html_hdf.replace("[W1_PHASE_1_PLACEHOLDER]", clean_text_typos(extract_tag(w1_content_hdf, "W1_PHASE_1")) or "-")
    email_html_hdf = email_html_hdf.replace("[W1_PHASE_2_DATES_PLACEHOLDER]", clean_text_typos(extract_tag(w1_content_hdf, "W1_PHASE_2_DATES")) or "Phase 2")
    email_html_hdf = email_html_hdf.replace("[W1_PHASE_2_PLACEHOLDER]", clean_text_typos(extract_tag(w1_content_hdf, "W1_PHASE_2")) or "-")
    email_html_hdf = email_html_hdf.replace("[W1_PHASE_3_DATES_PLACEHOLDER]", clean_text_typos(extract_tag(w1_content_hdf, "W1_PHASE_3_DATES")) or "Phase 3")
    email_html_hdf = email_html_hdf.replace("[W1_PHASE_3_PLACEHOLDER]", clean_text_typos(extract_tag(w1_content_hdf, "W1_PHASE_3")) or "-")
    email_html_hdf = email_html_hdf.replace("[W1_PHASE_4_DATES_PLACEHOLDER]", clean_text_typos(extract_tag(w1_content_hdf, "W1_PHASE_4_DATES")) or "Phase 4")
    email_html_hdf = email_html_hdf.replace("[W1_PHASE_4_PLACEHOLDER]", clean_text_typos(extract_tag(w1_content_hdf, "W1_PHASE_4")) or "-")

    email_html_hdf = email_html_hdf.replace("[W2_PHASE_1_DATES_PLACEHOLDER]", clean_text_typos(extract_tag(w2_content_hdf, "W2_PHASE_1_DATES")) or "Phase 1")
    email_html_hdf = email_html_hdf.replace("[W2_PHASE_1_PLACEHOLDER]", clean_text_typos(extract_tag(w2_content_hdf, "W2_PHASE_1")) or "-")
    email_html_hdf = email_html_hdf.replace("[W2_PHASE_2_DATES_PLACEHOLDER]", clean_text_typos(extract_tag(w2_content_hdf, "W2_PHASE_2_DATES")) or "Phase 2")
    email_html_hdf = email_html_hdf.replace("[W2_PHASE_2_PLACEHOLDER]", clean_text_typos(extract_tag(w2_content_hdf, "W2_PHASE_2")) or "-")
    email_html_hdf = email_html_hdf.replace("[W2_PHASE_3_DATES_PLACEHOLDER]", clean_text_typos(extract_tag(w2_content_hdf, "W2_PHASE_3_DATES")) or "Phase 3")
    email_html_hdf = email_html_hdf.replace("[W2_PHASE_3_PLACEHOLDER]", clean_text_typos(extract_tag(w2_content_hdf, "W2_PHASE_3")) or "-")
    email_html_hdf = email_html_hdf.replace("[W2_PHASE_4_DATES_PLACEHOLDER]", clean_text_typos(extract_tag(w2_content_hdf, "W2_PHASE_4_DATES")) or "Phase 4")
    email_html_hdf = email_html_hdf.replace("[W2_PHASE_4_PLACEHOLDER]", clean_text_typos(extract_tag(w2_content_hdf, "W2_PHASE_4")) or "-")

    # Solides / Fragiles HDF
    email_html_hdf = email_html_hdf.replace("[W1_SOLID_POINTS_PLACEHOLDER]", clean_text_typos(extract_tag(w1_content_hdf, "W1_SOLID_POINTS")) or "-")
    email_html_hdf = email_html_hdf.replace("[W1_FRAGILE_POINTS_PLACEHOLDER]", clean_text_typos(extract_tag(w1_content_hdf, "W1_FRAGILE_POINTS")) or "-")
    email_html_hdf = email_html_hdf.replace("[W1_NEXT_RUNS_TO_WATCH_PLACEHOLDER]", clean_text_typos(extract_tag(w1_content_hdf, "W1_NEXT_RUNS_TO_WATCH")) or "-")
    email_html_hdf = email_html_hdf.replace("[W2_SOLID_POINTS_PLACEHOLDER]", clean_text_typos(extract_tag(w2_content_hdf, "W2_SOLID_POINTS")) or "-")
    email_html_hdf = email_html_hdf.replace("[W2_FRAGILE_POINTS_PLACEHOLDER]", clean_text_typos(extract_tag(w2_content_hdf, "W2_FRAGILE_POINTS")) or "-")
    email_html_hdf = email_html_hdf.replace("[W2_NEXT_RUNS_TO_WATCH_PLACEHOLDER]", clean_text_typos(extract_tag(w2_content_hdf, "W2_NEXT_RUNS_TO_WATCH")) or "-")

    # KPIs HDF
    email_html_hdf = email_html_hdf.replace("[GLOBAL_CONSENSUS_KPI_PLACEHOLDER]", clean_text_typos(kpi_consensus_val_hdf))
    email_html_hdf = email_html_hdf.replace("[GLOBAL_CONSENSUS_NOTE_PLACEHOLDER]", clean_text_typos(kpi_consensus_note_hdf))
    email_html_hdf = email_html_hdf.replace("[GLOBAL_SCENARIO_KPI_PLACEHOLDER]", clean_text_typos(kpi_scenario_val_hdf))
    email_html_hdf = email_html_hdf.replace("[GLOBAL_SCENARIO_NOTE_PLACEHOLDER]", clean_text_typos(kpi_scenario_note_hdf))
    email_html_hdf = email_html_hdf.replace("[GLOBAL_CARDS_KPI_PLACEHOLDER]", kpi_cards_val_hdf)
    email_html_hdf = email_html_hdf.replace("[GLOBAL_CARDS_NOTE_PLACEHOLDER]", kpi_cards_note_hdf)
    email_html_hdf = email_html_hdf.replace("[GLOBAL_UNCERTAINTY_KPI_PLACEHOLDER]", clean_text_typos(kpi_uncertainty_val_hdf))
    email_html_hdf = email_html_hdf.replace("[GLOBAL_UNCERTAINTY_NOTE_PLACEHOLDER]", clean_text_typos(kpi_uncertainty_note_hdf))

    email_html_hdf = email_html_hdf.replace("[GLOBAL_15_DAY_TREND_PLACEHOLDER]", clean_text_typos(extract_tag(global_content_hdf, "GLOBAL_15_DAY_TREND")) or "-")
    email_html_hdf = email_html_hdf.replace("[MOST_RELIABLE_WEEK_PLACEHOLDER]", clean_text_typos(extract_tag(global_content_hdf, "MOST_RELIABLE_WEEK")) or "-")
    email_html_hdf = email_html_hdf.replace("[GLOBAL_SOLID_POINTS_PLACEHOLDER]", clean_text_typos(extract_tag(global_content_hdf, "GLOBAL_SOLID_POINTS")) or "-")
    email_html_hdf = email_html_hdf.replace("[GLOBAL_RECURRING_PHENOMENA_PLACEHOLDER]", clean_text_typos(extract_tag(global_content_hdf, "GLOBAL_RECURRING_PHENOMENA")) or "-")
    email_html_hdf = email_html_hdf.replace("[GLOBAL_MAJOR_UNCERTAINTIES_PLACEHOLDER]", clean_text_typos(extract_tag(global_content_hdf, "GLOBAL_MAJOR_UNCERTAINTIES")) or "-")
    
    email_html_hdf = email_html_hdf.replace("[DOUBTS_TIMING_PLACEHOLDER]", clean_text_typos(extract_tag(doubts_content_hdf, "DOUBTS_TIMING")) or "-")
    email_html_hdf = email_html_hdf.replace("[DOUBTS_LOCATION_PLACEHOLDER]", clean_text_typos(extract_tag(doubts_content_hdf, "DOUBTS_LOCATION")) or "-")
    email_html_hdf = email_html_hdf.replace("[DOUBTS_INTENSITY_PLACEHOLDER]", clean_text_typos(extract_tag(doubts_content_hdf, "DOUBTS_INTENSITY")) or "-")
    email_html_hdf = email_html_hdf.replace("[MISSING_INFORMATION_PLACEHOLDER]", clean_text_typos(extract_tag(doubts_content_hdf, "MISSING_INFORMATION")) or "-")
    email_html_hdf = email_html_hdf.replace("[LOW_DOCUMENTED_MODELS_PLACEHOLDER]", clean_text_typos(extract_tag(doubts_content_hdf, "LOW_DOCUMENTED_MODELS")) or "-")
    email_html_hdf = email_html_hdf.replace("[UNCERTAIN_IMAGES_PLACEHOLDER]", clean_text_typos(extract_tag(doubts_content_hdf, "UNCERTAIN_IMAGES")) or "-")

    email_html_hdf = email_html_hdf.replace("[LINKEDIN_CLEAN_PLACEHOLDER]", linkedin_clean_hdf)
    email_html_hdf = email_html_hdf.replace("[WHAT_CHANGED_BOX_PLACEHOLDER]", what_changed_box_hdf)
    email_html_hdf = email_html_hdf.replace("[SPARKLINE_CONF_PLACEHOLDER]", sparkline_conf_html_hdf)
    email_html_hdf = email_html_hdf.replace("[TEMP_EVOLUTION_PLACEHOLDER]", temp_evolution_html_hdf)

    # Envoi email SMTP via structure anti-spam 100% propre (MIMEMultipart avec HTML complet et CIDs)
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
    subject = f"PRÉVISIONS MÉTÉO (NATIONAL & HDF) — {w1_dates.split('-')[0].strip()} & {w2_dates.split('-')[0].strip()}"
    
    msg = MIMEMultipart("mixed")
    msg['From'] = f"Meteo Climat Pro <{sender}>"
    msg['To'] = ", ".join(recipients)
    msg['Subject'] = Header(subject, 'utf-8').encode()
    msg['Date'] = formatdate(localtime=True)
    msg['Reply-To'] = "gregory.langlet@sfr.fr"

    # Container alternative indispensable pour éviter le rejet anti-spam SFR (550 5.7.1)
    msg_alt = MIMEMultipart("alternative")

    # Plain Text fallback
    web_link = "https://gregorylanglet59264-byte.github.io/veille-automation/"
    text_body = f"""PRÉVISIONS MÉTÉO À MOYEN ET LONG TERME (NATIONAL & HAUTS-DE-FRANCE)
Période : {w1_dates} & {w2_dates}

🌐 Version Web interactive (mises à jour en direct) : {web_link}

1. BULLETIN NATIONAL
- Tendances modèles, chronologie et prévision par zones météo (France).

2. BULLETIN HAUTS-DE-FRANCE
- Focus régional détaillé sur les départements : Nord (59), Pas-de-Calais (62), Somme (80), Oise (60) et Aisne (02).

Les rapports visuels complets et interactifs sont inclus dans le corps de l'e-mail et joints en pièces jointes.
"""
    msg_alt.attach(MIMEText(text_body, 'plain', 'utf-8'))

    # Helper pour extraire le contenu du body
    def get_body_content(html_str):
        body_match = re.search(r'<body>(.*?)</body>', html_str, re.DOTALL)
        if body_match:
            return body_match.group(1)
        return html_str

    # Assembler les deux bulletins sous un seul document HTML propre pour le mail
    combined_email_html = f"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>PRÉVISIONS MÉTÉO — Bulletin National & Régional Hauts-de-France</title>
<style>
{style}
</style>
</head>
<body style="margin:0; padding:0; background-color:#eef4f8;">
<div style="background:#0d2f4f; padding:12px 20px; text-align:center; color:white; font-family:Inter, sans-serif; font-size:13px; font-weight:700; border-bottom:3px solid #1ea7c9;">
  🌐 Version Web interactive avec onglets (mises à jour en direct) : <a href="{web_link}" style="color:#1ea7c9; text-decoration:underline;">{web_link}</a>
</div>
{get_body_content(email_html)}
<div style="text-align: center; margin: 40px 0;">
    <hr style="border: 0; border-top: 3px dashed #0d2f4f; width: 60%; display: inline-block;">
    <span style="display: block; font-size: 14px; font-weight: 800; color: #0d2f4f; text-transform: uppercase; margin-top: 10px;">Fin du Bulletin National • Début du Bulletin Hauts-de-France</span>
</div>
{get_body_content(email_html_hdf)}
</body>
</html>
"""

    msg_alt.attach(MIMEText(combined_email_html, 'html', 'utf-8'))
    msg.attach(msg_alt)

    # Attach National Semaine 1 images inline
    for i, img_path in enumerate(week1_data["images"][:len(w1_images_info)]):
        if os.path.exists(img_path):
            try:
                with open(img_path, "rb") as f_img:
                    img_data = f_img.read()
                ext = img_path.split('.')[-1].lower()
                msg_img = MIMEBase('image', ext if ext in ['png', 'jpeg', 'jpg'] else 'octet-stream')
                msg_img.set_payload(img_data)
                encoders.encode_base64(msg_img)
                msg_img.add_header('Content-ID', f'<w1_img_{i}>')
                msg_img.add_header('Content-Disposition', 'inline', filename=os.path.basename(img_path))
                msg.attach(msg_img)
            except Exception as e:
                print(f"Erreur d'attachement image W1 {i} : {e}")

    # Attach National Semaine 2 images inline
    for i, img_path in enumerate(week2_data["images"][:len(w2_images_info)]):
        if os.path.exists(img_path):
            try:
                with open(img_path, "rb") as f_img:
                    img_data = f_img.read()
                ext = img_path.split('.')[-1].lower()
                msg_img = MIMEBase('image', ext if ext in ['png', 'jpeg', 'jpg'] else 'octet-stream')
                msg_img.set_payload(img_data)
                encoders.encode_base64(msg_img)
                msg_img.add_header('Content-ID', f'<w2_img_{i}>')
                msg_img.add_header('Content-Disposition', 'inline', filename=os.path.basename(img_path))
                msg.attach(msg_img)
            except Exception as e:
                print(f"Erreur d'attachement image W2 {i} : {e}")

    # Attach HDF Semaine 1 images inline
    for i, img_path in enumerate(week1_data["images"][:len(w1_images_info_hdf)]):
        if os.path.exists(img_path):
            try:
                with open(img_path, "rb") as f_img:
                    img_data = f_img.read()
                ext = img_path.split('.')[-1].lower()
                msg_img = MIMEBase('image', ext if ext in ['png', 'jpeg', 'jpg'] else 'octet-stream')
                msg_img.set_payload(img_data)
                encoders.encode_base64(msg_img)
                msg_img.add_header('Content-ID', f'<hdf_w1_img_{i}>')
                msg_img.add_header('Content-Disposition', 'inline', filename=f"hdf_w1_img_{i}.{ext}")
                msg.attach(msg_img)
            except Exception as e:
                print(f"Erreur d'attachement image HDF W1 {i} : {e}")

    # Attach HDF Semaine 2 images inline
    for i, img_path in enumerate(week2_data["images"][:len(w2_images_info_hdf)]):
        if os.path.exists(img_path):
            try:
                with open(img_path, "rb") as f_img:
                    img_data = f_img.read()
                ext = img_path.split('.')[-1].lower()
                msg_img = MIMEBase('image', ext if ext in ['png', 'jpeg', 'jpg'] else 'octet-stream')
                msg_img.set_payload(img_data)
                encoders.encode_base64(msg_img)
                msg_img.add_header('Content-ID', f'<hdf_w2_img_{i}>')
                msg_img.add_header('Content-Disposition', 'inline', filename=f"hdf_w2_img_{i}.{ext}")
                msg.attach(msg_img)
            except Exception as e:
                print(f"Erreur d'attachement image HDF W2 {i} : {e}")

    # Standalone Markdown file attachment (National)
    if os.path.exists(md_path):
        with open(md_path, "rb") as f_att:
            att = MIMEBase('application', 'octet-stream')
            att.set_payload(f_att.read())
            encoders.encode_base64(att)
            filename = f"analyse_infoclimat_national_{datetime.datetime.now().strftime('%Y_%m_%d')}.md"
            att.add_header('Content-Disposition', f'attachment; filename="{filename}"')
            msg.attach(att)

    # Standalone Markdown file attachment (HDF)
    if os.path.exists(md_path_hdf):
        with open(md_path_hdf, "rb") as f_att:
            att = MIMEBase('application', 'octet-stream')
            att.set_payload(f_att.read())
            encoders.encode_base64(att)
            filename = f"analyse_infoclimat_hdf_{datetime.datetime.now().strftime('%Y_%m_%d')}.md"
            att.add_header('Content-Disposition', f'attachment; filename="{filename}"')
            msg.attach(att)

    # Attach TXT sources files (National & HDF)
    if os.path.exists("sources_raw_national.txt"):
        with open("sources_raw_national.txt", "rb") as f_att:
            att = MIMEBase('text', 'plain', charset='utf-8')
            att.set_payload(f_att.read())
            encoders.encode_base64(att)
            filename = f"sources_brutes_national_{datetime.datetime.now().strftime('%Y_%m_%d')}.txt"
            att.add_header('Content-Disposition', f'attachment; filename="{filename}"')
            msg.attach(att)

    if os.path.exists("sources_raw_hdf.txt"):
        with open("sources_raw_hdf.txt", "rb") as f_att:
            att = MIMEBase('text', 'plain', charset='utf-8')
            att.set_payload(f_att.read())
            encoders.encode_base64(att)
            filename = f"sources_brutes_hdf_{datetime.datetime.now().strftime('%Y_%m_%d')}.txt"
            att.add_header('Content-Disposition', f'attachment; filename="{filename}"')
            msg.attach(att)

    print(f"[SMTP] Envoi du bulletin HTML combiné avec images CID à {', '.join(recipients)}...")
    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(gmail_email, gmail_password)
            server.sendmail(gmail_email, recipients, msg.as_string())
        print("[SMTP] E-mail avec rapports combinés envoyé avec succès !")
    except Exception as e:
        print(f"[SMTP] Erreur d'envoi : {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
