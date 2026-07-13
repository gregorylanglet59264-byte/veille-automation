# -*- coding: utf-8 -*-
"""
capture_debrief.py
Génère l'infographie Twitter du débriefing :
  1. Lit data/latest_tweets.json (produit par fetch_tweets.py)
  2. Sélectionne les 9 meilleurs tweets (3 colonnes)
  3. Génère une page HTML autonome (tout inline, pas de fichiers externes)
  4. La capture en 1920x1080 JPG via Playwright
"""
import json
import os
import sys
import base64
from datetime import datetime, timezone
from playwright.sync_api import sync_playwright

SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
DATA_FILE   = os.path.join(SCRIPT_DIR, "data", "latest_tweets.json")
LOGO_FILE   = os.path.join(SCRIPT_DIR, "logo_mm.png")
BG_FILE     = os.path.join(SCRIPT_DIR, "data", "bg_twitter.png")
OUTPUT      = os.path.join(SCRIPT_DIR, "debrief_twitter.jpg")
TWEET_FILE  = os.path.join(SCRIPT_DIR, "data", "debrief_tweet.txt")

# ── Helpers ──────────────────────────────────────────────────────────────────

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

def color_for_tweet(t):
    if t.get("is_alert"):       return "#ff4444"
    if t.get("is_model_trend"): return "#7b61ff"
    return "#1DA1F2"

def badge_for_tweet(t):
    if t.get("is_alert"):       return "🚨 ALERTE"
    if t.get("is_model_trend"): return "📡 MODÈLES"
    return "🌤️ MÉTÉO"

# ── Build self-contained HTML ─────────────────────────────────────────────────

def build_html(tweets, logo_b64, bg_b64):
    now = datetime.now(timezone.utc)
    heure = now.strftime("%H:%M UTC")
    date  = now.strftime("%d/%m/%Y")

    bg_css = f"background-image: url('{bg_b64}'); background-size: cover; background-position: center;" \
             if bg_b64 else "background: linear-gradient(135deg, #0a0a2e 0%, #1a1a4e 50%, #0d1b3e 100%);"

    logo_html = f'<img src="{logo_b64}" style="height:60px;object-fit:contain;">' if logo_b64 else \
                '<span style="color:#1DA1F2;font-size:28px;font-weight:900;">@Monsieurmeteo07</span>'

    # Take top 9, split into 3 columns of 3
    top = tweets[:9]
    while len(top) < 9:
        top.append(None)

    def card(t):
        if t is None:
            return '<div style="flex:1;min-width:0;"></div>'
        color = color_for_tweet(t)
        badge = badge_for_tweet(t)
        name  = (t.get("name") or t.get("username") or "Météo")[:24]
        username = t.get("username", "")
        text  = truncate(t.get("text", ""), 180)
        likes = t.get("likes", 0)
        rts   = t.get("retweets", 0)
        return f"""
        <div style="flex:1;min-width:0;background:rgba(255,255,255,0.06);border:1px solid {color}44;
                    border-radius:14px;padding:18px 16px;display:flex;flex-direction:column;gap:8px;
                    box-shadow:0 4px 20px rgba(0,0,0,0.4);">
          <div style="display:flex;align-items:center;justify-content:space-between;">
            <span style="background:{color}22;color:{color};font-size:11px;font-weight:700;
                         padding:3px 10px;border-radius:20px;border:1px solid {color}66;">{badge}</span>
            <span style="color:#888;font-size:11px;">❤️ {likes} &nbsp; 🔁 {rts}</span>
          </div>
          <div style="font-weight:700;color:#fff;font-size:13px;">@{username}</div>
          <div style="color:#ccc;font-size:12.5px;line-height:1.5;">{text}</div>
        </div>"""

    cols = ["", "", ""]
    for i, t in enumerate(top):
        cols[i % 3] += f'<div style="display:flex;margin-bottom:12px;">{card(t)}</div>'

    cols_html = "".join(
        f'<div style="flex:1;display:flex;flex-direction:column;min-width:0;">{c}</div>'
        for c in cols
    )

    return f"""<!DOCTYPE html>
<html lang="fr">
<head><meta charset="utf-8">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;900&display=swap" rel="stylesheet">
<style>
  * {{ margin:0;padding:0;box-sizing:border-box; }}
  body {{ width:1920px;height:1080px;overflow:hidden;font-family:'Inter',sans-serif;color:#fff;
          {bg_css}
          position:relative; }}
  body::before {{ content:'';position:absolute;inset:0;background:rgba(5,10,30,0.72);z-index:0; }}
  .wrap {{ position:relative;z-index:1;display:flex;flex-direction:column;height:100%;
           padding:32px 48px; }}
</style>
</head>
<body>
<div class="wrap">

  <!-- HEADER -->
  <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:24px;">
    {logo_html}
    <div style="text-align:center;">
      <div style="font-size:22px;font-weight:900;color:#fff;letter-spacing:1px;">
        🌐 DÉBRIEFING MÉTÉO TWITTER
      </div>
      <div style="font-size:14px;color:#aaa;margin-top:4px;">Fil de veille scientifique — {date} à {heure}</div>
    </div>
    <div style="text-align:right;color:#888;font-size:13px;">
      <div>Données temps réel</div>
      <div>API Twitter/X</div>
    </div>
  </div>

  <!-- SEPARATOR -->
  <div style="height:1px;background:linear-gradient(90deg,transparent,#1DA1F2,transparent);margin-bottom:24px;"></div>

  <!-- 3 COLUMNS -->
  <div style="flex:1;display:flex;gap:20px;min-height:0;">
    {cols_html}
  </div>

  <!-- FOOTER -->
  <div style="margin-top:20px;display:flex;align-items:center;justify-content:space-between;">
    <div style="font-size:12px;color:#666;">Source : fil de veille météorologique @Monsieurmeteo07</div>
    <div style="font-size:13px;font-weight:700;color:#1DA1F2;">monsieurmeteo.com</div>
  </div>
</div>
</body></html>"""

# ── Main ─────────────────────────────────────────────────────────────────────

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

    logo_b64 = img_to_b64(LOGO_FILE)
    bg_b64   = img_to_b64(BG_FILE)

    html = build_html(tweets, logo_b64, bg_b64)

    # Write tweet text for publication
    os.makedirs(os.path.dirname(TWEET_FILE), exist_ok=True)
    top3 = [t for t in tweets[:3] if t]
    lines = ["🌤️ Débriefing Météo du fil de veille :\n"]
    for t in top3:
        lines.append(f"• @{t.get('username','?')} : {truncate(t.get('text',''), 90)}")
    lines.append("\n#Météo #MeteoFrance #Vigilance")
    with open(TWEET_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    # Capture via Playwright (serve from temp file for CORS-free loading)
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w", encoding="utf-8") as tmp:
        tmp.write(html)
        tmp_path = tmp.name

    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.set_viewport_size({"width": 1920, "height": 1080})
            page.goto(f"file:///{tmp_path.replace(os.sep, '/')}")
            page.wait_for_timeout(2500)  # Wait for fonts
            page.screenshot(path=OUTPUT, quality=92, type="jpeg")
            browser.close()
        print(f"✅ Infographie générée : {OUTPUT}")
    except Exception as e:
        print(f"ERROR capturing screenshot: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        os.unlink(tmp_path)

if __name__ == "__main__":
    main()
