# -*- coding: utf-8 -*-
"""
fetch_tweets.py
Fetches recent tweets from the user's Twitter/X abonnements list using the free, no-cookie,
no-credentials syndication API. Runs concurrently to fetch 100+ accounts in seconds.
Saves the structured 9-item list to data/latest_tweets.json for capture_debrief.py.
"""
import argparse
import json
import os
import sys
import re
import urllib.request
import unicodedata
from datetime import datetime, timezone, timedelta
import concurrent.futures

ACCOUNTS = [
    "laradiometeo", "AEMET_Esp", "AEMET_Aragon", "Aigle_e", "stormchaser_a81", "AlexyMeteo",
    "AnthoGrillon", "Arameteo_france", "globerourdiales", "ChroChao", "Cycloneoi", "DorianDziadula",
    "TropicalTidbits", "SergeZaka", "ElTiempoes", "Estofex", "EtienneFargetMC", "EvelyneDheliat",
    "extremetemps", "FayenceMeteo", "FeuxdeForet_FR", "Florent_Boutet", "FloC36", "ForceThirteen",
    "l_garcelon", "GregCornard", "GJauseau", "Meteovilles", "GWoznica", "Guitri13", "hurrtrackerapp",
    "GlobalCyclones", "ROrage09", "infoccitanie", "InfoMeteoTuit", "Infosyclone_44", "peacockreports",
    "Alpenweerman", "JulienSugier", "KeraunosObs", "StormChaser220", "Kevin_Fillin", "Firinga_le_site",
    "lachainemeteo", "meteo_reunion", "LyonMeteo69", "Marc_Hay_Meteo", "MatthieuSorel", "MaxenceLeDrogo1",
    "metofficestorms", "tiempo_guada", "meteo60", "meteociel", "meteophile", "MeteoredFR", "Meteouragans",
    "T2mike", "MeteoMonsieur", "Vincent_06v", "37Meteo", "MeteoBretagne", "meteoconcept", "MeteoExpress",
    "MeteoNord", "MeteoHerault", "MeteoLanguedoc", "MeteoNordParis", "msa6768", "Meteoinfo_FR", "meteofrance",
    "MeteoFrance_AG", "meteo_76", "MeteoCarnoux", "meteosuisse", "meteovillages", "nicolasberrod",
    "NicolasLeFriant", "Ninofishing", "meteo_tropicale", "ouragans", "Pat_wx", "La_Meteo_du_13",
    "philklotzbach", "SkyPhilippe", "previneige", "Prefet971", "Prefet972", "Prefet974", "romumartinik",
    "smlmrn", "Thom_Wx", "Stormyalert", "StevenTual_off", "sxmcyclone", "ThomasBlanchar2", "lePlaymobil28",
    "TimeoLepert", "Djpuco", "Navarrameteo", "AutanTramontane", "VigiMeteoFrance", "StormchaserUKEU",
    "wxcharts", "Zactus_re"
]

def get_output_file():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(script_dir, "data")
    os.makedirs(data_dir, exist_ok=True)
    return os.path.join(data_dir, "latest_tweets.json")

def parse_args():
    parser = argparse.ArgumentParser(description="Fetch and filter recent tweets from Twitter accounts.")
    parser.add_argument("--hours", type=float, default=2.0, help="Filter tweets from the last N hours (default: 2.0)")
    parser.add_argument("--limit", type=int, default=100)
    return parser.parse_args()

def clean_accents(s):
    nfkd = unicodedata.normalize('NFKD', s)
    return "".join([c for c in nfkd if not unicodedata.combining(c)]).lower()

def is_alert_tweet(text):
    if not text: return False
    triggers = ["vigilance rouge", "vigilance orange", "alerte rouge", "alerte orange",
                "incendie", "tornade", "record absolu", "record mensuel", "tempete",
                "inondation", "canicule", "orage", "grele", "foudre", "inondations", "seisme", "alerte"]
    ct = clean_accents(text)
    return any(t in ct for t in triggers)

