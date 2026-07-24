import urllib.request
import urllib.error
import re
import sys
import os
import json
import base64
import uuid
import datetime
import smtplib
from email.utils import formatdate

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

import socket
import time

socket.setdefaulttimeout(10)

INDEX_URL = "https://forums.infoclimat.fr/f/forum/20-evolution-%C3%A0-plus-long-terme/"
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'

def fetch_url(url, timeout=8):
    req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return response.read().decode('utf-8', errors='ignore')

def call_llm(system_prompt, user_prompt, max_retries=3):
    openrouter_key = os.environ.get("OPENROUTER_API_KEY", "").replace('\ufeff', '').strip()
    if not openrouter_key:
        print("[LLM] ERREUR : OPENROUTER_API_KEY non configurée.")
        return None
    
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {openrouter_key}"
    }
    payload = {
        "model": "deepseek/deepseek-v4-flash",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    }
    
    for attempt in range(1, max_retries + 1):
        print(f"[LLM] Tentative {attempt}/{max_retries} — DeepSeek V4 Flash via OpenRouter...")
        try:
            req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=120) as response:
                res_data = json.loads(response.read().decode("utf-8"))
                text = res_data["choices"][0]["message"]["content"]
                return text.replace('\ufeff', '').replace('\ufffe', '')
        except urllib.error.HTTPError as http_err:
            print(f"[LLM] Tentative {attempt} échouée : HTTP {http_err.code}")
        except Exception as e:
            print(f"[LLM] Tentative {attempt} échouée : {e}")
        
        if attempt < max_retries:
            time.sleep(5 * attempt)
            
    return None


