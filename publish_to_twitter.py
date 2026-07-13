# -*- coding: utf-8 -*-
"""
publish_to_twitter.py
Posts a tweet with an image. Uses requests + requests_oauthlib directly
for maximum transparency and debugging.
"""
import os
import sys
import argparse
import requests
from requests_oauthlib import OAuth1

def get_creds():
    keys = {
        "api_key":    os.environ.get("TWITTER_API_KEY", "").strip(),
        "api_secret": os.environ.get("TWITTER_API_SECRET", "").strip(),
        "access_tok": os.environ.get("TWITTER_ACCESS_TOKEN", "").strip(),
        "access_sec": os.environ.get("TWITTER_ACCESS_SECRET", "").strip(),
    }
    missing = [k for k, v in keys.items() if not v]
    if missing:
        print(f"ERROR: Missing credentials: {missing}", file=sys.stderr)
        sys.exit(1)
    for k, v in keys.items():
        print(f"  {k}: {v[:6]}...{v[-4:]} (len={len(v)})")
    return keys

def make_auth(k):
    return OAuth1(k["api_key"], k["api_secret"], k["access_tok"], k["access_sec"])

def upload_media(image_path, auth):
    """Upload image via v1.1 (required for media attach)."""
    if not os.path.exists(image_path):
        print(f"Image not found: {image_path} — skipping upload.")
        return None
    print(f"Uploading {image_path} ...")
    with open(image_path, "rb") as f:
        r = requests.post(
            "https://upload.twitter.com/1.1/media/upload.json",
            auth=auth,
            files={"media": f},
            timeout=60,
        )
    print(f"  Upload HTTP {r.status_code}: {r.text[:300]}")
    if r.status_code == 200:
        mid = r.json().get("media_id_string")
        print(f"  Media ID: {mid}")
        return mid
    print("  Upload failed — will post text only.")
    return None

def post_tweet(text, media_id, auth):
    """Post tweet via v2 API with OAuth 1.0a."""
    payload = {"text": text}
    if media_id:
        payload["media"] = {"media_ids": [media_id]}

    r = requests.post(
        "https://api.twitter.com/2/tweets",
        auth=auth,
        json=payload,
        headers={"Content-Type": "application/json"},
        timeout=30,
    )
    print(f"  create_tweet HTTP {r.status_code}: {r.text[:500]}")
    if r.status_code in (200, 201):
        data = r.json().get("data", {})
        tid = data.get("id", "?")
        print(f"✅ Tweet publié ! https://x.com/i/status/{tid}")
        return True
    print(f"ERROR posting tweet: {r.status_code} — {r.text}", file=sys.stderr)
    sys.exit(1)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--image",     required=True)
    parser.add_argument("--text-file", required=True)
    args = parser.parse_args()

    if not os.path.exists(args.text_file):
        print(f"ERROR: text file not found: {args.text_file}", file=sys.stderr)
        sys.exit(1)
    with open(args.text_file, encoding="utf-8") as f:
        tweet_text = f.read().strip()
    if len(tweet_text) > 280:
        tweet_text = tweet_text[:277] + "…"

    print(f"\nTweet ({len(tweet_text)} chars):\n{tweet_text}\n")
    print("Credentials:")
    k = get_creds()
    auth = make_auth(k)

    media_id = upload_media(args.image, auth)
    post_tweet(tweet_text, media_id, auth)

if __name__ == "__main__":
    main()
