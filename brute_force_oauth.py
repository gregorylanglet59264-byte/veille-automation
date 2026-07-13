# -*- coding: utf-8 -*-
"""
brute_force_oauth.py
Tests combinations of ambiguous characters in Twitter secrets to find the exact pair
that authenticates successfully with Twitter API v2.
"""
import os
import sys
import urllib.parse
import requests
from requests_oauthlib import OAuth1
from concurrent.futures import ThreadPoolExecutor, as_completed

def test_combination(api_key, api_secret, access_token, access_token_secret):
    auth = OAuth1(api_key, api_secret, access_token, access_token_secret)
    try:
        r = requests.get(
            "https://api.twitter.com/2/users/me",
            auth=auth,
            timeout=5
        )
        if r.status_code == 200:
            return {
                "api_key": api_key,
                "api_secret": api_secret,
                "access_token": access_token,
                "access_token_secret": access_token_secret,
                "response": r.json()
            }
    except Exception:
        pass
    return None

def main():
    # 1. Test Bearer Token (with URL-decoding)
    raw_bearer = os.environ.get("TWITTER_BEARER_TOKEN", "").strip()
    bearer = urllib.parse.unquote(raw_bearer)
    
    print("Testing Bearer Token (URL-decoded)...")
    r = requests.get(
        "https://api.twitter.com/2/tweets/search/recent?query=from:monsieurmeteo07&max_results=10",
        headers={"Authorization": f"Bearer {bearer}"},
        timeout=10
    )
    print(f"Bearer test status: {r.status_code}")
    if r.status_code == 200:
        print("✅ Bearer Token is VALID!")
    else:
        print(f"❌ Bearer Token test failed: {r.text[:200]}")

    # 2. Brute force OAuth1 Keys
    api_key = os.environ.get("TWITTER_API_KEY", "").strip()
    access_token = os.environ.get("TWITTER_ACCESS_TOKEN", "").strip()
    
    raw_api_secret = os.environ.get("TWITTER_API_SECRET", "").strip()
    raw_access_secret = os.environ.get("TWITTER_ACCESS_SECRET", "").strip()
    
    if not all([api_key, raw_api_secret, access_token, raw_access_secret]):
        print("Missing OAuth1 credentials in env.")
        sys.exit(1)

    print("\nStarting OAuth1 credentials verification...")
    
    # Check if the keys work out-of-the-box
    res = test_combination(api_key, raw_api_secret, access_token, raw_access_secret)
    if res:
        print("✅ Provided credentials are already 100% VALID!")
        # Save correct credentials
        with open("data/correct_creds.json", "w") as f:
            import json
            json.dump(res, f)
        sys.exit(0)
        
    print("Provided credentials returned 401. Running brute-force for ambiguous characters...")

    # Let's define candidates for the Consumer Secret (raw_api_secret)
    # E.g. "9QBebgaQFekofi49WYppQyUV3vJ6z7YAzY8SlF0Rr9P5VIoJ0S"
    # Ambiguity 1: "Sl" after "Y8"
    # Ambiguity 2: "I" in "5VIoJ0S"
    api_secret_base_left = "9QBebgaQFekofi49WYppQyUV3vJ6z7YAzY8"
    api_secret_base_mid = "F0Rr9P5V"
    api_secret_base_right = "oJ0S"
    
    x1_candidates = ["Sl", "SI", "S1", "sl", "sI", "s1", "5l", "5I", "51", "l", "I", "1"]
    x2_candidates = ["I", "l", "1"]
    
    api_secret_combos = []
    for x1 in x1_candidates:
        for x2 in x2_candidates:
            combo = f"{api_secret_base_left}{x1}{api_secret_base_mid}{x2}{api_secret_base_right}"
            if len(combo) == 50: # Only keep valid 50-character secrets
                api_secret_combos.append(combo)
    
    # Add the raw one just in case
    if raw_api_secret not in api_secret_combos:
        api_secret_combos.append(raw_api_secret)

    # Let's define candidates for the Access Token Secret (raw_access_secret)
    # E.g. "gXGWKUdOWDqVu7pVZWZ2MvIt0QDa0OnSqD2dhDMBMtpos"
    # Ambiguity 1: "pV" after "Vu7"
    # Ambiguity 2: "I" in "MvIt0Q"
    access_secret_base_left = "gXGWKUdOWDqVu7"
    access_secret_base_mid = "ZWZ2Mv"
    access_secret_base_right = "t0QDa0OnSqD2dhDMBMtpos"
    
    y1_candidates = ["pV", "pv", "Pv", "PV", "qV", "qv"]
    y2_candidates = ["I", "l", "1"]
    
    access_secret_combos = []
    for y1 in y1_candidates:
        for y2 in y2_candidates:
            combo = f"{access_secret_base_left}{y1}{access_secret_base_mid}{y2}{access_secret_base_right}"
            if len(combo) == 45: # Only keep valid 45-character secrets
                access_secret_combos.append(combo)
                
    if raw_access_secret not in access_secret_combos:
        access_secret_combos.append(raw_access_secret)

    print(f"Testing {len(api_secret_combos)} Consumer Secret and {len(access_secret_combos)} Access Secret combinations...")
    
    tasks = []
    for sec in api_secret_combos:
        for a_sec in access_secret_combos:
            tasks.append((api_key, sec, access_token, a_sec))
            
    success_res = None
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = {
            executor.submit(test_combination, t[0], t[1], t[2], t[3]): t 
            for t in tasks
        }
        for future in as_completed(futures):
            res = future.result()
            if res:
                success_res = res
                # Cancel other tasks
                break

    if success_res:
        print("✅ SUCCESS! Found working credential combination:")
        print(f"  API Key: {success_res['api_key']}")
        print(f"  API Secret: {success_res['api_secret']}")
        print(f"  Access Token: {success_res['access_token']}")
        print(f"  Access Secret: {success_res['access_token_secret']}")
        print(f"  Connected User: @{success_res['response'].get('data', {}).get('username')}")
        
        # Save correct credentials
        os.makedirs("data", exist_ok=True)
        with open("data/correct_creds.json", "w") as f:
            import json
            json.dump(success_res, f)
    else:
        print("❌ Brute force failed. None of the key combinations could authenticate.")
        sys.exit(1)

if __name__ == "__main__":
    main()
