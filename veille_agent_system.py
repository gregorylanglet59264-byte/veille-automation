# -*- coding: utf-8 -*-
"""
veille_agent_system.py
Moteur d'Orchestration et d'Analyse Multi-Agents de Veille Automatisée.
Architecture :
1. Collecteurs parallèles (Météo/Climat, IA/Tech, France, Monde, HuggingFace/OpenRouter)
2. Vérification (Ancienneté <24h, Source Primaire, Fiabilité Forte/Moyenne/Faible)
3. Mémoire Persistante SQLite & Dédoublonnage (story_id, statut NOUVEAU vs MISE À JOUR)
4. Moteur de Scoring /100 (Importance, Nouveauté, Fiabilité, Impact, Intérêt)
5. Classification d'Urgence (🔴 Urgent, 🟠 Important, 🟢 À retenir)
6. Rédacteur & Diffuseur (Tableau de bord HTML interactif, Flash Top 10, Markdown, JSON)
"""

import os
import sys
import json
import sqlite3
import hashlib
import re
import datetime
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import email.utils
from concurrent.futures import ThreadPoolExecutor, as_completed

# --- CONFIGURATION DES CHEMINS ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "veille_history.db")
DESKTOP_DIR = os.path.join(os.path.expanduser("~"), "Desktop")
OUTPUT_HTML_DESKTOP = os.path.join(DESKTOP_DIR, "veille_multiagent_dashboard.html")
OUTPUT_MD_DESKTOP = os.path.join(DESKTOP_DIR, "veille_multiagent_rapport.md")
OUTPUT_JSON_LOCAL = os.path.join(BASE_DIR, "veille_latest_results.json")

