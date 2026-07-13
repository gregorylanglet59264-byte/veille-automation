# -*- coding: utf-8 -*-
"""
fetch_tweets.py
Scans the specified Twitter/X list timeline using opencli, filters tweets
posted within the last N hours, and flags high-priority alerts and weather models/trends.
"""
import argparse
import json
import os
import subprocess
import sys
import unicodedata
from datetime import datetime, timezone, timedelta

DEFAULT_LIST_ID = "1270471213819854852"
DATA_DIR = r"C:\Users\grego\.gemini\config\skills\twitter\data"
OUTPUT_FILE = os.path.join(DATA_DIR, "latest_tweets.json")

def parse_args():
    parser = argparse.ArgumentParser(description="Fetch and filter recent tweets from a Twitter list.")
    parser.add_argument("--hours", type=float, default=6.0, help="Filter tweets from the last N hours (default: 6.0)")
    parser.add_argument("--list-id", type=str, default=DEFAULT_LIST_ID, help="Twitter list ID (default: Actu Météo)")
    parser.add_argument("--limit", type=int, default=100, help="Initial number of tweets to fetch (default: 100)")
    return parser.parse_args()

def fetch_list_tweets(list_id, limit):
    cmd = [
        "opencli", "twitter", "list-tweets", list_id,
        "--limit", str(limit),
        "-f", "json"
    ]
    try:
        # Run command and capture output
        # ponytail: running via subprocess directly using system-installed opencli with shell=True for Windows compatibility
        result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="ignore", shell=True)
        if result.returncode != 0:
            print(f"Error running opencli: {result.stderr.strip()}", file=sys.stderr)
            return None
        return json.loads(result.stdout.strip())
    except Exception as e:
        print(f"Failed to fetch tweets: {e}", file=sys.stderr)
        return None

def clean_accents(s):
    nfkd = unicodedata.normalize('NFKD', s)
    return "".join([c for c in nfkd if not unicodedata.combining(c)]).lower()

def is_alert_tweet(text):
    if not text:
        return False
    # ponytail: key alert triggers to immediately identify high-priority weather and emergency events
    alert_triggers = [
        "vigilance rouge", "vigilance orange", "alerte rouge", "alerte orange",
        "incendie", "feu de for", "tornade", "record absolu", "record mensuel",
        "tempête", "inondation", "canicule", "orage", "braise"
    ]
    cleaned_text = clean_accents(text)
    for trigger in alert_triggers:
        if clean_accents(trigger) in cleaned_text:
            return True
    return False

def is_model_trend_tweet(text):
    if not text:
        return False
    # ponytail: weather models, numerical runs, and medium/long-term forecasting terms
    model_triggers = [
        "arome", "arpege", "ifs", "ecmwf", "gfs", "icon", "ukmo", "gem", "aifs",
        "ncep", "meteogramme", "meteogram", "gefs", "cep", "calcul numerique",
        "calculs numeriques", "modele", "saisonniere", "saisonnier", "moyen terme",
        "long terme", "tendance", "anomalie", "projection", "scenario"
    ]
    cleaned_text = clean_accents(text)
    for trigger in model_triggers:
        if clean_accents(trigger) in cleaned_text:
            return True
    return False

def filter_tweets_by_age(tweets, hours):
    if not tweets:
        return []
        
    filtered = []
    now = datetime.now(timezone.utc)
    threshold = timedelta(hours=hours)
    
    for t in tweets:
        created_at_str = t.get("created_at")
        if not created_at_str:
            continue
            
        try:
            # E.g., "Mon Jul 13 09:57:42 +0000 2026"
            # ponytail: using native datetime parsing with %z timezone offset support
            tweet_time = datetime.strptime(created_at_str, "%a %b %d %H:%M:%S %z %Y")
            age = now - tweet_time
            if age <= threshold:
                # Add engagement score for relevance sorting/flagging
                likes = int(t.get("likes", 0) or 0)
                retweets = int(t.get("retweets", 0) or 0)
                replies = int(t.get("replies", 0) or 0)
                engagement = likes * 1 + retweets * 3 + replies * 2
                
                # Tag alerts and models, boost score
                is_alert = is_alert_tweet(t.get("text", ""))
                is_model_trend = is_model_trend_tweet(t.get("text", ""))
                
                if is_alert:
                    engagement += 100
                if is_model_trend:
                    engagement += 100
                
                t["age_hours"] = round(age.total_seconds() / 3600, 2)
                t["engagement_score"] = engagement
                t["is_alert"] = is_alert
                t["is_model_trend"] = is_model_trend
                filtered.append(t)
        except ValueError:
            # Skip if date format is unexpected
            continue
            
    # Sort by engagement score descending so alerts, models and popular tweets are at the top
    filtered.sort(key=lambda x: -x["engagement_score"])
    return filtered

def main():
    args = parse_args()
    
    print(f"Fetching up to {args.limit} tweets from list ID {args.list_id}...")
    raw_tweets = fetch_list_tweets(args.list_id, args.limit)
    
    if raw_tweets is None:
        print("Error: Could not retrieve tweets. Check if opencli is configured and authenticated.", file=sys.stderr)
        sys.exit(1)
        
    print(f"Retrieved {len(raw_tweets)} raw tweets. Filtering for the last {args.hours} hours...")
    filtered_tweets = filter_tweets_by_age(raw_tweets, args.hours)
    
    # Ensure data directory exists
    os.makedirs(DATA_DIR, exist_ok=True)
    
    # Save to JSON
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(filtered_tweets, f, ensure_ascii=False, indent=2)
        
    print(f"Success: Found {len(filtered_tweets)} tweets from the last {args.hours} hours.")
    print(f"Data saved to: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