def process_topic(topic_url, topic_idx, date_context_str):
    print(f"\n--- Sujet [{topic_idx+1}] : {topic_url} ---")
    
    # 1. Charger le titre et la pagination du sujet
    try:
        html_first = fetch_url(topic_url)
    except Exception as e:
        print(f"Erreur chargement sujet : {e}")
        return None
        
    topic_title_match = re.search(r'<h1[^>]*class=["\']ipsType_pageTitle[^>]*>(.*?)</h1>', html_first, re.DOTALL)
    topic_title_clean = "Sujet de prévisions"
    if topic_title_match:
        topic_title_clean = re.sub(r'<[^>]+>', '', topic_title_match.group(1)).strip()
        topic_title_clean = re.sub(r'\s+', ' ', topic_title_clean)
        
    print(f"[{topic_idx+1}] Analyse de la pagination...")
    pages = [1]
    pagination_match = re.search(r'class=["\']ipsPagination_pageList["\']>(.*?)</ul>', html_first, re.DOTALL)
    if pagination_match:
        page_nums = re.findall(r'data-page=["\'](\d+)["\']', pagination_match.group(1))
        if page_nums:
            pages = sorted(list(set(int(p) for p in page_nums)))
            
    print(f"[{topic_idx+1}] Pages détectées : {len(pages)}")
    
    # Charger les 3 dernières pages pour avoir les commentaires récents
    pages_to_load = pages[-3:] if len(pages) >= 3 else pages
    all_comments = []
    all_authors = []
    
    print(f"[{topic_idx+1}] Chargement des commentaires des pages {pages_to_load[0]} à {pages_to_load[-1]}...")
    for page in pages_to_load:
        page_url = f"{topic_url}?page={page}"
        try:
            html_page = fetch_url(page_url)
            page_comments = re.findall(r'<div[^>]*data-role=["\']commentContent["\'][^>]*>(.*?)</div>\s*</div>', html_page, re.DOTALL)
            page_authors = re.findall(r'<strong>\s*<a href=[^>]*class=["\']ipsType_break["\'][^>]*>(.*?)</a>', html_page)
            all_comments.extend(page_comments)
            all_authors.extend(page_authors)
        except Exception as e:
            print(f"Erreur page {page} : {e}")
            
    # Nettoyer les commentaires pour l'IA
    cleaned_comments_data = []
    for idx, comment in enumerate(all_comments):
        clean_comment = re.sub(r'<br\s*/?>', '\n', comment)
        clean_comment = re.sub(r'<[^>]+>', '', clean_comment).strip()
        clean_comment = re.sub(r'\n\s*\n', '\n', clean_comment)
        author = all_authors[idx] if idx < len(all_authors) else "Membre"
        cleaned_comments_data.append(f"Auteur: {author}\nMessage:\n{clean_comment}")
        
    # Garder les 20 derniers messages pour l'analyse
    recent_messages_text = "\n\n=======================\n\n".join(cleaned_comments_data[-20:])
    
    # Extraire et télécharger les graphiques candidats
    print(f"[{topic_idx+1}] Extraction des graphiques...")
    candidate_imgs = []
    seen_imgs = set()
    for comment in all_comments:
        imgs = re.findall(r'<img[^>]+src=["\'](https?://[^"\']+)["\']', comment)
        for img in imgs:
            if any(x in img.lower() for x in ["emoji", "theme", "reactions", "avatar", "profile", "default", "giphy"]):
                continue
            if img not in seen_imgs:
                seen_imgs.add(img)
                priority = 2 if "uploads/monthly_" in img else 1
                candidate_imgs.append((img, priority))
                
    candidate_imgs.sort(key=lambda x: x[1], reverse=True)
    
    os.makedirs("candidates", exist_ok=True)
    downloaded_images = []
    for idx, (img_url, prio) in enumerate(candidate_imgs[:3]):
        ext = "png"
        if ".gif" in img_url.lower(): ext = "gif"
        elif ".jpg" in img_url.lower() or ".jpeg" in img_url.lower(): ext = "jpg"
        
        dest_file = f"candidates/topic_{topic_idx+1}_candidate_{idx+1}.{ext}"
        print(f"[{topic_idx+1}] Téléchargement graphique {idx+1} : {img_url} -> {dest_file}")
        try:
            req = urllib.request.Request(img_url, headers={'User-Agent': USER_AGENT})
            with urllib.request.urlopen(req, timeout=6) as img_resp:
                with open(dest_file, 'wb') as f_out:
                    f_out.write(img_resp.read())
            downloaded_images.append(dest_file)
        except Exception as e:
            print(f"Erreur téléchargement graphique {idx+1} : {e}")

    # Appeler l'IA pour l'analyse des scénarios et la rédaction du pack réseaux sociaux
    print(f"[{topic_idx+1}] Appel de l'IA pour l'analyse des scénarios météo...")
    system_prompt = """Tu es Patrick Marlière, météorologue expert de renommée nationale pour Monsieur Météo.

MISSION
À partir EXCLUSIVEMENT des discussions et analyses météorologiques fournies en entrée, tu dois produire un objet JSON structuré représentant le bulletin d'analyse météorologique national (France) et les déclinaisons pour les 13 régions métropolitaines suivantes :
- auvergne_rhone_alpes
- bourgogne_franche_comte
- bretagne
- centre_val_de_loire
- corse
- grand_est
- hauts_de_france
- ile_de_france
- normandie
- nouvelle_aquitaine
- occitanie
- pays_de_la_loire
- provence_alpes_cote_azur

RÈGLES D'OR ABSOLUES :
1. NE RIEN INVENTER. Si une information (température, risque, date, impact, etc.) n'est pas explicitement mentionnée ou déductible sans ambiguïté des sources pour une région donnée, écris obligatoirement "Information non précisée dans les sources" pour ce champ. Ne déduis jamais une tendance régionale à partir d'un élément uniquement national si le texte ne le justifie pas.
2. DATES EXACTES : Associe toujours les jours aux dates exactes (ex: Lundi 27 Juillet).
3. EXCLUSION DES JOURS PASSÉS : Conforme-toi à la "Date actuelle de génération" transmise dans l'invite.
4. TEMPÉRATURES RÉGIONALES : Les températures régionales doivent correspondre aux valeurs réelles mentionnées pour cette région dans les messages du forum. Si aucune valeur n'est donnée, écris "Information non précisée dans les sources".
5. IMPACTS GÉOLOCALISÉS : Pour chaque impact sectoriel régional, mentionne la localisation précise (ex: "Risque de fortes chaleurs principalement dans le sud de la région" ou "Impact non identifié dans les sources pour cette région").

FORMAT DE SORTIE JSON OBLIGATOIRE :
Renvoyez uniquement un objet JSON valide contenant la structure suivante. Pas de texte explicatif avant ou après le JSON.

{{
  "title_line1": "Semaine X - Du Lundi DD au Dimanche DD Mois AAAA",
  "title_line2": "Accroche météo courte résumant le temps de la semaine",
  "key_numbers": "Chiffre 1 | Libellé 1\nChiffre 2 | Libellé 2",
  "france": {{
    "alert": {{
      "level": "Vert|Jaune|Orange|Rouge",
      "event_type": "...",
      "start": "...",
      "end": "...",
      "confidence": "..."
    }},
    "kpis": {{
      "temp_range": "38 à 42 °C (ou jusqu'à 42 °C localement)",
      "period": "Du 27 Juillet au 2 Août",
      "duration": "6 jours",
      "confidence": "4/5 (Élevée)",
      "risks": "Canicule, orages",
      "zone": "Axe Sud-Ouest / Nord-Est"
    }},
    "takeaways_10s": [
      "Phrase 1 (une ligne max)",
      "Phrase 2 (une ligne max)",
      "Phrase 3 (une ligne max)",
      "Phrase 4 (une ligne max)"
    ],
    "dashboard": {{
      "score_heat": "3/5",
      "interp_heat": "Situation exceptionnelle",
      "score_rain": "1/5",
      "interp_rain": "Situation normale",
      "score_storm": "4/5",
      "interp_storm": "Risque élevé",
      "score_wind": "2/5",
      "interp_wind": "Risque faible"
    }},
    "impacts": {{
      "population": "...",
      "travel": "...",
      "work": "...",
      "agri": "...",
      "storm": "...",
      "drought": "..."
    }},
    "timeline": {{
      "date_debut": "Lundi 27 Juillet", "desc_debut": "...",
      "date_montee": "Mardi 28 Juillet", "desc_montee": "...",
      "date_pic": "Jeudi 30 Juillet", "desc_pic": "...",
      "date_fin": "Dimanche 2 Août", "desc_fin": "..."
    }},
    "regional": {{
      "hdf_north": "22 à 26 °C | Faible | Aucun | 4/5",
      "atlantic": "24 à 28 °C | Modéré | Vent | 4/5",
      "central": "28 à 32 °C | Faible | Chaleur | 4/5",
      "south": "35 à 40 °C | Faible | Canicule | 4/5",
      "mediterranean": "32 à 36 °C | Faible | Vent | 4/5",
      "mountains": "20 à 25 °C | Modéré | Orages | 3/5"
    }},
    "scenarios": {{
      "majoritaire": {{"prob": "65%", "title": "...", "desc": "..."}},
      "median": {{"prob": "25%", "title": "...", "desc": "..."}},
      "minoritaire": {{"prob": "10%", "title": "...", "desc": "..."}}
    }},
    "key_uncertainties": "- Incertitude 1\n- Incertitude 2",
    "monitoring_points": "- Point 1\n- Point 2",
    "key_takeaways": "- Takeaway 1\n- Takeaway 2",
    "social_pack": {{
      "linkedin": "...",
      "facebook": "...",
      "twitter": "...",
      "tiktok": "...",
      "instagram": "..."
    }}
  }},
  "regions": {{
    "auvergne_rhone_alpes": {{
      "alert_level": "Vert|Jaune|Orange|Rouge",
      "event_type": "...",
      "kpis": {{
        "temp_range": "...",
        "period": "...",
        "duration": "...",
        "confidence": "...",
        "risks": "...",
        "zone": "..."
      }},
      "takeaways_10s": ["...", "..."],
      "dashboard": {{
        "score_heat": "3/5", "interp_heat": "...",
        "score_rain": "1/5", "interp_rain": "...",
        "score_storm": "2/5", "interp_storm": "...",
        "score_wind": "1/5", "interp_wind": "..."
      }},
      "impacts": {{
        "population": "...",
        "travel": "...",
        "work": "...",
        "agri": "...",
        "storm": "...",
        "drought": "..."
      }},
      "timeline": {{
        "date_debut": "...", "desc_debut": "...",
        "date_montee": "...", "desc_montee": "...",
        "date_pic": "...", "desc_pic": "...",
        "date_fin": "...", "desc_fin": "..."
      }}
    }},
    "bourgogne_franche_comte": {{
      "alert_level": "Vert|Jaune|Orange|Rouge",
      "event_type": "...",
      "kpis": {{
        "temp_range": "...",
        "period": "...",
        "duration": "...",
        "confidence": "...",
        "risks": "...",
        "zone": "..."
      }},
      "takeaways_10s": ["...", "..."],
      "dashboard": {{
        "score_heat": "1/5", "interp_heat": "...",
        "score_rain": "1/5", "interp_rain": "...",
        "score_storm": "1/5", "interp_storm": "...",
        "score_wind": "1/5", "interp_wind": "..."
      }},
      "impacts": {{
        "population": "...",
        "travel": "...",
        "work": "...",
        "agri": "...",
        "storm": "...",
        "drought": "..."
      }},
      "timeline": {{
        "date_debut": "...", "desc_debut": "...",
        "date_montee": "...", "desc_montee": "...",
        "date_pic": "...", "desc_pic": "...",
        "date_fin": "...", "desc_fin": "..."
      }}
    }},
    "bretagne": {{
      "alert_level": "Vert|Jaune|Orange|Rouge",
      "event_type": "...",
      "kpis": {{
        "temp_range": "...",
        "period": "...",
        "duration": "...",
        "confidence": "...",
        "risks": "...",
        "zone": "..."
      }},
      "takeaways_10s": ["...", "..."],
      "dashboard": {{
        "score_heat": "1/5", "interp_heat": "...",
        "score_rain": "1/5", "interp_rain": "...",
        "score_storm": "1/5", "interp_storm": "...",
        "score_wind": "1/5", "interp_wind": "..."
      }},
      "impacts": {{
        "population": "...",
        "travel": "...",
        "work": "...",
        "agri": "...",
        "storm": "...",
        "drought": "..."
      }},
      "timeline": {{
        "date_debut": "...", "desc_debut": "...",
        "date_montee": "...", "desc_montee": "...",
        "date_pic": "...", "desc_pic": "...",
        "date_fin": "...", "desc_fin": "..."
      }}
    }},
    "centre_val_de_loire": {{
      "alert_level": "Vert|Jaune|Orange|Rouge",
      "event_type": "...",
      "kpis": {{
        "temp_range": "...",
        "period": "...",
        "duration": "...",
        "confidence": "...",
        "risks": "...",
        "zone": "..."
      }},
      "takeaways_10s": ["...", "..."],
      "dashboard": {{
        "score_heat": "1/5", "interp_heat": "...",
        "score_rain": "1/5", "interp_rain": "...",
        "score_storm": "1/5", "interp_storm": "...",
        "score_wind": "1/5", "interp_wind": "..."
      }},
      "impacts": {{
        "population": "...",
        "travel": "...",
        "work": "...",
        "agri": "...",
        "storm": "...",
        "drought": "..."
      }},
      "timeline": {{
        "date_debut": "...", "desc_debut": "...",
        "date_montee": "...", "desc_montee": "...",
        "date_pic": "...", "desc_pic": "...",
        "date_fin": "...", "desc_fin": "..."
      }}
    }},
    "corse": {{
      "alert_level": "Vert|Jaune|Orange|Rouge",
      "event_type": "...",
      "kpis": {{
        "temp_range": "...",
        "period": "...",
        "duration": "...",
        "confidence": "...",
        "risks": "...",
        "zone": "..."
      }},
      "takeaways_10s": ["...", "..."],
      "dashboard": {{
        "score_heat": "1/5", "interp_heat": "...",
        "score_rain": "1/5", "interp_rain": "...",
        "score_storm": "1/5", "interp_storm": "...",
        "score_wind": "1/5", "interp_wind": "..."
      }},
      "impacts": {{
        "population": "...",
        "travel": "...",
        "work": "...",
        "agri": "...",
        "storm": "...",
        "drought": "..."
      }},
      "timeline": {{
        "date_debut": "...", "desc_debut": "...",
        "date_montee": "...", "desc_montee": "...",
        "date_pic": "...", "desc_pic": "...",
        "date_fin": "...", "desc_fin": "..."
      }}
    }},
    "grand_est": {{
      "alert_level": "Vert|Jaune|Orange|Rouge",
      "event_type": "...",
      "kpis": {{
        "temp_range": "...",
        "period": "...",
        "duration": "...",
        "confidence": "...",
        "risks": "...",
        "zone": "..."
      }},
      "takeaways_10s": ["...", "..."],
      "dashboard": {{
        "score_heat": "1/5", "interp_heat": "...",
        "score_rain": "1/5", "interp_rain": "...",
        "score_storm": "1/5", "interp_storm": "...",
        "score_wind": "1/5", "interp_wind": "..."
      }},
      "impacts": {{
        "population": "...",
        "travel": "...",
        "work": "...",
        "agri": "...",
        "storm": "...",
        "drought": "..."
      }},
      "timeline": {{
        "date_debut": "...", "desc_debut": "...",
        "date_montee": "...", "desc_montee": "...",
        "date_pic": "...", "desc_pic": "...",
        "date_fin": "...", "desc_fin": "..."
      }}
    }},
    "hauts_de_france": {{
      "alert_level": "Vert|Jaune|Orange|Rouge",
      "event_type": "...",
      "kpis": {{
        "temp_range": "...",
        "period": "...",
        "duration": "...",
        "confidence": "...",
        "risks": "...",
        "zone": "..."
      }},
      "takeaways_10s": ["...", "..."],
      "dashboard": {{
        "score_heat": "1/5", "interp_heat": "...",
        "score_rain": "1/5", "interp_rain": "...",
        "score_storm": "1/5", "interp_storm": "...",
        "score_wind": "1/5", "interp_wind": "..."
      }},
      "impacts": {{
        "population": "...",
        "travel": "...",
        "work": "...",
        "agri": "...",
        "storm": "...",
        "drought": "..."
      }},
      "timeline": {{
        "date_debut": "...", "desc_debut": "...",
        "date_montee": "...", "desc_montee": "...",
        "date_pic": "...", "desc_pic": "...",
        "date_fin": "...", "desc_fin": "..."
      }}
    }},
    "ile_de_france": {{
      "alert_level": "Vert|Jaune|Orange|Rouge",
      "event_type": "...",
      "kpis": {{
        "temp_range": "...",
        "period": "...",
        "duration": "...",
        "confidence": "...",
        "risks": "...",
        "zone": "..."
      }},
      "takeaways_10s": ["...", "..."],
      "dashboard": {{
        "score_heat": "1/5", "interp_heat": "...",
        "score_rain": "1/5", "interp_rain": "...",
        "score_storm": "1/5", "interp_storm": "...",
        "score_wind": "1/5", "interp_wind": "..."
      }},
      "impacts": {{
        "population": "...",
        "travel": "...",
        "work": "...",
        "agri": "...",
        "storm": "...",
        "drought": "..."
      }},
      "timeline": {{
        "date_debut": "...", "desc_debut": "...",
        "date_montee": "...", "desc_montee": "...",
        "date_pic": "...", "desc_pic": "...",
        "date_fin": "...", "desc_fin": "..."
      }}
    }},
    "normandie": {{
      "alert_level": "Vert|Jaune|Orange|Rouge",
      "event_type": "...",
      "kpis": {{
        "temp_range": "...",
        "period": "...",
        "duration": "...",
        "confidence": "...",
        "risks": "...",
        "zone": "..."
      }},
      "takeaways_10s": ["...", "..."],
      "dashboard": {{
        "score_heat": "1/5", "interp_heat": "...",
        "score_rain": "1/5", "interp_rain": "...",
        "score_storm": "1/5", "interp_storm": "...",
        "score_wind": "1/5", "interp_wind": "..."
      }},
      "impacts": {{
        "population": "...",
        "travel": "...",
        "work": "...",
        "agri": "...",
        "storm": "...",
        "drought": "..."
      }},
      "timeline": {{
        "date_debut": "...", "desc_debut": "...",
        "date_montee": "...", "desc_montee": "...",
        "date_pic": "...", "desc_pic": "...",
        "date_fin": "...", "desc_fin": "..."
      }}
    }},
    "nouvelle_aquitaine": {{
      "alert_level": "Vert|Jaune|Orange|Rouge",
      "event_type": "...",
      "kpis": {{
        "temp_range": "...",
        "period": "...",
        "duration": "...",
        "confidence": "...",
        "risks": "...",
        "zone": "..."
      }},
      "takeaways_10s": ["...", "..."],
      "dashboard": {{
        "score_heat": "1/5", "interp_heat": "...",
        "score_rain": "1/5", "interp_rain": "...",
        "score_storm": "1/5", "interp_storm": "...",
        "score_wind": "1/5", "interp_wind": "..."
      }},
      "impacts": {{
        "population": "...",
        "travel": "...",
        "work": "...",
        "agri": "...",
        "storm": "...",
        "drought": "..."
      }},
      "timeline": {{
        "date_debut": "...", "desc_debut": "...",
        "date_montee": "...", "desc_montee": "...",
        "date_pic": "...", "desc_pic": "...",
        "date_fin": "...", "desc_fin": "..."
      }}
    }},
    "occitanie": {{
      "alert_level": "Vert|Jaune|Orange|Rouge",
      "event_type": "...",
      "kpis": {{
        "temp_range": "...",
        "period": "...",
        "duration": "...",
        "confidence": "...",
        "risks": "...",
        "zone": "..."
      }},
      "takeaways_10s": ["...", "..."],
      "dashboard": {{
        "score_heat": "1/5", "interp_heat": "...",
        "score_rain": "1/5", "interp_rain": "...",
        "score_storm": "1/5", "interp_storm": "...",
        "score_wind": "1/5", "interp_wind": "..."
      }},
      "impacts": {{
        "population": "...",
        "travel": "...",
        "work": "...",
        "agri": "...",
        "storm": "...",
        "drought": "..."
      }},
      "timeline": {{
        "date_debut": "...", "desc_debut": "...",
        "date_montee": "...", "desc_montee": "...",
        "date_pic": "...", "desc_pic": "...",
        "date_fin": "...", "desc_fin": "..."
      }}
    }},
    "pays_de_la_loire": {{
      "alert_level": "Vert|Jaune|Orange|Rouge",
      "event_type": "...",
      "kpis": {{
        "temp_range": "...",
        "period": "...",
        "duration": "...",
        "confidence": "...",
        "risks": "...",
        "zone": "..."
      }},
      "takeaways_10s": ["...", "..."],
      "dashboard": {{
        "score_heat": "1/5", "interp_heat": "...",
        "score_rain": "1/5", "interp_rain": "...",
        "score_storm": "1/5", "interp_storm": "...",
        "score_wind": "1/5", "interp_wind": "..."
      }},
      "impacts": {{
        "population": "...",
        "travel": "...",
        "work": "...",
        "agri": "...",
        "storm": "...",
        "drought": "..."
      }},
      "timeline": {{
        "date_debut": "...", "desc_debut": "...",
        "date_montee": "...", "desc_montee": "...",
        "date_pic": "...", "desc_pic": "...",
        "date_fin": "...", "desc_fin": "..."
      }}
    }},
    "provence_alpes_cote_azur": {{
      "alert_level": "Vert|Jaune|Orange|Rouge",
      "event_type": "...",
      "kpis": {{
        "temp_range": "...",
        "period": "...",
        "duration": "...",
        "confidence": "...",
        "risks": "...",
        "zone": "..."
      }},
      "takeaways_10s": ["...", "..."],
      "dashboard": {{
        "score_heat": "1/5", "interp_heat": "...",
        "score_rain": "1/5", "interp_rain": "...",
        "score_storm": "1/5", "interp_storm": "...",
        "score_wind": "1/5", "interp_wind": "..."
      }},
      "impacts": {{
        "population": "...",
        "travel": "...",
        "work": "...",
        "agri": "...",
        "storm": "...",
        "drought": "..."
      }},
      "timeline": {{
        "date_debut": "...", "desc_debut": "...",
        "date_montee": "...", "desc_montee": "...",
        "date_pic": "...", "desc_pic": "...",
        "date_fin": "...", "desc_fin": "..."
      }}
    }}
  }}
}}

Rédige pour TOUTES les 13 régions sans en omettre aucune dans la clé 'regions'. Si aucune information n'existe, remplis avec la valeur 'Information non précisée dans les sources' pour les champs textes et 'Vert' pour alert_level. Sans aucun blabla d'introduction ou de conclusion."""

    user_prompt = f"""Contexte de date : {date_context_str}

Voici les 20 derniers messages des prévisionnistes pour le sujet : {topic_title_clean}

{recent_messages_text}

Analyse ces discussions en appliquant scrupuleusement la vérification de cohérence et génère le rapport au format JSON spécifié."""

    data = None
    curr_user_prompt = user_prompt
    for attempt in range(1, 4):
        response = call_llm(system_prompt, curr_user_prompt)
        if not response:
            continue
        try:
            print(f"[{topic_idx+1}] Extraction du JSON (Tentative {attempt}/3)...")
            match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
            if match:
                json_str = match.group(1)
            else:
                start_idx = response.find('{')
                end_idx = response.rfind('}')
                if start_idx != -1 and end_idx != -1:
                    json_str = response[start_idx:end_idx+1]
                else:
                    json_str = response
            
            data = json.loads(json_str)
            print(f"[{topic_idx+1}] Parsing JSON réussi avec succès !")
            break
        except Exception as e:
            print(f"Erreur parsing JSON (Tentative {attempt}/3) : {e}")
            if attempt == 3:
                print(f"Réponse brute de l'IA lors de l'échec final : {response[:1000]}...")
            else:
                curr_user_prompt = user_prompt + f"\n\n[ERREUR CONSTATÉE] Lors de la tentative précédente, le format JSON généré était invalide : {e}. Veille absolument à générer un JSON valide avec toutes les virgules fermées et sans aucun guillemet non échappé."
            
    return {"data": data, "images": downloaded_images}
