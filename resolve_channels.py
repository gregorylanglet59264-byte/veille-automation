import json
import urllib.request
import re
import time
import os

SUBS_FILE = "subscriptions.json"

def get_channel_id(handle):
    if not handle.startswith("@"):
        handle = "@" + handle
        
    url = f"https://www.youtube.com/{handle}"
    req = urllib.request.Request(
        url, 
        headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'fr,fr-FR;q=0.9,en;q=0.8'
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read().decode('utf-8', errors='ignore')
            
            # Essayer différentes expressions régulières pour trouver le channel ID UC...
            match1 = re.search(r'<meta itemprop="channelId" content="(UC[a-zA-Z0-9_-]{22})">', html)
            if match1:
                return match1.group(1)
                
            match2 = re.search(r'"channelId"\s*:\s*"(UC[a-zA-Z0-9_-]{22})"', html)
            if match2:
                return match2.group(1)
                
            match3 = re.search(r'href="https://www.youtube.com/channel/(UC[a-zA-Z0-9_-]{22})"', html)
            if match3:
                return match3.group(1)
                
    except Exception as e:
        print(f"Erreur pour {handle} : {e}")
    return None

def main():
    if not os.path.exists(SUBS_FILE):
        print(f"Fichier {SUBS_FILE} introuvable.")
        return
        
    with open(SUBS_FILE, 'r', encoding='utf-8') as f:
        channels = json.load(f)
        
    updated_count = 0
    for idx, c in enumerate(channels):
        cid = c.get("id", "")
        handle = c.get("handle", "")
        name = c.get("name", "")
        
        if not cid.startswith("UC") and handle:
            print(f"[{idx+1}/{len(channels)}] Résolution du channel ID pour {name} ({handle})...")
            real_id = get_channel_id(handle)
            if real_id:
                c["id"] = real_id
                print(f"  -> Trouvé : {real_id}")
                updated_count += 1
            else:
                print(f"  -> ÉCHEC pour {name}")
            time.sleep(0.5)
            
            # Sauvegarder périodiquement
            if updated_count % 5 == 0:
                with open(SUBS_FILE, 'w', encoding='utf-8') as f_out:
                    json.dump(channels, f_out, indent=2, ensure_ascii=False)
                    
    with open(SUBS_FILE, 'w', encoding='utf-8') as f_out:
        json.dump(channels, f_out, indent=2, ensure_ascii=False)
        
    print(f"Terminé ! {updated_count} chaînes mises à jour.")

if __name__ == "__main__":
    main()
