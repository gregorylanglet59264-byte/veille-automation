"""
fast_veille.py — Veille RSS ultra-rapide, zéro appel LLM.
- Collecte tous les flux RSS en parallèle
- Collecte les nouveaux modèles LLM (OpenRouter, HuggingFace, GitHub)
- Filtre les 24 dernières heures
- Génère un email HTML premium par catégorie
- Temps d'exécution : 5-15 secondes"""
import os
import sys
import json
import argparse
import datetime
import smtplib
import concurrent.futures
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formatdate, make_msgid

# ─── Flux RSS ────────────────────────────────────────────────────────────────

FEEDS = {
    "🇫🇷 France": {
        "Le Monde":    "https://www.lemonde.fr/rss/une.xml",
        "BFM TV":      "https://www.bfmtv.com/rss/news-24-7/",
        "FranceInfo":  "https://www.francetvinfo.fr/titres.rss",
        "Le Figaro":   "https://www.lefigaro.fr/rss/figaro_actualites.xml",
        "Libération":  "https://www.liberation.fr/arc/outboundfeeds/rss/?outputType=xml",
        "L'Obs":       "https://www.nouvelobs.com/rss.xml",
    },
    "🌍 International": {
        "France 24":      "https://www.france24.com/fr/rss",
        "RFI Monde":      "https://www.rfi.fr/fr/g%C3%A9n%C3%A9ral/rss",
        "Euronews FR":    "https://fr.euronews.com/rss?format=xml",
        "Courrier Int.":  "https://www.courrierinternational.com/feed/all/rss.xml",
        "BBC World":      "https://feeds.bbci.co.uk/news/world/rss.xml",
    },
    "🏭 Hauts-de-France": {
        "France 3 HDF":       "https://france3-regions.francetvinfo.fr/hauts-de-france/rss",
        "France 3 NPC":       "https://france3-regions.francetvinfo.fr/hauts-de-france/nord-pas-de-calais/rss",
        "La Voix du Nord":    "https://www.lavoixdunord.fr/arc/outboundfeeds/rss/?outputType=xml",
        "BFM Grand Lille":    "https://www.bfmtv.com/rss/grand-lille/",
        "BFM Grand Littoral": "https://www.bfmtv.com/rss/grand-littoral/",
    },
    "🤖 Intelligence Artificielle": {
        "BFM Tech IA":      "https://www.bfmtv.com/rss/tech/intelligence-artificielle/",
        "Numerama":         "https://www.numerama.com/feed/",
        "PresseCitron":     "https://www.presse-citron.net/feed/",
        "TechCrunch":       "https://techcrunch.com/feed/",
        "MIT Tech Review":  "https://www.technologyreview.com/feed/",
        "Hacker News":      "https://hnrss.org/frontpage",
    },
    "🌦️ Météo & Climat": {
        "BFM TV":          "https://www.bfmtv.com/rss/news-24-7/",
        "FranceInfo":      "https://www.francetvinfo.fr/titres.rss",
        "Science & Vie":   "https://www.science-et-vie.com/feed",
        "Le Monde":        "https://www.lemonde.fr/planete/rss_full.xml",
    },
    "⚡ Intempéries & Risques": {
        "FranceInfo":  "https://www.francetvinfo.fr/titres.rss",
        "BFM TV":      "https://www.bfmtv.com/rss/news-24-7/",
        "Le Monde":    "https://www.lemonde.fr/rss/une.xml",
        "France 24":   "https://www.france24.com/fr/rss",
    },
    "🎯 Bons Plans IA & Outils": {
        # Lancements & nouveaux outils
        "ProductHunt AI":     "https://www.producthunt.com/feed?category=ai",
        "OpenAI Blog":        "https://openai.com/news/rss.xml",
        "HuggingFace Blog":   "https://huggingface.co/blog/feed.xml",
        # Newsletters IA (abonnements, promos, outils)
        "Ben's Bites":        "https://bensbites.substack.com/feed",
        "Import AI":          "https://importai.substack.com/feed",
        "Latent Space":       "https://www.latent.space/feed",
        # Médias Tech (section IA)
        "TechCrunch AI":      "https://techcrunch.com/category/artificial-intelligence/feed/",
        "VentureBeat AI":     "https://venturebeat.com/category/ai/feed/",
        "Wired AI":           "https://www.wired.com/feed/tag/ai/latest/rss",
        "MarkTechPost":       "https://www.marktechpost.com/feed/",
        # Communautés (Show HN = nouveaux outils publiés)
        "HN Show AI":         "https://hnrss.org/show?q=AI",
    },
}