def is_model_trend_tweet(text):
    if not text: return False
    triggers = ["arome", "arpege", "ifs", "ecmwf", "gfs", "icon", "ukmo", "gem", "aifs",
                "modele", "tendance", "anomalie", "projection", "moyen terme", "long terme",
                "saisonniere", "saisonnier", "graphe", "run", "simulation"]
    ct = clean_accents(text)
    return any(t in ct for t in triggers)

def fetch_single_account(username):
    url = f"https://syndication.twitter.com/srv/timeline-profile/screen-name/{username}"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
    tweets = []
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read().decode('utf-8')
            m = re.search(r'__NEXT_DATA__.*?>(.*?)<\/script>', html)
            if not m:
                return []
            data = json.loads(m.group(1))
            entries = data.get('props', {}).get('pageProps', {}).get('timeline', {}).get('entries', [])
            for entry in entries:
                if entry.get('type') == 'tweet':
                    t = entry.get('content', {}).get('tweet', {})
                    if t:
                        tweets.append(t)
    except Exception as e:
        # Ignore errors for single accounts to avoid halting the pipeline
        pass
    return tweets

def process_raw_tweet(t, now):
    try:
        created_at_str = t.get('created_at', '')
        tweet_time = datetime.strptime(created_at_str, "%a %b %d %H:%M:%S %z %Y")
        age = now - tweet_time
        
        likes = int(t.get("favorite_count", 0) or 0)
        retweets = int(t.get("retweet_count", 0) or 0)
        replies = int(t.get("reply_count", 0) or 0)
        engagement = likes + retweets * 3 + replies * 2
        
        text = t.get("full_text", "")
        is_alert = is_alert_tweet(text)
        is_model = is_model_trend_tweet(text)
        if is_alert: engagement += 100
        if is_model: engagement += 100
        
        media_urls = []
        entities = t.get("entities", {})
        if "media" in entities:
            for m_item in entities["media"]:
                if m_item.get("type") == "photo":
                    m_url = m_item.get("media_url_https")
                    if m_url:
                        media_urls.append(m_url)
                        
        user_info = t.get("user", {})
        username = user_info.get("screen_name", "unknown")
        
        return {
            "id": str(t.get("id_str", t.get("id", ""))),
            "text": text,
            "created_at": created_at_str,
            "tweet_time": tweet_time,
            "username": username,
            "name": user_info.get("name", username),
            "likes": likes,
            "retweets": retweets,
            "replies": replies,
            "engagement_score": engagement,
            "is_alert": is_alert,
            "is_model_trend": is_model,
            "media_urls": media_urls,
            "url": f"https://x.com/{username}/status/{t.get('id_str', t.get('id', ''))}",
            "age_hours": round(age.total_seconds() / 3600, 2)
        }
    except Exception:
        return None

def filter_and_classify(processed_tweets, hours_limit):
    now = datetime.now(timezone.utc)
    threshold = timedelta(hours=hours_limit)
    
    seen_ids = set()
    filtered = []
    for t in processed_tweets:
        if t["id"] in seen_ids:
            continue
        age = now - t["tweet_time"]
        if age <= threshold:
            t["age_hours"] = round(age.total_seconds() / 3600, 2)
            seen_ids.add(t["id"])
            filtered.append(t)
            
    # Classify
    alerts = [t for t in filtered if t["is_alert"]]
    models = [t for t in filtered if t["is_model_trend"]]
    general = [t for t in filtered if not t["is_alert"] and not t["is_model_trend"]]
    
    # Sort by engagement
    alerts.sort(key=lambda x: -x["engagement_score"])
    models.sort(key=lambda x: -x["engagement_score"])
    general.sort(key=lambda x: -x["engagement_score"])
    
    return alerts, models, general

