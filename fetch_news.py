# -*- coding: utf-8 -*-
"""
fetch_news.py
Fetches recent weather news from Google News RSS feed,
categorizes them into Alerts, General, and Models/Trends,
and formats them for capture_debrief.py.
"""
import os
import sys
import json
import requests
import xml.etree.ElementTree as ET
import unicodedata
from datetime import datetime, timezone

def clean_accents(s):
    nfkd = unicodedata.normalize('NFKD', s)
    return "".join([c for c in nfkd if not unicodedata.combining(c)]).lower()

def is_alert_text(text):
    triggers = ["vigilance", "alerte", "canicule", "orage", "tempete", "inondation", 
                "grele", "foudre", "record", "chaleur", "extreme", "secours", "sinistre"]
    ct = clean_accents(text)
    return any(t in ct for t in triggers)

def is_model_text(text):
    triggers = ["modele", "tendance", "prevision", "carte", "cartographie", "evolution",
                "semaine", "arome", "arpege", "ifs", "gfs", "copernicus", "anomalie"]
    ct = clean_accents(text)
    return any(t in ct for t in triggers)

def fetch_rss_news(query):
    url = f"https://news.google.com/rss/search?q={requests.utils.quote(query)}&hl=fr&gl=FR&ceid=FR:fr"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    try:
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code != 200:
            print(f"Error fetching RSS: HTTP {r.status_code}", file=sys.stderr)
            return []
        
        root = ET.fromstring(r.content)
        items = []
        for item in root.findall('.//item'):
            title = item.find('title').text if item.find('title') is not None else ""
            link = item.find('link').text if item.find('link') is not None else ""
            pub_date = item.find('pubDate').text if item.find('pubDate') is not None else ""
            source = "Google News"
            
            # Clean source name from title (Google News appends " - Source Name" at the end)
            source_el = item.find('source')
            if source_el is not None and source_el.text:
                source = source_el.text.strip()
                suffix = f" - {source}"
                if title.endswith(suffix):
                    title = title[:-len(suffix)].strip()
            
            items.append({
                "title": title,
                "link": link,
                "pub_date": pub_date,
                "source": source
            })
        return items
    except Exception as e:
        print(f"Error parsing RSS: {e}", file=sys.stderr)
        return []

def main():
    print("Fetching weather news from Google News RSS...")
    
    # Fetch general weather and alert weather
    news_items = fetch_rss_news("meteo france OR orages OR canicule")
    
    # Filter duplicates and classify
    seen_titles = set()
    alerts = []
    models = []
    general = []
    
    for item in news_items:
        title = item["title"]
        title_clean = clean_accents(title)
        if title_clean in seen_titles:
            continue
        seen_titles.add(title_clean)
        
        # Build structured object matching capture_debrief.py format
        news_obj = {
            "id": str(hash(title)),
            "text": title,
            "created_at": item["pub_date"],
            "username": item["source"],
            "name": item["source"],
            "likes": 45,      # Mock metrics for visual styling
            "retweets": 15,
            "replies": 4,
            "engagement_score": 100,
            "is_alert": False,
            "is_model_trend": False,
            "media_urls": [],
            "url": item["link"]
        }
        
        if is_alert_text(title):
            news_obj["is_alert"] = True
            news_obj["engagement_score"] += 150
            alerts.append(news_obj)
        elif is_model_text(title):
            news_obj["is_model_trend"] = True
            news_obj["engagement_score"] += 120
            models.append(news_obj)
        else:
            general.append(news_obj)

    print(f"Classified: {len(alerts)} alerts, {len(models)} models/trends, {len(general)} general news.")

    # We need exactly 3 items per category to fit the 3 columns (Col 1: Alerts, Col 2: General, Col 3: Models)
    # Fill up if any category is lacking
    while len(alerts) < 3:
        if general:
            item = general.pop(0)
            item["is_alert"] = True
            alerts.append(item)
        elif models:
            item = models.pop(0)
            item["is_alert"] = True
            alerts.append(item)
        else:
            alerts.append(None)
            
    while len(models) < 3:
        if general:
            item = general.pop(0)
            item["is_model_trend"] = True
            models.append(item)
        elif alerts:
            # Avoid taking from the first 3 alerts
            if len(alerts) > 3:
                item = alerts.pop(3)
                item["is_model_trend"] = True
                models.append(item)
            else:
                models.append(None)
        else:
            models.append(None)
            
    while len(general) < 3:
        general.append(None)

    # Merge into the specific order expected by capture_debrief's column layout:
    # Index 0, 3, 6 -> Column 1 (Alerts)
    # Index 1, 4, 7 -> Column 2 (General Météo)
    # Index 2, 5, 8 -> Column 3 (Models/Trends)
    final_list = [
        alerts[0], general[0], models[0],
        alerts[1], general[1], models[1],
        alerts[2], general[2], models[2]
    ]

    # Save to data/latest_tweets.json
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "latest_tweets.json")
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(final_list, f, ensure_ascii=False, indent=2)

    print(f"Successfully saved 9 structured news items to {output_file}")

if __name__ == "__main__":
    main()