# Mots-clés pour filtrer les catégories dédiées
KEYWORDS_METEO = ["météo", "canicule", "orage", "tempête", "cyclone", "inondation", "sécheresse", "chaleur", "froid", "neige", "pluie", "vent", "vigilance", "climat", "réchauffement"]
KEYWORDS_INTEMPERIES = ["orage", "inondation", "cyclone", "tempête", "grêle", "tornade", "canicule", "alerte", "vigilance", "crues", "feux", "incendie", "catastrophe"]
KEYWORDS_IA = ["ia", "intelligence artificielle", "chatgpt", "gemini", "claude", "llm", "mistral", "openai", "anthropic", "deepseek", "gpt", "modèle", "machine learning", "algorithme", "robot", "automation", "agent ia"]
KEYWORDS_BONSPLANS = [
    # Français
    "gratuit", "lancement", "nouveau", "beta", "offre", "abonnement", "essai",
    "freemium", "promo", "promotion", "réduction", "rabais", "outil ia",
    "chatgpt plus", "claude pro", "gemini pro", "open source", "accès gratuit",
    # Anglais (newsletters et sources US)
    "free", "launch", "new", "deal", "discount", "subscription", "trial",
    "release", "api", "tool", "app", "platform", "model", "agent",
    "chatgpt", "claude", "gemini", "openai", "anthropic", "mistral",
    "open-source", "open source", "free tier", "limited time", "lifetime",
    "pro plan", "ai tool", "ai app", "ai platform", "ai agent",
]

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# Sources anglophones dont on traduit les titres/descriptions
ENGLISH_SOURCES = {
    "BBC World", "BBC News",
    "TechCrunch", "TechCrunch AI",
    "VentureBeat AI",
    "Wired AI",
    "MIT Tech Review",
    "Hacker News", "HN Show AI",
    "MarkTechPost",
    "Import AI",
    "Latent Space",
    "Ben's Bites",
    "AppSumo",
    "HuggingFace Blog",
    "OpenAI Blog",
}

def _gtranslate(text):
    """Translate text to French via the free Google Translate public endpoint."""
    if not text or len(text) < 5:
        return text
    try:
        import urllib.parse
        url = (
            "https://translate.googleapis.com/translate_a/single"
            "?client=gtx&sl=auto&tl=fr&dt=t&q=" + urllib.parse.quote(text[:400])
        )
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=5) as r:
            data = json.loads(r.read().decode())
            # Response: [[[translated, original, ...], ...], ...]
            return "".join(seg[0] for seg in data[0] if seg[0])
    except Exception:
        return text  # Fallback: texte original

def translate_articles(articles):
    """Translate TITLES of English articles to French in parallel (desc kept as-is for speed)."""
    english = [(i, a) for i, a in enumerate(articles) if a.get("source") in ENGLISH_SOURCES]
    if not english:
        return articles

    def _translate_one(idx_art):
        idx, a = idx_art
        title_fr = _gtranslate(a.get("title", ""))
        return idx, title_fr

    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
        for idx, title_fr in pool.map(_translate_one, english):
            articles[idx]["title"] = title_fr

    return articles

# ─── Collecte RSS ─────────────────────────────────────────────────────────────


