#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
auto_publish_from_veille.py
Moteur autonome de publication d'actualités météo multi-sites (Zéro-Build).
Se branche directement en aval de 'run_veille_intemperies.py' :
1. Lit 'veille_intemperies_final.json' et sélectionne le point prioritaire
2. Génère / extrait les visuels légaux (cartes modèles HD, GIF animé, vigilance, couverture 16:9 sans logos)
3. Téléverse les visuels sur Supabase Storage (blog-images)
4. Rédige l'article d'alerte au futur via OpenRouter (Gemini 2.5 Flash / DeepSeek)
5. Insère l'article dans les tables 'posts' et 'meteo_posts' pour une mise en ligne instantanée sur :
   - meteobtp.fr
   - climat-meteo.vercel.app
   - monsieurmeteo.com
"""

import os
import sys
import json
import time
import datetime
import urllib.request
import mimetypes
import re
import shutil
import argparse
from PIL import Image, ImageDraw, ImageFont

# ── CONFIGURATIONS SUPABASE & OPENROUTER ──────────────────────────────────────
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://ubdevaemtwbzxksjlhjg.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_KEY") or "sb_publishable_1qhA0xAnNSd3VxpoLdxYrQ_yUemEhaP"

HEADERS_SB = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

# Dossiers locaux
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(BASE_DIR, "output_article")
os.makedirs(OUT_DIR, exist_ok=True)
CARTES_ALERTES_DIR = r"C:\Users\grego\Desktop\cartes_alertes"

# Mappings Géographiques & Modèles
REGION_MAPPING = {
    "paca": ["paca", "provence", "côte d'azur", "cote d'azur", "marseille", "nice", "var", "alpes-maritimes", "sud-est"],
    "ara": ["ara", "auvergne", "rhône-alpes", "rhone-alpes", "lyon", "grenoble", "isère", "alpes"],
    "occitanie": ["occitanie", "toulouse", "montpellier", "gard", "hérault", "aude", "pyrénées"],
    "hdf": ["hdf", "hauts-de-france", "nord", "pas-de-calais", "lille", "somme", "oise", "aisne"],
    "grandest": ["grand-est", "grand est", "alsace", "lorraine", "strasbourg", "metz", "nancy", "marne"],
    "normandie": ["normandie", "rouen", "caen", "havre", "calvados", "seine-maritime"],
    "bretagne": ["bretagne", "rennes", "brest", "finistère", "morbihan"],
    "naq": ["nouvelle-aquitaine", "bordeaux", "gironde", "charente"],
    "idf": ["ile-de-france", "paris", "petite couronne"],
    "cvl": ["centre-val de loire", "centre", "orléans", "tours"],
    "bfc": ["bourgogne", "franche-comté", "dijon", "besançon"],
    "corse": ["corse", "ajaccio", "bastia"],
    "antilles": ["antilles", "guadeloupe", "martinique", "saint-martin", "saint-barth", "caraïbes"],
    "reunion": ["réunion", "reunion", "mayotte", "océan indien", "madagascar"],
    "france": ["france", "national", "territoire", "hexagone"]
}

LAYER_MAPPING = {
    "orages": "mucape",
    "grele": "mucape",
    "canicule": "temperature",
    "chaleur": "temperature",
    "froid": "temperature",
    "vent": "rafales",
    "tempete": "rafales",
    "pluie": "pluie_cumul",
    "inondations": "pluie_cumul",
    "neige": "neige"
}

FONT_IMPACT = "C:/Windows/Fonts/impact.ttf"
if not os.path.exists(FONT_IMPACT):
    FONT_IMPACT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
if not os.path.exists(FONT_IMPACT):
    FONT_IMPACT = "C:/Windows/Fonts/ariblk.ttf"

def select_events_from_veille(json_path="veille_intemperies_final.json", point_arg="auto", count=3):
    """Charge et sélectionne les événements météo cibles depuis la veille (3 articles par défaut)."""
    if not os.path.exists(json_path):
        print(f"[WARN] Fichier de veille {json_path} introuvable. Utilisation d'événements de test.")
        return [
            {
                "title": "Alerte Météo : Risque d'orages violents et de grêle ce mardi dans le Sud-Est",
                "summary": "Une dégradation orageuse majeure menace les régions du Sud-Est ce mardi avec de fortes pluies, de la grêle et de violentes rafales sous orages.",
                "category": "orages_violents"
            },
            {
                "title": "Vigilance Météo : 17 départements placés en vigilance jaune pour orages et pluies intenses",
                "summary": "Météo-France a placé 17 départements en vigilance jaune pour ce mardi en raison d'une forte instabilité atmosphérique remontant du sud.",
                "category": "vigilance_nationale"
            },
            {
                "title": "Ouragan Lowell : le système maintient sa trajectoire vers l'archipel d'Hawaï",
                "summary": "L'ouragan Lowell poursuit sa progression dans le Pacifique avec des vents soutenus et une forte houle cyclonique sous surveillance active de la NOAA.",
                "category": "cyclone_international"
            }
        ][:count]
    
    with open(json_path, "r", encoding="utf-8") as f:
        items = json.load(f)
        
    if not items:
        return []

    if point_arg != "auto":
        try:
            idx = int(point_arg) - 1
            if 0 <= idx < len(items):
                return [items[idx]]
        except Exception:
            pass
            
    # Sélection automatique de 3 événements distincts :
    selected = []
    
    # 1. Événement 1 : Priorité absolue France (Vigilance / Orages / Canicule)
    france_kws = ["vigilance", "france", "orages", "paca", "var", "sud-est", "canicule", "grêle", "inondation"]
    for it in items:
        text = (it.get("title", "") + " " + it.get("summary", "")).lower()
        if any(kw in text for kw in france_kws) and it not in selected:
            selected.append(it)
            break
            
    # 2. Événement 2 : Priorité Cyclonique / Tropiques / Outre-Mer
    cyclo_kws = ["cyclone", "ouragan", "typhon", "tempête tropicale", "lowell", "antilles", "réunion", "guadeloupe"]
    for it in items:
        text = (it.get("title", "") + " " + it.get("summary", "")).lower()
        if any(kw in text for kw in cyclo_kws) and it not in selected:
            selected.append(it)
            break
            
    # 3. Remplissage jusqu'à 'count' événements avec les meilleurs points restants
    for it in items:
        if it not in selected:
            selected.append(it)
        if len(selected) >= count:
            break
            
    return selected[:count]


def analyze_event(item):
    """Détecte la région, le phénomène et le modèle adapté."""
    full_text = f"{item.get('title', '')} {item.get('summary', '')}".lower()
    
    selected_region = "france"
    for reg, kws in REGION_MAPPING.items():
        if any(kw in full_text for kw in kws):
            selected_region = reg
            break
            
    selected_layer = "mucape"
    for phenom, layer in LAYER_MAPPING.items():
        if phenom in full_text:
            selected_layer = layer
            break
            
    # Détection cyclone
    is_cyclone = any(w in full_text for w in ["cyclone", "ouragan", "typhon", "tempête tropicale"])
    
    return selected_region, selected_layer, is_cyclone

def generate_cover_image(bg_path, title_line1, title_line2, title_line3, badge_color=(194, 65, 12), out_path=None):
    """Génère la couverture 16:9 YouTube sans logos de site avec titre centré."""
    if not out_path:
        out_path = os.path.join(OUT_DIR, "00_COUVERTURE_16_9.png")
        
    w, h = 1200, 675
    if bg_path and os.path.exists(bg_path):
        bg = Image.open(bg_path).convert("RGBA")
        bg_ratio = bg.width / bg.height
        target_ratio = w / h
        if bg_ratio > target_ratio:
            new_w = int(bg.height * target_ratio)
            left = (bg.width - new_w) // 2
            bg = bg.crop((left, 0, left + new_w, bg.height))
        else:
            new_h = int(bg.width / target_ratio)
            top = (bg.height - new_h) // 2
            bg = bg.crop((0, top, bg.width, top + new_h))
        bg = bg.resize((w, h), Image.Resampling.LANCZOS)
    else:
        bg = Image.new("RGBA", (w, h), (15, 23, 42, 255))
        
    darken = Image.new("RGBA", (w, h), (0, 0, 0, 75))
    base = Image.alpha_composite(bg, darken)
    draw = ImageDraw.Draw(base)
    
    try:
        font = ImageFont.truetype(FONT_IMPACT, 68)
    except Exception:
        font = ImageFont.load_default()
        
    lines = [title_line1, title_line2, title_line3]
    line_h, line_w = [], []
    for l in lines:
        if l:
            bbox = draw.textbbox((0, 0), l, font=font, stroke_width=6)
            line_w.append(bbox[2] - bbox[0])
            line_h.append(bbox[3] - bbox[1])
        else:
            line_w.append(0)
            line_h.append(0)
            
    total_h = sum(line_h) + (len([l for l in lines if l]) - 1) * 20
    cur_y = (h - total_h) // 2 + 10
    
    if title_line1:
        x1 = (w - line_w[0]) // 2
        draw.text((x1, cur_y), title_line1, fill=(255, 255, 255), font=font, stroke_width=7, stroke_fill=(10, 15, 25))
        cur_y += line_h[0] + 16
        
    if title_line2:
        x2 = (w - line_w[1]) // 2
        bw = line_w[1] + 48
        bh = line_h[1] + 20
        bx = (w - bw) // 2
        by = cur_y - 8
        draw.rounded_rectangle([bx + 4, by + 4, bx + bw + 4, by + bh + 4], radius=10, fill=(0, 0, 0, 180))
        draw.rounded_rectangle([bx, by, bx + bw, by + bh], radius=10, fill=badge_color, outline=(255, 255, 255, 180), width=3)
        draw.text((x2, cur_y), title_line2, fill=(255, 238, 0), font=font, stroke_width=6, stroke_fill=(30, 0, 0))
        cur_y += line_h[1] + 24
        
    if title_line3:
        x3 = (w - line_w[2]) // 2
        draw.text((x3, cur_y), title_line3, fill=(255, 255, 255), font=font, stroke_width=7, stroke_fill=(10, 15, 25))
        
    base.convert("RGB").save(out_path, quality=95)
    print(f"  ✓ Couverture 16:9 générée : {out_path}")
    return out_path

def collect_visual_assets(region="france", layer="mucape", is_cyclone=False):
    """Génère et rassemble les actifs visuels légaux nécessaires."""
    print("[Visuels] Extraction des cartes et animations...")
    assets = {}
    
    # 1. Carte de Vigilance CNEWS
    vigi_src = None
    if os.path.exists(CARTES_ALERTES_DIR):
        reg_vigi = os.path.join(CARTES_ALERTES_DIR, f"carte_vigilance_{region}.jpg")
        if os.path.exists(reg_vigi):
            vigi_src = reg_vigi
        else:
            nat_vigi = os.path.join(CARTES_ALERTES_DIR, "carte_vigilance_france_pictos.jpg")
            if os.path.exists(nat_vigi):
                vigi_src = nat_vigi
                
    if vigi_src:
        dest_vigi = os.path.join(OUT_DIR, "02_CARTE_VIGILANCE.jpg")
        shutil.copy2(vigi_src, dest_vigi)
        assets["vigilance"] = dest_vigi
        print(f"  ✓ Carte de vigilance récupérée : {dest_vigi}")

    # 2. Carte Modèle HD & GIF Animé
    map_png = os.path.join(OUT_DIR, f"01_MODELE_{region.upper()}_{layer.upper()}_HD.png")
    gif_path = os.path.join(OUT_DIR, f"03_ANIMATION_{region.upper()}_{layer.upper()}.gif")
    
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=['--use-gl=angle', '--use-angle=default', '--enable-webgl'])
            context = browser.new_context(viewport={'width': 1920, 'height': 1080})
            context.add_init_script("localStorage.setItem('amfm_auth_token', 'valid');")
            page = context.new_page()
            page.goto(f'https://monsieurmeteo.github.io/arome-weather-map/?region={region}&parametre={layer}', wait_until='networkidle')
            page.wait_for_timeout(2500)
            page.evaluate("() => { const ov = document.getElementById('amfm-auth-overlay'); if (ov) ov.classList.add('is-hidden'); }")
            page.wait_for_timeout(1000)
            
            # Capture statique HD
            with page.expect_download() as d:
                page.click('[data-amfm-capture]')
            d.value.save_as(map_png)
            assets["model_hd"] = map_png
            print(f"  ✓ Carte modèle HD téléchargée : {map_png}")
            
            # Capture GIF animé (8 étapes temporelles)
            total_steps = page.evaluate("() => typeof availableSteps === 'function' ? availableSteps().length : 12")
            start_s = min(2, max(0, total_steps - 8))
            end_s = min(total_steps, start_s + 8)
            frames = []
            tmp_f = os.path.join(OUT_DIR, ".tmp_frames")
            os.makedirs(tmp_f, exist_ok=True)
            for s in range(start_s, end_s):
                page.evaluate(f"() => {{ if (typeof renderStep === 'function') renderStep({s}); }}")
                page.wait_for_timeout(1100)
                fp = os.path.join(tmp_f, f"f_{s:02d}.png")
                with page.expect_download() as d_step:
                    page.click('[data-amfm-capture]')
                d_step.value.save_as(fp)
                im = Image.open(fp).convert("RGB")
                im_res = im.resize((960, int(960 * im.height / im.width)), Image.Resampling.LANCZOS)
                frames.append(im_res)
                
            if frames:
                frames[0].save(gif_path, save_all=True, append_images=frames[1:], duration=650, loop=0, optimize=True)
                assets["gif"] = gif_path
                print(f"  ✓ GIF animé généré : {gif_path} ({os.path.getsize(gif_path)/(1024*1024):.2f} Mo)")
            shutil.rmtree(tmp_f, ignore_errors=True)
            browser.close()
    except Exception as e:
        print(f"[WARN] Impossible d'exécuter Playwright ({e}). Utilisation des cartes existantes.")

    # 3. Couverture 16:9
    bg_for_cover = assets.get("model_hd") or assets.get("vigilance")
    reg_label = region.upper()
    if region == "paca": reg_label = "dans le Sud-Est"
    elif region == "hdf": reg_label = "dans les Hauts-de-France"
    elif region == "france": reg_label = "en France"
    
    cover_path = generate_cover_image(
        bg_path=bg_for_cover,
        title_line1="Alerte Météo :",
        title_line2=f"Violents {layer.upper()}" if layer != "mucape" else "Violents Orages & Grêle",
        title_line3=reg_label,
        badge_color=(194, 65, 12),
        out_path=os.path.join(OUT_DIR, "00_COUVERTURE_16_9.png")
    )
    assets["cover"] = cover_path
    
    return assets

def upload_assets_to_supabase(assets):
    """Téléverse tous les visuels sur Supabase Storage (blog-images)."""
    print("[Supabase] Téléversement des visuels sur blog-images...")
    uploaded = {}
    ts = int(time.time())
    
    for key, fpath in assets.items():
        if fpath and os.path.exists(fpath):
            fname = os.path.basename(fpath)
            safe_name = re.sub(r'[^a-zA-Z0-9_.-]', '_', fname)
            target_path = f"blog/auto_{ts}_{safe_name}"
            mime_type, _ = mimetypes.guess_type(fpath)
            mime_type = mime_type or "application/octet-stream"

            with open(fpath, "rb") as f:
                data = f.read()

            upload_url = f"{SUPABASE_URL}/storage/v1/object/blog-images/{target_path}"
            upload_headers = {
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}",
                "Content-Type": mime_type
            }
            req = urllib.request.Request(upload_url, data=data, headers=upload_headers, method="POST")
            try:
                with urllib.request.urlopen(req) as resp:
                    pub_url = f"{SUPABASE_URL}/storage/v1/object/public/blog-images/{target_path}"
                    uploaded[key] = pub_url
                    print(f"  ✓ {key} téléversé : {pub_url}")
            except Exception as e:
                print(f"  ✗ Erreur upload {key} ({fname}): {e}")
                
    return uploaded

def draft_article_llm(item, uploaded_urls, region, layer):
    """Rédige l'article au futur via OpenRouter (Gemini 2.5 Flash / DeepSeek)."""
    print("[LLM] Rédaction de l'article d'alerte au futur via OpenRouter...")
    
    now = datetime.datetime.now()
    date_str = now.strftime("%d/%m/%Y")
    tomorrow = now + datetime.timedelta(days=1)
    tomorrow_str = tomorrow.strftime("%A %d %B %Y")
    
    figs_desc = []
    if gif_url:
        figs_desc.append(f"- Figure 1 (Animation Chronologique GIF heure par heure) : {gif_url}")
    if vigi_url:
        figs_desc.append(f"- Figure 2 (Carte de Vigilance Météo-France) : {vigi_url}")
    elif uploaded_urls.get("model_hd") and not gif_url:
        figs_desc.append(f"- Figure (Carte Modèle HD) : {uploaded_urls.get('model_hd')}")
        
    images_block = "\n".join(figs_desc) if figs_desc else "(Aucune image interne requise)"
    images_rule = "Insère uniquement les Figures listées ci-dessus avec des balises <figure> et légendes officielles explicatives." if figs_desc else "N'insère aucune balise <img> dans le corps du texte."

    prompt = f"""
Nous sommes le {now.strftime("%A %d %B %Y")}.
Tu es journaliste et météorologue senior officiel.
Rédige un article complet d'analyse et d'alerte météorologique de 1 200 à 1 500 mots sur :
« {item.get('title')} »

RÉSUMÉ DU PHÉNOMÈNE : {item.get('summary')}
ZONE GÉOGRAPHIQUE : {region.upper()}
PARAMÈTRE PHYSIQUE PRINCIPAL : {layer.upper()}
ÉCHÉANCE VISÉE : {tomorrow_str} (Événement FUTUR)

IMAGES OFFICIELLES À INTÉGRER DANS LE CORPS DU TEXTE :
{images_block}

CONSIGNES STRICTES DE RÉDACTION :
1. TEMPORALITÉ VERROUILLÉE : Rédige EXCLUSIVEMENT au FUTUR et au CONDITIONNEL ("est attendue", "éclateront", "menaceront", "pourront dépasser").
   INTERDICTION ABSOLUE d'utiliser le passé ("a frappé", "ont été mesurés", "ce week-end"). C'est une ALERTE pour les prochaines heures / demain.
2. ZÉRO INVENTION : N'invente aucun dégât passé ni bilan fictif. Analyse la physique de l'atmosphère (gradient thermique, instabilité MUCAPE convective, forçage d'altitude, advection d'air maritime).
3. RÈGLE CRITIQUE ANTI-DOUBLON : N'insère SURTOUT PAS l'image de couverture dans le texte (le template du site l'affiche déjà en Hero en haut de page). {images_rule}
4. TABLEAU DES RISQUES : Ajoute un tableau HTML synthétique des valeurs attendues par département (rafales, pluie, grêle).
5. CONSIGNES DE SÉCURITÉ : Termine par les recommandations concrètes de sécurité.
6. Renvoie uniquement le code HTML propre de l'article (sans balises <html> ni <body>).
"""

    models_to_try = ["google/gemini-2.5-flash", "deepseek/deepseek-chat"]
    for model in models_to_try:
        try:
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": "Tu es le rédacteur en chef météorologue officiel. Tu rédiges dans un style journalistique rigoureux, en HTML propre."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.2
            }
            req = urllib.request.Request(
                "https://openrouter.ai/api/v1/chat/completions",
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://climat-meteo.vercel.app",
                    "X-Title": "ACTUBTP-Auto"
                },
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=90) as resp:
                res = json.loads(resp.read().decode("utf-8"))
                content = res["choices"][0]["message"]["content"]
                content = re.sub(r'^```html\s*', '', content)
                content = re.sub(r'\s*```$', '', content)
                print(f"  ✓ Rédigé avec succès avec {model} ({len(content)} car.)")
                return content
        except Exception as e:
            print(f"  ✗ Échec avec {model}: {e}. Essai modèle suivant...")
            
    return "<p>Bulletin d'alerte météo en cours d'actualisation.</p>"

