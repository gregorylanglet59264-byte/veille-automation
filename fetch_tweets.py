# -*- coding: utf-8 -*-
"""
fetch_tweets.py
Fetches recent tweets from a Twitter/X list using the Tweepy API v2 (works on GitHub Actions).
Filters tweets locally by age to avoid X API list_tweets start_time parameter errors.
"""
import argparse
import json
import os
import sys
import unicodedata
from datetime import datetime, timezone, timedelta

DEFAULT_LIST_ID = "1270471213819854852"

def get_output_file():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(script_dir, "data")
    os.makedirs(data_dir, exist_ok=True)
    return os.path.join(data_dir, "latest_tweets.json")

def parse_args():
    parser = argparse.ArgumentParser(description="Fetch and filter recent tweets from a Twitter list.")
    parser.add_argument("--hours", type=float, default=2.0, help="Filter tweets from the last N hours (default: 2.0)")
    parser.add_argument("--list-id", type=str, default=DEFAULT_LIST_ID)
    parser.add_argument("--limit", type=int, default=100)
    return parser.parse_args()

def clean_accents(s):
    nfkd = unicodedata.normalize('NFKD', s)
    return "".join([c for c in nfkd if not unicodedata.combining(c)]).lower()

def is_alert_tweet(text):
    if not text: return False
    triggers = ["vigilance rouge","vigilance orange","alerte rouge","alerte orange",
                "incendie","tornade","record absolu","record mensuel","tempête",
                "inondation","canicule","orage"]
    ct = clean_accents(text)
    return any(clean_accents(t) in ct for t in triggers)

def is_model_trend_tweet(text):
    if not text: return False
    triggers = ["arome","arpege","ifs","ecmwf","gfs","icon","ukmo","gem","aifs",
                "modele","tendance","anomalie","projection","moyen terme","long terme",
                "saisonniere","saisonnier"]
    ct = clean_accents(text)
    return any(clean_accents(t) in ct for t in triggers)

def fetch_via_tweepy(list_id, limit, hours):
    """Fetch list tweets using Tweepy API v2 — works on GitHub Actions."""
    try:
        import tweepy
    except ImportError:
        print("Tweepy not installed.", file=sys.stderr)
        return None

    api_key    = os.environ.get("TWITTER_API_KEY")
    api_secret = os.environ.get("TWITTER_API_SECRET")
    access_tok = os.environ.get("TWITTER_ACCESS_TOKEN")
    access_sec = os.environ.get("TWITTER_ACCESS_SECRET")
    
    if not all([api_key, api_secret, access_tok, access_sec]):
        print("Twitter API credentials not found in environment.", file=sys.stderr)
        return None

    try:
        client = tweepy.Client(
            consumer_key=api_key,
            consumer_secret=api_secret,
            access_token=access_tok,
            access_token_secret=access_sec,
            wait_on_rate_limit=True
        )
        
        tweets = []
        # Note: X API v2 list_tweets does NOT support start_time parameter.
        # We fetch the latest tweets and filter them by age locally in Python.
        paginator = tweepy.Paginator(
            client.get_list_tweets,
            id=list_id,
            tweet_fields=["created_at", "author_id", "public_metrics", "attachments"],
            expansions=["author_id", "attachments.media_keys"],
            media_fields=["url", "preview_image_url", "type"],
            user_fields=["username", "name"],
            max_results=min(limit, 100),
            limit=2
        )
        
        users_map = {}
        media_map = {}
        
        for response in paginator:
            if response.includes:
                if response.includes.get("users"):
                    for u in response.includes["users"]:
                        users_map[u.id] = u
                if response.includes.get("media"):
                    for m in response.includes["media"]:
                        media_map[m.media_key] = m

            if not response.data:
                continue
            for t in response.data:
                user = users_map.get(t.author_id)
                metrics = t.public_metrics or {}
                likes    = metrics.get("like_count", 0)
                retweets = metrics.get("retweet_count", 0)
                replies  = metrics.get("reply_count", 0)
                engagement = likes + retweets * 3 + replies * 2

                text = t.text or ""
                is_alert = is_alert_tweet(text)
                is_model = is_model_trend_tweet(text)
                if is_alert: engagement += 100
                if is_model:  engagement += 100

                media_urls = []
                if t.attachments and t.attachments.get("media_keys"):
                    for mk in t.attachments["media_keys"]:
                        m = media_map.get(mk)
                        if m and m.type == "photo":
                            media_urls.append(m.url)

                tweets.append({
                    "id": str(t.id),
                    "text": text,
                    "created_at": t.created_at.strftime("%a %b %d %H:%M:%S +0000 %Y") if t.created_at else "",
                    "username": user.username if user else "unknown",
                    "name": user.name if user else "unknown",
                    "likes": likes,
                    "retweets": retweets,
                    "replies": replies,
                    "engagement_score": engagement,
                    "is_alert": is_alert,
                    "is_model_trend": is_model,
                    "media_urls": media_urls,
                    "url": f"https://x.com/{user.username if user else 'i'}/status/{t.id}"
                })
        
        # Filter by age locally
        now = datetime.now(timezone.utc)
        threshold = timedelta(hours=hours)
        filtered_tweets = []
        
        for t in tweets:
            created_at_str = t.get("created_at", "")
            try:
                # e.g. "Mon Jul 13 12:45:02 +0000 2026"
                tweet_time = datetime.strptime(created_at_str, "%a %b %d %H:%M:%S %z %Y")
                age = now - tweet_time
                if age <= threshold:
                    t["age_hours"] = round(age.total_seconds() / 3600, 2)
                    filtered_tweets.append(t)
            except ValueError:
                continue
                
        filtered_tweets.sort(key=lambda x: -x["engagement_score"])
        return filtered_tweets
        
    except Exception as e:
        print(f"Tweepy error: {e}", file=sys.stderr)
        return None

def main():
    args = parse_args()
    output_file = get_output_file()
    
    print(f"Fetching tweets from list {args.list_id} (last {args.hours}h)...")
    
    tweets = fetch_via_tweepy(args.period_id if hasattr(args, 'period_id') else args.list_id, args.limit, args.hours)
    
    if tweets is None:
        print("ERROR: Could not fetch tweets via Tweepy.", file=sys.stderr)
        # Fallback to empty list to prevent downstream crashes
        tweets = []
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(tweets, f, ensure_ascii=False, indent=2)
    
    print(f"Done: {len(tweets)} tweets saved to {output_file}")

if __name__ == "__main__":
    main()
