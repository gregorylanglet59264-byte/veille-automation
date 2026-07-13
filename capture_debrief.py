# -*- coding: utf-8 -*-
"""
capture_debrief.py
Generates the official Monsieur Météo Twitter infographic:
  1. Loads data/latest_tweets.json (scraped by fetch_tweets.py)
  2. Reads index_debrief.html as a template
  3. Formulates the DEBRIEF_DATA structure (3 columns: Alerts, General, Models)
  4. Injects data, background base64, and logo base64 into the HTML template
  5. Captures a 1920x1080 JPEG screenshot using Playwright
"""
import json
import os
import sys
import base64
import tempfile
from datetime import datetime, timezone
from playwright.sync_api import sync_playwright

SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
DATA_FILE   = os.path.join(SCRIPT_DIR, "data", "latest_tweets.json")
HTML_TEMPLATE = os.path.join(SCRIPT_DIR, "index_debrief.html")
LOGO_FILE   = os.path.join(SCRIPT_DIR, "logo_mm.png")
BG_FILE     = os.path.join(SCRIPT_DIR, "data", "bg_twitter.png")
OUTPUT      = os.path.join(SCRIPT_DIR, "debrief_twitter.jpg")
TWEET_FILE  = os.path.join(SCRIPT_DIR, "data", "debrief_tweet.txt")

def img_to_b64(path):
    if not path or not os.path.exists(path):
        return None
    ext = os.path.splitext(path)[1].lower().lstrip(".")
    mime = {"png": "png", "jpg": "jpeg", "jpeg": "jpeg"}.get(ext, "png")
    with open(path, "rb") as f:
        return f"data:image/{mime};base64,{base64.b64encode(f.read()).decode()}"

def truncate(text, max_chars=200):
    if not text:
        return ""
    text = text.replace("\n", " ").strip()
    return text[:max_chars] + "…" if len(text) > max_chars else text

def main():
    # Load tweets
    if not os.path.exists(DATA_FILE):
        print(f"ERROR: {DATA_FILE} not found. Run fetch_tweets.py first.", file=sys.stderr)
        sys.exit(1)

    with open(DATA_FILE, encoding="utf-8") as f:
        tweets = json.load(f)

    if not tweets:
        print("No tweets found — skipping infographic generation.", file=sys.stderr)
        sys.exit(0)

    # Separate by category (Alerts, General, Models) based on their index (0,3,6 for Col 1; 1,4,7 for Col 2; 2,5,8 for Col 3)
    # Let's map them from the interleaved structure:
    # Index 0, 3, 6 are Alerts
    # Index 1, 4, 7 are General
    # Index 2, 5, 8 are Models
    alerts = []
    general = []
    models = []
    
    for i in [0, 3, 6]:
        if i < len(tweets) and tweets[i]:
            alerts.append(tweets[i])
    for i in [1, 4, 7]:
        if i < len(tweets) and tweets[i]:
            general.append(tweets[i])
    for i in [2, 5, 8]:
        if i < len(tweets) and tweets[i]:
            models.append(tweets[i])

    now = datetime.now(timezone.utc)
    date_str = now.strftime("%d/%m/%Y")
    heure_str = now.strftime("%H:%M UTC")

    # Format the data array for the HTML template
    # Title format text should be short to fit Outfit 25px
    def format_tweet_text(t):
        if not t or t.get("id", "").startswith("mock_"):
            return t.get("text", "")
        return f"@{t.get('username')}: {t.get('text')}"

    debrief_data = {
        "title": "DEBRIEF MÉTÉO",
        "subtitle": f"Veille Météo & Climat — {date_str} à {heure_str}",
        "has_custom_bg": True,
        "columns": [
            {
                "id": "alerts",
                "title": "ALERTES & VIGILANCE",
                "theme": "red-theme",
                "type": "text",
                "data": [format_tweet_text(t) for t in alerts if t]
            },
            {
                "id": "default",
                "title": "MÉTÉO GÉNÉRALE",
                "theme": "green-theme",
                "type": "text",
                "data": [format_tweet_text(t) for t in general if t]
            },
            {
                "id": "models",
                "title": "TENDANCES & MODÈLES",
                "theme": "blue-theme",
                "type": "text",
                "data": [format_tweet_text(t) for t in models if t]
            }
        ]
    }

    # Load assets base64
    logo_b64 = img_to_b64(LOGO_FILE)
    bg_b64   = img_to_b64(BG_FILE)

    # Load template HTML
    if not os.path.exists(HTML_TEMPLATE):
        print(f"ERROR: Template file {HTML_TEMPLATE} not found.", file=sys.stderr)
        sys.exit(1)

    with open(HTML_TEMPLATE, encoding="utf-8") as f:
        html_content = f.read()

    # Perform placeholder replacements
    # 1. Replace the external data.js script link with inline DEBRIEF_DATA assignment
    html_content = html_content.replace(
        '<script src="data/data.js"></script>',
        f'<script>const DEBRIEF_DATA = {json.dumps(debrief_data, ensure_ascii=False, indent=2)};</script>'
    )
    
    # 2. Replace background image placeholder
    if bg_b64:
        html_content = html_content.replace(
            "file:///C:/Users/grego/Documents/METEO_CLIMAT/meteo%20cnews%202/bg_landscape.png",
            bg_b64
        )
        
    # 3. Replace logo image placeholder
    if logo_b64:
        html_content = html_content.replace(
            "file:///C:/Users/grego/Documents/METEO_CLIMAT/meteo%20cnews%202/logo_mm.png",
            logo_b64
        )

    # Write tweet text for publication
    os.makedirs(os.path.dirname(TWEET_FILE), exist_ok=True)
    report_text = (
        f"DEBRIEF METEO - {date_str} ({heure_str})\n\n"
        f"Retrouvez le debriefing en direct du reseau de veille scientifique (alertes, observations et tendances des modeles).\n\n"
        f"Details complets sur l'infographie ci-dessous.\n"
        f"#Meteo #Climat"
    )
    with open(TWEET_FILE, "w", encoding="utf-8") as f:
        f.write(report_text)

    # Capture via Playwright
    with tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w", encoding="utf-8") as tmp:
        tmp.write(html_content)
        tmp_path = tmp.name

    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.set_viewport_size({"width": 1920, "height": 1080})
            page.goto(f"file:///{tmp_path.replace(os.sep, '/')}")
            page.wait_for_timeout(3000)  # Wait 3s for Outfit font to load fully
            page.screenshot(path=OUTPUT, quality=92, type="jpeg")
            browser.close()
        print(f"✅ Infographie générée avec la charte graphique officielle : {OUTPUT}")
    except Exception as e:
        print(f"ERROR capturing screenshot: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass

if __name__ == "__main__":
    main()