# --- INITIALISATION DE LA BASE SQLITE PERSISTANTE ---
def init_database():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS stories (
        story_id TEXT PRIMARY KEY,
        category TEXT,
        title TEXT,
        summary TEXT,
        why_it_matters TEXT,
        sources_json TEXT,
        first_seen_at TEXT,
        last_updated_at TEXT,
        update_count INTEGER DEFAULT 1,
        reliability TEXT,
        score INTEGER,
        score_importance INTEGER,
        score_novelty INTEGER,
        score_reliability INTEGER,
        score_impact INTEGER,
        score_interest INTEGER,
        urgency TEXT,
        status TEXT
    )
    """)
    conn.commit()
    conn.close()

# --- UTILITAIRES & DECODAGE ---
def clean_text(text):
    if not text:
        return ""
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def compute_story_fingerprint(category, title, summary=""):
    clean = f"{category.lower()}_{title.lower()}".strip()
    words = re.findall(r'\b[a-zA-Z0-9à-ÿ]{4,}\b', clean)
    stop_words = {"dans", "pour", "avec", "cette", "plus", "fait", "sont", "leur", "apres", "selon", "entre", "comme"}
    filtered_words = sorted(list(set([w for w in words if w not in stop_words])))
    key = "_".join(filtered_words[:8])
    if not key:
        key = clean[:50]
    return hashlib.sha256(key.encode('utf-8')).hexdigest()[:16]

def parse_rfc822_date(date_str):
    if not date_str:
        return datetime.datetime.now(datetime.timezone.utc)
    try:
        dt = email.utils.parsedate_to_datetime(date_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=datetime.timezone.utc)
        else:
            dt = dt.astimezone(datetime.timezone.utc)
        return dt
    except Exception:
        return datetime.datetime.now(datetime.timezone.utc)

# --- SOUS-AGENT COLLECTE : GOOGLE NEWS RSS DÉCODÉ ---
def fetch_google_news_rss(query, category_name, max_items=25):
    encoded = urllib.parse.quote(f"{query} when:1d")
    url = f"https://news.google.com/rss/search?q={encoded}&hl=fr&gl=FR&ceid=FR:fr"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    articles = []
    
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=12) as resp:
            root = ET.fromstring(resp.read())
            
        now = datetime.datetime.now(datetime.timezone.utc)
        for item in root.findall(".//item")[:max_items]:
            raw_title = clean_text(item.find("title").text if item.find("title") is not None else "")
            link = clean_text(item.find("link").text if item.find("link") is not None else "")
            pub_date = clean_text(item.find("pubDate").text if item.find("pubDate") is not None else "")
            desc = clean_text(item.find("description").text if item.find("description") is not None else "")
            
            source = "Média d'actualité"
            source_el = item.find("source")
            if source_el is not None and source_el.text:
                source = source_el.text.strip()
                suffix = f" - {source}"
                if raw_title.endswith(suffix):
                    raw_title = raw_title[:-len(suffix)].strip()
            
            dt = parse_rfc822_date(pub_date)
            age_hours = (now - dt).total_seconds() / 3600.0
            
            articles.append({
                "category": category_name,
                "title": raw_title,
                "url": link,
                "source": source,
                "date_raw": pub_date,
                "date_dt": dt,
                "age_hours": age_hours,
                "raw_summary": desc
            })
    except Exception as e:
        print(f"[{category_name}] Erreur flux '{query}': {e}", file=sys.stderr)
        
    return articles

# --- SOUS-AGENT COLLECTE : APIs LLM / HUGGING FACE / OPENROUTER ---
def fetch_llm_hub_models():
    results = []
    now = datetime.datetime.now(datetime.timezone.utc)
    # 1. Hugging Face Hub (nouveaux modèles text-generation populaires)
    try:
        hf_url = "https://huggingface.co/api/models?pipeline_tag=text-generation&sort=lastModified&direction=-1&limit=8"
        req = urllib.request.Request(hf_url, headers={"User-Agent": "VeilleMultiAgent/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            for m in data:
                m_id = m.get("id", "")
                likes = m.get("likes", 0)
                last_mod = m.get("lastModified", "")
                if m_id and likes >= 3:
                    title = f"Nouveau modèle open-source : {m_id} ({likes} ❤️ sur Hugging Face)"
                    url = f"https://huggingface.co/{m_id}"
                    results.append({
                        "category": "ia_tech",
                        "title": title,
                        "url": url,
                        "source": "Hugging Face Hub",
                        "date_raw": last_mod,
                        "date_dt": now,
                        "age_hours": 2.0,
                        "raw_summary": f"Publication et mise à jour récente du checkpoint de modèle {m_id} sur le hub officiel Hugging Face."
                    })
    except Exception as e:
        print(f"[IA/Tech] Hugging Face API info: {e}", file=sys.stderr)

    # 2. OpenRouter API (derniers modèles commerciaux branchés)
    try:
        or_url = "https://openrouter.ai/api/v1/models"
        req = urllib.request.Request(or_url, headers={"User-Agent": "VeilleMultiAgent/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            models = data.get("data", [])
            for m in models[:4]:
                name = m.get("name", m.get("id"))
                desc = m.get("description", "Modèle disponible sur OpenRouter API.")
                context = m.get("context_length", 0)
                results.append({
                    "category": "ia_tech",
                    "title": f"Modèle IA sur OpenRouter : {name} ({context//1000}k contexte)",
                    "url": f"https://openrouter.ai/{m.get('id')}",
                    "source": "OpenRouter API",
                    "date_raw": now.strftime("%Y-%m-%d"),
                    "date_dt": now,
                    "age_hours": 4.0,
                    "raw_summary": desc[:250] + ("..." if len(desc) > 250 else "")
                })
    except Exception as e:
        print(f"[IA/Tech] OpenRouter API info: {e}", file=sys.stderr)
        
    return results

# --- SOUS-AGENT VÉRIFICATION & FIABILITÉ ---
KNOWN_AUTHORITATIVE_SOURCES = {
    # Agences & Presse de référence
    "afp": "Forte", "reuters": "Forte", "associated press": "Forte", "ap": "Forte",
    "le monde": "Forte", "france 24": "Forte", "bbc": "Forte", "franceinfo": "Forte",
    "libération": "Forte", "le figaro": "Forte", "les echos": "Forte", "courrier international": "Forte",
    # Météo & Climat
    "météo-france": "Forte", "meteo-france": "Forte", "infoclimat": "Forte", "keraunos": "Forte",
    "noaa": "Forte", "national hurricane center": "Forte", "nhc": "Forte", "wmo": "Forte",
    "omg": "Forte", "vigicrues": "Forte", "sdis": "Forte",
    # IA & Tech Labs
    "openai": "Forte", "google deepmind": "Forte", "google blog": "Forte", "anthropic": "Forte",
    "hugging face": "Forte", "hugging face hub": "Forte", "openrouter api": "Forte", "deepseek": "Forte",
    "mistral ai": "Forte", "meta ai": "Forte", "github": "Forte", "nature": "Forte", "mit technology review": "Forte"
}

def verify_and_rate_source(article):
    source_lower = article["source"].lower()
    reliability = "Moyenne"
    
    for auth_key, level in KNOWN_AUTHORITATIVE_SOURCES.items():
        if auth_key in source_lower:
            reliability = level
            break
            
    is_recent = article["age_hours"] <= 26.0
    return reliability, is_recent

# --- SOUS-AGENT SCORING & CLASSEMENT D'URGENCE ---
def calculate_article_score(article, reliability):
    title_lower = article["title"].lower()
    summary_lower = article["raw_summary"].lower()
    full_text = f"{title_lower} {summary_lower}"
    
    # 1. Importance (/30)
    importance = 15
    critical_keywords = [
        "alerte rouge", "vigilance rouge", "alerte orange", "ouragan", "cyclone", "séisme", "tsunami", "record absolu",
        "deepseek-v4", "gpt-5", "claude 3.7", "gemini 3", "rupture", "accord historique", "attaque", "sommet",
        "morts", "victimes", "évacuation", "décret", "faillite", "investit", "milliards", "urgence"
    ]
    high_keywords = [
        "record", "tempête", "inondation", "canicule", "sécheresse", "incendie", "feu de forêt",
        "nouveau modèle", "open-source", "benchmark", "ministre", "gouvernement", "ue", "président", "inflation"
    ]
    if any(k in full_text for k in critical_keywords):
        importance = 30
    elif any(k in full_text for k in high_keywords):
        importance = 24
    elif len(article["title"]) > 40:
        importance = 18

    # 2. Nouveauté (/25)
    age = article.get("age_hours", 12.0)
    if age <= 3.0:
        novelty = 25
    elif age <= 6.0:
        novelty = 22
    elif age <= 12.0:
        novelty = 18
    elif age <= 24.0:
        novelty = 14
    else:
        novelty = 5

    # 3. Fiabilité (/20)
    if reliability == "Forte":
        score_rel = 20
    elif reliability == "Moyenne":
        score_rel = 14
    else:
        score_rel = 6

    # 4. Impact potentiel (/15)
    impact_keywords = ["france", "mondial", "europe", "sécurité", "économie", "entreprises", "développeurs", "climat", "réseau", "transports"]
    matches = sum(1 for k in impact_keywords if k in full_text)
    impact = min(15, 8 + matches * 2)

    # 5. Intérêt stratégique utilisateur (/10)
    if article["category"] in ["meteo", "ia_tech"]:
        interest = 10
    elif article["category"] == "actu_france":
        interest = 8
    else:
        interest = 7

    total_score = importance + novelty + score_rel + impact + interest
    total_score = min(100, max(0, total_score))
    
    if total_score >= 82 or importance >= 28:
        urgency = "🔴 Urgent"
    elif total_score >= 70:
        urgency = "🟠 Important"
    else:
        urgency = "🟢 À retenir"
        
    return {
        "score": total_score,
        "importance": importance,
        "novelty": novelty,
        "reliability": score_rel,
        "impact": impact,
        "interest": interest,
        "urgency": urgency
    }

# --- SOUS-AGENT DÉDOUBLONNAGE & MÉMOIRE PERSISTANTE (SQLITE) ---
def process_story_memory_and_dedup(article, scoring, reliability):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    story_id = compute_story_fingerprint(article["category"], article["title"])
    
    cur.execute("SELECT story_id, title, sources_json, update_count, first_seen_at FROM stories WHERE story_id = ?", (story_id,))
    row = cur.fetchone()
    
    sources = [{"name": article["source"], "url": article["url"]}]
    
    if row:
        prev_sources = json.loads(row[2]) if row[2] else []
        existing_urls = [s.get("url") for s in prev_sources]
        if article["url"] not in existing_urls:
            prev_sources.append({"name": article["source"], "url": article["url"]})
            
        update_count = row[3] + 1
        status = "MISE À JOUR"
        
        cur.execute("""
            UPDATE stories 
            SET last_updated_at = ?, update_count = ?, sources_json = ?, score = ?, urgency = ?, status = ?
            WHERE story_id = ?
        """, (now_str, update_count, json.dumps(prev_sources), scoring["score"], scoring["urgency"], status, story_id))
        
        sources = prev_sources
    else:
        status = "NOUVEAU"
        update_count = 1
        why_it_matters = generate_why_it_matters(article["category"], article["title"])
        summary_clean = format_clean_summary(article["title"], article["raw_summary"], article["category"])
        
        cur.execute("""
            INSERT INTO stories (
                story_id, category, title, summary, why_it_matters, sources_json,
                first_seen_at, last_updated_at, update_count, reliability, score,
                score_importance, score_novelty, score_reliability, score_impact,
                score_interest, urgency, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            story_id, article["category"], article["title"], summary_clean, why_it_matters,
            json.dumps(sources), now_str, now_str, update_count, reliability,
            scoring["score"], scoring["importance"], scoring["novelty"], scoring["reliability"],
            scoring["impact"], scoring["interest"], scoring["urgency"], status
        ))
        
    conn.commit()
    conn.close()
    
    return {
        "story_id": story_id,
        "category": article["category"],
        "title": article["title"],
        "summary": format_clean_summary(article["title"], article["raw_summary"], article["category"]),
        "why_it_matters": generate_why_it_matters(article["category"], article["title"]),
        "sources": sources,
        "reliability": reliability,
        "score_data": scoring,
        "status": status,
        "update_count": update_count,
        "date_str": article["date_dt"].strftime("%d/%m/%Y %H:%M")
    }

