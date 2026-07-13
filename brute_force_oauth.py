# -*- coding: utf-8 -*-
"""
brute_force_oauth.py
Tests combinations of ambiguous characters in Twitter secrets by performing a media upload test.
Media upload (v1.1) works on the Free tier and does not post any tweets, making it the perfect
non-destructive test for credentials validity.
"""
import os
import sys
import io
import json
import requests
from requests_oauthlib import OAuth1
from concurrent.futures import ThreadPoolExecutor, as_completed

# Generate a tiny 1x1 GIF image in memory for testing upload
TINY_GIF = b'GIF89a\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;'

def test_combination(api_key, api_secret, access_token, access_token_secret):
    auth = OAuth1(api_key, api_secret, access_token, access_token_secret)
    try:
        # We perform a media upload test which is supported on the Free tier
        # and doesn't post any public tweet.
        r = requests.post(
            "https://upload.twitter.com/1.1/media/upload.json",
            auth=auth,
            files={"media": ("test.gif", TINY_GIF, "image/gif")},
            timeout=4
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
    # Load raw secrets from env
    raw_api_key = os.environ.get("TWITTER_API_KEY", "").strip()
    raw_api_secret = os.environ.get("TWITTER_API_SECRET", "").strip()
    access_token = os.environ.get("TWITTER_ACCESS_TOKEN", "").strip()
    raw_access_secret = os.environ.get("TWITTER_ACCESS_SECRET", "").strip()
    
    if not all([raw_api_key, raw_api_secret, access_token, raw_access_secret]):
        print("Missing OAuth1 credentials in env.")
        sys.exit(1)

    print("\nStarting OAuth1 credentials verification via Media Upload...")
    
    # 1. First check if the keys work as they are
    res = test_combination(raw_api_key, raw_api_secret, access_token, raw_access_secret)
    if res:
        print("✅ Provided credentials are already 100% VALID!")
        os.makedirs("data", exist_ok=True)
        with open("data/correct_creds.json", "w") as f:
            json.dump(res, f)
        sys.exit(0)
        
    print("Provided credentials returned 401. Running brute-force for ambiguous characters...")

    # 2. Generate combinations for API Key
    # E.g. "dBuAhm2VgKRSWePZew6Fz1PAB"
    # Ambiguity 1: "V" in "2Vg" (could be "v")
    # Ambiguity 2: "1" in "6Fz1PAB" (could be "l" or "I")
    api_key_combos = []
    api_key_base_left = "dBuAhm2"
    api_key_base_mid = "gKRSWePZew6Fz"
    api_key_base_right = "PAB"
    
    v_chars = ["V", "v"]
    one_chars = ["1", "l", "I"]
    for v in v_chars:
        for one in one_chars:
            api_key_combos.append(f"{api_key_base_left}{v}{api_key_base_mid}{one}{api_key_base_right}")
            
    if raw_api_key not in api_key_combos:
        api_key_combos.append(raw_api_key)

    # 3. Generate combinations for Consumer Secret
    # E.g. "9QBebgaQFekofi49WYppQyUV3vJ6z7YAzY8SlF0Rr9P5VIoJ0S"
    # Ambiguity 1: "Sl" after "Y8"
    # Ambiguity 2: "I" in "5VIoJ0S"
    api_secret_base_left = "9QBebgaQFekofi49WYppQyUV3vJ6z7YAzY8"
    api_secret_base_mid = "F0Rr9P5V"
    api_secret_base_right = "oJ0S"
    
    x1_candidates = ["Sl", "SI", "S1", "sl", "sI", "s1", "l", "I", "1"]
    x2_candidates = ["I", "l", "1"]
    
    api_secret_combos = []
    for x1 in x1_candidates:
        for x2 in x2_candidates:
            combo = f"{api_secret_base_left}{x1}{api_secret_base_mid}{x2}{api_secret_base_right}"
            if len(combo) in (49, 50):
                api_secret_combos.append(combo)
                
    if raw_api_secret not in api_secret_combos:
        api_secret_combos.append(raw_api_secret)

    # 4. Generate combinations for Access Token Secret
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
            if len(combo) in (44, 45):
                access_secret_combos.append(combo)
                
    if raw_access_secret not in access_secret_combos:
        access_secret_combos.append(raw_access_secret)

    # Compile list of all combinations
    tasks = []
    for key in api_key_combos:
        for sec in api_secret_combos:
            for a_sec in access_secret_combos:
                tasks.append((key, sec, access_token, a_sec))
                
    print(f"Testing {len(tasks)} combinations using up to 40 concurrent workers...")
    
    success_res = None
    # We use a larger thread pool to test combinations quickly (takes < 20s for 1000 tasks)
    with ThreadPoolExecutor(max_workers=40) as executor:
        futures = {
            executor.submit(test_combination, t[0], t[1], t[2], t[3]): t 
            for t in tasks
        }
        for future in as_completed(futures):
            res = future.result()
            if res:
                success_res = res
                # Cancel all remaining futures
                for f in futures:
                    f.cancel()
                break

    if success_res:
        print("✅ SUCCESS! Found working credential combination:")
        print(f"  API Key: {success_res['api_key']}")
        print(f"  API Secret: {success_res['api_secret']}")
        print(f"  Access Token: {success_res['access_token']}")
        print(f"  Access Secret: {success_res['access_token_secret']}")
        
        # Save correct credentials
        os.makedirs("data", exist_ok=True)
        with open("data/correct_creds.json", "w") as f:
            json.dump(success_res, f)
    else:
        print("❌ Brute force failed. None of the key combinations could authenticate.")
        sys.exit(1)

if __name__ == "__main__":
    main()
