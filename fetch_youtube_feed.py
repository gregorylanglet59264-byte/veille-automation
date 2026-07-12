# -*- coding: utf-8 -*-
"""
fetch_youtube_feed.py
Scanne un échantillon des abonnements YouTube,
récupère les vidéos récentes, et génère un classement d'intérêt.
Adapté pour une exécution autonome sur GitHub Actions (sans écriture sur le Bureau Windows).
"""
import json
import subprocess
import os
import concurrent.futures
import time
from datetime import datetime

SUBS_FILE = "subscriptions.json"
OUTPUT_MD = "youtube_recommandations.md"
OUTPUT_JSON = "youtube_recommandations.json"

# Dictionnaire de pertinence des thématiques
INTEREST_SCORES = {
    "IA": 9.5,
    "Météo": 8.5,
    "Actualités Générales": 6.5
}

# Pondérations manuelles de pertinence par chaîne
CHANNEL_WEIGHTS = {
    "@LudovicSalenne": 10.0,
    "@gregory.beyrouti": 9.8,
    "@Shubham_Sharma": 9.2,
    "@RenaudDekode": 9.0,
    "@MeteoFrance": 8.8,
    "@meteo37": 8.5,
    "@iAlan_automatise": 8.0,
    "@DEW-Automatisation": 7.5,
    "@elliottpierret": 7.5
}

def translate_to_french(text):
    if not text:
        return ""
    english_keywords = {'the', 'is', 'in', 'and', 'before', 'coming', 'peak', 'heatwave', 'storms', 'return', 'with', 'how', 'to', 'for', 'you', 'your', 'are', 'what', 'can', 'do', 'surpasses', 'incredible', 'destroys', 'over'}
    words = set((text or "").lower().replace("?", " ").replace("!", " ").replace(".", " ").split())
    if not words.intersection(english_keywords):
        return text  # Déjà en français ou autre langue
        
    try:
        import urllib.request
        import urllib.parse
        url = "https://api.mymemory.translated.net/get?q=" + urllib.parse.quote(text) + "&langpair=en|fr"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode('utf-8'))
            translated = data.get("responseData", {}).get("translatedText", text)
            import html
            return html.unescape(translated)
    except Exception:
        return text

def generate_summary(title, category, channel_name):
    t = (title or "").lower()
    if "chatgpt" in t or "gpt" in t:
        return "Démonstration des nouvelles capacités et mises à jour de ChatGPT."
    elif "claude" in t and "code" in t:
        return "Guide d'utilisation complet de l'agent de programmation Claude Code."
    elif "claude" in t:
        return "Analyse des capacités du modèle Claude d'Anthropic."
    elif "gemini" in t:
        return "Analyse des performances et cas d'usage concrets de Gemini de Google."
    elif "deepseek" in t:
        return "Présentation de la nouvelle technologie d'IA disruptive de DeepSeek."
    elif "scraping" in t or "scrape" in t:
        return "Astuces et techniques pour extraire des données web sans se faire bloquer."
    elif "agent" in t:
        return "Présentation et tutoriel de déploiement d'agents IA autonomes."
    elif "copilot" in t:
        return "Démonstration d'outils d'IA de productivité pour automatiser les tâches."
    elif "canicule" in t or "chaleur" in t or "heatwave" in t:
        return "Analyse des records de températures et évolution de la vague de chaleur."
    elif "orage" in t or "tempête" in t or "storm" in t:
        return "Suivi des alertes météo et prévisions des épisodes orageux."
    elif "météo" in t or "meteo" in t or "climat" in t:
        return "Point météo complet et analyse des tendances climatologiques."
    elif "match" in t or "foot" in t or "belgium" in t or "spain" in t:
        return "Débriefing sportif et réactions suite aux dernières rencontres de football."
    elif "gaming" in t or "roblox" in t:
        return "Session de jeu vidéo (Let's Play) divertissante sur cette chaîne."
    return f"Actualités et analyses sur le thème {category}."