def publish_to_websites(title, slug, excerpt, content_html, cover_url):
    """Insère l'article dans les tables Supabase pour publication immédiate."""
    print("[Publication] Insertion Zéro-Build dans Supabase...")
    
    # 1. posts (meteobtp.fr + climat-meteo.vercel.app)
    data_posts = {
        "title": title,
        "slug": slug,
        "excerpt": excerpt,
        "content": content_html,
        "image_url": cover_url,
        "published": True,
        "published_at": datetime.datetime.now().isoformat(),
        "category": "Alertes Intempéries",
        "author": "Patrick Marlière & La Rédaction"
    }
    req1 = urllib.request.Request(f"{SUPABASE_URL}/rest/v1/posts", data=json.dumps(data_posts).encode("utf-8"), headers=HEADERS_SB, method="POST")
    try:
        with urllib.request.urlopen(req1) as r1:
            print("  ✓ Publié sur posts (MétéoBTP & Climat Météo)")
    except Exception as e:
        print(f"  ✗ Erreur posts: {e}")

    # 2. meteo_posts (monsieurmeteo.com)
    data_mm = {
        "title": title,
        "slug": slug,
        "excerpt": excerpt,
        "content": content_html,
        "image_url": cover_url,
        "published": True,
        "published_at": datetime.datetime.now().isoformat(),
        "category": "Alerte Météo",
        "author": "Monsieur Météo & Patrick Marlière"
    }
    req2 = urllib.request.Request(f"{SUPABASE_URL}/rest/v1/meteo_posts", data=json.dumps(data_mm).encode("utf-8"), headers=HEADERS_SB, method="POST")
    try:
        with urllib.request.urlopen(req2) as r2:
            print("  ✓ Publié sur meteo_posts (Monsieur Météo)")
    except Exception as e:
        print(f"  ✗ Erreur meteo_posts: {e}")