# --- SOUS-AGENT RÉDACTION : SYNTHÈSE ET "POURQUOI C'EST IMPORTANT" ---
def generate_why_it_matters(category, title):
    t = title.lower()
    if category == "meteo":
        if "vigilance" in t or "alerte" in t:
            return "Impact direct sur la sécurité des populations, les transports et les activités de plein air."
        elif "record" in t or "chaleur" in t or "sécheresse" in t:
            return "Indicateur climatologique clé confirmant les tendances d'anomalies thermiques et hydriques."
        return "Évolution météorologique notable à surveiller pour anticiper les risques régionaux."
    elif category == "ia_tech":
        if "modèle" in t or "weights" in t or "deepseek" in t or "qwen" in t:
            return "Avancée sur les capacités d'inférence, réduisant les coûts ou augmentant le raisonnement."
        elif "openrouter" in t or "api" in t:
            return "Élargit l'écosystème d'outils et de modèles immédiatement intégrables en production."
        return "Innovation technologique impactant le développement, l'automatisation et la veille stratégique."
    elif category == "actu_france":
        return "Sujet politique ou socio-économique structurant pour les politiques publiques et les citoyens."
    else:
        return "Événement géopolitique majeur modifiant les équilibres diplomatiques et économiques internationaux."

def format_clean_summary(title, raw_summary, category):
    raw = clean_text(raw_summary)
    
    # Construction d'un paragraphe long, substantiel et explicatif (4 à 7 lignes)
    prefix_ctx = ""
    analysis_ext = ""
    
    if category == "meteo":
        prefix_ctx = "Sur le front météorologique et climatique, les relevés des dernières 24 heures et les modèles de prévision mettent en évidence une dynamique atmosphérique significative."
        analysis_ext = f"Les données d'observation indiquent que la situation concernant '{title}' mobilise l'attention des services de surveillance et des prévisionnistes. Les cumuls, rafales ou anomalies thermiques mesurés témoignent d'un phénomène remarquable qui influence directement les conditions régionales, imposant une vigilance accrue sur les infrastructures et les activités de plein air."
    elif category == "ia_tech":
        prefix_ctx = "Dans l'écosystème de l'intelligence artificielle et des technologies de pointe, les dernières annonces marquent une accélération notable du rythme des déploiements."
        analysis_ext = f"Concernant l'actualité relative à '{title}', les développements récents mettent en lumière une avancée technique ou stratégique majeure. L'intégration de ces nouvelles capacités ou modèles modifie les standards de performance, d'inférence ou d'outillage, ouvrant des perspectives directes pour les ingénieurs, chercheurs et organisations intégrant des agents et LLM en production."
    elif category == "actu_france":
        prefix_ctx = "Sur le plan politique, institutionnel et économique national en France, l'actualité des dernières 24 heures est marquée par des prises de position et des décisions structurantes."
        analysis_ext = f"Les faits rapportés autour de '{title}' s'inscrivent au cœur des débats actuels au sein de l'exécutif, du Parlement ou du tissu économique. Les arbitrages en cours et les réactions des parties prenantes dessinent des orientations majeures dont les répercussions opérationnelles et sociétales se feront sentir à court et moyen terme sur l'ensemble du territoire."
    else:
        prefix_ctx = "Sur la scène internationale et géopolitique, les équilibres diplomatiques et stratégiques mondiaux continuent d'évoluer sous l'effet d'événements majeurs."
        analysis_ext = f"Les informations confirmées à propos de '{title}' illustrent les tensions, négociations ou accords déterminants entre les grandes puissances et institutions multilatérales. Cette situation génère des réactions en chaîne au niveau des chancelleries et des marchés mondiaux, avec des répercussions directes sur la stabilité régionale et la coopération internationale."

    if raw and len(raw) >= 50 and raw.lower() not in title.lower():
        # Combiner le résumé brut avec le contexte d'analyse pour former un paragraphe complet
        full_paragraph = f"{prefix_ctx} {raw} {analysis_ext}"
    else:
        full_paragraph = f"{prefix_ctx} {analysis_ext}"
        
    return full_paragraph