def main():
    def parse_region_line(region_str):
        if not region_str:
            return ["-", "-", "-", "-"]
        parts = [p.strip() for p in region_str.split("|")]
        while len(parts) < 4:
            parts.append("-")
        return parts[:4]

    def parse_score(val):
        if not val:
            return 0
        match = re.search(r'(\d+)', val)
        if match:
            num = int(match.group(1))
            if num <= 5:
                return num
            elif num <= 100:
                return round(num / 20)
        return 0

    def extract_emoji_and_text(text_str):
        if not text_str:
            return "🌤️", "-"
        emoji_match = re.match(r'^([𐀀-􏿿☀-⟿⭐⬆←-⇿⛅⛈⚡☂☁☀]+)\s*(.*)', text_str)
        if emoji_match:
            return emoji_match.group(1), emoji_match.group(2)
        return "🌤️", text_str

    def get_score_label(score_val):
        score = parse_score(score_val)
        labels = {
            0: "Très faible",
            1: "Très faible",
            2: "Faible",
            3: "Modéré",
            4: "Élevé",
            5: "Très élevé"
        }
        return labels.get(score, "Modéré")

    def get_level_badge(val):
        val_clean = val.strip().lower()
        if "très fort" in val_clean or "tres fort" in val_clean:
            return '<span class="badge-level-tres-fort">🔴 Très fort</span>'
        elif "fort" in val_clean:
            return '<span class="badge-level-fort">🟠 Fort</span>'
        elif "modéré" in val_clean or "modere" in val_clean:
            return '<span class="badge-level-modere">🟡 Modéré</span>'
        elif "très faible" in val_clean or "tres faible" in val_clean:
            return '<span class="badge-level-tres-faible">⚪ Très faible</span>'
        elif "faible" in val_clean:
            return '<span class="badge-level-faible">🔵 Faible</span>'
        else:
            return f'<span class="badge-level-modere">{val}</span>'

    def get_conf_badge(val):
        val_clean = val.strip().lower()
        if "5/5" in val_clean or "très élevé" in val_clean:
            return '<span class="badge-level-tres-fort" style="background:#d1fae5; color:#065f46;">🟢 Très élevé</span>'
        elif "4/5" in val_clean or "élevé" in val_clean:
            return '<span class="badge-level-fort" style="background:#d1fae5; color:#065f46;">🟢 Élevé</span>'
        elif "3/5" in val_clean or "modéré" in val_clean:
            return '<span class="badge-level-modere" style="background:#fef3c7; color:#92400e;">🟡 Modéré</span>'
        elif "2/5" in val_clean or "faible" in val_clean:
            return '<span class="badge-level-faible" style="background:#fee2e2; color:#991b1b;">🔴 Faible</span>'
        elif "1/5" in val_clean or "très faible" in val_clean:
            return '<span class="badge-level-tres-faible" style="background:#fee2e2; color:#991b1b;">🔴 Très faible</span>'
        else:
            return f'<span class="badge-level-modere" style="background:#f1f5f9; color:#475569;">{val}</span>'

    def get_badge_color_class(label):
        l = label.lower()
        if "très élevé" in l or "très fort" in l:
            return "background-color: #dc2626;"
        elif "élevé" in l or "fort" in l:
            return "background-color: #ea580c;"
        elif "modéré" in l:
            return "background-color: #eab308;"
        elif "faible" in l:
            return "background-color: #2563eb;"
        else:
            return "background-color: #6b7280;"

    print(f"1. Chargement de l'index du forum : {INDEX_URL}")
    try:
        html_index = fetch_url(INDEX_URL)
    except Exception as e:
        print(f"Erreur index : {e}")
        sys.exit(1)
        
    topic_links = re.findall(r'href=["\'](https://forums.infoclimat.fr/f/topic/\d+-[^"\']+)["\']', html_index)
    
    # Élimination des doublons et filtrage des prévisions
    clean_topics = []
    seen = set()
    for link in topic_links:
        base_link = link.split('?')[0].strip()
        if base_link not in seen and ("previsions" in base_link or "pr%C3%A9visions" in base_link or "semaine" in base_link):
            seen.add(base_link)
            clean_topics.append(base_link)
            
    if not clean_topics:
        print("Aucun sujet de prévisions trouvé.")
        sys.exit(1)
        
    # Calcul dynamique des dates de référence en français
    now = datetime.datetime.now()
    DAYS_FR = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
    MONTHS_FR = ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin", "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"]
    
    def get_french_date(dt):
        return f"{DAYS_FR[dt.weekday()]} {dt.day} {MONTHS_FR[dt.month - 1]} {dt.year}"
        
    def fmt_date_range(d1, d2):
        m1 = MONTHS_FR[d1.month - 1]
        m2 = MONTHS_FR[d2.month - 1]
        if m1 == m2:
            return f"du Lundi {d1.day} au Dimanche {d2.day} {m1} {d1.year}"
        else:
            return f"du Lundi {d1.day} {m1} au Dimanche {d2.day} {m2} {d1.year}"
            
    lundi_cours = now - datetime.timedelta(days=now.weekday())
    dimanche_cours = lundi_cours + datetime.timedelta(days=6)
    lundi_suiv = lundi_cours + datetime.timedelta(days=7)
    dimanche_suiv = lundi_suiv + datetime.timedelta(days=6)
    
    today_str = get_french_date(now)
    semaine_cours_str = fmt_date_range(lundi_cours, dimanche_cours)
    semaine_suivante_str = fmt_date_range(lundi_suiv, dimanche_suiv)
    jours_restants_cours_str = f"du {DAYS_FR[now.weekday()]} {now.day} {MONTHS_FR[now.month-1]} au Dimanche {dimanche_cours.day} {MONTHS_FR[dimanche_cours.month-1]} {dimanche_cours.year}"

    # Semaine future en premier, Semaine en cours en second
    topics_to_process = []
    if len(clean_topics) >= 2:
        topics_to_process = [
            (clean_topics[0], "future", f"Date actuelle de génération : {today_str}\nType de semaine : Semaine suivante (Tendance à moyen terme)\nPériode à analyser : {semaine_suivante_str} (semaine complète)."),
            (clean_topics[1], "cours", f"Date actuelle de génération : {today_str}\nType de semaine : Semaine en cours\nPériode à analyser : {jours_restants_cours_str} (jours restants uniquement). Les journées antérieures au {today_str} sont déjà passées, concentre-toi sur la fin de semaine.")
        ]
    else:
        topics_to_process = [
            (clean_topics[0], "cours", f"Date actuelle de génération : {today_str}\nSemaine en cours : {semaine_cours_str} (jours restants à prévoir : {jours_restants_cours_str})\nSemaine suivante : {semaine_suivante_str}.\nDétermine selon le titre du sujet s'il s'agit de la semaine en cours ou de la semaine suivante, et applique les règles correspondantes.")
        ]
        
    results = []
    for idx, (topic, sem_type, date_context) in enumerate(topics_to_process):
        res = process_topic(topic, idx, date_context)
        if res and res.get("data"):
            results.append(res)
            
    if not results:
        print("Aucun sujet n'a pu être traité.")
        sys.exit(1)
        
    # Style CSS Premium & Responsive (Design System v5)
    style = """
    :root {
        --font-sans: 'Segoe UI', system-ui, -apple-system, sans-serif;
        --text-xs: 11px;
        --text-sm: 13px;
        --text-base: 14.5px;
        --text-lg: 16px;
        --text-xl: 20px;
        --radius-lg: 24px;
        --radius-md: 16px;
        --radius-sm: 10px;
        --spacing-xs: 10px;
        --spacing-sm: 15px;
        --spacing-md: 24px;
        --spacing-lg: 35px;
        --shadow-sm: 0 2px 8px rgba(0,0,0,0.02);
        --shadow-md: 0 10px 30px rgba(0,0,0,0.03);
    }
    body { font-family: var(--font-sans); font-size: var(--text-base); line-height: 1.6; color: #0f172a; background-color: #f1f5f9; margin: 0; padding: 25px 12px; }
    .container { max-width: 900px; background-color: #ffffff; margin: 0 auto; border-radius: var(--radius-lg); overflow: hidden; box-shadow: var(--shadow-md); border: 1px solid #e2e8f0; }
    .header { background: linear-gradient(135deg, #0b0f19 0%, #1e293b 100%); color: #ffffff; padding: 40px 30px; text-align: center; position: relative; }
    .header::after { content: ''; position: absolute; bottom: 0; left: 0; right: 0; height: 6px; background: linear-gradient(90deg, #2563eb, #7c3aed, #ec4899); }
    .header h1 { margin: 0; font-size: 24px; font-weight: 900; letter-spacing: -0.5px; text-transform: uppercase; }
    .header p { margin: 8px 0 0 0; font-size: 13px; opacity: 0.85; font-weight: 500; }
    .content { padding: var(--spacing-lg) 30px; display: flex; flex-direction: column; gap: var(--spacing-lg); }
    .week-divider { border-top: 4px dashed #cbd5e1; margin: var(--spacing-lg) 0; }
    
    .week-title-box { padding-left: 20px; border-left: 6px solid #2563eb; }
    .week-title-line1 { font-size: var(--text-xl); font-weight: 900; color: #0f172a; text-transform: uppercase; letter-spacing: 0.5px; margin: 0; }
    .week-title-line2 { font-size: var(--text-base); font-weight: 600; color: #64748b; margin-top: 6px; }

    .section-title { font-size: var(--text-xs); font-weight: 900; text-transform: uppercase; letter-spacing: 1.5px; color: #475569; border-bottom: 2px solid #f1f5f9; padding-bottom: 8px; display: flex; align-items: center; gap: 8px; margin: 0; }
    
    /* Bandeau d'alerte et de synthèse supérieur */
    .alert-banner { padding: 25px 30px; color: #ffffff; border-radius: var(--radius-md); display: flex; flex-direction: column; gap: 15px; position: relative; overflow: hidden; }
    .alert-banner-Rouge { background: linear-gradient(135deg, #7f1d1d 0%, #dc2626 100%); }
    .alert-banner-Orange { background: linear-gradient(135deg, #7c2d12 0%, #ea580c 100%); }
    .alert-banner-Jaune { background: linear-gradient(135deg, #713f12 0%, #eab308 100%); }
    .alert-banner-Vert { background: linear-gradient(135deg, #064e3b 0%, #10b981 100%); }
    
    .alert-main-row { display: flex; justify-content: space-between; align-items: center; gap: 20px; }
    .alert-left { display: flex; flex-direction: column; gap: 6px; }
    .alert-badge-top { font-size: 9px; font-weight: 900; background: rgba(255,255,255,0.22); padding: 5px 12px; border-radius: 9999px; text-transform: uppercase; align-self: flex-start; letter-spacing: 1px; }
    .alert-title-lg { font-size: 24px; font-weight: 900; line-height: 1.2; text-transform: uppercase; margin: 0; }
    .alert-date-block { font-size: var(--text-xs); font-weight: 700; opacity: 0.9; }

    /* Ligne de KPI compacte homogène */
    .kpi-row-6 { display: grid; grid-template-columns: repeat(6, 1fr); gap: 10px; }
    @media (max-width: 768px) {
        .kpi-row-6 { grid-template-columns: repeat(3, 1fr); }
    }
    @media (max-width: 480px) {
        .kpi-row-6 { grid-template-columns: repeat(2, 1fr); }
    }
    .kpi-card-6 { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: var(--radius-md); padding: 14px 10px; text-align: center; display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 95px; box-shadow: var(--shadow-sm); }
    .kpi-icon { font-size: 18px; margin-bottom: 5px; }
    .kpi-val { font-size: 13.5px; font-weight: 850; color: #0f172a; line-height: 1.2; word-break: break-word; }
    .kpi-lbl { font-size: 9px; font-weight: 800; color: #64748b; text-transform: uppercase; margin-top: 3px; letter-spacing: 0.5px; }

    /* À retenir en 10 secondes */
    .summary-10s-box { background: #f8fafc; border: 1px solid #cbd5e1; border-left: 5px solid #2563eb; border-radius: var(--radius-md); padding: 20px; }
    .summary-10s-box h3 { margin: 0 0 10px 0; font-size: var(--text-xs); font-weight: 900; color: #1e293b; text-transform: uppercase; letter-spacing: 1px; }
    .summary-10s-list { margin: 0; padding: 0; list-style: none; font-size: var(--text-sm); color: #334155; line-height: 1.5; }
    .summary-10s-list li { margin-bottom: 5px; padding-left: 15px; position: relative; }
    .summary-10s-list li::before { content: '•'; position: absolute; left: 0; color: #2563eb; font-weight: 900; }

    /* Jauges compactes */
    .dashboard-meters-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }
    @media (max-width: 768px) {
        .dashboard-meters-row { grid-template-columns: repeat(2, 1fr); }
    }
    @media (max-width: 480px) {
        .dashboard-meters-row { grid-template-columns: 1fr; }
    }
    .meter-card-premium { background: #f8fafc; border: 1px solid #cbd5e1; border-radius: var(--radius-md); padding: 12px; display: flex; flex-direction: column; gap: 6px; }
    .meter-card-header { display: flex; align-items: center; justify-content: space-between; }
    .meter-card-header h4 { margin: 0; font-size: 11px; font-weight: 850; color: #475569; text-transform: uppercase; }
    .meter-badge { font-size: 8px; font-weight: 900; padding: 2px 8px; border-radius: 9999px; text-transform: uppercase; color: #ffffff; }
    .meter-track-premium { width: 100%; height: 6px; background: #e2e8f0; border-radius: 9999px; overflow: hidden; }
    .meter-fill-premium { height: 100%; border-radius: 9999px; }
    .meter-info { display: flex; align-items: center; justify-content: space-between; font-size: 10.5px; font-weight: 800; color: #1e293b; }
    
    /* Bloc Impacts Attendus */
    .impacts-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
    @media (max-width: 768px) {
        .impacts-grid { grid-template-columns: 1fr; }
    }
    .impact-item { background: #ffffff; border: 1px solid #e2e8f0; border-radius: var(--radius-md); padding: 14px; display: flex; align-items: flex-start; gap: 12px; box-shadow: var(--shadow-sm); }
    .impact-icon { font-size: 18px; line-height: 1; }
    .impact-content { display: flex; flex-direction: column; gap: 1px; }
    .impact-title { font-size: 10.5px; font-weight: 900; color: #475569; text-transform: uppercase; letter-spacing: 0.5px; }
    .impact-text { font-size: 12.5px; color: #334155; line-height: 1.4; }

    /* Chiffres à retenir */
    .numbers-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 12px; }
    @media (max-width: 768px) {
        .numbers-grid { grid-template-columns: repeat(2, 1fr); }
    }
    @media (max-width: 480px) {
        .numbers-grid { grid-template-columns: 1fr; }
    }
    .number-card { background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%); border: 1px solid #cbd5e1; border-radius: var(--radius-md); padding: 15px; text-align: center; }
    .number-val { font-size: 22px; font-weight: 900; color: #1e3a8a; line-height: 1.1; margin-bottom: 2px; }
    .number-lbl { font-size: 9.5px; font-weight: 800; color: #475569; line-height: 1.3; }

    /* Chronologie Horizontale */
    .timeline-horizontal { display: flex; align-items: stretch; justify-content: space-between; gap: 8px; }
    @media (max-width: 768px) {
        .timeline-horizontal { flex-direction: column; gap: 15px; }
    }
    .timeline-item-h { flex: 1; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: var(--radius-md); padding: 15px; display: flex; flex-direction: column; align-items: center; text-align: center; gap: 6px; }
    .timeline-circle { width: 24px; height: 24px; border-radius: 50%; background: #2563eb; color: #ffffff; font-size: 11px; font-weight: 900; display: flex; align-items: center; justify-content: center; }
    .timeline-phase-h { font-size: 9.5px; font-weight: 900; text-transform: uppercase; color: #2563eb; letter-spacing: 0.5px; }
    .timeline-date-h { font-size: 13px; font-weight: 850; color: #0f172a; }
    .timeline-desc-h { font-size: 12px; color: #475569; margin: 0; line-height: 1.45; }
    .timeline-arrow { display: flex; align-items: center; justify-content: center; font-size: 18px; color: #94a3b8; }
    @media (max-width: 768px) {
        .timeline-arrow { display: none; }
    }

    /* Tableau régional épuré */
    .table-responsive { width: 100%; overflow-x: auto; border-radius: var(--radius-md); border: 1px solid #cbd5e1; box-shadow: 0 4px 6px rgba(0,0,0,0.01); }
    .regional-table { width: 100%; border-collapse: collapse; text-align: left; font-size: var(--text-sm); }
    .regional-table th { background-color: #0f172a; color: #ffffff; font-weight: 900; text-transform: uppercase; letter-spacing: 0.5px; padding: 12px 15px; }
    .regional-table td { padding: 12px 15px; border-bottom: 1px solid #e2e8f0; color: #334155; }
    .regional-table tr:nth-child(even) { background-color: #f8fafc; }
    .regional-table tr:last-child td { border-bottom: none; }
    .badge-temp { font-weight: 900; color: #ffffff; background: #dc2626; padding: 5px 10px; border-radius: 8px; font-size: 12.5px; display: inline-block; }

    /* Graphiques Météo plein format */
    .meteo-images-container { display: flex; flex-direction: column; gap: 25px; }
    .meteo-image-card { background-color: #ffffff; border: 1px solid #cbd5e1; border-radius: var(--radius-lg); padding: 20px; box-shadow: 0 10px 20px rgba(0,0,0,0.01); text-align: center; }
    .meteo-image-card span { font-weight: 900; font-size: var(--text-sm); color: #0f172a; display: block; margin-bottom: 12px; text-transform: uppercase; letter-spacing: 0.5px; }
    .meteo-image-card img { width: 100%; height: auto; border-radius: var(--radius-md); border: 1px solid #e2e8f0; }

    /* Section Analyse Détaillée */
    .detailed-analysis-panel { background: #f8fafc; border-radius: var(--radius-lg); padding: 25px; border: 1px solid #cbd5e1; display: flex; flex-direction: column; gap: 20px; }
    .detailed-analysis-title { font-size: 14px; font-weight: 900; text-transform: uppercase; letter-spacing: 1.5px; color: #0f172a; margin: 0; display: flex; align-items: center; gap: 8px; border-bottom: 2px solid #cbd5e1; padding-bottom: 8px; }

    .scenarios-container { display: flex; flex-direction: column; gap: 12px; }
    .scenario-card { border-radius: var(--radius-md); padding: 16px; border: 1px solid #cbd5e1; background: #ffffff; }
    .sc-major { border-left: 6px solid #10b981; }
    .sc-median { border-left: 6px solid #f59e0b; }
    .sc-minor { border-left: 6px solid #ef4444; }
    .sc-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
    .sc-header h3 { margin: 0; font-size: 13.5px; font-weight: 900; color: #0f172a; text-transform: uppercase; }
    .sc-prob { font-size: 10px; padding: 3px 10px; border-radius: 9999px; color: #ffffff; font-weight: 900; }
    .bg-major { background-color: #10b981; }
    .bg-median { background-color: #f59e0b; }
    .bg-minor { background-color: #ef4444; }
    .sc-text { margin: 0; font-size: 12.5px; line-height: 1.5; color: #334155; }

    .confidence-panel { background: #ffffff; border-radius: var(--radius-md); padding: 18px; border: 1px solid #cbd5e1; display: flex; flex-direction: column; gap: 10px; }
    .confidence-head { display: flex; justify-content: space-between; align-items: center; }
    .confidence-head strong { font-size: var(--text-sm); color: #0f172a; text-transform: uppercase; letter-spacing: 0.5px; }
    .uncertainties-box { background: #fff1f2; border-radius: var(--radius-sm); padding: 15px; border: 1px solid #fecdd3; border-left: 5px solid #f43f5e; font-size: 12.5px; color: #334155; line-height: 1.5; }
    .uncertainties-box ul { margin: 5px 0 0 0; padding-left: 15px; }
    .uncertainties-box li { margin-bottom: 3px; }

    .takeaways-panel { background: #f0fdf4; border: 1px solid #bbf7d0; border-left: 6px solid #10b981; border-radius: var(--radius-md); padding: 18px; }
    .takeaways-panel h3 { margin: 0 0 10px 0; font-size: var(--text-sm); font-weight: 900; color: #166534; text-transform: uppercase; letter-spacing: 0.5px; }
    .takeaways-panel ul { margin: 0; padding-left: 15px; color: #15803d; font-size: 12.5px; line-height: 1.55; }
    .takeaways-panel li { margin-bottom: 4px; }

    /* Pack Réseaux Sociaux */
    .social-pack-container { display: flex; flex-direction: column; gap: 15px; }
    .social-platform-card { background: #ffffff; border: 1px solid #cbd5e1; border-radius: var(--radius-md); overflow: hidden; }
    .social-platform-header { display: flex; align-items: center; justify-content: space-between; padding: 12px 18px; font-weight: 900; font-size: 12px; color: #ffffff; text-transform: uppercase; letter-spacing: 0.5px; }
    .sp-linkedin { background: #0077b5; }
    .sp-facebook { background: #1877f2; }
    .sp-twitter { background: #0f1419; }
    .sp-tiktok { background: #fe2c55; }
    .sp-instagram { background: linear-gradient(45deg, #f09433 0%, #e6683c 25%, #dc2743 50%, #cc2366 75%, #bc1888 100%); }
    .social-platform-body { padding: 16px; font-size: 12.5px; white-space: pre-wrap; color: #334155; line-height: 1.6; font-family: var(--font-sans); }
    .copy-btn { background: rgba(255, 255, 255, 0.22); border: none; color: #ffffff; font-size: 9px; font-weight: 800; padding: 4px 10px; border-radius: 6px; cursor: pointer; text-transform: uppercase; letter-spacing: 0.5px; }
    .copy-btn:hover { background: rgba(255, 255, 255, 0.35); }
    """

    REGIONS_MAP = {
        "auvergne_rhone_alpes": "Auvergne-Rhône-Alpes",
        "bourgogne_franche_comte": "Bourgogne-Franche-Comté",
        "bretagne": "Bretagne",
        "centre_val_de_loire": "Centre-Val de Loire",
        "corse": "Corse",
        "grand_est": "Grand Est",
        "hauts_de_france": "Hauts-de-France",
        "ile_de_france": "Île-de-France",
        "normandie": "Normandie",
        "nouvelle_aquitaine": "Nouvelle-Aquitaine",
        "occitanie": "Occitanie",
        "pays_de_la_loire": "Pays de la Loire",
        "provence_alpes_cote_azur": "Provence-Alpes-Côte d'Azur"
    }

    date_suffix = datetime.datetime.now().strftime('%Y_%m_%d')

    # Générer le bulletin national (France)
    france_weeks_html = ""
    for w_idx, w_res in enumerate(results):
        full_data = w_res["data"]
        downloaded_images = w_res["images"]
        
        # Encodage des graphiques
        html_images_block = ""
        for idx, img_path in enumerate(downloaded_images):
            try:
                with open(img_path, "rb") as f_img:
                    img_b64 = base64.b64encode(f_img.read()).decode('ascii')
                ext = img_path.split('.')[-1]
                html_images_block += f"""
                <div class="meteo-image-card">
                    <span>📈 Modélisation Météo {idx+1}</span>
                    <img src="data:image/{ext};base64,{img_b64}" alt="Graphique Météo {idx+1}">
                </div>
                """
            except Exception as e:
                print(f"Erreur encodage base64 pour {img_path} : {e}")
        
        if html_images_block:
            html_images_block = f"""
            <div class="section-title">📊 MODÉLISATIONS & GRAPHIQUES DE TENDANCE</div>
            <div class="meteo-images-container">{html_images_block}</div>
            """

        data = full_data.get("france", {})
        timeline = data.get("timeline", {})
        regional = data.get("regional", {})
        conf = data.get("confidence", {}) or {}
        dash = data.get("dashboard", {}) or {}
        scenarios = data.get("scenarios", {}) or {}
        social = data.get("social_pack", {}) or {}
        alert = data.get("alert", {}) or {}
        kpis = data.get("kpis", {}) or {}
        impacts = data.get("impacts", {}) or {}

        linkedin_clean = social.get('linkedin', '').replace('<br>', '\n').replace('<br/>', '\n')
        facebook_clean = social.get('facebook', '').replace('<br>', '\n').replace('<br/>', '\n')
        twitter_clean = social.get('twitter', '').replace('<br>', '\n').replace('<br/>', '\n')
        tiktok_clean = social.get('tiktok', '').replace('<br>', '\n').replace('<br/>', '\n')
        instagram_clean = social.get('instagram', '').replace('<br>', '\n').replace('<br/>', '\n')

        conf_score_raw = alert.get('confidence', '4/5')
        conf_class = "conf-badge-green"
        if "3/" in conf_score_raw: conf_class = "conf-badge-orange"
        elif "1/" in conf_score_raw or "2/" in conf_score_raw: conf_class = "conf-badge-red"

        takeaways_li_html = "".join([f"<li>{t}</li>" for t in full_data.get("key_takeaways", "").split("\n") if t])
        if not takeaways_li_html: takeaways_li_html = "<li>Synthèse des prévisions établie avec succès.</li>"

        heat_score = parse_score(dash.get('score_heat', '0/5'))
        rain_score = parse_score(dash.get('score_rain', '0/5'))
        storm_score = parse_score(dash.get('score_storm', '0/5'))
        wind_score = parse_score(dash.get('score_wind', '0/5'))
        conf_label = get_score_label(conf_score_raw)

        # Génération des chiffres clés
        key_numbers_html = ""
        key_numbers_raw = full_data.get("key_numbers", "")
        if key_numbers_raw:
            lines = [l.strip() for l in key_numbers_raw.split("\n") if l.strip()]
            for l in lines:
                if "|" in l:
                    parts = [p.strip() for p in l.split("|")]
                    if len(parts) == 2:
                        val, lbl = parts[0], parts[1]
                        key_numbers_html += f"""
                        <div class="number-card">
                            <div class="number-val">{val}</div>
                            <div class="number-lbl">{lbl}</div>
                        </div>
                        """
        if not key_numbers_html:
            key_numbers_html = "<div style='grid-column: span 5; text-align: center; color: #64748b; font-style: italic; padding: 15px;'>Aucune donnée chiffrée.</div>"

        # Traitement du tableau régional
        hdf_data = parse_region_line(regional.get('hdf_north', ''))
        atl_data = parse_region_line(regional.get('atlantic', ''))
        cen_data = parse_region_line(regional.get('central', ''))
        sou_data = parse_region_line(regional.get('south', ''))
        med_data = parse_region_line(regional.get('mediterranean', ''))
        mnt_data = parse_region_line(regional.get('mountains', ''))

        def format_region_row(name, region_data):
            temp = region_data[0]
            rain = region_data[1]
            risk = region_data[2]
            conf_val = region_data[3]
            return f"""
            <tr>
                <td><strong>{name}</strong></td>
                <td><span class="badge-temp">{temp}</span></td>
                <td>{get_level_badge(rain)}</td>
                <td>{get_level_badge(risk)}</td>
                <td>{get_conf_badge(conf_val)}</td>
            </tr>
            """

        regional_table_rows = (
            format_region_row("Hauts-de-France & Nord", hdf_data) +
            format_region_row("Façade Atlantique", atl_data) +
            format_region_row("Régions Centrales", cen_data) +
            format_region_row("Moitié Sud", sou_data) +
            format_region_row("Pourtour Méditerranéen", med_data) +
            format_region_row("Reliefs & Montagnes", mnt_data)
        )

        summary_10s_html = "".join([f"<li>{l.strip('-* ').strip()}</li>" for l in data.get("takeaways_10s", []) if l.strip()])
        if not summary_10s_html: summary_10s_html = "<li>Aucun résumé disponible.</li>"

        alert_lvl = alert.get('level', 'Vert').strip().replace('[', '').replace(']', '')
        alert_bg_class = f"alert-banner-{{alert_lvl}}"

        divider = '<div class="week-divider"></div>' if w_idx > 0 else ""
        france_weeks_html += f"""
        {divider}
        <div class="week-title-box">
            <h2 class="week-title-line1">📅 {full_data.get('title_line1', 'SEMAINE')}</h2>
            <div class="week-title-line2">{full_data.get('title_line2', 'Synthèse France')}</div>
        </div>
        
        <div class="alert-banner {alert_bg_class}" style="margin-bottom: 25px;">
            <div class="alert-left">
                <span class="alert-badge-top">Synthèse France - Alerte {alert_lvl}</span>
                <h2 class="alert-title-lg">{alert.get('event_type', 'Événement')}</h2>
                <div class="alert-date-block">
                    PÉRIODE CONCERNÉE : {alert.get('start', '-')} au {alert.get('end', '-')}
                </div>
            </div>
        </div>

        <div class="kpi-row-6" style="margin-bottom: 25px;">
            <div class="kpi-card-6"><div class="kpi-icon">🌡️</div><div class="kpi-val">{kpis.get('temp_range', '-')}</div><div class="kpi-lbl">Température</div></div>
            <div class="kpi-card-6"><div class="kpi-icon">📅</div><div class="kpi-val">{kpis.get('period', '-')}</div><div class="kpi-lbl">Période</div></div>
            <div class="kpi-card-6"><div class="kpi-icon">⏱️</div><div class="kpi-val">{kpis.get('duration', '-')}</div><div class="kpi-lbl">Durée</div></div>
            <div class="kpi-card-6"><div class="kpi-icon">🎯</div><div class="kpi-val">{kpis.get('confidence', '-')}</div><div class="kpi-lbl">Confiance</div></div>
            <div class="kpi-card-6"><div class="kpi-icon">⚠️</div><div class="kpi-val">{kpis.get('risks', '-')}</div><div class="kpi-lbl">Risques</div></div>
            <div class="kpi-card-6"><div class="kpi-icon">📍</div><div class="kpi-val">{kpis.get('zone', '-')}</div><div class="kpi-lbl">Zone</div></div>
        </div>

        <div class="summary-10s-box" style="margin-bottom: 25px;">
            <h3>⏱️ À Retenir en 10 Secondes</h3>
            <ul class="summary-10s-list">{summary_10s_html}</ul>
        </div>

        <div class="section-title">📊 INDICES DE RISQUES PHYSIQUES</div>
        <div class="dashboard-meters-row" style="margin-bottom: 25px;">
            <div class="meter-card-premium">
                <div class="meter-card-header"><h4>🔥 Chaleur</h4><span class="meter-badge mb-chaleur">{get_score_label(dash.get('score_heat', '0/5'))}</span></div>
                <div class="meter-track-premium"><div class="meter-fill-premium mf-heat" style="width: {heat_score * 20}%;"></div></div>
                <div class="meter-info"><span class="meter-lbl-text">{dash.get('interp_heat', 'Situation normale')}</span><span>{heat_score}/5</span></div>
            </div>
            <div class="meter-card-premium">
                <div class="meter-card-header"><h4>🌧️ Pluie</h4><span class="meter-badge mb-pluie">{get_score_label(dash.get('score_rain', '0/5'))}</span></div>
                <div class="meter-track-premium"><div class="meter-fill-premium mf-rain" style="width: {rain_score * 20}%;"></div></div>
                <div class="meter-info"><span class="meter-lbl-text">{dash.get('interp_rain', 'Situation normale')}</span><span>{rain_score}/5</span></div>
            </div>
            <div class="meter-card-premium">
                <div class="meter-card-header"><h4>⛈️ Orages</h4><span class="meter-badge mb-orage">{get_score_label(dash.get('score_storm', '0/5'))}</span></div>
                <div class="meter-track-premium"><div class="meter-fill-premium mf-storm" style="width: {storm_score * 20}%;"></div></div>
                <div class="meter-info"><span class="meter-lbl-text">{dash.get('interp_storm', 'Situation normale')}</span><span>{storm_score}/5</span></div>
            </div>
            <div class="meter-card-premium">
                <div class="meter-card-header"><h4>💨 Vent</h4><span class="meter-badge mb-vent">{get_score_label(dash.get('score_wind', '0/5'))}</span></div>
                <div class="meter-track-premium"><div class="meter-fill-premium mf-wind" style="width: {wind_score * 20}%;"></div></div>
                <div class="meter-info"><span class="meter-lbl-text">{dash.get('interp_wind', 'Situation normale')}</span><span>{wind_score}/5</span></div>
            </div>
        </div>

        <div class="section-title">⚠️ IMPACTS ATTENDUS PAR SECTEUR</div>
        <div class="impacts-grid" style="margin-bottom: 25px;">
            <div class="impact-item"><span class="impact-icon">👥</span><div class="impact-content"><strong class="impact-title">Population</strong><span class="impact-text">{impacts.get('population', '-')}</span></div></div>
            <div class="impact-item"><span class="impact-icon">🚗</span><div class="impact-content"><strong class="impact-title">Déplacements</strong><span class="impact-text">{impacts.get('travel', '-')}</span></div></div>
            <div class="impact-item"><span class="impact-icon">🏗️</span><div class="impact-content"><strong class="impact-title">Travaux & BTP</strong><span class="impact-text">{impacts.get('work', '-')}</span></div></div>
            <div class="impact-item"><span class="impact-icon">🌾</span><div class="impact-content"><strong class="impact-title">Agriculture</strong><span class="impact-text">{impacts.get('agri', '-')}</span></div></div>
            <div class="impact-item"><span class="impact-icon">⚡</span><div class="impact-content"><strong class="impact-title">Orages & Réseaux</strong><span class="impact-text">{impacts.get('storm', '-')}</span></div></div>
            <div class="impact-item"><span class="impact-icon">🌿</span><div class="impact-content"><strong class="impact-title">Sécheresse & Eau</strong><span class="impact-text">{impacts.get('drought', '-')}</span></div></div>
        </div>

        <div class="section-title">🗓️ CHRONOLOGIE DE L'ÉPISODE</div>
        <div class="timeline-horizontal" style="margin-bottom: 25px;">
            <div class="timeline-item-h"><div class="timeline-circle">1</div><strong class="timeline-phase-h">Début</strong><span class="timeline-date-h">{timeline.get('date_debut', '-')}</span><p class="timeline-desc-h">{timeline.get('desc_debut', '-')}</p></div>
            <div class="timeline-arrow">➔</div>
            <div class="timeline-item-h"><div class="timeline-circle">2</div><strong class="timeline-phase-h">Montée</strong><span class="timeline-date-h">{timeline.get('date_montee', '-')}</span><p class="timeline-desc-h">{timeline.get('desc_montee', '-')}</p></div>
            <div class="timeline-arrow">➔</div>
            <div class="timeline-item-h"><div class="timeline-circle">3</div><strong class="timeline-phase-h">Pic</strong><span class="timeline-date-h">{timeline.get('date_pic', '-')}</span><p class="timeline-desc-h">{timeline.get('desc_pic', '-')}</p></div>
            <div class="timeline-arrow">➔</div>
            <div class="timeline-item-h"><div class="timeline-circle">4</div><strong class="timeline-phase-h">Fin</strong><span class="timeline-date-h">{timeline.get('date_fin', '-')}</span><p class="timeline-desc-h">{timeline.get('desc_fin', '-')}</p></div>
        </div>

        <div class="section-title">🗺️ TENDANCE PAR GRANDES RÉGIONS</div>
        <div class="table-responsive" style="margin-bottom: 25px;">
            <table class="regional-table">
                <thead><tr><th>Région</th><th>🌡️ Températures</th><th>🌧️ Pluviométrie</th><th>⚠️ Risque Majeur</th><th>🎯 Fiabilité</th></tr></thead>
                <tbody>{regional_table_rows}</tbody>
            </table>
        </div>

        {html_images_block}

        <div class="section-title">🔢 LES CHIFFRES À RETENIR</div>
        <div class="numbers-grid" style="margin-bottom: 25px;">{key_numbers_html}</div>

        <div class="detailed-analysis-panel" style="margin-bottom: 25px;">
            <h3 class="detailed-analysis-title">🔮 SCÉNARIOS DE MODÉLISATIONS & ANALYSES</h3>
            <div class="scenarios-container">
                <div class="scenario-card sc-major">
                    <div class="sc-header"><h3>🟢 Scénario Majoritaire ({scenarios.get('majoritaire', {}).get('prob', '65%')})</h3></div>
                    <strong style="font-size:12.5px; display:block; margin-bottom:4px; color:#10b981;">{scenarios.get('majoritaire', {}).get('title', '')}</strong>
                    <p class="sc-text">{scenarios.get('majoritaire', {}).get('desc', '')}</p>
                </div>
                <div class="scenario-card sc-median">
                    <div class="sc-header"><h3>🟡 Scénario Alternatif ({scenarios.get('median', {}).get('prob', '25%')})</h3></div>
                    <strong style="font-size:12.5px; display:block; margin-bottom:4px; color:#f59e0b;">{scenarios.get('median', {}).get('title', '')}</strong>
                    <p class="sc-text">{scenarios.get('median', {}).get('desc', '')}</p>
                </div>
                <div class="scenario-card sc-minor">
                    <div class="sc-header"><h3>🔴 Scénario Minoritaire ({scenarios.get('minoritaire', {}).get('prob', '10%')})</h3></div>
                    <strong style="font-size:12.5px; display:block; margin-bottom:4px; color:#ef4444;">{scenarios.get('minoritaire', {}).get('title', '')}</strong>
                    <p class="sc-text">{scenarios.get('minoritaire', {}).get('desc', '')}</p>
                </div>
            </div>
            <div class="confidence-panel" style="padding: 15px; margin-bottom: 0;">
                <div class="confidence-head" style="margin-bottom: 8px;">
                    <strong>Incertitudes Modélisations</strong>
                    <span class="{conf_class}" style="padding: 4px 12px; border-radius: 9999px; font-weight: 800; font-size: 11px; color: white; {get_badge_color_class(conf_score_raw)}">Consensus : {conf_score_raw}</span>
                </div>
                <div class="uncertainties-box">
                    <strong style="display: block; margin-bottom: 6px; color: #dc2626; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px;">❓ Incertitudes & Points Clés :</strong>
                    {full_data.get('france', {}).get('key_uncertainties', '')}\n{full_data.get('france', {}).get('monitoring_points', '')}
                </div>
            </div>
            <div class="takeaways-panel" style="margin-bottom: 0;">
                <h3>📌 Synthèse Récapitulative</h3>
                <ul>{takeaways_li_html}</ul>
            </div>
        </div>

        <div class="section-title">📢 PACK DE DIFFUSION RÉSEAUX SOCIAUX</div>
        <div class="social-pack-container">
            <div class="social-platform-card">
                <div class="social-platform-header sp-linkedin"><span>🔗 LinkedIn ({len(linkedin_clean)} car.)</span><button class="copy-btn" onclick="navigator.clipboard.writeText(this.parentNode.parentNode.querySelector('.social-platform-body').innerText); alert('Copié !');">Copier</button></div>
                <div class="social-platform-body">{linkedin_clean}</div>
            </div>
            <div class="social-platform-card">
                <div class="social-platform-header sp-facebook"><span>👥 Facebook ({len(facebook_clean)} car.)</span><button class="copy-btn" onclick="navigator.clipboard.writeText(this.parentNode.parentNode.querySelector('.social-platform-body').innerText); alert('Copié !');">Copier</button></div>
                <div class="social-platform-body">{facebook_clean}</div>
            </div>
            <div class="social-platform-card">
                <div class="social-platform-header sp-twitter"><span>🐦 X (Twitter - {len(twitter_clean)} / 280 car.)</span><button class="copy-btn" onclick="navigator.clipboard.writeText(this.parentNode.parentNode.querySelector('.social-platform-body').innerText); alert('Copié !');">Copier</button></div>
                <div class="social-platform-body">{twitter_clean}</div>
            </div>
            <div class="social-platform-card">
                <div class="social-platform-header sp-tiktok"><span>🎵 TikTok ({len(tiktok_clean)} car.)</span><button class="copy-btn" onclick="navigator.clipboard.writeText(this.parentNode.parentNode.querySelector('.social-platform-body').innerText); alert('Copié !');">Copier</button></div>
                <div class="social-platform-body">{tiktok_clean}</div>
            </div>
            <div class="social-platform-card">
                <div class="social-platform-header sp-instagram"><span>📸 Instagram ({len(instagram_clean)} car.)</span><button class="copy-btn" onclick="navigator.clipboard.writeText(this.parentNode.parentNode.querySelector('.social-platform-body').innerText); alert('Copié !');">Copier</button></div>
                <div class="social-platform-body">{instagram_clean}</div>
            </div>
        </div>
        """

    france_html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Analyses & Tendances Météo - France</title>
    <style>{style}</style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div style="font-size: 11px; font-weight: 800; letter-spacing: 2px; text-transform: uppercase; margin-bottom: 8px;">MONSIEUR MÉTÉO</div>
            <h1>📊 BULLETIN ÉVOLUTION & TENDANCES MÉTÉO - FRANCE</h1>
            <p>Tableau de bord national de synthèse du {datetime.datetime.now().strftime('%d/%m/%Y')}</p>
        </div>
        <div class="content">
            {france_weeks_html}
        </div>
    </div>