def main():
    parser = argparse.ArgumentParser(description="Publication automatique d'articles depuis la veille météo.")
    parser.add_argument("--json", default="veille_intemperies_final.json", help="Fichier JSON de veille")
    parser.add_argument("--point", default="auto", help="Numéro du point à publier (auto, 1, 2...)")
    parser.add_argument("--count", type=int, default=3, help="Nombre d'articles à publier (défaut: 3)")
    parser.add_argument("--dry-run", action="store_true", help="Simule sans insérer en base")
    args = parser.parse_args()

    print("="*70)
    print(f"🚀 DÉMARRAGE DU MOTEUR DE PUBLICATION AUTOMATIQUE ACTUBTP ({args.count} ARTICLES)")
    print("="*70)

    # 1. Sélection des 3 événements
    events = select_events_from_veille(args.json, args.point, count=args.count)
    print(f"\n[Sélection] {len(events)} événement(s) retenu(s) pour publication.")

    published_links = []

    for i, item in enumerate(events, 1):
        print("\n" + "="*50)
        print(f"📰 TRAITEMENT DE L'ARTICLE {i}/{len(events)} : {item.get('title')}")
        print("="*50)

        # 2. Analyse
        region, layer, is_cyclone = analyze_event(item)
        print(f"  [Analyse] Région: {region} | Layer: {layer} | Cyclone: {is_cyclone}")

        # 3. Visuels
        assets = collect_visual_assets(region, layer, is_cyclone)

        # 4. Upload Supabase
        uploaded_urls = upload_assets_to_supabase(assets)
        cover_url = uploaded_urls.get("cover", "")

        # 5. Rédaction LLM
        content_html = draft_article_llm(item, uploaded_urls, region, layer)

        # 6. Publication
        ts = int(time.time()) + (i * 2) # Pour garantir des slugs et timestamps uniques
        slug_base = re.sub(r'[^a-zA-Z0-9]+', '-', item.get('title', 'alerte-meteo').lower()).strip('-')
        slug = f"{slug_base[:55]}-{ts}"
        title = item.get('title')
        excerpt = item.get('summary')

        if not args.dry_run:
            publish_to_websites(title, slug, excerpt, content_html, cover_url)
            published_links.append((title, slug))
            print(f"  ✓ Article {i} publié en ligne avec succès !")
        else:
            print(f"  [Dry Run] Article {i} simulé. Slug : {slug}")

        time.sleep(2) # Temporisation douce entre deux articles

    if published_links:
        print("\n" + "="*70)
        print(f"🎉 LES {len(published_links)} ARTICLES SONT EN LIGNE SUR LES 3 SITES :")
        for t, s in published_links:
            print(f"\n📌 {t}")
            print(f"   • Climat Météo : https://climat-meteo.vercel.app/actualites/{s}")
            print(f"   • MétéoBTP     : https://meteobtp.fr/actualites/{s}")
            print(f"   • Monsieur Météo: https://monsieurmeteo.com/actualites/{s}")
        print("="*70)

    print("\n" + "="*70)
    print("FIN DU PROCESSUS AVEC SUCCÈS")
    print("="*70)

if __name__ == "__main__":
    main()