def _parse_date(date_str):
    if not date_str:
        return None
    for fmt in ("%a, %d %b %Y %H:%M:%S %z", "%a, %d %b %Y %H:%M:%S GMT", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%SZ"):
        try:
            return datetime.datetime.strptime(date_str.strip(), fmt).replace(tzinfo=datetime.timezone.utc)
        except ValueError:
            continue
    try:
        from email.utils import parsedate_to_datetime
        return parsedate_to_datetime(date_str.strip())
    except Exception:
        return None

def fetch_one_feed(name, url, max_hours=24):
    """Fetch a single RSS feed, return list of recent articles."""
    articles = []
    now = datetime.datetime.now(datetime.timezone.utc)
    cutoff = now - datetime.timedelta(hours=max_hours)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=10) as resp:
            root = ET.fromstring(resp.read())
        for item in root.findall(".//item"):
            title_el = item.find("title")
            link_el  = item.find("link")
            pub_el   = item.find("pubDate")
            desc_el  = item.find("description")
            title = (title_el.text or "").strip() if title_el is not None else ""
            link  = (link_el.text or "").strip() if link_el is not None else ""
            pub   = (pub_el.text or "") if pub_el is not None else ""
            desc  = (desc_el.text or "").strip() if desc_el is not None else ""
            # Strip HTML from description
            import re
            desc = re.sub(r"<[^>]+>", "", desc)[:200]
            pub_dt = _parse_date(pub)
            if pub_dt and pub_dt < cutoff:
                continue
            articles.append({"title": title, "url": link, "source": name, "date": pub, "desc": desc, "dt": pub_dt})
    except Exception as e:
        print(f"  [RSS] {name}: {e}")
    return articles

def fetch_category(category_name, feeds_dict, max_hours=24, keywords=None, max_items=12):
    """Fetch all feeds for a category in parallel, deduplicate and filter."""
    all_articles = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(feeds_dict)) as pool:
        futures = {pool.submit(fetch_one_feed, name, url, max_hours): name for name, url in feeds_dict.items()}
        for future in concurrent.futures.as_completed(futures):
            all_articles.extend(future.result())

    # Keyword filter for thematic categories
    if keywords:
        filtered = []
        for a in all_articles:
            text = (a["title"] + " " + a["desc"]).lower()
            if any(kw in text for kw in keywords):
                filtered.append(a)
        all_articles = filtered if filtered else all_articles  # fallback: keep all if too narrow

    # Deduplicate by title similarity (first 60 chars)
    seen = set()
    deduped = []
    for a in all_articles:
        key = a["title"][:60].lower()
        if key not in seen and a["url"]:
            seen.add(key)
            deduped.append(a)

    # Sort newest first
    deduped.sort(key=lambda x: x["dt"].timestamp() if x["dt"] else 0, reverse=True)
    deduped = deduped[:max_items]
    print(f"  [{category_name}] {len(deduped)} articles retenus")
    return translate_articles(deduped)

# ─── Collecte LLM (OpenRouter + HuggingFace + GitHub) ────────────────────────

