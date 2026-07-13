# -*- coding: utf-8 -*-
"""
publish_to_twitter.py
Posts a tweet with an image using Twitter API v2 (Free tier compatible).
Media upload still requires v1.1 OAuth1 — but falls back to text-only if upload fails.
"""
import os
import sys
import argparse
import tweepy

def get_client():
    api_key    = os.environ.get("TWITTER_API_KEY", "").strip()
    api_secret = os.environ.get("TWITTER_API_SECRET", "").strip()
    access_tok = os.environ.get("TWITTER_ACCESS_TOKEN", "").strip()
    access_sec = os.environ.get("TWITTER_ACCESS_SECRET", "").strip()

    if not all([api_key, api_secret, access_tok, access_sec]):
        print("ERROR: Missing Twitter API credentials.", file=sys.stderr)
        sys.exit(1)

    return api_key, api_secret, access_tok, access_sec

def upload_media(image_path, api_key, api_secret, access_tok, access_sec):
    """Upload image via v1.1 OAuth1 (required for media_upload endpoint)."""
    try:
        auth = tweepy.OAuth1UserHandler(api_key, api_secret, access_tok, access_sec)
        api_v1 = tweepy.API(auth)
        media = api_v1.media_upload(filename=image_path)
        print(f"✅ Image uploadée (media_id={media.media_id_string})")
        return media.media_id_string
    except tweepy.errors.Unauthorized as e:
        print(f"⚠️  Upload v1.1 refusé ({e}) — publication sans image.")
        return None
    except Exception as e:
        print(f"⚠️  Upload échoué ({e}) — publication sans image.")
        return None

def post_tweet(text, media_id, api_key, api_secret, access_tok, access_sec):
    """Post tweet via v2 Client."""
    client = tweepy.Client(
        consumer_key=api_key,
        consumer_secret=api_secret,
        access_token=access_tok,
        access_token_secret=access_sec,
    )
    kwargs = {"text": text}
    if media_id:
        kwargs["media_ids"] = [media_id]

    response = client.create_tweet(**kwargs)
    tweet_id = response.data["id"]
    print(f"✅ Tweet publié ! https://x.com/i/status/{tweet_id}")
    return tweet_id

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

    # Twitter hard limit: 280 chars
    if len(tweet_text) > 280:
        tweet_text = tweet_text[:277] + "…"

    print(f"Texte du tweet ({len(tweet_text)} chars) :\n---\n{tweet_text}\n---")

    api_key, api_secret, access_tok, access_sec = get_client()

    # Try to upload image; fall back to text-only if v1.1 not available
    media_id = None
    if os.path.exists(args.image):
        media_id = upload_media(args.image, api_key, api_secret, access_tok, access_sec)
    else:
        print(f"⚠️  Image not found: {args.image} — publication sans image.")

    post_tweet(tweet_text, media_id, api_key, api_secret, access_tok, access_sec)

if __name__ == "__main__":
    main()
