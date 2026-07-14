# -*- coding: utf-8 -*-
import urllib.request
import xml.etree.ElementTree as ET
import email.utils
import datetime
import json
import re

def filter_recent_articles(articles, max_hours=24):
    recent = []
    now = datetime.datetime.now(datetime.timezone.utc)
    for art in articles:
        pub_str = art.get("date")
        if not pub_str:
            recent.append(art)
            continue
        try:
            pub_dt = email.utils.parsedate_to_datetime(pub_str)
            if pub_dt.tzinfo is None:
                pub_dt = pub_dt.replace(tzinfo=datetime.timezone.utc)
            else:
                pub_dt = pub_dt.astimezone(datetime.timezone.utc)
            
            age = now - pub_dt
            art["age_seconds"] = age.total_seconds()
            art["age_hours"] = int(age.total_seconds() / 3600)
            if age <= datetime.timedelta(hours=max_hours):
                recent.append(art)
        except Exception:
            recent.append(art)
    return recent

def fetch_google_news(query):
    feeds = {
        "Le Monde": "https://www.lemonde.fr/rss/une.xml",
        "FranceInfo": "https://www.francetvinfo.fr/titres.rss",
        "France 3 HDF": "https://france3-regions.francetvinfo.fr/hauts-de-france/rss",
        "PresseCitron": "https://www.presse-citron.net/feed/"
    }
    
    all_articles = []
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    for name, url in feeds.items():
        try:
            req = urllib.request.Request(url, headers={"User-Agent": user_agent})
            with urllib.request.urlopen(req, timeout=10) as response:
                xml_data = response.read()
            
            root = ET.fromstring(xml_data)
            for item in root.findall(".//item"):
                title = item.find("title").text if item.find("title") is not None else ""
                link = item.find("link").text if item.find("link") is not None else ""
                pub_date = item.find("pubDate").text if item.find("pubDate") is not None else ""
                all_articles.append({
                    "title": title,
                    "url": link,
                    "date": pub_date,
                    "source": name
                })
        except Exception as e:
            print(f"[RSS] Échec du flux {name} : {e}")
            
    recent_articles = filter_recent_articles(all_articles, 24)
    if len(recent_articles) < 15:
        recent_articles = filter_recent_articles(all_articles, 48)
    if len(recent_articles) < 15:
        recent_articles = all_articles

    recent_articles = sorted(recent_articles, key=lambda x: x.get("age_seconds", 999999))

    query_lower = query.lower()
    is_meteo = any(w in query_lower for w in ["météo", "meteo", "climat", "vigilance", "records", "intempéries", "canicule"])
    is_ia = any(re.search(r'\b' + w + r'\b', query_lower) for w in ["ai", "ia"]) or any(w in query_lower for w in ["models", "tools", "claude", "gemini", "llama", "deepseek", "chatgpt", "openai"])
    is_hdf = any(w in query_lower for w in ["hauts-de-france", "hdf", "lille", "pas-de-calais", "nord"])
    
    filtered = []
    
    if is_meteo:
        meteo_keywords = ["météo", "meteo", "climat", "température", "chaleur", "pluie", "inondation", "vent", "tempête", "orage", "vigilance", "sécheresse", "neige", "copernicus", "records", "noaa", "canicule"]
        for art in recent_articles:
            title_lower = art["title"].lower()
            if any(kw in title_lower for kw in meteo_keywords):
                filtered.append(art)
    elif is_ia:
        ia_keywords = ["ia", "ai", "chatgpt", "openai", "claude", "gemini", "llama", "deepseek", "anthropic", "copilot", "midjourney", "sora", "robot", "algorithme", "machine learning", "technologie"]
        for art in recent_articles:
            title_lower = art["title"].lower()
            has_ia = False
            for kw in ia_keywords:
                if kw in ["ia", "ai"]:
                    if re.search(r'\b' + kw + r'\b', title_lower):
                        has_ia = True
                        break
                else:
                    if kw in title_lower:
                        has_ia = True
                        break
            if has_ia:
                filtered.append(art)
    elif is_hdf:
        hdf_keywords = ["nord", "pas-de-calais", "picardie", "lille", "hdf", "amiens", "arras", "dunkerque", "douai", "calais", "somme", "aisne", "oise"]
        for art in recent_articles:
            if art["source"] == "France 3 HDF":
                filtered.append(art)
            else:
                title_lower = art["title"].lower()
                if any(kw in title_lower for kw in hdf_keywords):
                    filtered.append(art)
    else:
        # General news (mondial, international, france)
        for art in recent_articles:
            if art["source"] in ["Le Monde", "FranceInfo"]:
                filtered.append(art)
                
    # Fallback to ensure we have enough items
    if len(filtered) < 15:
        seen_urls = {art["url"] for art in filtered}
        for art in recent_articles:
            if len(filtered) >= 20:
                break
            if art["url"] not in seen_urls:
                if is_ia and art["source"] != "PresseCitron":
                    continue
                filtered.append(art)
                seen_urls.add(art["url"])
                
    return filtered[:25]

# Run searches
queries = [
    "mondial",
    "ia",
    "meteo",
    "hdf"
]

for q in queries:
    res = fetch_google_news(q)
    print(f"Results for '{q}': {len(res)} items")
    for item in res[:3]:
        print(f"  - [{item['source']}] {item['title']} ({item.get('age_hours')}h ago) -> {item['url']}")
    print("-" * 60)
