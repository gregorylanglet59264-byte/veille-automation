# -*- coding: utf-8 -*-
"""
publish_to_twitter.py
Posts a tweet with image. Tests read access first, then write.
"""
import os, sys, argparse, requests
from requests_oauthlib import OAuth1

def get_creds():
    k = {
        "api_key":    os.environ.get("TWITTER_API_KEY", "").strip(),
        "api_secret": os.environ.get("TWITTER_API_SECRET", "").strip(),
        "access_tok": os.environ.get("TWITTER_ACCESS_TOKEN", "").strip(),
        "access_sec": os.environ.get("TWITTER_ACCESS_SECRET", "").strip(),
        "bearer":     os.environ.get("TWITTER_BEARER_TOKEN", "").strip(),
    }
    for name, val in k.items():
        if val:
            print(f"  {name}: {val[:6]}...{val[-4:]} (len={len(val)})")
        else:
            print(f"  {name}: NOT SET")
    return k

def test_bearer(bearer):
    """Test Bearer Token sur un endpoint app-only valide."""
    if not bearer:
        print("No bearer token — skipping.")
        return
    # /2/tweets/search/recent fonctionne avec Bearer sur Free tier
    r = requests.get(
        "https://api.twitter.com/2/tweets/search/recent?query=from:monsieurmeteo07&max_results=10",
        headers={"Authorization": f"Bearer {bearer}"},
        timeout=10
    )
    print(f"[BEARER TEST] search/recent → HTTP {r.status_code}: {r.text[:300]}")

def test_oauth1_read(k):
    """Vérifie les credentials OAuth1 avec v2 GET /2/users/me (Free tier compatible)."""
    auth = OAuth1(k["api_key"], k["api_secret"], k["access_tok"], k["access_sec"])
    r = requests.get(
        "https://api.twitter.com/2/users/me",
        auth=auth, timeout=10
    )
    print(f"[OAUTH1 v2 READ] GET /2/users/me → HTTP {r.status_code}: {r.text[:300]}")
    return r.status_code == 200

def upload_media(image_path, k):
    auth = OAuth1(k["api_key"], k["api_secret"], k["access_tok"], k["access_sec"])
    if not os.path.exists(image_path):
        print(f"Image not found: {image_path}")
        return None
    print(f"Uploading {image_path} ...")
    with open(image_path, "rb") as f:
        r = requests.post(
            "https://upload.twitter.com/1.1/media/upload.json",
            auth=auth, files={"media": f}, timeout=60
        )
    print(f"  Upload HTTP {r.status_code}: {r.text[:300]}")
    if r.status_code == 200:
        return r.json().get("media_id_string")
    return None

def post_tweet(text, media_id, k):
    auth = OAuth1(k["api_key"], k["api_secret"], k["access_tok"], k["access_sec"])
    payload = {"text": text}
    if media_id:
        payload["media"] = {"media_ids": [media_id]}
    r = requests.post(
        "https://api.twitter.com/2/tweets",
        auth=auth, json=payload, timeout=30
    )
    print(f"  create_tweet HTTP {r.status_code}: {r.text[:500]}")
    if r.status_code in (200, 201):
        tid = r.json().get("data", {}).get("id", "?")
        print(f"✅ Tweet publié ! https://x.com/i/status/{tid}")
        return True
    print(f"ERROR: {r.status_code} — {r.text}", file=sys.stderr)
    sys.exit(1)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--image",     required=True)
    parser.add_argument("--text-file", required=True)
    args = parser.parse_args()

    with open(args.text_file, encoding="utf-8") as f:
        tweet_text = f.read().strip()[:280]

    print(f"\nTweet ({len(tweet_text)} chars):\n{tweet_text}\n")
    print("Credentials:")
    k = get_creds()

    # Diagnostic : test lecture
    test_bearer(k["bearer"])
    ok = test_oauth1_read(k)

    if not ok:
        print("\n⚠️  OAuth1 verify_credentials a échoué.")
        print("→ Vérifiez que OAuth 1.0a est activé dans User Auth Settings sur developer.twitter.com")
        print("→ Et que les tokens ont été régénérés APRES la sauvegarde des settings.")
        sys.exit(1)

    # Publication
    media_id = upload_media(args.image, k)
    post_tweet(tweet_text, media_id, k)

if __name__ == "__main__":
    main()