def main():
    args = parse_args()
    output_file = get_output_file()
    
    print(f"Fetching tweets from {len(ACCOUNTS)} accounts...")
    
    raw_tweets = []
    # Concurrency to fetch all accounts in parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
        results = executor.map(fetch_single_account, ACCOUNTS)
        for res in results:
            raw_tweets.extend(res)
            
    print(f"Fetched {len(raw_tweets)} raw tweets. Processing...")
    
    now = datetime.now(timezone.utc)
    processed = []
    for r in raw_tweets:
        pt = process_raw_tweet(r, now)
        if pt:
            processed.append(pt)
            
    # Try different time windows to populate the 3x3 grid
    alerts, models, general = [], [], []
    chosen_hours = args.hours
    for h in [args.hours, 6.0, 12.0, 24.0, 48.0]:
        chosen_hours = h
        alerts, models, general = filter_and_classify(processed, h)
        # We need at least some tweets in each category or a decent total
        if len(alerts) >= 3 and len(models) >= 3 and len(general) >= 3:
            break
            
    print(f"Filtered window: {chosen_hours}h. Found {len(alerts)} alerts, {len(models)} models, {len(general)} general.")
    
    # Fill categories up to 3 using other categories or placeholders
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
            alerts.append({
                "id": "mock_alert",
                "text": "Pas d'alerte météo signalée récemment dans le réseau.",
                "created_at": "",
                "username": "Infos",
                "name": "Monsieur Météo",
                "likes": 0, "retweets": 0, "replies": 0,
                "engagement_score": 0, "is_alert": True, "is_model_trend": False,
                "media_urls": [], "url": "", "age_hours": 0
            })
            
    while len(models) < 3:
        if general:
            item = general.pop(0)
            item["is_model_trend"] = True
            models.append(item)
        elif alerts:
            if len(alerts) > 3:
                item = alerts.pop(3)
                item["is_model_trend"] = True
                models.append(item)
            else:
                models.append({
                    "id": "mock_model",
                    "text": "Pas de nouvelles projections de modèles météo récentes.",
                    "created_at": "",
                    "username": "Infos",
                    "name": "Monsieur Météo",
                    "likes": 0, "retweets": 0, "replies": 0,
                    "engagement_score": 0, "is_alert": False, "is_model_trend": True,
                    "media_urls": [], "url": "", "age_hours": 0
                })
        else:
            models.append({
                "id": "mock_model",
                "text": "Pas de nouvelles projections de modèles météo récentes.",
                "created_at": "",
                "username": "Infos",
                "name": "Monsieur Météo",
                "likes": 0, "retweets": 0, "replies": 0,
                "engagement_score": 0, "is_alert": False, "is_model_trend": True,
                "media_urls": [], "url": "", "age_hours": 0
            })
            
    while len(general) < 3:
        general.append({
            "id": "mock_general",
            "text": "Pas d'actualité générale signalée.",
            "created_at": "",
            "username": "Infos",
            "name": "Monsieur Météo",
            "likes": 0, "retweets": 0, "replies": 0,
            "engagement_score": 0, "is_alert": False, "is_model_trend": False,
            "media_urls": [], "url": "", "age_hours": 0
        })
        
    # Interleave to match capture_debrief.py format
    final_list = [
        alerts[0], general[0], models[0],
        alerts[1], general[1], models[1],
        alerts[2], general[2], models[2]
    ]
    
    # Save JSON
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(final_list, f, ensure_ascii=False, indent=2)
        
    # Generate text report summarizing the highlights in data/debrief_tweet.txt
    tweet_text_file = os.path.join(os.path.dirname(output_file), "debrief_tweet.txt")
    
    # Select the top 1 alert, top 1 general, and top 1 model
    a_txt = alerts[0]["text"] if alerts[0] else ""
    g_txt = general[0]["text"] if general[0] else ""
    m_txt = models[0]["text"] if models[0] else ""
    
    report_text = (
        f"🌤️ DEBRIEFING ACTUS MÉTÉO (Dernières {chosen_hours}h)\n\n"
        f"🚨 ALERTE : {a_txt[:100]}...\n\n"
        f"🌤️ GÉNÉRAL : {g_txt[:100]}...\n\n"
        f"📡 MODÈLES : {m_txt[:100]}...\n\n"
        f"Retrouvez l'infographie complète ci-dessous."
    )
    
    with open(tweet_text_file, "w", encoding="utf-8") as f:
        f.write(report_text)
        
    print(f"Successfully saved 9 tweets to {output_file} and debrief text to {tweet_text_file}")

if __name__ == "__main__":
    main()