def fetch_llm_section(days=1):
    """Collecte les nouveaux modèles LLM via APIs JSON publiques, sans LLM."""
    now = datetime.datetime.now(datetime.timezone.utc)
    cutoff = now - datetime.timedelta(days=days)
    results = []

    def _or_models():
        """Nouveaux modèles sur OpenRouter."""
        try:
            req = urllib.request.Request(
                "https://openrouter.ai/api/v1/models",
                headers={"User-Agent": UA}
            )
            with urllib.request.urlopen(req, timeout=12) as r:
                data = json.loads(r.read().decode())["data"]
            now_ts = now.timestamp()
            for m in sorted(data, key=lambda x: x.get("created", 0), reverse=True):
                age_days = (now_ts - m.get("created", 0)) / 86400
                if age_days > days:
                    break
                pricing = m.get("pricing", {})
                prompt_price = float(pricing.get("prompt", 0) or 0)
                price_label = "Gratuit" if prompt_price == 0 else f"{prompt_price*1e6:.2f}$/M tokens"
                results.append({
                    "title": f"[OpenRouter] {m.get('name', m.get('id'))}",
                    "url": f"https://openrouter.ai/models/{m.get('id', '')}",
                    "source": "OpenRouter",
                    "desc": f"{price_label} · {m.get('description', '')[:150]}",
                    "dt": datetime.datetime.fromtimestamp(m.get("created", 0), datetime.timezone.utc),
                })
        except Exception as e:
            print(f"  [LLM] OpenRouter: {e}")

    def _hf_models():
        """Nouveaux modèles text-generation sur HuggingFace."""
        try:
            url = "https://huggingface.co/api/models?filter=text-generation&sort=lastModified&direction=-1&limit=30"
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=12) as r:
                data = json.loads(r.read().decode())
            for m in data:
                lm = m.get("lastModified", "")
                if not lm:
                    continue
                dt = datetime.datetime.fromisoformat(lm.replace("Z", "+00:00"))
                if dt < cutoff:
                    continue
                model_id = m.get("id", "")
                likes = m.get("likes", 0)
                results.append({
                    "title": f"[HuggingFace] {model_id}",
                    "url": f"https://huggingface.co/{model_id}",
                    "source": "HuggingFace",
                    "desc": f"{likes} ❤️ · {m.get('author', '')} · text-generation",
                    "dt": dt,
                })
        except Exception as e:
            print(f"  [LLM] HuggingFace: {e}")

    def _github_releases():
        """Nouvelles releases GitHub des runtimes IA."""
        repos = [("ollama", "ollama"), ("ggerganov", "llama.cpp"), ("vllm-project", "vllm")]
        for owner, repo in repos:
            try:
                url = f"https://api.github.com/repos/{owner}/{repo}/releases"
                req = urllib.request.Request(url, headers={"User-Agent": UA})
                with urllib.request.urlopen(req, timeout=10) as r:
                    data = json.loads(r.read().decode())
                for rel in data:
                    pub = rel.get("published_at", "")
                    if not pub:
                        continue
                    dt = datetime.datetime.fromisoformat(pub.replace("Z", "+00:00"))
                    if dt < cutoff:
                        break
                    results.append({
                        "title": f"[{repo}] {rel.get('tag_name', '')}",
                        "url": rel.get("html_url", f"https://github.com/{owner}/{repo}/releases"),
                        "source": repo,
                        "desc": (rel.get("body", "") or "")[:180],
                        "dt": dt,
                    })
            except Exception as e:
                print(f"  [LLM] GitHub {repo}: {e}")

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        pool.submit(_or_models).result()
        pool.submit(_hf_models).result()
        pool.submit(_github_releases).result()

    results.sort(key=lambda x: x["dt"].timestamp() if x["dt"] else 0, reverse=True)
    deduped, seen = [], set()
    for a in results:
        key = a["title"][:60].lower()
        if key not in seen:
            seen.add(key)
            deduped.append(a)
    print(f"  [🧠 Modèles LLM] {len(deduped)} nouveautés retenues")
    # Tous les modèles LLM sont en anglais → traduction des titres uniquement (max 10)
    top = deduped[:15]
    llm_sources_backup = set(ENGLISH_SOURCES)
    ENGLISH_SOURCES.update(a["source"] for a in top)
    translated = translate_articles(top[:10])  # limite à 10 pour la vitesse
    translated += top[10:]  # reste sans traduction
    ENGLISH_SOURCES.clear()
    ENGLISH_SOURCES.update(llm_sources_backup)
    return translated


# ─── HTML Generation ──────────────────────────────────────────────────────────

CATEGORY_COLORS = {
    "🇫🇷 France":                  "#2563eb",
    "🌍 International":             "#7c3aed",
    "🏭 Hauts-de-France":           "#db2777",
    "🤖 Intelligence Artificielle": "#059669",
    "🌦️ Météo & Climat":            "#0891b2",
    "⚡ Intempéries & Risques":      "#dc2626",
    "🎯 Bons Plans IA & Outils":    "#d97706",
    "🧠 Modèles LLM":              "#6d28d9",
}

def _format_date_fr(dt):
    if not dt:
        return ""
    MONTHS = ["jan.", "fév.", "mars", "avr.", "mai", "juin", "juil.", "août", "sept.", "oct.", "nov.", "déc."]
    dt_local = dt.astimezone()
    return f"{dt_local.day} {MONTHS[dt_local.month-1]} {dt_local.strftime('%H:%M')}"

def get_date_fr():
    now = datetime.datetime.now()
    DAYS = ["Lundi","Mardi","Mercredi","Jeudi","Vendredi","Samedi","Dimanche"]
    MONTHS = ["janvier","février","mars","avril","mai","juin","juillet","août","septembre","octobre","novembre","décembre"]
    return f"{DAYS[now.weekday()]} {now.day} {MONTHS[now.month-1]} {now.year}"

