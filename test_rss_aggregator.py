# -*- coding: utf-8 -*-
import urllib.request
import xml.etree.ElementTree as ET
import email.utils
import datetime
import json

def fetch_rss(url):
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    req = urllib.request.Request(url, headers={"User-Agent": user_agent})
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return response.read()
    except Exception as e:
        print(f"Error fetching RSS {url}: {e}")
        return None

def parse_rss(xml_data, source_name):
    if not xml_data:
        return []
    try:
        root = ET.fromstring(xml_data)
        articles = []
        # Support RSS 2.0 (channel/item) and Atom (entry)
        for item in root.findall(".//item"):
            title = item.find("title").text if item.find("title") is not None else ""
            link = item.find("link").text if item.find("link") is not None else ""
            pub_date = item.find("pubDate").text if item.find("pubDate") is not None else ""
            desc = item.find("description").text if item.find("description") is not None else ""
            articles.append({
                "title": title,
                "url": link,
                "date": pub_date,
                "desc": desc,
                "source": source_name
            })
        return articles
    except Exception as e:
        print(f"Error parsing RSS {source_name}: {e}")
        return []

def filter_and_categorize():
    feeds = {
        "Le Monde": "https://www.lemonde.fr/rss/une.xml",
        "FranceInfo": "https://www.francetvinfo.fr/titres.rss",
        "PresseCitron": "https://www.presse-citron.net/feed/",
        "Clubic": "https://www.clubic.com/feed/news.xml"
    }
    
    all_articles = []
    for name, url in feeds.items():
        xml = fetch_rss(url)
        all_articles.extend(parse_rss(xml, name))
        
    print(f"Total parsed: {len(all_articles)} articles.")
    
    # Filter by date (< 24h)
    now = datetime.datetime.now(datetime.timezone.utc)
    recent = []
    for art in all_articles:
        pub_str = art.get("date")
        if not pub_str:
            continue
        try:
            pub_dt = email.utils.parsedate_to_datetime(pub_str)
            if pub_dt.tzinfo is None:
                pub_dt = pub_dt.replace(tzinfo=datetime.timezone.utc)
            else:
                pub_dt = pub_dt.astimezone(datetime.timezone.utc)
            
            age = now - pub_dt
            if age <= datetime.timedelta(hours=24):
                art["age_hours"] = int(age.total_seconds() / 3600)
                recent.append(art)
        except Exception as e:
            pass
            
    print(f"Recent (< 24h): {len(recent)} articles.")
    
    # Categorization
    categories = {
        "actu_mondial": [],
        "actu_international": [],
        "actu_france": [],
        "actu_hdf": [],
        "ia": [],
        "meteo": []
    }
    
    hdf_keywords = ["nord", "pas-de-calais", "picardie", "lille", "hdf", "amiens", "arras", "dunkerque", "douai"]
    meteo_keywords = ["météo", "meteo", "climat", "température", "chaleur", "pluie", "inondation", "vent", "tempête", "orage", "vigilance", "sécheresse", "copernicus", "noaa"]
    ia_keywords = ["ia", "ai ", "chatgpt", "openai", "claude", "gemini", "llama", "deepseek", "anthropic", "copilot", "midjourney", "sora", "machine learning"]
    
    for art in recent:
        title_lower = art["title"].lower()
        desc_lower = art.get("desc", "").lower() if art.get("desc") else ""
        content = title_lower + " " + desc_lower
        
        # IA check
        if any(kw in content for kw in ia_keywords):
            categories["ia"].append(art)
        # Meteo check
        elif any(kw in content for kw in meteo_keywords):
            categories["meteo"].append(art)
        # HDF check
        elif any(kw in content for kw in hdf_keywords):
            categories["actu_hdf"].append(art)
        # General check
        else:
            # Simple heuristic
            if "monde" in content or "international" in content or "guerre" in content or "usa" in content or "chine" in content:
                categories["actu_international"].append(art)
            elif "france" in content or "macron" in content or "gouvernement" in content:
                categories["actu_france"].append(art)
            else:
                categories["actu_mondial"].append(art)
                
    for cat, list_art in categories.items():
        print(f"Category {cat}: {len(list_art)} articles.")
        for a in list_art[:2]:
            print(f"  - [{a['source']}] {a['title']} ({a['age_hours']}h ago) - {a['url']}")
            
filter_and_categorize()
