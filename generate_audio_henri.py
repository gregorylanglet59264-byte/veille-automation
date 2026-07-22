# -*- coding: utf-8 -*-
"""
generate_audio_henri.py
Génère le podcast MP3 final de la veille globale à l'aide d'edge_tts
avec la voix neuronale fr-FR-HenriNeural à une vitesse ralentie de -10%,
en mixant une musique de fond si disponible via ffmpeg.
"""
import os
import re
import asyncio
import subprocess

import datetime
import argparse

async def main():
    parser = argparse.ArgumentParser(description="Génère le podcast MP3 final d'une veille à l'aide d'edge_tts")
    parser.add_argument("--script", type=str, help="Chemin complet du fichier script texte")
    parser.add_argument("--output", type=str, help="Chemin complet du fichier MP3 final de sortie")
    args = parser.parse_args()
    
    scratch_dir = r"C:\Users\grego\.gemini\antigravity\scratch"
    
    script_path = args.script
    if not script_path:
        # Essayer de trouver le script du jour ou fallback sur le 19 juillet
        today_str = datetime.datetime.now().strftime("%Y_%m_%d")
        today_script = os.path.join(scratch_dir, f"veille_complete_script_{today_str}.txt")
        if os.path.exists(today_script):
            script_path = today_script
        else:
            script_path = os.path.join(scratch_dir, "veille_complete_script_2026_07_19.txt")
            
    dest_mp3 = args.output
    if not dest_mp3:
        basename = os.path.basename(script_path)
        if "veille_complete_script" in basename:
            dest_mp3 = os.path.join(scratch_dir, "veille_globale_henri.mp3")
        else:
            # Dériver le nom (ex: veille_ia_script_2026_07_22.txt -> veille_ia_henri.mp3)
            name_part = basename.replace("_script", "").replace(".txt", "")
            dest_mp3 = os.path.join(scratch_dir, f"{name_part}_henri.mp3")
            
    raw_mp3 = os.path.join(scratch_dir, "raw_voice.mp3")
    
    # Résolution dynamique de la musique de fond
    bg_music_options = [
        r"C:\Users\grego\Documents\METEO_CLIMAT\veille-automation\assets\musique_de_fond.mp3",
        r"C:\Users\grego\Documents\METEO_CLIMAT\desktop_assets\A_CONSERVER_ABSOLUMENT\musique de fond.mp3",
        r"C:\Users\grego\Documents\METEO_CLIMAT\meteo cnews 2\A_CONSERVER_ABSOLUMENT\musique de fond.mp3",
        r"C:\Users\grego\Documents\METEO_CLIMAT\meteo-kappa\meteo_cnews_2\A_CONSERVER_ABSOLUMENT\musique de fond.mp3"
    ]
    bg_music = next((p for p in bg_music_options if os.path.exists(p)), bg_music_options[0])
    
    if not os.path.exists(script_path):
        print(f"Erreur : Le fichier script est introuvable à {script_path}")
        return
        
    print(f"[Henri Audio] Lecture du script : {script_path}")
    with open(script_path, "r", encoding="utf-8") as f:
        text = f.read()
        
    # Nettoyage du texte pour la voix de synthèse :
    # 1. Enlever les séparateurs physiques du type =============
    clean_text = re.sub(r'=+', '', text)
    # 2. Enlever les indications de jingles ou effets entre parenthèses
    clean_text = re.sub(r'\(JINGLE[^\)]*\)', '', clean_text)
    clean_text = re.sub(r'\(Pause[^\)]*\)', '', clean_text)
    clean_text = re.sub(r'\([^\)]*SONORE[^\)]*\)', '', clean_text)
    # 3. Remplacer les retours à la ligne multiples pour éviter trop de silences prolongés
    clean_text = re.sub(r'\n\s*\n', '\n', clean_text)
    clean_text = clean_text.strip()
    
    print("[Henri Audio] Lancement d'edge-tts (voix fr-FR-HenriNeural, vitesse -10%)...")
    try:
        import edge_tts
        communicate = edge_tts.Communicate(clean_text, "fr-FR-HenriNeural", rate="-10%")
        await communicate.save(raw_mp3)
        print(f"[Henri Audio] Fichier brut de voix généré : {raw_mp3}")
        
        # Mixage de la musique de fond s'il existe et si ffmpeg est installé
        mixed = False
        if os.path.exists(bg_music):
            print(f"[Henri Audio] Musique de fond détectée à {bg_music}. Tentative de mixage avec ffmpeg...")
            try:
                # Commande de mixage ffmpeg
                cmd = [
                    "ffmpeg", "-y", "-i", raw_mp3, "-stream_loop", "-1", "-i", bg_music,
                    "-filter_complex", "[0:a]volume=1.0[v];[1:a]volume=0.06[m];[v][m]amix=inputs=2:duration=first[a]",
                    "-map", "[a]", dest_mp3
                ]
                subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                print(f"[Henri Audio] Mixage finalisé avec succès sur {dest_mp3}")
                mixed = True
            except Exception as ffmpeg_err:
                print(f"[Henri Audio] Échec du mixage ffmpeg (sera ignoré) : {ffmpeg_err}")
                
        if not mixed:
            # Si pas de mixage, on déplace le brut vers la destination finale
            if os.path.exists(dest_mp3):
                os.remove(dest_mp3)
            os.rename(raw_mp3, dest_mp3)
            print(f"[Henri Audio] Fichier final copié : {dest_mp3}")
            
        # Nettoyage du fichier temporaire
        if os.path.exists(raw_mp3):
            os.remove(raw_mp3)
            
        print("[Henri Audio] Processus terminé avec succès !")
    except ImportError:
        print("Erreur : La bibliothèque 'edge_tts' n'est pas installée dans l'environnement Python.")
    except Exception as e:
        print(f"Erreur globale lors de la génération audio : {e}")

if __name__ == "__main__":
    asyncio.run(main())
