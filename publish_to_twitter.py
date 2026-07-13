# -*- coding: utf-8 -*-
"""
publish_to_twitter.py
Authenticates with the Twitter API using OAuth 1.0a/v2 keys,
uploads the provided image, and posts the tweet text.
"""
import os
import sys
import argparse
import tweepy

def publish_tweet(image_path, text_path):
    # Load secrets
    api_key = os.environ.get("TWITTER_API_KEY")
    api_secret = os.environ.get("TWITTER_API_SECRET")
    access_token = os.environ.get("TWITTER_ACCESS_TOKEN")
    access_secret = os.environ.get("TWITTER_ACCESS_SECRET")
    
    if not all([api_key, api_secret, access_token, access_secret]):
        print("Error: Missing one or more Twitter API credentials in environment variables.")
        print(f"DEBUG keys presence: Key: {bool(api_key)}, Secret: {bool(api_secret)}, Token: {bool(access_token)}, Token Secret: {bool(access_secret)}")
        sys.exit(1)
        
    # Read text content
    if not os.path.exists(text_path):
        print(f"Error: Text file not found at {text_path}")
        sys.exit(1)
    with open(text_path, "r", encoding="utf-8") as f:
        tweet_text = f.read().strip()
        
    print(f"Posting tweet with text ({len(tweet_text)} chars)...")
    print(f"Content:\n---\n{tweet_text}\n---")
    
    try:
        # OAuth 1.0a authentication for media upload (Twitter API v1.1)
        auth = tweepy.OAuth1UserHandler(api_key, api_secret, access_token, access_secret)
        api_v1 = tweepy.API(auth)
        
        # Upload the media
        print(f"Uploading image: {image_path}...")
        media = api_v1.media_upload(filename=image_path)
        media_id = media.media_id_string
        print(f"Media uploaded successfully! ID: {media_id}")
        
        # Twitter API v2 Client for posting the tweet
        client = tweepy.Client(
            consumer_key=api_key,
            consumer_secret=api_secret,
            access_token=access_token,
            access_token_secret=access_secret
        )
        
        # Create tweet with the media ID attached
        response = client.create_tweet(text=tweet_text, media_ids=[media_id])
        print("Tweet posted successfully!")
        print(f"Tweet details: {response}")
        
    except Exception as e:
        print(f"Error posting tweet: {e}")
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Publishes a tweet with an image to X.")
    parser.add_argument("--image", required=True, help="Path to the image file")
    parser.add_argument("--text-file", required=True, help="Path to the text file containing the tweet body")
    args = parser.parse_args()
    
    publish_tweet(args.image, args.text_file)
