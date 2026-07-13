# -*- coding: utf-8 -*-
"""
capture_debrief.py
Reads the structured debrief JSON, dynamically copies the custom background
from Desktop/cartes_alertes/images twitter, writes data.js,
and captures index_debrief.html as a 1920x1080 JPG infographic.
"""
import json
import os
import sys
import shutil
from playwright.sync_api import sync_playwright

script_dir = os.path.dirname(os.path.abspath(__file__))
if "veille-automation" in script_dir.lower():
    TWITTER_DIR = script_dir
else:
    TWITTER_DIR = r"C:\Users\grego\.gemini\config\skills\twitter"

STRUCTURED_FILE = os.path.join(TWITTER_DIR, "data", "debrief_structured.json")
JS_DATA_FILE = os.path.join(TWITTER_DIR, "data", "data.js")
HTML_FILE = os.path.join(TWITTER_DIR, "index_debrief.html")

if not os.path.exists(r"C:\Users\grego"):
    OUTPUT_IMAGE = os.path.join(script_dir, "debrief_twitter.jpg")
else:
    OUTPUT_IMAGE = r"C:\Users\grego\Desktop\cartes_alertes\debrief_twitter.jpg"

CUSTOM_BG_DIR = r"C:\Users\grego\Desktop\cartes_alertes\images twitter"
LOCAL_BG_TARGET = os.path.join(TWITTER_DIR, "data", "bg_twitter.png")

def sync_custom_background():
    """
    Scans the custom background directory on the desktop and copies the first image
    found (png/jpg) to a standard local path. If none is found, fallback is handled.
    """
    if not os.path.exists(CUSTOM_BG_DIR):
        print(f"Custom background directory not found: {CUSTOM_BG_DIR}. Fallback will be used.")
        return False
        
    try:
        files = os.listdir(CUSTOM_BG_DIR)
        image_files = [f for f in files if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        
        if image_files:
            source_path = os.path.join(CUSTOM_BG_DIR, image_files[0])
            os.makedirs(os.path.dirname(LOCAL_BG_TARGET), exist_ok=True)
            shutil.copy2(source_path, LOCAL_BG_TARGET)
            print(f"Successfully copied custom background from: {source_path}")
            return True
        else:
            print("No background images found in desktop folder. Fallback will be used.")
            return False
    except Exception as e:
        print(f"Warning syncing custom background: {e}", file=sys.stderr)
        return False

def generate_js_data(bg_exists):
    if not os.path.exists(STRUCTURED_FILE):
        print(f"Error: Structured debrief file not found: {STRUCTURED_FILE}", file=sys.stderr)
        return False
        
    try:
        with open(STRUCTURED_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        # Add background check info to the data
        data["has_custom_bg"] = bg_exists
        
        # Write to JS data file to bypass CORS restrictions when loading local files
        js_content = f"const DEBRIEF_DATA = {json.dumps(data, ensure_ascii=False, indent=2)};"
        os.makedirs(os.path.dirname(JS_DATA_FILE), exist_ok=True)
        with open(JS_DATA_FILE, "w", encoding="utf-8") as js_f:
            js_f.write(js_content)
        print("Successfully generated data.js")
        return True
    except Exception as e:
        print(f"Failed to generate data.js: {e}", file=sys.stderr)
        return False

def capture_screenshot():
    if not os.path.exists(HTML_FILE):
        print(f"Error: HTML template not found: {HTML_FILE}", file=sys.stderr)
        return False
        
    # Standard local file url
    # Convert backslashes to forward slashes for Chrome compatibility
    file_url = f"file:///{HTML_FILE.replace(os.sep, '/')}"
    
    os.makedirs(os.path.dirname(OUTPUT_IMAGE), exist_ok=True)
    
    print(f"Launching headless browser to capture: {file_url}...")
    try:
        with sync_playwright() as p:
            # Launch chromium
            # ponytail: chromium.launch with headless=True using standard playwright sync api
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            # Set 16:9 HD resolution
            page.set_viewport_size({"width": 1920, "height": 1080})
            
            # Navigate to local HTML file
            page.goto(file_url)
            
            # Wait for dynamic rendering and web fonts to load
            page.wait_for_timeout(2000)
            
            # Take screenshot
            page.screenshot(path=OUTPUT_IMAGE, quality=92, type="jpeg")
            print(f"Screenshot successfully saved to: {OUTPUT_IMAGE}")
            browser.close()
            return True
    except Exception as e:
        print(f"Failed to capture screenshot: {e}", file=sys.stderr)
        return False

def main():
    bg_exists = sync_custom_background()
    if generate_js_data(bg_exists):
        if capture_screenshot():
            print("Twitter debrief infographic generated successfully!")
            sys.exit(0)
    sys.exit(1)

if __name__ == "__main__":
    main()