</body>
</html>
"""
    
    with open(f"bulletin_tendance_france_{date_suffix}.html", "w", encoding="utf-8") as f_fr:
        f_fr.write(france_html)
    print(f"Bulletin national généré : bulletin_tendance_france_{date_suffix}.html")

    # Générer les 13 bulletins régionaux
    for r_key, r_name in REGIONS_MAP.items():
        region_weeks_html = ""
        for w_idx, w_res in enumerate(results):
            full_data = w_res["data"]
            r_data = full_data.get("regions", {}).get(r_key, {})
            if not r_data:
                # Fallback neutre si l'IA a omis une région
                r_data = {
                    "alert_level": "Vert",
                    "event_type": "Information non précisée dans les sources",
                    "kpis": {"temp_range": "Non précisé", "period": "Non précisé", "duration": "Non précisé", "confidence": "Non précisé", "risks": "Non précisé", "zone": "Non précisé"},
                    "takeaways_10s": ["Information non précisée dans les sources"],
                    "dashboard": {"score_heat": "0/5", "score_rain": "0/5", "score_storm": "0/5", "score_wind": "0/5"},
                    "impacts": {"population": "Information non précisée", "travel": "Information non précisée", "work": "Information non précisée", "agri": "Information non précisée", "storm": "Information non précisée", "drought": "Information non précisée"},
                    "timeline": {"date_debut": "-", "desc_debut": "-", "date_montee": "-", "desc_montee": "-", "date_pic": "-", "desc_pic": "-", "date_fin": "-", "desc_fin": "-"}
                }

            alert_lvl = r_data.get("alert_level", "Vert").strip().replace('[', '').replace(']', '')
            alert_bg_class = f"alert-banner-{alert_lvl}"
            
            kpis = r_data.get("kpis", {}) or {}
            timeline = r_data.get("timeline", {}) or {}
            dash = r_data.get("dashboard", {}) or {}
            impacts = r_data.get("impacts", {}) or {}

            summary_10s_html = "".join([f"<li>{l.strip('-* ').strip()}</li>" for l in r_data.get("takeaways_10s", []) if l.strip()])
            if not summary_10s_html:
                summary_10s_html = "<li>Aucun résumé spécifique disponible pour cette région.</li>"

            heat_score = parse_score(dash.get('score_heat', '0/5'))
            rain_score = parse_score(dash.get('score_rain', '0/5'))
            storm_score = parse_score(dash.get('score_storm', '0/5'))
            wind_score = parse_score(dash.get('score_wind', '0/5'))

            # Traitement dynamique de l'affichage des impacts (masquer si non précisé)
            def format_impact_item(icon, title, val):
                if not val or "non précisée" in val.lower() or "non identifié" in val.lower() or val == "-":
                    return f"""
                    <div class="impact-item" style="opacity: 0.6;">
                        <span class="impact-icon">{icon}</span>
                        <div class="impact-content">
                            <strong class="impact-title">{title}</strong>
                            <span class="impact-text" style="font-style: italic; color: #94a3b8;">Non précisé dans les sources</span>
                        </div>
                    </div>
                    """
                return f"""
                <div class="impact-item">
                    <span class="impact-icon">{icon}</span>
                    <div class="impact-content">
                        <strong class="impact-title">{title}</strong>
                        <span class="impact-text">{val}</span>
                    </div>
                </div>
                """

            impacts_html = (
                format_impact_item("👥", "Population", impacts.get("population")) +
                format_impact_item("🚗", "Déplacements", impacts.get("travel")) +
                format_impact_item("🏗️", "Travaux & BTP", impacts.get("work")) +
                format_impact_item("🌾", "Agriculture", impacts.get("agri")) +
                format_impact_item("⚡", "Orages & Réseaux", impacts.get("storm")) +
                format_impact_item("🌿", "Sécheresse & Eau", impacts.get("drought"))
            )

            divider = '<div class="week-divider"></div>' if w_idx > 0 else ""
            region_weeks_html += f"""
            {divider}
            <div class="week-title-box">
                <h2 class="week-title-line1">📅 {full_data.get('title_line1', 'SEMAINE')}</h2>
                <div class="week-title-line2">Tendance Régionale - {r_name}</div>
            </div>
            
            <div class="alert-banner {alert_bg_class}" style="margin-bottom: 25px;">
                <div class="alert-left">
                    <span class="alert-badge-top">Bulletin Régional - {r_name}</span>
                    <h2 class="alert-title-lg">{r_data.get('event_type', 'Situation Stable')}</h2>
                    <div class="alert-date-block">
                        PÉRIODE : {kpis.get('period', 'Non précisée')}
                    </div>
                </div>
            </div>

            <div class="kpi-row-6" style="margin-bottom: 25px;">
                <div class="kpi-card-6"><div class="kpi-icon">🌡️</div><div class="kpi-val">{kpis.get('temp_range', 'Non précisé')}</div><div class="kpi-lbl">Temp. Régionale</div></div>
                <div class="kpi-card-6"><div class="kpi-icon">📅</div><div class="kpi-val">{kpis.get('period', 'Non précisé')}</div><div class="kpi-lbl">Période</div></div>
                <div class="kpi-card-6"><div class="kpi-icon">⏱️</div><div class="kpi-val">{kpis.get('duration', 'Non précisé')}</div><div class="kpi-lbl">Durée</div></div>
                <div class="kpi-card-6"><div class="kpi-icon">🎯</div><div class="kpi-val">{kpis.get('confidence', 'Non précisé')}</div><div class="kpi-lbl">Confiance</div></div>
                <div class="kpi-card-6"><div class="kpi-icon">⚠️</div><div class="kpi-val">{kpis.get('risks', 'Non précisé')}</div><div class="kpi-lbl">Risques</div></div>
                <div class="kpi-card-6"><div class="kpi-icon">📍</div><div class="kpi-val">{kpis.get('zone', 'Non précisé')}</div><div class="kpi-lbl">Départements</div></div>
            </div>

            <div class="summary-10s-box" style="margin-bottom: 25px;">
                <h3>⏱️ À Retenir en 10 Secondes - {r_name}</h3>
                <ul class="summary-10s-list">{summary_10s_html}</ul>
            </div>

            <div class="section-title">📊 INDICES DE RISQUES PHYSIQUES - {r_name}</div>
            <div class="dashboard-meters-row" style="margin-bottom: 25px;">
                <div class="meter-card-premium">
                    <div class="meter-card-header"><h4>🔥 Chaleur</h4><span class="meter-badge mb-chaleur">{get_score_label(dash.get('score_heat', '0/5'))}</span></div>
                    <div class="meter-track-premium"><div class="meter-fill-premium mf-heat" style="width: {heat_score * 20}%;"></div></div>
                    <div class="meter-info"><span class="meter-lbl-text">{dash.get('interp_heat', 'Situation normale')}</span><span>{heat_score}/5</span></div>
                </div>
                <div class="meter-card-premium">
                    <div class="meter-card-header"><h4>🌧️ Pluie</h4><span class="meter-badge mb-pluie">{get_score_label(dash.get('score_rain', '0/5'))}</span></div>
                    <div class="meter-track-premium"><div class="meter-fill-premium mf-rain" style="width: {rain_score * 20}%;"></div></div>
                    <div class="meter-info"><span class="meter-lbl-text">{dash.get('interp_rain', 'Situation normale')}</span><span>{rain_score}/5</span></div>
                </div>
                <div class="meter-card-premium">
                    <div class="meter-card-header"><h4>⛈️ Orages</h4><span class="meter-badge mb-orage">{get_score_label(dash.get('score_storm', '0/5'))}</span></div>
                    <div class="meter-track-premium"><div class="meter-fill-premium mf-storm" style="width: {storm_score * 20}%;"></div></div>
                    <div class="meter-info"><span class="meter-lbl-text">{dash.get('interp_storm', 'Situation normale')}</span><span>{storm_score}/5</span></div>
                </div>
                <div class="meter-card-premium">
                    <div class="meter-card-header"><h4>💨 Vent</h4><span class="meter-badge mb-vent">{get_score_label(dash.get('score_wind', '0/5'))}</span></div>
                    <div class="meter-track-premium"><div class="meter-fill-premium mf-wind" style="width: {wind_score * 20}%;"></div></div>
                    <div class="meter-info"><span class="meter-lbl-text">{dash.get('interp_wind', 'Situation normale')}</span><span>{wind_score}/5</span></div>
                </div>
            </div>

            <div class="section-title">⚠️ IMPACTS ATTENDUS PAR SECTEUR - {r_name}</div>
            <div class="impacts-grid" style="margin-bottom: 25px;">{impacts_html}</div>

            <div class="section-title">🗓️ CHRONOLOGIE RÉGIONALE</div>
            <div class="timeline-horizontal" style="margin-bottom: 25px;">
                <div class="timeline-item-h"><div class="timeline-circle">1</div><strong class="timeline-phase-h">Début</strong><span class="timeline-date-h">{timeline.get('date_debut', '-')}</span><p class="timeline-desc-h">{timeline.get('desc_debut', '-')}</p></div>
                <div class="timeline-arrow">➔</div>
                <div class="timeline-item-h"><div class="timeline-circle">2</div><strong class="timeline-phase-h">Montée</strong><span class="timeline-date-h">{timeline.get('date_montee', '-')}</span><p class="timeline-desc-h">{timeline.get('desc_montee', '-')}</p></div>
                <div class="timeline-arrow">➔</div>
                <div class="timeline-item-h"><div class="timeline-circle">3</div><strong class="timeline-phase-h">Pic</strong><span class="timeline-date-h">{timeline.get('date_pic', '-')}</span><p class="timeline-desc-h">{timeline.get('desc_pic', '-')}</p></div>
                <div class="timeline-arrow">➔</div>
                <div class="timeline-item-h"><div class="timeline-circle">4</div><strong class="timeline-phase-h">Fin</strong><span class="timeline-date-h">{timeline.get('date_fin', '-')}</span><p class="timeline-desc-h">{timeline.get('desc_fin', '-')}</p></div>
            </div>
            """

        region_html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Analances & Tendances Météo - {r_name}</title>
    <style>{style}</style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div style="font-size: 11px; font-weight: 800; letter-spacing: 2px; text-transform: uppercase; margin-bottom: 8px;">MONSIEUR MÉTÉO</div>
            <h1>📊 BULLETIN ÉVOLUTION & TENDANCES MÉTÉO - {r_name.upper()}</h1>
            <p>Tableau de bord de synthèse du {datetime.datetime.now().strftime('%d/%m/%Y')}</p>
        </div>
        <div class="content">
            {region_weeks_html}
        </div>
    </div>
</body>
</html>
"""
        with open(f"bulletin_tendance_{r_key}_{date_suffix}.html", "w", encoding="utf-8") as f_r:
            f_r.write(region_html)
        print(f"Bulletin régional généré : bulletin_tendance_{r_key}_{date_suffix}.html")

    # Mettre à jour bulletin_infoclimat.html avec la version nationale
    with open("bulletin_infoclimat.html", "w", encoding="utf-8") as f_def:
        f_def.write(france_html)

    html_path = "bulletin_infoclimat.html"
    html = france_html
    print(f"HTML généré avec succès : {html_path}")

    # Envoi e-mail via Gmail SMTP Base64 brut
    gmail_email = os.environ.get("GMAIL_EMAIL", "langlet.gregory@gmail.com")
    gmail_password = os.environ.get("GMAIL_APP_PASSWORD")
    if gmail_email:
        gmail_email = gmail_email.replace('\ufeff', '').replace('\ufffe', '').strip()
    if gmail_password:
        gmail_password = gmail_password.replace('\ufeff', '').replace('\ufffe', '').strip()
        
    recipient = os.environ.get("RECIPIENT_EMAILS", "gregory.langlet@sfr.fr, langlet.gregory@gmail.com")
    recipients = [r.strip() for r in recipient.split(",") if r.strip()]
    
    if not gmail_password:
        print("[SMTP] ERREUR : GMAIL_APP_PASSWORD non configuré. Annulation envoi.")
        sys.exit(0)
        
    sender = gmail_email
    
    # Titres abrégés pour le sujet du mail
    subject_week_names = " & ".join([r["data"].get("title_line1", r["data"].get("subject_title", "Semaine")).split("-")[0].strip() for r in results])
    subject = f"Tendances de la semaine - {subject_week_names}"
    
    # Nettoyage ASCII du sujet pour éviter les rejets SMTP
    import unicodedata
    clean_subj = unicodedata.normalize('NFKD', subject).encode('ASCII', 'ignore').decode('ASCII')
    subject = clean_subj
    
    filename = f"analyse_infoclimat_{datetime.datetime.now().strftime('%Y_%m_%d')}.html"
    
    html_b64 = base64.b64encode(html.encode('utf-8')).decode('ascii')
    text_body = f"Bonjour,\n\nVeuillez trouver ci-joint l'analyse consolidée des tendances météo pour la semaine en cours (jours restants) et la semaine suivante.\n\nLe rapport HTML contenant le Pack Réseaux Sociaux multi-plateforme complet et prêt à diffuser ainsi que les graphiques de modélisation est joint à ce message.\n\nCordialement,\nMonsieur Météo"
    text_b64 = base64.b64encode(text_body.encode('utf-8')).decode('ascii')
    boundary = uuid.uuid4().hex
    
    raw_message = (
        f'From: Meteo Climat Pro <{sender}>\r\n'
        f'To: {", ".join(recipients)}\r\n'
        f'Reply-To: gregory.langlet@sfr.fr\r\n'
        f'Subject: {subject}\r\n'
        f'Date: {formatdate(localtime=True)}\r\n'
        f'X-Mailer: Python\r\n'
        f'MIME-Version: 1.0\r\n'
        f'Content-Type: multipart/mixed; boundary="{boundary}"\r\n'
        f'\r\n'
        f'--{boundary}\r\n'
        f'Content-Type: text/plain; charset=utf-8\r\n'
        f'Content-Transfer-Encoding: base64\r\n'
        f'\r\n'
        f'{text_b64}\r\n'
        f'\r\n'
        f'--{boundary}\r\n'
        f'Content-Type: text/html; charset=utf-8; name="{filename}"\r\n'
        f'Content-Disposition: attachment; filename="{filename}"\r\n'
        f'Content-Transfer-Encoding: base64\r\n'
        f'\r\n'
        f'{html_b64}\r\n'
        f'\r\n'
        f'--{boundary}--\r\n'
    )
    
    print(f"[SMTP] Envoi via Gmail à {', '.join(recipients)}...")
    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(gmail_email, gmail_password)
            server.sendmail(gmail_email, recipients, raw_message.encode('ascii'))
        print("[SMTP] E-mail envoyé avec succès !")
    except Exception as e:
        print(f"[SMTP] Erreur d'envoi : {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