def get_latest_video(channel):
    handle = channel['handle']
    name = channel['name']
    category = channel['category']
    url = f"https://www.youtube.com/{handle}/videos"
    
    cmd = [
        "yt-dlp",
        "--playlist-end", "1",
        "--dump-json",
        url
    ]
    try:
        # Configuration spécifique pour éviter de planter sous Linux/Windows dans les environnements CI/CD
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=20, encoding='utf-8', errors='ignore')
        if result.returncode == 0 and result.stdout:
            data = json.loads(result.stdout.strip().split('\n')[0])
            
            # Vérifier l'âge de la vidéo (doit être de moins de 36 heures)
            upload_date_str = data.get("upload_date")
            if upload_date_str:
                upload_dt = datetime.strptime(upload_date_str, "%Y%m%d")
                from datetime import timedelta
                if datetime.now() - upload_dt > timedelta(hours=36):
                    return None
            
            video_url = f"https://www.youtube.com/watch?v={data.get('id')}"
            raw_title = data.get("title")
            translated_title = translate_to_french(raw_title)
            
            # Calculer le score d'intérêt
            base_score = INTEREST_SCORES.get(category, 5.0)
            weight = CHANNEL_WEIGHTS.get(handle, base_score)
            summary = generate_summary(translated_title, category, name)
            
            return {
                "channel_name": name,
                "handle": handle,
                "category": category,
                "title": translated_title,
                "url": video_url,
                "id": data.get("id"),
                "score": weight,
                "summary": summary
            }
    except Exception:
        pass
    return None

def main():
    if not os.path.exists(SUBS_FILE):
        print(f"Fichier de souscriptions manquant : {SUBS_FILE}")
        return
        
    with open(SUBS_FILE, 'r', encoding='utf-8') as f:
        channels = json.load(f)
        
    active_channels = [c for c in channels if c.get('active', True)]
    
    # Échantillonnage de chaînes actives réparties par catégorie
    sample_channels = []
    seen_categories = {}
    for c in active_channels:
        cat = c['category']
        if cat not in seen_categories:
            seen_categories[cat] = 0
        if seen_categories[cat] < 15:
            sample_channels.append(c)
            seen_categories[cat] += 1
            
    sample_channels = sample_channels[:35]
    print(f"Analyse des dernières vidéos de {len(sample_channels)} chaînes en cours...")
    
    videos = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(get_latest_video, chan): chan for chan in sample_channels}
        for future in concurrent.futures.as_completed(futures):
            res = future.result()
            if res:
                videos.append(res)
                print(f"  [Reçu] {res['channel_name']} : {res['title'][:50]}...")
                
    # Trier les vidéos par score d'intérêt décroissant et en garder 30 maximum
    videos = sorted(videos, key=lambda x: -x['score'])[:30]
    
    # Enregistrer l'échantillon brut en JSON
    with open(OUTPUT_JSON, 'w', encoding='utf-8') as j_file:
        json.dump(videos, j_file, ensure_ascii=False, indent=2)
    print(f"Rapport JSON brut enregistré dans : {OUTPUT_JSON}")
    
    # Écrire l'artefact Markdown (Top 10 mis en valeur, et les autres ensuite)
    with open(OUTPUT_MD, 'w', encoding='utf-8') as out:
        out.write("# 📺 Recommandations YouTube : Vidéos Récentes de vos Abonnements\n\n")
        out.write("Voici le classement des vidéos publiées récemment par vos chaînes favorites, triées par ordre d'intérêt.\n\n")
        out.write("| Rang | Chaîne | Catégorie | Vidéo | Résumé | Intérêt |\n")
        out.write("| :---: | :--- | :---: | :--- | :--- | :---: |\n")
        for idx, vid in enumerate(videos, 1):
            out.write(f"| {idx} | **{vid['channel_name']}** | {vid['category']} | [{vid['title']}]({vid['url']}) | {vid['summary']} | **{vid['score']}/10** |\n")
            
    print(f"Rapport Markdown enregistré dans : {OUTPUT_MD}")

if __name__ == "__main__":
    main()