def build_html(all_data, date_str):
    total = sum(len(v) for v in all_data.values())
    
    sections_html = ""
    for cat, articles in all_data.items():
        if not articles:
            continue
        color = CATEGORY_COLORS.get(cat, "#334155")
        items_html = ""
        for a in articles:
            date_label = _format_date_fr(a.get("dt"))
            desc = a.get("desc", "")
            items_html += f"""
            <div style="padding:12px 0;border-bottom:1px solid #f1f5f9;">
              <div style="display:flex;align-items:flex-start;gap:10px;">
                <div style="width:4px;min-width:4px;height:100%;background:{color};border-radius:2px;margin-top:4px;"></div>
                <div>
                  <a href="{a['url']}" target="_blank"
                     style="font-size:14px;font-weight:600;color:#1e293b;text-decoration:none;line-height:1.4;display:block;">
                    {a['title']}
                  </a>
                  {"<p style='margin:4px 0 0;font-size:12px;color:#64748b;line-height:1.5;'>"+desc+"</p>" if desc else ""}
                  <div style="margin-top:5px;display:flex;gap:10px;align-items:center;">
                    <span style="font-size:11px;font-weight:700;color:#fff;background:{color};padding:2px 8px;border-radius:12px;">{a['source']}</span>
                    {"<span style='font-size:11px;color:#94a3b8;'>"+date_label+"</span>" if date_label else ""}
                  </div>
                </div>
              </div>
            </div>"""

        sections_html += f"""
        <div style="margin:24px 0;background:#fff;border-radius:12px;border:1px solid #e2e8f0;overflow:hidden;box-shadow:0 1px 4px rgba(0,0,0,.06);">
          <div style="background:{color};padding:14px 20px;display:flex;align-items:center;gap:10px;">
            <div style="flex:1;">
              <h2 style="margin:0;font-size:15px;font-weight:700;color:#fff;letter-spacing:.3px;">{cat}</h2>
              <span style="font-size:11px;color:rgba(255,255,255,.75);">{len(articles)} article{"s" if len(articles)>1 else ""}</span>
            </div>
          </div>
          <div style="padding:0 18px;">{items_html}</div>
        </div>"""

    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Veille Rapide — {date_str}</title>
</head>
<body style="margin:0;padding:0;background:#f8fafc;font-family:'Segoe UI',Arial,sans-serif;">
  <div style="max-width:680px;margin:0 auto;padding:20px 10px;">

    <!-- Header -->
    <div style="background:linear-gradient(135deg,#1e3a5f,#2563eb);border-radius:16px;padding:30px 28px;margin-bottom:8px;text-align:center;">
      <p style="margin:0 0 6px;font-size:12px;color:rgba(255,255,255,.65);letter-spacing:2px;text-transform:uppercase;">Veille Médias — RSS Direct</p>
      <h1 style="margin:0;font-size:24px;font-weight:800;color:#fff;line-height:1.2;">📰 {date_str}</h1>
      <p style="margin:10px 0 0;font-size:13px;color:rgba(255,255,255,.7);">{total} articles · {len([c for c,v in all_data.items() if v])} catégories · Dernières 24h</p>
    </div>

    <!-- Notice -->
    <div style="background:#eff6ff;border:1px solid #bfdbfe;border-radius:10px;padding:12px 16px;margin:12px 0;font-size:12px;color:#1d4ed8;text-align:center;">
      ⚡ <strong>Veille rapide — aucune IA</strong> · Flux RSS bruts filtrés sur les dernières 24 heures · Cliquez sur les titres pour lire l'article complet
    </div>

    {sections_html}

    <!-- Footer -->
    <div style="text-align:center;padding:20px;color:#94a3b8;font-size:11px;">
      Généré automatiquement par <strong>fast_veille.py</strong> · Flux RSS public · Zéro token LLM<br>
      <a href="mailto:gregory.langlet@sfr.fr" style="color:#60a5fa;">gregory.langlet@sfr.fr</a>
    </div>
  </div>