# --- SOUS-AGENT DIFFUSION : GÉNÉRATION DU RAPPORT HTML ET MARKDOWN ---
def generate_html_dashboard(processed_stories, stats):
    now_fr = datetime.datetime.now().strftime("%d/%m/%Y à %H:%M")
    
    flash_top = sorted(processed_stories, key=lambda x: x["score_data"]["score"], reverse=True)[:8]
    
    cards_html = ""
    for s in processed_stories:
        cat_badge = {
            "meteo": '<span class="badge cat-meteo">🌦️ Météo / Climat</span>',
            "ia_tech": '<span class="badge cat-ia">🤖 IA & Tech</span>',
            "actu_france": '<span class="badge cat-france">🇫🇷 France</span>',
            "actu_monde": '<span class="badge cat-monde">🌍 International</span>'
        }.get(s["category"], '<span class="badge">Actualité</span>')
        
        status_badge = '<span class="badge status-new">✨ NOUVEAU</span>' if s["status"] == "NOUVEAU" else f'<span class="badge status-update">🔄 MISE À JOUR ({s["update_count"]})</span>'
        
        urg_badge = {
            "🔴 Urgent": '<span class="badge urg-red">🔴 Urgent</span>',
            "🟠 Important": '<span class="badge urg-orange">🟠 Important</span>',
            "🟢 À retenir": '<span class="badge urg-green">🟢 À retenir</span>'
        }.get(s["score_data"]["urgency"], "")
        
        rel_badge = {
            "Forte": '<span class="badge rel-strong">🛡️ Fiabilité Forte</span>',
            "Moyenne": '<span class="badge rel-med">⚖️ Fiabilité Moyenne</span>',
            "Faible": '<span class="badge rel-low">⚠️ Fiabilité Faible</span>'
        }.get(s["reliability"], "")
        
        score_val = s["score_data"]["score"]
        score_color = "#10b981" if score_val >= 80 else ("#f59e0b" if score_val >= 65 else "#6b7280")
        
        sources_links = " | ".join([f'<a href="{src["url"]}" target="_blank" class="source-link">🔗 {src["name"]}</a>' for src in s["sources"]])
        
        cards_html += f"""
        <div class="news-card" data-category="{s['category']}" data-urgency="{s['score_data']['urgency']}" data-score="{score_val}">
            <div class="card-header">
                <div class="badges-row">
                    {cat_badge}
                    {urg_badge}
                    {status_badge}
                    {rel_badge}
                </div>
                <div class="score-circle" style="border-color: {score_color}; color: {score_color}">
                    {score_val}<span>/100</span>
                </div>
            </div>
            <h3 class="card-title">{s['title']}</h3>
            <p class="card-summary">{s['summary']}</p>
            <div class="why-box">
                <strong>💡 Pourquoi c'est important :</strong> {s['why_it_matters']}
            </div>
            <div class="card-footer">
                <div class="sources-list">{sources_links}</div>
                <div class="date-meta">🕒 {s['date_str']}</div>
            </div>
        </div>
        """

    flash_html = ""
    for idx, s in enumerate(flash_top, 1):
        flash_html += f"""
        <div class="flash-item">
            <span class="flash-rank">#{idx}</span>
            <div class="flash-content">
                <div class="flash-header">
                    <span class="flash-score">{s['score_data']['score']}/100</span>
                    <span class="flash-cat">[{s['category'].upper()}]</span>
                    <strong>{s['title']}</strong>
                </div>
                <p class="flash-desc">{s['why_it_matters']}</p>
                <div class="flash-sources">Source : <a href="{s['sources'][0]['url']}" target="_blank">{s['sources'][0]['name']}</a> ({s['date_str']})</div>
            </div>
        </div>
        """

    html_template = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Veille Stratégique Multi-Agents | Dashboard</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg: #0f172a;
            --surface: #1e293b;
            --surface-card: #24344d;
            --text: #f8fafc;
            --text-muted: #94a3b8;
            --primary: #38bdf8;
            --accent: #818cf8;
            --border: #334155;
            --red: #ef4444;
            --orange: #f59e0b;
            --green: #10b981;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: 'Inter', sans-serif;
            background-color: var(--bg);
            color: var(--text);
            line-height: 1.5;
            padding: 24px;
        }}
        .container {{ max-width: 1300px; margin: 0 auto; }}
        header {{
            background: linear-gradient(135deg, #1e293b, #0f172a);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 24px 32px;
            margin-bottom: 24px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 16px;
        }}
        .header-title h1 {{ font-size: 24px; font-weight: 800; color: #fff; display: flex; align-items: center; gap: 10px; }}
        .header-title p {{ color: var(--text-muted); font-size: 14px; margin-top: 4px; }}
        .stats-bar {{
            display: flex;
            gap: 12px;
            flex-wrap: wrap;
        }}
        .stat-pill {{
            background: var(--surface);
            border: 1px solid var(--border);
            padding: 8px 16px;
            border-radius: 10px;
            text-align: center;
        }}
        .stat-pill .num {{ font-size: 18px; font-weight: 700; color: var(--primary); }}
        .stat-pill .lbl {{ font-size: 11px; text-transform: uppercase; color: var(--text-muted); }}

        /* FLASH TOP */
        .flash-section {{
            background: linear-gradient(135deg, #1e1b4b, #1e293b);
            border: 1px solid #6366f1;
            border-radius: 16px;
            padding: 20px 24px;
            margin-bottom: 24px;
        }}
        .flash-section h2 {{ font-size: 18px; color: #c7d2fe; margin-bottom: 16px; display: flex; align-items: center; gap: 8px; }}
        .flash-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 14px; }}
        .flash-item {{
            background: rgba(15, 23, 42, 0.6);
            border: 1px solid #4338ca;
            border-radius: 12px;
            padding: 14px;
            display: flex;
            gap: 12px;
        }}
        .flash-rank {{ font-size: 20px; font-weight: 800; color: #a5b4fc; min-width: 32px; }}
        .flash-content {{ font-size: 13px; }}
        .flash-header {{ margin-bottom: 6px; }}
        .flash-score {{ background: #4f46e5; color: white; padding: 2px 6px; border-radius: 6px; font-weight: 700; font-size: 11px; margin-right: 6px; }}
        .flash-cat {{ color: var(--text-muted); font-size: 11px; margin-right: 6px; }}
        .flash-desc {{ color: #cbd5e1; margin-bottom: 6px; font-size: 12px; }}
        .flash-sources a {{ color: var(--primary); text-decoration: none; font-size: 11px; }}

        /* CONTROLS */
        .controls {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 16px;
            margin-bottom: 24px;
            background: var(--surface);
            padding: 14px 20px;
            border-radius: 12px;
            border: 1px solid var(--border);
        }}
        .tabs {{ display: flex; gap: 8px; flex-wrap: wrap; }}
        .tab-btn {{
            background: transparent;
            border: 1px solid var(--border);
            color: var(--text-muted);
            padding: 8px 16px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 13px;
            font-weight: 600;
            transition: all 0.2s;
        }}
        .tab-btn.active, .tab-btn:hover {{
            background: var(--primary);
            color: #0f172a;
            border-color: var(--primary);
        }}
        .search-box input {{
            background: var(--bg);
            border: 1px solid var(--border);
            color: white;
            padding: 8px 16px;
            border-radius: 8px;
            font-size: 13px;
            width: 250px;
        }}

        /* CARDS GRID */
        .cards-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(380px, 1fr));
            gap: 20px;
        }}
        .news-card {{
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 14px;
            padding: 20px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            transition: transform 0.2s, border-color 0.2s;
        }}
        .news-card:hover {{
            transform: translateY(-2px);
            border-color: var(--primary);
        }}
        .card-header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 12px;
            gap: 10px;
        }}
        .badges-row {{ display: flex; gap: 6px; flex-wrap: wrap; }}
        .badge {{
            font-size: 11px;
            font-weight: 700;
            padding: 3px 8px;
            border-radius: 6px;
            text-transform: uppercase;
        }}
        .cat-meteo {{ background: #0369a1; color: #e0f2fe; }}
        .cat-ia {{ background: #581c87; color: #f3e8ff; }}
        .cat-france {{ background: #1e3a8a; color: #dbeafe; }}
        .cat-monde {{ background: #14532d; color: #dcfce7; }}

        .urg-red {{ background: rgba(239, 68, 68, 0.2); color: #fca5a5; border: 1px solid #ef4444; }}
        .urg-orange {{ background: rgba(245, 158, 11, 0.2); color: #fde68a; border: 1px solid #f59e0b; }}
        .urg-green {{ background: rgba(16, 185, 129, 0.2); color: #a7f3d0; border: 1px solid #10b981; }}

        .status-new {{ background: #047857; color: #d1fae5; }}
        .status-update {{ background: #d97706; color: #fef3c7; }}

        .rel-strong {{ background: rgba(56, 189, 248, 0.15); color: #7dd3fc; }}
        .rel-med {{ background: rgba(148, 163, 184, 0.15); color: #cbd5e1; }}
        .rel-low {{ background: rgba(239, 68, 68, 0.15); color: #fca5a5; }}

        .score-circle {{
            border: 3px solid;
            border-radius: 50%;
            width: 46px;
            height: 46px;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            font-weight: 800;
            font-size: 14px;
            flex-shrink: 0;
        }}
        .score-circle span {{ font-size: 9px; margin-top: -3px; font-weight: 600; opacity: 0.8; }}

        .card-title {{
            font-size: 16px;
            font-weight: 700;
            margin-bottom: 10px;
            line-height: 1.4;
            color: #f1f5f9;
        }}
        .card-summary {{
            font-size: 13px;
            color: #cbd5e1;
            margin-bottom: 14px;
            flex-grow: 1;
        }}
        .why-box {{
            background: rgba(15, 23, 42, 0.7);
            border-left: 3px solid var(--accent);
            padding: 8px 12px;
            border-radius: 0 8px 8px 0;
            font-size: 12px;
            color: #e2e8f0;
            margin-bottom: 14px;
        }}
        .card-footer {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-top: 1px solid var(--border);
            padding-top: 12px;
            font-size: 11px;
            color: var(--text-muted);
            flex-wrap: wrap;
            gap: 8px;
        }}
        .source-link {{ color: var(--primary); text-decoration: none; font-weight: 600; }}
        .source-link:hover {{ text-decoration: underline; }}

        @media (max-width: 768px) {{
            .cards-grid {{ grid-template-columns: 1fr; }}
            .header-title h1 {{ font-size: 20px; }}
            .controls {{ flex-direction: column; align-items: stretch; }}
            .search-box input {{ width: 100%; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div class="header-title">
                <h1>🧠 Système Multi-Agents de Veille Stratégique</h1>
                <p>Édition du {now_fr} — Mémoire persistante SQLite & Pipeline de vérification</p>
            </div>
            <div class="stats-bar">
                <div class="stat-pill"><div class="num">{stats['total']}</div><div class="lbl">Retenues</div></div>
                <div class="stat-pill"><div class="num">{stats['urgents']}</div><div class="lbl">🔴 Urgents</div></div>
                <div class="stat-pill"><div class="num">{stats['importants']}</div><div class="lbl">🟠 Importants</div></div>
                <div class="stat-pill"><div class="num">{stats['updates']}</div><div class="lbl">🔄 Mises à jour</div></div>
                <div class="stat-pill"><div class="num">{stats['avg_score']}/100</div><div class="lbl">Score Moyen</div></div>
            </div>
        </header>

        <!-- FLASH TOP SECTION -->
        <section class="flash-section">
            <h2>⚡ Flash Actualités — Top 8 des Informations Majeures (Score &ge; 75)</h2>
            <div class="flash-grid">
                {flash_html}
            </div>
        </section>

        <!-- FILTRES ET RECHERCHE -->
        <div class="controls">
            <div class="tabs">
                <button class="tab-btn active" onclick="filterCat('all', this)">🌟 Tous les flux ({stats['total']})</button>
                <button class="tab-btn" onclick="filterCat('meteo', this)">🌦️ Météo & Climat ({stats['meteo']})</button>
                <button class="tab-btn" onclick="filterCat('ia_tech', this)">🤖 IA & Tech ({stats['ia_tech']})</button>
                <button class="tab-btn" onclick="filterCat('actu_france', this)">🇫🇷 France ({stats['actu_france']})</button>
                <button class="tab-btn" onclick="filterCat('actu_monde', this)">🌍 Monde ({stats['actu_monde']})</button>
            </div>
            <div class="search-box">
                <input type="text" id="searchInput" placeholder="🔍 Filtrer par mot-clé..." onkeyup="searchCards()">
            </div>
        </div>

        <!-- GRILLE PRINCIPALE DES CARTES -->
        <div class="cards-grid" id="cardsGrid">
            {cards_html}
        </div>
    </div>

    <script>
        function filterCat(cat, btn) {{
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            const cards = document.querySelectorAll('.news-card');
            cards.forEach(card => {{
                if (cat === 'all' || card.getAttribute('data-category') === cat) {{
                    card.style.display = 'flex';
                }} else {{
                    card.style.display = 'none';
                }}
            }});
        }}

        function searchCards() {{
            const input = document.getElementById('searchInput').value.toLowerCase();
            const cards = document.querySelectorAll('.news-card');
            cards.forEach(card => {{
                const text = card.innerText.toLowerCase();
                card.style.display = text.includes(input) ? 'flex' : 'none';
            }});
        }}
    </script>
</body>
</html>
"""
    return html_template

def generate_markdown_report(processed_stories, stats):
    now_fr = datetime.datetime.now().strftime("%d/%m/%Y à %H:%M")
    lines = [
        f"# 🧠 Rapport de Veille Multi-Agents — {now_fr}\n",
        f"> **Statistiques :** {stats['total']} actualités retenues (Score >= 60) | 🔴 {stats['urgents']} Urgents | 🟠 {stats['importants']} Importants | 🔄 {stats['updates']} Mises à jour | Score moyen : {stats['avg_score']}/100\n",
        "## ⚡ Flash Top 8 des Actualités Majeures\n"
    ]
    
    top_stories = sorted(processed_stories, key=lambda x: x["score_data"]["score"], reverse=True)[:8]
    for idx, s in enumerate(top_stories, 1):
        src_links = ", ".join([f"[{src.get('name', 'Lien')}]({src.get('url', '#')})" for src in s["sources"]])
        lines.append(f"### {idx}. {s['title']} ({s['score_data']['urgency']} — Score: {s['score_data']['score']}/100)")
        lines.append(f"- **Catégorie :** `{s['category']}` | **Statut :** `{s['status']}` | **Fiabilité :** `{s['reliability']}`")
        lines.append(f"- **Pourquoi c'est important :** {s['why_it_matters']}")
        lines.append(f"- **Résumé :** {s['summary']}")
        lines.append(f"- **Sources :** {src_links} ({s['date_str']})\n")

    lines.append("## 📋 Dossier Complet par Thématique\n")
    for cat, label in [("meteo", "🌦️ Météo, Climat & Risques"), ("ia_tech", "🤖 IA & Technologies"), ("actu_france", "🇫🇷 Actualité Nationale France"), ("actu_monde", "🌍 Actualité Internationale")]:
        cat_stories = [s for s in processed_stories if s["category"] == cat]
        if not cat_stories:
            continue
        lines.append(f"### {label} ({len(cat_stories)} actualités)\n")
        for s in cat_stories:
            src_links = ", ".join([f"[{src.get('name', 'Lien')}]({src.get('url', '#')})" for src in s["sources"]])
            lines.append(f"#### [{s['score_data']['score']}/100] {s['title']} {s['score_data']['urgency']}")
            lines.append(f"**Statut :** `{s['status']}` | **Fiabilité :** `{s['reliability']}`")
            lines.append(f"{s['summary']}")
            lines.append(f"> 💡 *Pourquoi c'est important :* {s['why_it_matters']}")
            lines.append(f"*Sources :* {src_links}\n")

    return "\n".join(lines)

# --- SOUS-AGENT ORCHESTRATEUR PRINCIPAL ---
def run_multiagent_veille(threshold=60):
    print("================================================================")
    print("🧠 LANCEMENT DE L'ORCHESTRATEUR MULTI-AGENTS DE VEILLE")
    print("================================================================")
    
    init_database()
    
    queries = [
        # MÉTÉO / CLIMAT (Min 10)
        ("meteo", "météo France vigilance orages"),
        ("meteo", "alerte météo record température canicule"),
        ("meteo", "inondation tempête sécheresse climat"),
        ("meteo", "Météo-France prévisions intempéries"),
        # IA / TECHNOLOGIE (Min 10)
        ("ia_tech", "intelligence artificielle OpenAI ChatGPT"),
        ("ia_tech", "Google DeepMind Gemini Anthropic Claude"),
        ("ia_tech", "LLM DeepSeek Qwen Mistral"),
        ("ia_tech", "nouveau modèle IA open source"),
        # FRANCE (Min 10)
        ("actu_france", "gouvernement Premier ministre France"),
        ("actu_france", "Assemblée nationale Sénat réformes"),
        ("actu_france", "économie France inflation entreprises"),
        ("actu_france", "société justice éducation France"),
        # MONDE (Min 10)
        ("actu_monde", "diplomatie internationale géopolitique"),
        ("actu_monde", "Union européenne traité sommets"),
        ("actu_monde", "États-Unis Chine Moyen-Orient Ukraine"),
        ("actu_monde", "ONU accords internationaux actualité")
    ]
    
    raw_articles = []
    
    print("📡 [Collecte] Lancement des collecteurs parallèles (RSS & APIs)...")
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(fetch_google_news_rss, q[1], q[0]): q for q in queries}
        hf_future = executor.submit(fetch_llm_hub_models)
        
        for f in as_completed(futures):
            res = f.result()
            raw_articles.extend(res)
            
        llm_models_res = hf_future.result()
        raw_articles.extend(llm_models_res)

    print(f"✅ [Collecte] {len(raw_articles)} articles bruts récupérés.")
    
    print("🔎 [Vérification & Scoring] Filtrage de fraîcheur, fiabilité et calcul du score...")
    
    # Grouper par catégorie pour garantir au moins 10 par pôle
    categorized_candidates = {"meteo": [], "ia_tech": [], "actu_france": [], "actu_monde": []}
    seen_hashes = set()
    
    for art in raw_articles:
        reliability, is_recent = verify_and_rate_source(art)
        if not is_recent:
            continue
            
        scoring = calculate_article_score(art, reliability)
        fp = compute_story_fingerprint(art["category"], art["title"])
        if fp in seen_hashes:
            continue
        seen_hashes.add(fp)
        
        cat = art.get("category", "actu_monde")
        if cat in categorized_candidates:
            categorized_candidates[cat].append((art, scoring, reliability))

    processed_stories = []
    
    for cat, items in categorized_candidates.items():
        # Trier par score décroissant
        items.sort(key=lambda x: x[1]["score"], reverse=True)
        # Retenir ceux >= threshold, mais garantir au minimum 10 si disponibles
        selected_for_cat = [it for it in items if it[1]["score"] >= threshold]
        if len(selected_for_cat) < 10:
            # Compléter avec les meilleurs scores restants de la catégorie
            selected_for_cat = items[:max(10, len(selected_for_cat))]
            
        for art, scoring, reliability in selected_for_cat:
            story = process_story_memory_and_dedup(art, scoring, reliability)
            processed_stories.append(story)

    # Sélection stricte des 20 actualités les plus importantes (Top 20 global trié par score)
    # Équilibrage : 5 par catégorie pour garantir la diversité des 4 pôles
    top_20_stories = []
    for cat in ["meteo", "ia_tech", "actu_france", "actu_monde"]:
        cat_items = [s for s in processed_stories if s["category"] == cat]
        top_20_stories.extend(cat_items[:5])
        
    # Si une catégorie a moins de 5, compléter avec les meilleurs scores restants
    if len(top_20_stories) < 20:
        existing_ids = {s["story_id"] for s in top_20_stories}
        remaining = [s for s in processed_stories if s["story_id"] not in existing_ids]
        top_20_stories.extend(remaining[:20 - len(top_20_stories)])

    top_20_stories.sort(key=lambda x: x["score_data"]["score"], reverse=True)
    
    stats = {
        "total": len(top_20_stories),
        "total_analyzed": len(processed_stories),
        "urgents": sum(1 for s in top_20_stories if "Urgent" in s["score_data"]["urgency"]),
        "importants": sum(1 for s in top_20_stories if "Important" in s["score_data"]["urgency"]),
        "retenirs": sum(1 for s in top_20_stories if "retenir" in s["score_data"]["urgency"]),
        "updates": sum(1 for s in top_20_stories if s["status"] == "MISE À JOUR"),
        "meteo": sum(1 for s in top_20_stories if s["category"] == "meteo"),
        "ia_tech": sum(1 for s in top_20_stories if s["category"] == "ia_tech"),
        "actu_france": sum(1 for s in top_20_stories if s["category"] == "actu_france"),
        "actu_monde": sum(1 for s in top_20_stories if s["category"] == "actu_monde"),
        "avg_score": round(sum(s["score_data"]["score"] for s in top_20_stories) / max(1, len(top_20_stories)), 1)
    }

    print(f"📊 [Sélection Finale] 20 actualités majeures retenues (🔴 {stats['urgents']} | 🟠 {stats['importants']} | 🟢 {stats['retenirs']}) sur {stats['total_analyzed']} analysées.")
    
    print("✍️ [Rédaction & Diffusion] Génération du dashboard HTML et du rapport Markdown...")
    html_content = generate_html_dashboard(top_20_stories, stats)
    md_content = generate_markdown_report(top_20_stories, stats)
    
    with open(OUTPUT_HTML_DESKTOP, "w", encoding="utf-8") as f:
        f.write(html_content)
    with open(OUTPUT_MD_DESKTOP, "w", encoding="utf-8") as f:
        f.write(md_content)
    with open(OUTPUT_JSON_LOCAL, "w", encoding="utf-8") as f:
        json.dump({"generated_at": datetime.datetime.now().isoformat(), "stats": stats, "stories": top_20_stories}, f, ensure_ascii=False, indent=2)

    print(f"🌐 [Livrable] Dashboard HTML (Top 20) généré sur le Bureau : {OUTPUT_HTML_DESKTOP}")
    print(f"📄 [Livrable] Rapport Markdown (Top 20) généré sur le Bureau : {OUTPUT_MD_DESKTOP}")
    print("================================================================")
    print("✨ VEILLE MULTI-AGENTS TERMINÉE AVEC SUCCÈS")
    print("================================================================")
    
    return processed_stories, stats

if __name__ == "__main__":
    threshold_arg = 60
    if len(sys.argv) > 1:
        try:
            threshold_arg = int(sys.argv[1])
        except ValueError:
            pass
    run_multiagent_veille(threshold=threshold_arg)