</body>
</html>"""

# ─── Email ────────────────────────────────────────────────────────────────────

def send_email(html_body, date_str):
    gmail_email    = (os.environ.get("GMAIL_EMAIL", "langlet.gregory@gmail.com") or "").strip()
    gmail_password = (os.environ.get("GMAIL_APP_PASSWORD") or "").strip()
    recipients_raw = os.environ.get("RECIPIENT_EMAILS", "gregory.langlet@sfr.fr")
    recipients     = [r.strip() for r in recipients_raw.split(",") if r.strip()]

    if not gmail_password:
        print("[SMTP] ERREUR : GMAIL_APP_PASSWORD manquant.")
        sys.exit(1)

    msg = MIMEMultipart("alternative")
    msg["Subject"]  = f"⚡ Veille Rapide RSS — {date_str}"
    msg["From"]     = f"Veille Rapide <{gmail_email}>"
    msg["To"]       = ", ".join(recipients)
    msg["Reply-To"] = "gregory.langlet@sfr.fr"
    msg["Date"]     = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid(domain="gmail.com")
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    print(f"[SMTP] Envoi à {', '.join(recipients)} via Gmail...")
    with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as s:
        s.ehlo(); s.starttls(); s.ehlo()
        s.login(gmail_email, gmail_password)
        s.sendmail(gmail_email, recipients, msg.as_string())
    print("[SMTP] ✅ Email envoyé avec succès !")

# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    import time as _time
    parser = argparse.ArgumentParser(description="Veille RSS rapide — zéro LLM")
    parser.add_argument("--dry-run", action="store_true", help="Sauvegarde le HTML en local sans envoyer")
    parser.add_argument("--hours", type=int, default=24, help="Fenêtre de filtrage en heures (défaut: 24)")
    args = parser.parse_args()

    t0 = _time.time()
    date_str = get_date_fr()
    print(f"=== Veille Rapide RSS + LLM — {date_str} ===")
    print(f"Fenêtre : {args.hours}h | {len(FEEDS)} catégories RSS + 1 catégorie LLM | {sum(len(v) for v in FEEDS.values())} flux")
    print()

    KEYWORD_MAP = {
        "🌦️ Météo & Climat":           KEYWORDS_METEO,
        "⚡ Intempéries & Risques":     KEYWORDS_INTEMPERIES,
        "🤖 Intelligence Artificielle": KEYWORDS_IA,
        "🎯 Bons Plans IA & Outils": KEYWORDS_BONSPLANS,
    }

    all_data = {}

    # Collecte RSS + LLM en parallèle
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(FEEDS) + 1) as pool:
        # Flux RSS
        rss_futures = {
            pool.submit(
                fetch_category,
                cat, feeds_dict, args.hours,
                KEYWORD_MAP.get(cat), 12
            ): cat
            for cat, feeds_dict in FEEDS.items()
        }
        # LLM (OpenRouter + HuggingFace + GitHub) — fenêtre 24h
        llm_future = pool.submit(fetch_llm_section, days=max(1, args.hours // 24))

        for future in concurrent.futures.as_completed(rss_futures):
            all_data[rss_futures[future]] = future.result()

        all_data["🧠 Modèles LLM"] = llm_future.result()

    # Réordonner : RSS d'abord, LLM en dernier
    ordered = {k: all_data[k] for k in FEEDS if k in all_data}
    ordered["🧠 Modèles LLM"] = all_data.get("🧠 Modèles LLM", [])

    total = sum(len(v) for v in ordered.values())
    elapsed = _time.time() - t0
    print(f"\n✅ {total} éléments collectés en {elapsed:.1f} secondes")

    html = build_html(ordered, date_str)

    if args.dry_run:
        out = "veille_rapide_dryrun.html"
        with open(out, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"[Dry-run] HTML sauvegardé dans '{out}'")
        # Copie automatique sur le Bureau
        desktop = os.path.join(os.path.expanduser("~"), "Desktop", out)
        try:
            import shutil
            shutil.copy(out, desktop)
            print(f"[Dry-run] Copié sur le Bureau : {desktop}")
        except Exception:
            pass
    else:
        send_email(html, date_str)
    print(f"Terminé en {_time.time() - t0:.1f} secondes.")

if __name__ == "__main__":
    main()
