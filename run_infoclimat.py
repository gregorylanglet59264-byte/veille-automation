import urllib.request
import urllib.error
import urllib.parse
import re
import sys
import os
import json
import base64
import uuid
import datetime
import smtplib
import socket
import time
import unicodedata
import concurrent.futures
from email.utils import formatdate
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

socket.setdefaulttimeout(10)

INDEX_URL = "https://forums.infoclimat.fr/f/forum/20-evolution-%C3%A0-plus-long-terme/"
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'

REGIONS_CONFIG = {
    "auvergne_rhone_alpes": ("Auvergne-Rhône-Alpes", "ARA.html"),
    "bourgogne_franche_comte": ("Bourgogne-Franche-Comté", "BFC.html"),
    "bretagne": ("Bretagne", "BRE.html"),
    "centre_val_de_loire": ("Centre-Val de Loire", "CVL.html"),
    "corse": ("Corse", "COR.html"),
    "grand_est": ("Grand Est", "GES.html"),
    "hauts_de_france": ("Hauts-de-France", "HDF.html"),
    "ile_de_france": ("Île-de-France", "IDF.html"),
    "normandie": ("Normandie", "NOR.html"),
    "nouvelle_aquitaine": ("Nouvelle-Aquitaine", "NAQ.html"),
    "occitanie": ("Occitanie", "OCC.html"),
    "pays_de_la_loire": ("Pays de la Loire", "PDL.html"),
    "provence_alpes_cote_azur": ("Provence-Alpes-Côte d'Azur", "PACA.html"),
}

# Ancres géographiques précises par région : départements + villes + orientation cardinale interne
# Utilisé dans le prompt LLM pour éviter qu'un "nord-ouest" générique soit mal attribué
REGIONS_GEO = {
    "auvergne_rhone_alpes": (
        "Départements : Ain (01), Allier (03), Ardèche (07), Cantal (15), Drôme (26), Isère (38), "
        "Loire (42), Haute-Loire (43), Puy-de-Dôme (63), Rhône (69), Savoie (73), Haute-Savoie (74). "
        "Villes : Lyon, Grenoble, Saint-Étienne, Clermont-Ferrand, Annecy, Chambéry, Valence, Bourg-en-Bresse. "
        "Repères : Nord = Ain/Bourg-en-Bresse | Nord-Ouest = Allier/Moulins | Ouest = Loire/Saint-Étienne | "
        "Centre = Rhône/Lyon, Puy-de-Dôme/Clermont | Est = Isère/Grenoble, Savoie/Chambéry | "
        "Sud-Est = Haute-Savoie/Annecy, Alpes | Sud = Ardèche, Drôme/Valence | Sud-Ouest = Cantal, Haute-Loire."
    ),
    "bourgogne_franche_comte": (
        "Départements : Côte-d'Or (21), Doubs (25), Jura (39), Nièvre (58), Haute-Saône (70), "
        "Saône-et-Loire (71), Yonne (89), Territoire de Belfort (90). "
        "Villes : Dijon, Besançon, Chalon-sur-Saône, Mâcon, Belfort, Auxerre, Nevers, Lons-le-Saunier. "
        "Repères : Nord-Ouest = Yonne/Auxerre, Nièvre/Nevers | Nord = Côte-d'Or/Dijon | "
        "Nord-Est = Haute-Saône, Belfort | Est = Doubs/Besançon, Jura/Lons | "
        "Sud = Saône-et-Loire/Chalon, Mâcon."
    ),
    "bretagne": (
        "Départements : Côtes-d'Armor (22), Finistère (29), Ille-et-Vilaine (35), Morbihan (56). "
        "Villes : Rennes, Brest, Quimper, Lorient, Vannes, Saint-Brieuc, Saint-Malo, Morlaix, Concarneau. "
        "Repères : Nord = Côtes-d'Armor/Saint-Brieuc, Ille-et-Vilaine nord/Saint-Malo | "
        "Nord-Ouest = Finistère nord/Brest, Morlaix | Ouest = Pointe du Finistère/Quimper | "
        "Sud-Ouest = Morbihan ouest/Lorient | Sud = Morbihan/Vannes | Est = Ille-et-Vilaine/Rennes."
    ),
    "centre_val_de_loire": (
        "Départements : Cher (18), Eure-et-Loir (28), Indre (36), Indre-et-Loire (37), "
        "Loir-et-Cher (41), Loiret (45). "
        "Villes : Orléans, Tours, Bourges, Chartres, Blois, Châteauroux, Vierzon. "
        "Repères : Nord = Eure-et-Loir/Chartres, Loiret nord | Centre = Loir-et-Cher/Blois, Loiret/Orléans | "
        "Ouest = Indre-et-Loire/Tours | Sud-Ouest = Indre/Châteauroux | Sud-Est = Cher/Bourges."
    ),
    "corse": (
        "Départements : Haute-Corse (2B), Corse-du-Sud (2A). "
        "Villes : Ajaccio, Bastia, Porto-Vecchio, Corte, Bonifacio, Calvi, L'Île-Rousse. "
        "Repères : Nord = Cap Corse, Bastia, Haute-Corse/Calvi | Centre = Corte, massif central corse | "
        "Sud = Corse-du-Sud/Ajaccio, Porto-Vecchio | Sud-Est = Bonifacio, Alta Rocca | "
        "Côte Ouest (mer Tyrrhénienne) = Ajaccio, Porto | Côte Est = Bastia, Ghisonaccia."
    ),
    "grand_est": (
        "Départements : Ardennes (08), Aube (10), Marne (51), Haute-Marne (52), Meurthe-et-Moselle (54), "
        "Meuse (55), Moselle (57), Bas-Rhin (67), Haut-Rhin (68), Vosges (88). "
        "Villes : Strasbourg, Reims, Metz, Nancy, Mulhouse, Colmar, Troyes, Charleville-Mézières, Épinal, Bar-le-Duc. "
        "Repères : Nord-Ouest = Ardennes/Charleville-Mézières | Nord = Moselle/Metz, Meurthe-et-Moselle/Nancy | "
        "Ouest = Marne/Reims, Aube/Troyes, Haute-Marne | Centre = Meuse/Bar-le-Duc, Vosges/Épinal | "
        "Est = Bas-Rhin/Strasbourg, Haut-Rhin/Mulhouse, Colmar (façade rhénane)."
    ),
    "hauts_de_france": (
        "Départements : Nord (59), Pas-de-Calais (62), Somme (80), Aisne (02), Oise (60). "
        "Villes : Lille, Amiens, Valenciennes, Dunkerque, Calais, Boulogne-sur-Mer, Arras, "
        "Beauvais, Laon, Compiègne, Maubeuge, Roubaix, Tourcoing. "
        "Repères : Nord = Nord (59)/Lille, Dunkerque, littoral flamand | Nord-Ouest = Pas-de-Calais/Calais, "
        "Boulogne, Côte d'Opale | Ouest = Somme/Amiens, baie de Somme | Sud = Oise/Beauvais, Compiègne | "
        "Sud-Est = Aisne/Laon, Saint-Quentin | Est = Valenciennes, Maubeuge, frontière belge."
    ),
    "ile_de_france": (
        "Départements : Paris (75), Seine-et-Marne (77), Yvelines (78), Essonne (91), "
        "Hauts-de-Seine (92), Seine-Saint-Denis (93), Val-de-Marne (94), Val-d'Oise (95). "
        "Villes : Paris, Versailles, Boulogne-Billancourt, Créteil, Pontoise, Meaux, Évry, Melun, Bobigny. "
        "Repères : Nord = Val-d'Oise/Pontoise, Roissy | Nord-Est = Seine-Saint-Denis/Bobigny | "
        "Est = Seine-et-Marne/Meaux, Melun | Sud-Est = Val-de-Marne/Créteil | "
        "Sud = Essonne/Évry | Sud-Ouest = Yvelines/Versailles | Ouest = Hauts-de-Seine/Boulogne | "
        "Centre = Paris."
    ),
    "normandie": (
        "Départements : Calvados (14), Eure (27), Manche (50), Orne (61), Seine-Maritime (76). "
        "Villes : Rouen, Caen, Le Havre, Cherbourg, Évreux, Alençon, Dieppe, Fécamp, Lisieux, Granville. "
        "Repères : Nord-Ouest = Manche/Cherbourg, Cotentin | Nord = Seine-Maritime/Dieppe, Fécamp, côte d'Albâtre | "
        "Nord-Est = Seine-Maritime/Le Havre, Rouen | Est = Eure/Évreux | "
        "Centre = Calvados/Caen, Orne/Alençon | Sud = Orne intérieur."
    ),
    "nouvelle_aquitaine": (
        "Départements : Charente (16), Charente-Maritime (17), Corrèze (19), Creuse (23), Dordogne (24), "
        "Gironde (33), Landes (40), Lot-et-Garonne (47), Pyrénées-Atlantiques (64), Deux-Sèvres (79), "
        "Vienne (86), Haute-Vienne (87). "
        "Villes : Bordeaux, Limoges, Poitiers, Bayonne, Pau, La Rochelle, Angoulême, Brive-la-Gaillarde, Périgueux, Agen. "
        "Repères : Nord = Deux-Sèvres/Poitiers, Vienne/Poitiers | Nord-Ouest = Charente-Maritime/La Rochelle | "
        "Ouest = Gironde/Bordeaux, Landes/côte Atlantique | Sud-Ouest = Pyrénées-Atlantiques/Bayonne, Pau | "
        "Sud = piémont pyrénéen | Est = Haute-Vienne/Limoges, Creuse, Corrèze/Brive | "
        "Centre = Dordogne/Périgueux, Lot-et-Garonne/Agen."
    ),
    "occitanie": (
        "Départements : Ariège (09), Aude (11), Aveyron (12), Gard (30), Haute-Garonne (31), Gers (32), "
        "Hérault (34), Lot (46), Lozère (48), Hautes-Pyrénées (65), Pyrénées-Orientales (66), Tarn (81), "
        "Tarn-et-Garonne (82). "
        "Villes : Toulouse, Montpellier, Nîmes, Perpignan, Narbonne, Carcassonne, Albi, Tarbes, Cahors, Rodez, Mende. "
        "Repères : Nord = Lot/Cahors, Aveyron/Rodez, Lozère/Mende | Nord-Est = Gard/Nîmes | "
        "Est = Hérault/Montpellier, Gard, littoral méditerranéen | Sud-Est = Pyrénées-Orientales/Perpignan | "
        "Sud = piémont pyrénéen (Hautes-Pyrénées/Tarbes, Ariège) | Ouest = Gers, Tarn-et-Garonne/Montauban | "
        "Centre = Haute-Garonne/Toulouse, Tarn/Albi, Aude/Carcassonne."
    ),
    "pays_de_la_loire": (
        "Départements : Loire-Atlantique (44), Maine-et-Loire (49), Mayenne (53), Sarthe (72), Vendée (85). "
        "Villes : Nantes, Angers, Le Mans, Saint-Nazaire, La Roche-sur-Yon, Laval, Cholet, Les Sables-d'Olonne. "
        "Repères : Nord = Mayenne/Laval, Sarthe/Le Mans | Nord-Ouest = Loire-Atlantique nord/Saint-Nazaire | "
        "Ouest = Loire-Atlantique/Nantes, côte atlantique | Sud-Ouest = Vendée/Les Sables, La Roche-sur-Yon | "
        "Sud = Vendée intérieure, Maine-et-Loire sud/Cholet | Centre-Est = Maine-et-Loire/Angers."
    ),
    "provence_alpes_cote_azur": (
        "Départements : Alpes-de-Haute-Provence (04), Hautes-Alpes (05), Alpes-Maritimes (06), "
        "Bouches-du-Rhône (13), Var (83), Vaucluse (84). "
        "Villes : Marseille, Nice, Toulon, Aix-en-Provence, Avignon, Gap, Cannes, Antibes, "
        "Arles, Digne-les-Bains, Fréjus, Draguignan. "
        "Repères : Nord = Hautes-Alpes/Gap, Alpes-de-Haute-Provence/Digne | Nord-Ouest = Vaucluse/Avignon | "
        "Ouest = Bouches-du-Rhône/Marseille, Arles, Camargue | Centre = Var/Toulon, Fréjus | "
        "Est = Alpes-Maritimes/Nice, Cannes, Menton | Sud = littoral méditerranéen."
    ),
}

REGIONS_MAP = {k: v[0] for k, v in REGIONS_CONFIG.items()}


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

def process_topic(target_topic, topic_idx, date_context_str):
    decoded_topic = urllib.parse.unquote(target_topic)
    topic_title_slug = decoded_topic.rstrip('/').split('/')[-1]
    topic_title_slug = re.sub(r'^\d+-', '', topic_title_slug)
    topic_title_clean = topic_title_slug.replace('-', ' ').title()
    print(f"\n--- Sujet [{topic_idx+1}] : {topic_title_clean} ({target_topic}) ---")
    
    print(f"[{topic_idx+1}] Analyse de la pagination...")
    try:
        html_topic = fetch_url(target_topic)
    except Exception as e:
        print(f"Erreur sujet : {e}")
        return None
        
    pages = re.findall(r'\?page=(\d+)', html_topic)
    last_page = 1
    if pages:
        last_page = max(int(p) for p in pages)
    print(f"[{topic_idx+1}] Pages détectées : {last_page}")
    
    start_page = max(1, last_page - 2)
    all_comments = []
    all_authors = []
    
    print(f"[{topic_idx+1}] Chargement des commentaires des pages {start_page} à {last_page}...")
    for page in range(start_page, last_page + 1):
        page_url = f"{target_topic}?page={page}"
        try:
            html_page = fetch_url(page_url)
            page_comments = re.findall(r'<div[^>]*data-role=["\']commentContent["\'][^>]*>(.*?)</div>\s*</div>', html_page, re.DOTALL)
            page_authors = re.findall(r'<strong>\s*<a href=[^>]*class=["\']ipsType_break["\'][^>]*>(.*?)</a>', html_page)
            all_comments.extend(page_comments)
            all_authors.extend(page_authors)
        except Exception as e:
            print(f"Erreur page {page} : {e}")
            
    cleaned_comments_data = []
    for idx, comment in enumerate(all_comments):
        clean_comment = re.sub(r'<br\s*/?>', '\n', comment)
        clean_comment = re.sub(r'<[^>]+>', '', clean_comment).strip()
        clean_comment = re.sub(r'\n\s*\n', '\n', clean_comment)
        author = all_authors[idx] if idx < len(all_authors) else "Membre"
        cleaned_comments_data.append(f"Auteur: {author}\nMessage:\n{clean_comment}")
        
    recent_messages_text = "\n\n=======================\n\n".join(cleaned_comments_data[-20:])
    
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

    print(f"[{topic_idx+1}] Appel de l'IA pour l'analyse des scénarios météo...")
    system_prompt = """Tu es Patrick Marlière, météorologue expert de renommée nationale pour Monsieur Météo.

MISSION
À partir EXCLUSIVEMENT des discussions et analyses météorologiques fournies en entrée, tu dois produire un bulletin d'analyse météorologique professionnel, grand public, hyper-visuel, pédagogique et directement exploitable sur le web et les réseaux sociaux sans aucune modification manuelle.

RÈGLE D'OR N°1 : DATES EXACTES ET JOURS NOMMÉS DANS 100% DES SECTIONS
Dans TOUTES les sections (Résumé, Chronologie, Régions, Scénarios, Incertitudes, À Retenir, Posts Sociaux), tu devez mentionner les jours précis associés à leurs dates exactes (ex: Lundi 20 juillet, Mardi 21 juillet, Mercredi 22 juillet, Jeudi 23 juillet, Vendredi 24 juillet, Samedi 25 juillet, Dimanche 26 juillet). Ne dis plus jamais "début de semaine" ou "week-end" sans les associer directement à leur date.

RÈGLE D'OR N°2 : INTÉGRATION DE LA DATE DE GÉNÉRATION & PÉRIODE PERTINENTE
- Analyse avec attention la "Date actuelle de génération" transmise dans l'invite.
- Si le sujet correspond à la "Semaine en cours" : toute journée précédant cette date est déjà passée. Les prévisions doivent se concentrer EXCLUSIVEMENT sur la période allant de la date de génération au dimanche de cette semaine. Ignore ou mentionne comme "déjà écoulées" les journées passées.
- Si le sujet correspond à la "Semaine suivante" (Semaine future) : c'est la véritable semaine de tendance à moyen terme. Rédige les prévisions complètes jour par jour, du lundi au dimanche.

RÈGLE D'OR N°3 : PÉDAGOGIE SYNOPTIQUE VULGARISÉE
Explique de manière simple et pédagogique le mécanisme synoptique sous-jacent (goutte froide, dorsale anticyclonique, talweg, marais barométrique, flux océanique) en une phrase fluide pour montrer notre expertise météorologique sans perdre le grand public.

RÈGLE D'OR N°4 : IMPACTS CONCRETS SUR LA VIE QUOTIDIENNE
Mentionne systématiquement les répercussions pratiques du temps prévu : confort/ressenti thermique (chaleur lourde, fraîcheur humide), vacances et activités extérieures, transports/déplacements, travaux agricoles/BTP, orages ou pluies bénéfiques.

RÈGLE D'OR N°5 : CALIBRAGE DES SCÉNARIOS & RAISON DU CHOIX
Indique précisément POURQUOI le Scénario Majoritaire est privilégié par rapport aux deux autres.
- Majoritaire : ~130 à 150 mots maximum.
- Alternatif & Minoritaire : 80 à 120 mots maximum chacun.

RÈGLE D'OR N°6 : PACK MULTI-RÉSEAUX SOCIAUX CONÇU POUR MOBILES
Rédige 5 publications distinctes, spécifiquement adaptées à l'audience, au style et aux limites de caractères de chaque plateforme :
- **LinkedIn** : Storytelling expert météo captivant, ton pro et pédagogique. Paragraphes courts, émojis et hashtags ciblés. (250-300 mots)
- **Facebook** : Message chaleureux, axé vie quotidienne et communauté. Paragraphes aérés, émojis.
- **X (Twitter)** : Post court, percutant et dynamique. Limite stricte de 280 caractères, hashtags inclus.
- **TikTok** : Description de vidéo dynamique, phrases courtes, appel à l'action visuel et hashtags tendance.
- **Instagram** : Légende soignée, esthétique, invitant à la contemplation ou à la préparation, avec un appel à l'action pour lire le rapport HTML complet en bio.

VÉRIFICATION QUALITÉ AUTOMATIQUE SILENCIEUSE (AVANT D'ÉMETTRE) :
1. Les probabilités des 3 scénarios totalisent-elles EXACTEMENT 100% ?
2. Les jours passés pour la semaine en cours ont-ils bien été exclus des prévisions à venir ?
3. Le post X (Twitter) fait-il moins de 280 caractères ?
4. Toutes les dates et jours correspondent-ils à la semaine analysée ?
5. Aucune donnée chiffrée n'a-t-elle été inventée ?
6. Le post LinkedIn est-il en paragraphes très courts sans aucun markdown ?

FORMAT DE SORTIE OBLIGATOIRE - Utilise EXACTEMENT ces balises :

[SUBJECT_TITLE_LINE1]
Semaine X - Du Lundi DD au Dimanche DD Mois AAAA

[SUBJECT_TITLE_LINE2]
Accroche météo courte résumant le temps de la semaine avec dates exactes

[EXPRESS_SUMMARY]
2 phrases ultra-concises allant à l'essentiel avec les jours et dates précis (ex: Du Lundi 20 au Mercredi 22 juillet, temps sec et chaud...).

[EXPRESS_TREND]
1 à 3 mots max

[EXPRESS_TEMPERATURES]
1 à 3 mots max

[EXPRESS_PRECIPITATIONS]
1 à 3 mots max

[EXPRESS_MAIN_RISK]
1 à 3 mots max

[GLOBAL_CONFIDENCE_SCORE]
4/5 (ou 3/5, 5/5)

[GLOBAL_CONFIDENCE_DESC]
Une phrase courte expliquant la raison du niveau de confiance.

[TIMELINE_EARLY_WEEK]
Jours exacts : Prévisions, mécanisme synoptique vulgarisé et impacts concrets.

[TIMELINE_MID_WEEK]
Jours exacts : Évolution chronologique, ressenti et activités.

[TIMELINE_LATE_WEEK]
Jours exacts : Tendance pour la fin de semaine et vigilance.

[TIMELINE_WEEKEND]
Jours exacts : Prévisions pour le week-end et loisirs extérieurs.

[REGIONAL_HDF_NORTH]
1-2 phrases pour Hauts-de-France & Nord.

[REGIONAL_ATLANTIC]
1-2 phrases pour Façade Atlantique.

[REGIONAL_CENTRAL]
1-2 phrases pour Régions Centrales.

[REGIONAL_SOUTH]
1-2 phrases pour Moitié Sud.

[REGIONAL_MEDITERRANEAN]
1-2 phrases pour Pourtour Méditerranéen.

[REGIONAL_MOUNTAINS]
1-2 phrases pour Reliefs.

[SCENARIO_MAJORITAIRE_PROB]
65%

[SCENARIO_MAJORITAIRE_TITLE]
Titre synoptique court

[SCENARIO_MAJORITAIRE_DESC]
Description concise (~130-150 mots)

[SCENARIO_MEDIAN_PROB]
25%

[SCENARIO_MEDIAN_TITLE]
Titre synoptique court

[SCENARIO_MEDIAN_DESC]
Description concise (80-120 mots)

[SCENARIO_MINORITAIRE_PROB]
10%

[SCENARIO_MINORITAIRE_TITLE]
Titre synoptique court

[SCENARIO_MINORITAIRE_DESC]
Description concise (80-120 mots)

[KEY_UNCERTAINTIES]
- Incertitude 1
- Incertitude 2

[MONITORING_POINTS]
- Point de vigilance 1
- Point de vigilance 2

[KEY_TAKEAWAYS]
- Puce essentielle 1 avec date
- Puce essentielle 2 avec date
- Puce essentielle 3 avec date
- Puce essentielle 4 avec impact concret

[SOCIAL_LINKEDIN]
Post LinkedIn réseaux sociaux captivant en texte brut (250-300 mots) aéré en paragraphes très courts pour smartphone avec dates exactes et question d'interaction finale.

[SOCIAL_FACEBOOK]
Post Facebook chaleureux et aéré pour grand public, avec émojis et dates exactes.

[SOCIAL_TWITTER]
Post X (Twitter) percutant et court (MAXIMUM 280 caractères, espaces compris) avec hashtags.

[SOCIAL_TIKTOK]
Description TikTok avec accroches, émojis et hashtags ciblés.

[SOCIAL_INSTAGRAM]
Légende Instagram soignée et esthétique avec appel à l'action pour bio.

[LINKEDIN_HASHTAGS]
#Meteo #Previsions #France #Climat #MonsieurMeteo"""

    user_prompt = f"""Contexte de date : {date_context_str}

Voici les 20 derniers messages des prévisionnistes pour le sujet : {topic_title_clean}

{recent_messages_text}

Analyse ces discussions en appliquant scrupuleusement la vérification de cohérence et génère le rapport complet."""

    response = call_llm(system_prompt, user_prompt)
    
    data = None
    if response:
        try:
            print(f"[{topic_idx+1}] Parsing de la réponse de l'IA...")
            blocks = {
                "title_line1": r"\[SUBJECT_TITLE_LINE1\]\s*\n(.*?)(?=\n\s*\[|$)",
                "title_line2": r"\[SUBJECT_TITLE_LINE2\]\s*\n(.*?)(?=\n\s*\[|$)",
                "express_summary": r"\[EXPRESS_SUMMARY\]\s*\n(.*?)(?=\n\s*\[|$)",
                "express_trend": r"\[EXPRESS_TREND\]\s*\n(.*?)(?=\n\s*\[|$)",
                "express_temperatures": r"\[EXPRESS_TEMPERATURES\]\s*\n(.*?)(?=\n\s*\[|$)",
                "express_precipitations": r"\[EXPRESS_PRECIPITATIONS\]\s*\n(.*?)(?=\n\s*\[|$)",
                "express_main_risk": r"\[EXPRESS_MAIN_RISK\]\s*\n(.*?)(?=\n\s*\[|$)",
                "global_confidence_score": r"\[GLOBAL_CONFIDENCE_SCORE\]\s*\n(.*?)(?=\n\s*\[|$)",
                "global_confidence_desc": r"\[GLOBAL_CONFIDENCE_DESC\]\s*\n(.*?)(?=\n\s*\[|$)",
                "timeline_early": r"\[TIMELINE_EARLY_WEEK\]\s*\n(.*?)(?=\n\s*\[|$)",
                "timeline_mid": r"\[TIMELINE_MID_WEEK\]\s*\n(.*?)(?=\n\s*\[|$)",
                "timeline_late": r"\[TIMELINE_LATE_WEEK\]\s*\n(.*?)(?=\n\s*\[|$)",
                "timeline_weekend": r"\[TIMELINE_WEEKEND\]\s*\n(.*?)(?=\n\s*\[|$)",
                "regional_hdf_north": r"\[REGIONAL_HDF_NORTH\]\s*\n(.*?)(?=\n\s*\[|$)",
                "regional_atlantic": r"\[REGIONAL_ATLANTIC\]\s*\n(.*?)(?=\n\s*\[|$)",
                "regional_central": r"\[REGIONAL_CENTRAL\]\s*\n(.*?)(?=\n\s*\[|$)",
                "regional_south": r"\[REGIONAL_SOUTH\]\s*\n(.*?)(?=\n\s*\[|$)",
                "regional_mediterranean": r"\[REGIONAL_MEDITERRANEAN\]\s*\n(.*?)(?=\n\s*\[|$)",
                "regional_mountains": r"\[REGIONAL_MOUNTAINS\]\s*\n(.*?)(?=\n\s*\[|$)",
                "majoritaire_prob": r"\[SCENARIO_MAJORITAIRE_PROB\]\s*\n(.*?)(?=\n\s*\[|$)",
                "majoritaire_title": r"\[SCENARIO_MAJORITAIRE_TITLE\]\s*\n(.*?)(?=\n\s*\[|$)",
                "majoritaire_desc": r"\[SCENARIO_MAJORITAIRE_DESC\]\s*\n(.*?)(?=\n\s*\[|$)",
                "median_prob": r"\[SCENARIO_MEDIAN_PROB\]\s*\n(.*?)(?=\n\s*\[|$)",
                "median_title": r"\[SCENARIO_MEDIAN_TITLE\]\s*\n(.*?)(?=\n\s*\[|$)",
                "median_desc": r"\[SCENARIO_MEDIAN_DESC\]\s*\n(.*?)(?=\n\s*\[|$)",
                "minoritaire_prob": r"\[SCENARIO_MINORITAIRE_PROB\]\s*\n(.*?)(?=\n\s*\[|$)",
                "minoritaire_title": r"\[SCENARIO_MINORITAIRE_TITLE\]\s*\n(.*?)(?=\n\s*\[|$)",
                "minoritaire_desc": r"\[SCENARIO_MINORITAIRE_DESC\]\s*\n(.*?)(?=\n\s*\[|$)",
                "key_uncertainties": r"\[KEY_UNCERTAINTIES\]\s*\n(.*?)(?=\n\s*\[|$)",
                "monitoring_points": r"\[MONITORING_POINTS\]\s*\n(.*?)(?=\n\s*\[|$)",
                "key_takeaways": r"\[KEY_TAKEAWAYS\]\s*\n(.*?)(?=\n\s*\[|$)",
                "social_linkedin": r"\[SOCIAL_LINKEDIN\]\s*\n(.*?)(?=\n\s*\[|$)",
                "social_facebook": r"\[SOCIAL_FACEBOOK\]\s*\n(.*?)(?=\n\s*\[|$)",
                "social_twitter": r"\[SOCIAL_TWITTER\]\s*\n(.*?)(?=\n\s*\[|$)",
                "social_tiktok": r"\[SOCIAL_TIKTOK\]\s*\n(.*?)(?=\n\s*\[|$)",
                "social_instagram": r"\[SOCIAL_INSTAGRAM\]\s*\n(.*?)(?=\n\s*\[|$)",
                "linkedin_hashtags": r"\[LINKEDIN_HASHTAGS\]\s*\n(.*?)(?=\n\s*\[|$)",
            }
            
            parsed = {}
            for key, pattern in blocks.items():
                match = re.search(pattern, response, re.DOTALL)
                if match:
                    parsed[key] = match.group(1).strip()
                else:
                    parsed[key] = ""
            
            if (parsed["title_line1"] or parsed["title_line2"]) and (parsed["express_summary"] or parsed["majoritaire_desc"]):
                data = {
                    "title_line1": parsed["title_line1"] or topic_title_clean,
                    "title_line2": parsed["title_line2"] or "Tendances et synthèses météorologiques",
                    "express": {
                        "summary": parsed["express_summary"],
                        "trend": parsed["express_trend"],
                        "temperatures": parsed["express_temperatures"],
                        "precipitations": parsed["express_precipitations"],
                        "main_risk": parsed["express_main_risk"],
                    },
                    "confidence": {
                        "score": parsed["global_confidence_score"] or "4/5",
                        "desc": parsed["global_confidence_desc"],
                    },
                    "timeline": {
                        "early": parsed["timeline_early"],
                        "mid": parsed["timeline_mid"],
                        "late": parsed["timeline_late"],
                        "weekend": parsed["timeline_weekend"],
                    },
                    "regional": {
                        "hdf_north": parsed["regional_hdf_north"],
                        "atlantic": parsed["regional_atlantic"],
                        "central": parsed["regional_central"],
                        "south": parsed["regional_south"],
                        "mediterranean": parsed["regional_mediterranean"],
                        "mountains": parsed["regional_mountains"],
                    },
                    "scenarios": {
                        "majoritaire": {"prob": parsed["majoritaire_prob"] or "65%", "title": parsed["majoritaire_title"] or "Scénario Majoritaire", "desc": parsed["majoritaire_desc"]},
                        "median": {"prob": parsed["median_prob"] or "25%", "title": parsed["median_title"] or "Scénario Alternatif", "desc": parsed["median_desc"]},
                        "minoritaire": {"prob": parsed["minoritaire_prob"] or "10%", "title": parsed["minoritaire_title"] or "Scénario Minoritaire", "desc": parsed["minoritaire_desc"]}
                    },
                    "key_uncertainties": parsed["key_uncertainties"],
                    "monitoring_points": parsed["monitoring_points"],
                    "key_takeaways": parsed["key_takeaways"],
                    "social_pack": {
                        "linkedin": parsed["social_linkedin"],
                        "facebook": parsed["social_facebook"],
                        "twitter": parsed["social_twitter"],
                        "tiktok": parsed["social_tiktok"],
                        "instagram": parsed["social_instagram"],
                    },
                    "linkedin_hashtags": parsed["linkedin_hashtags"],
                }
                print(f"[{topic_idx+1}] Parsing textuel réussi avec succès !")
        except Exception as e:
            print(f"[{topic_idx+1}] Erreur parsing textuel : {e}")
            
    if not data:
        print(f"[{topic_idx+1}] ERREUR : Parsing échoué — vérifier les logs du LLM ci-dessus.")
        return None
    return {
        "data": data,
        "images": downloaded_images,
        "raw_comments": recent_messages_text  # conservé pour injection directe dans les bulletins régionaux
    }

def process_region_query(r_key, r_name, recent_messages_text, topic_title_clean, date_context_str, topic_idx):
    """Même prompt que le national, 2 semaines couverts, même richesse — focalisé sur r_name."""
    geo_anchors = REGIONS_GEO.get(r_key, "Non spécifié")
    system_prompt = f"""Tu es Patrick Marlière, météorologue expert de renommée nationale pour Monsieur Météo.

MISSION
À partir EXCLUSIVEMENT des discussions et analyses météorologiques fournies en entrée, tu dois produire un bulletin d'analyse météorologique professionnel et complet pour la région : {r_name}
Le bulletin doit couvrir les DEUX semaines fournies en contexte : la semaine en cours ET la semaine suivante.

RÈGLE D'OR N°0 : RÉALITÉ SAISONNIÈRE & FOCUS GÉOGRAPHIQUE
- La date et la saison sont précisées dans le contexte. Respecte-les ABSOLUMENT.
- En été (juin/juillet/août), les mentions de neige en plaine, de gel, de températures négatives sont INTERDITES sauf en haute altitude (>1500m) si les sources le mentionnent EXPLICITEMENT.
- Toutes les analyses, températures, risques et impacts doivent concerner EXCLUSIVEMENT {r_name} (ses départements, villes, reliefs ou zones côtières).
- Pour t'aider à faire le lien entre les termes généraux des prévisionnistes (comme 'nord-ouest de la France', 'sud-ouest', 'flanc est', etc.) et ta région spécifique, voici tes points d'ancrage géographiques officiels :
  === ANCRAGE GÉOGRAPHIQUE DE LA RÉGION {r_name.upper()} ===
  {geo_anchors}
  ======================================================
- Utilise ces repères pour savoir si les mentions du forum s'appliquent à ta région ou non. Si les messages parlent d'un phénomène touchant une zone qui correspond à un de tes repères, décris-le pour ta région. Sinon, si l'information n'est vraiment pas applicable ou non précisée pour ta région, écris "Information non précisée dans les sources pour {r_name}". Ne déduis jamais depuis une autre région sans rapport.

RÈGLE D'OR N°1 : DATES EXACTES ET JOURS NOMMÉS DANS 100% DES SECTIONS
Dans TOUTES les sections, tu dois mentionner les jours précis avec leurs dates exactes (ex: Lundi 27 Juillet, Mardi 28 Juillet).

RÈGLE D'OR N°2 : INTÉGRATION DE LA DATE DE GÉNÉRATION
Analyse la "Date actuelle de génération". Les journées déjà passées sont exclues des prévisions à venir.

RÈGLE D'OR N°3 : PÉDAGOGIE SYNOPTIQUE VULGARISÉE
Explique le mécanisme synoptique (dorsale, talweg, goutte froide, flux océanique) en une phrase simple et pédagogique.

RÈGLE D'OR N°4 : IMPACTS CONCRETS SUR LA VIE QUOTIDIENNE EN {r_name.upper()}
Mentionne les répercussions pratiques : confort thermique, vacances, transports, agriculture/BTP, orages locaux.

RÈGLE D'OR N°5 : CALIBRAGE DES SCÉNARIOS POUR {r_name.upper()}
3 scénarios calibrés pour cette région spécifique. Les probabilités totalisent EXACTEMENT 100%.
- Majoritaire : ~130 à 150 mots maximum.
- Alternatif & Minoritaire : 80 à 120 mots maximum chacun.

RÈGLE D'OR N°6 : PACK MULTI-RÉSEAUX SOCIAUX POUR {r_name.upper()}
5 publications distinctes adaptées à chaque plateforme, mentionnant la région {r_name} explicitement :
- LinkedIn (250-300 mots, storytelling expert)
- Facebook (message chaleureux, communauté locale)
- X/Twitter (MAXIMUM 280 caractères, hashtags)
- TikTok (description vidéo dynamique)
- Instagram (légende soignée, CTA bio)

VÉRIFICATION QUALITÉ AUTOMATIQUE SILENCIEUSE :
1. Probabilités des 3 scénarios = exactement 100% ?
2. Post Twitter < 280 caractères ?
3. Toutes les données concernent bien {r_name} ?
4. Aucune donnée chiffrée inventée ?

FORMAT DE SORTIE OBLIGATOIRE - Utilise EXACTEMENT ces balises :

[SUBJECT_TITLE_LINE1]
Semaine X - Du Lundi DD au Dimanche DD Mois AAAA — {r_name}

[SUBJECT_TITLE_LINE2]
Accroche météo courte résumant le temps de la semaine pour {r_name}

[EXPRESS_SUMMARY]
2 phrases ultra-concises avec jours et dates précis pour {r_name}.

[EXPRESS_TREND]
1 à 3 mots max

[EXPRESS_TEMPERATURES]
1 à 3 mots max

[EXPRESS_PRECIPITATIONS]
1 à 3 mots max

[EXPRESS_MAIN_RISK]
1 à 3 mots max

[GLOBAL_CONFIDENCE_SCORE]
4/5 (ou 3/5, 5/5)

[GLOBAL_CONFIDENCE_DESC]
Une phrase courte expliquant la raison du niveau de confiance pour {r_name}.

[TIMELINE_EARLY_WEEK]
Semaine en cours — début (Lundi/Mardi) : météo, mécanisme synoptique et impacts pour {r_name}.

[TIMELINE_MID_WEEK]
Semaine en cours — fin (Mercredi à Dimanche) : évolution chronologique pour {r_name}.

[TIMELINE_LATE_WEEK]
Semaine suivante — début (Lundi/Mardi) : premières tendances pour {r_name}.

[TIMELINE_WEEKEND]
Semaine suivante — fin (Mercredi à Dimanche) : tendances de fin de semaine pour {r_name}.

[REGIONAL_HDF_NORTH]
Sous-zone ou secteur nord / nord-ouest de {r_name} (si pertinent).

[REGIONAL_ATLANTIC]
Sous-zone ou secteur ouest / façade maritime de {r_name} (si pertinent).

[REGIONAL_CENTRAL]
Secteur central / intérieur de {r_name} (si pertinent).

[REGIONAL_SOUTH]
Sous-zone ou secteur sud de {r_name} (si pertinent).

[REGIONAL_MEDITERRANEAN]
Secteur méditerranéen / côtier de {r_name} (si pertinent, sinon "Non applicable").

[REGIONAL_MOUNTAINS]
Secteur montagneux / relief de {r_name} (si pertinent, sinon "Non applicable").

[SCENARIO_MAJORITAIRE_PROB]
65%

[SCENARIO_MAJORITAIRE_TITLE]
Titre synoptique court pour {r_name}

[SCENARIO_MAJORITAIRE_DESC]
Description concise (~130-150 mots) pour {r_name}

[SCENARIO_MEDIAN_PROB]
25%

[SCENARIO_MEDIAN_TITLE]
Titre synoptique court

[SCENARIO_MEDIAN_DESC]
Description concise (80-120 mots) pour {r_name}

[SCENARIO_MINORITAIRE_PROB]
10%

[SCENARIO_MINORITAIRE_TITLE]
Titre synoptique court

[SCENARIO_MINORITAIRE_DESC]
Description concise (80-120 mots) pour {r_name}

[KEY_UNCERTAINTIES]
- Incertitude 1 propre à {r_name}
- Incertitude 2 propre à {r_name}

[MONITORING_POINTS]
- Point de vigilance 1 pour {r_name}
- Point de vigilance 2 pour {r_name}

[KEY_TAKEAWAYS]
- Puce essentielle 1 avec date pour {r_name}
- Puce essentielle 2 avec date pour {r_name}
- Puce essentielle 3 avec date pour {r_name}
- Puce essentielle 4 avec impact concret pour {r_name}

[SOCIAL_LINKEDIN]
Post LinkedIn expert pour {r_name} (250-300 mots, paragraphes courts smartphone).

[SOCIAL_FACEBOOK]
Post Facebook chaleureux pour la communauté de {r_name}, avec émojis.

[SOCIAL_TWITTER]
Post X (MAXIMUM 280 caractères) pour {r_name} avec hashtags.

[SOCIAL_TIKTOK]
Description TikTok pour {r_name} avec accroches, émojis et hashtags.

[SOCIAL_INSTAGRAM]
Légende Instagram pour {r_name} avec CTA bio.

[LINKEDIN_HASHTAGS]
#Meteo #{r_name.replace('-', '').replace(' ', '').replace("'", '')} #Previsions #France #MonsieurMeteo"""

    user_prompt = f"""Contexte de date : {date_context_str}
Région analysée : {r_name}

Voici les analyses des prévisionnistes pour : {topic_title_clean}

{recent_messages_text}

Analyse ces discussions EXCLUSIVEMENT pour la région {r_name} et génère le rapport complet au format spécifié."""

    response = None
    for attempt in range(1, 4):
        print(f"[Région {r_name}] Tentative {attempt}/3...")
        r = call_llm(system_prompt, user_prompt)
        if r:
            response = r
            break

    if not response:
        print(f"[Région {r_name}] ERREUR : Pas de réponse LLM")
        return r_key, None

    blocks = {
        "title_line1": r"\[SUBJECT_TITLE_LINE1\]\s*\n(.*?)(?=\n\s*\[|$)",
        "title_line2": r"\[SUBJECT_TITLE_LINE2\]\s*\n(.*?)(?=\n\s*\[|$)",
        "express_summary": r"\[EXPRESS_SUMMARY\]\s*\n(.*?)(?=\n\s*\[|$)",
        "express_trend": r"\[EXPRESS_TREND\]\s*\n(.*?)(?=\n\s*\[|$)",
        "express_temperatures": r"\[EXPRESS_TEMPERATURES\]\s*\n(.*?)(?=\n\s*\[|$)",
        "express_precipitations": r"\[EXPRESS_PRECIPITATIONS\]\s*\n(.*?)(?=\n\s*\[|$)",
        "express_main_risk": r"\[EXPRESS_MAIN_RISK\]\s*\n(.*?)(?=\n\s*\[|$)",
        "global_confidence_score": r"\[GLOBAL_CONFIDENCE_SCORE\]\s*\n(.*?)(?=\n\s*\[|$)",
        "global_confidence_desc": r"\[GLOBAL_CONFIDENCE_DESC\]\s*\n(.*?)(?=\n\s*\[|$)",
        "timeline_early": r"\[TIMELINE_EARLY_WEEK\]\s*\n(.*?)(?=\n\s*\[|$)",
        "timeline_mid": r"\[TIMELINE_MID_WEEK\]\s*\n(.*?)(?=\n\s*\[|$)",
        "timeline_late": r"\[TIMELINE_LATE_WEEK\]\s*\n(.*?)(?=\n\s*\[|$)",
        "timeline_weekend": r"\[TIMELINE_WEEKEND\]\s*\n(.*?)(?=\n\s*\[|$)",
        "regional_hdf_north": r"\[REGIONAL_HDF_NORTH\]\s*\n(.*?)(?=\n\s*\[|$)",
        "regional_atlantic": r"\[REGIONAL_ATLANTIC\]\s*\n(.*?)(?=\n\s*\[|$)",
        "regional_central": r"\[REGIONAL_CENTRAL\]\s*\n(.*?)(?=\n\s*\[|$)",
        "regional_south": r"\[REGIONAL_SOUTH\]\s*\n(.*?)(?=\n\s*\[|$)",
        "regional_mediterranean": r"\[REGIONAL_MEDITERRANEAN\]\s*\n(.*?)(?=\n\s*\[|$)",
        "regional_mountains": r"\[REGIONAL_MOUNTAINS\]\s*\n(.*?)(?=\n\s*\[|$)",
        "majoritaire_prob": r"\[SCENARIO_MAJORITAIRE_PROB\]\s*\n(.*?)(?=\n\s*\[|$)",
        "majoritaire_title": r"\[SCENARIO_MAJORITAIRE_TITLE\]\s*\n(.*?)(?=\n\s*\[|$)",
        "majoritaire_desc": r"\[SCENARIO_MAJORITAIRE_DESC\]\s*\n(.*?)(?=\n\s*\[|$)",
        "median_prob": r"\[SCENARIO_MEDIAN_PROB\]\s*\n(.*?)(?=\n\s*\[|$)",
        "median_title": r"\[SCENARIO_MEDIAN_TITLE\]\s*\n(.*?)(?=\n\s*\[|$)",
        "median_desc": r"\[SCENARIO_MEDIAN_DESC\]\s*\n(.*?)(?=\n\s*\[|$)",
        "minoritaire_prob": r"\[SCENARIO_MINORITAIRE_PROB\]\s*\n(.*?)(?=\n\s*\[|$)",
        "minoritaire_title": r"\[SCENARIO_MINORITAIRE_TITLE\]\s*\n(.*?)(?=\n\s*\[|$)",
        "minoritaire_desc": r"\[SCENARIO_MINORITAIRE_DESC\]\s*\n(.*?)(?=\n\s*\[|$)",
        "key_uncertainties": r"\[KEY_UNCERTAINTIES\]\s*\n(.*?)(?=\n\s*\[|$)",
        "monitoring_points": r"\[MONITORING_POINTS\]\s*\n(.*?)(?=\n\s*\[|$)",
        "key_takeaways": r"\[KEY_TAKEAWAYS\]\s*\n(.*?)(?=\n\s*\[|$)",
        "social_linkedin": r"\[SOCIAL_LINKEDIN\]\s*\n(.*?)(?=\n\s*\[|$)",
        "social_facebook": r"\[SOCIAL_FACEBOOK\]\s*\n(.*?)(?=\n\s*\[|$)",
        "social_twitter": r"\[SOCIAL_TWITTER\]\s*\n(.*?)(?=\n\s*\[|$)",
        "social_tiktok": r"\[SOCIAL_TIKTOK\]\s*\n(.*?)(?=\n\s*\[|$)",
        "social_instagram": r"\[SOCIAL_INSTAGRAM\]\s*\n(.*?)(?=\n\s*\[|$)",
        "linkedin_hashtags": r"\[LINKEDIN_HASHTAGS\]\s*\n(.*?)(?=\n\s*\[|$)",
    }

    parsed = {}
    for key, pattern in blocks.items():
        match = re.search(pattern, response, re.DOTALL)
        parsed[key] = match.group(1).strip() if match else ""

    data = {
        "title_line1": parsed["title_line1"] or f"Semaine — {r_name}",
        "title_line2": parsed["title_line2"] or f"Tendances pour {r_name}",
        "region_name": r_name,
        "express": {
            "summary": parsed["express_summary"],
            "trend": parsed["express_trend"],
            "temperatures": parsed["express_temperatures"],
            "precipitations": parsed["express_precipitations"],
            "main_risk": parsed["express_main_risk"],
        },
        "confidence": {
            "score": parsed["global_confidence_score"] or "4/5",
            "desc": parsed["global_confidence_desc"],
        },
        "timeline": {
            "early": parsed["timeline_early"],
            "mid": parsed["timeline_mid"],
            "late": parsed["timeline_late"],
            "weekend": parsed["timeline_weekend"],
        },
        "regional": {
            "hdf_north": parsed["regional_hdf_north"],
            "atlantic": parsed["regional_atlantic"],
            "central": parsed["regional_central"],
            "south": parsed["regional_south"],
            "mediterranean": parsed["regional_mediterranean"],
            "mountains": parsed["regional_mountains"],
        },
        "scenarios": {
            "majoritaire": {"prob": parsed["majoritaire_prob"] or "65%", "title": parsed["majoritaire_title"], "desc": parsed["majoritaire_desc"]},
            "median": {"prob": parsed["median_prob"] or "25%", "title": parsed["median_title"], "desc": parsed["median_desc"]},
            "minoritaire": {"prob": parsed["minoritaire_prob"] or "10%", "title": parsed["minoritaire_title"], "desc": parsed["minoritaire_desc"]},
        },
        "key_uncertainties": parsed["key_uncertainties"],
        "monitoring_points": parsed["monitoring_points"],
        "key_takeaways": parsed["key_takeaways"],
        "social_pack": {
            "linkedin": parsed["social_linkedin"],
            "facebook": parsed["social_facebook"],
            "twitter": parsed["social_twitter"],
            "tiktok": parsed["social_tiktok"],
            "instagram": parsed["social_instagram"],
        },
        "linkedin_hashtags": parsed["linkedin_hashtags"],
    }

    print(f"[Région {r_name}] Bulletin parsé avec succès !")
    return r_key, data

def clean_html_for_email(html_content):
    # Enlever les boutons de copie, les scripts/onclick et les images base64 (trop lourdes pour SFR/Gmail inline)
    cleaned = re.sub(r'<div class="copy-note">.*?</div>', '', html_content, flags=re.DOTALL)
    cleaned = re.sub(r'\s*onclick="[^"]*"', '', cleaned)
    # Supprimer les blocs img base64 (src="data:image/...") qui gonflent le corps et le font rejeter
    cleaned = re.sub(r'<div class="meteo-image-card".*?</div>\s*</div>', '', cleaned, flags=re.DOTALL)
    cleaned = re.sub(r'<div class="meteo-images-container".*?</div>\s*</div>', '', cleaned, flags=re.DOTALL)
    return cleaned

def main():
    print(f"1. Chargement de l'index du forum : {INDEX_URL}")
    try:
        html_index = fetch_url(INDEX_URL)
    except Exception as e:
        print(f"Erreur index : {e}")
        sys.exit(1)
        
    topic_links = re.findall(r'href=["\'](https://forums.infoclimat.fr/f/topic/\d+-[^"\']+)["\']', html_index)
    clean_topics = []
    seen = set()
    for link in topic_links:
        base_link = link.split('?')[0].split('#')[0]
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

    # Extraction et tri robuste des numéros de semaine pour l'ordre chronologique
    current_iso_week = now.isocalendar()[1]

    def get_topic_week_num(url):
        match = re.search(r'semaine-(\d+)', url.lower())
        return int(match.group(1)) if match else 0

    # Filtrer : garder uniquement les sujets dont le n° de semaine est dans la fenêtre
    # [semaine_courante - 1 .. semaine_courante + 4] pour éviter les anciens fils hiver/printemps
    # La tolérance -1 couvre le cas du lundi matin où le sujet "semaine en cours" n'est pas encore créé.
    relevant_topics = [
        t for t in clean_topics
        if current_iso_week - 1 <= get_topic_week_num(t) <= current_iso_week + 4
    ]

    if not relevant_topics:
        # Fallback : prendre les 2 topics avec le plus grand numéro de semaine
        print(f"[WARN] Aucun topic dans la fenêtre semaine {current_iso_week}. Fallback sur les 2 plus récents.")
        relevant_topics = sorted(clean_topics, key=get_topic_week_num, reverse=True)[:2]

    # Trier par numéro de semaine croissant : semaine en cours d'abord, suivante ensuite
    relevant_topics.sort(key=get_topic_week_num)
    print(f"[INFO] Topics retenus (semaine ISO {current_iso_week}) : {[get_topic_week_num(t) for t in relevant_topics]} → {relevant_topics}")

    # Construire la liste des topics à traiter (toujours 2 semaines si disponibles)
    topics_to_process = []
    if len(relevant_topics) >= 2:
        topics_to_process = [
            (relevant_topics[0], "cours", f"Date actuelle de génération : {today_str}\nType de semaine : Semaine en cours\nPériode à analyser : {jours_restants_cours_str} (jours restants uniquement). Les journées antérieures au {today_str} sont déjà passées, concentre-toi sur la fin de semaine."),
            (relevant_topics[1], "future", f"Date actuelle de génération : {today_str}\nType de semaine : Semaine suivante (Tendance à moyen terme)\nPériode à analyser : {semaine_suivante_str} (semaine complète).")
        ]
    else:
        topics_to_process = [
            (relevant_topics[0], "cours", f"Date actuelle de génération : {today_str}\nSemaine en cours : {semaine_cours_str} (jours restants : {jours_restants_cours_str})\nSemaine suivante : {semaine_suivante_str}.")
        ]

    results = []
    for idx, (topic, sem_type, date_context) in enumerate(topics_to_process):
        res = process_topic(topic, idx, date_context)
        if res:
            results.append(res)
            
    if not results:
        print("Aucun sujet n'a pu être traité.")
        sys.exit(1)
        
    # Style CSS Premium & Responsive (Stripe-inspired)
    style = """
    * { box-sizing: border-box; }
    body { margin: 0; background: #f1f5f9; font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; color: #0f172a; font-size: 16px; line-height: 1.6; }
    .wrap { max-width: 920px; margin: 24px auto; background: #ffffff; border: 1px solid #e2e8f0; border-radius: 24px; overflow: hidden; box-shadow: 0 20px 25px -5px rgb(0 0 0 / 0.05), 0 8px 10px -6px rgb(0 0 0 / 0.05); }
    .pad { padding: 32px; }
    .header { padding: 40px 32px; background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); color: #ffffff; border-bottom: 1px solid #334155; }
    .kicker { font-size: 12px; letter-spacing: 2px; text-transform: uppercase; font-weight: 800; color: #38bdf8; margin-bottom: 4px; }
    .hero-title { font-size: 32px; line-height: 1.15; margin: 8px 0; font-weight: 800; letter-spacing: -0.5px; }
    .sub { font-size: 15px; line-height: 1.5; color: #94a3b8; }
    .section { margin-top: 36px; }
    .section-title { font-size: 14px; letter-spacing: 1px; text-transform: uppercase; color: #1e293b; font-weight: 800; border-bottom: 1px solid #e2e8f0; padding-bottom: 8px; margin-bottom: 16px; display: flex; align-items: center; gap: 8px; }
    .week { border: 1px solid #e2e8f0; border-radius: 20px; overflow: hidden; margin-top: 24px; background: #ffffff; box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.05); }
    .week-head { padding: 24px; background: #f8fafc; border-bottom: 1px solid #e2e8f0; }
    .week-head h2 { font-size: 22px; line-height: 1.25; margin: 0 0 6px; color: #0f172a; font-weight: 800; }
    .week-head p { margin: 0; font-size: 15px; line-height: 1.5; color: #475569; }
    
    .alert { padding: 20px; border-radius: 16px; margin-top: 20px; border: 1px solid transparent; }
    .alert .eyebrow { font-size: 11px; text-transform: uppercase; letter-spacing: 1.5px; font-weight: 800; margin-bottom: 6px; }
    .alert h3 { font-size: 18px; line-height: 1.4; margin: 6px 0 8px; font-weight: 700; }
    .alert p { font-size: 14.5px; line-height: 1.5; margin: 0; }
    
    .alert.orange { background: #fffbeb; color: #78350f; border-color: #fef3c7; }
    .alert.orange .eyebrow { color: #d97706; }
    .alert.orange h3 { color: #78350f; }
    .alert.orange p { color: #92400e; }
    
    .alert.blue { background: #eff6ff; color: #1e3a8a; border-color: #dbeafe; }
    .alert.blue .eyebrow { color: #2563eb; }
    .alert.blue h3 { color: #1e3a8a; }
    .alert.blue p { color: #1e40af; }
    
    .alert.green { background: #f0fdf4; color: #14532d; border-color: #dcfce7; }
    .alert.green .eyebrow { color: #16a34a; }
    .alert.green h3 { color: #14532d; }
    .alert.green p { color: #166534; }
    
    .grid2 { display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px; margin: 16px 0; }
    .grid3 { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin: 16px 0; }
    .grid4 { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin: 16px 0; }
    
    .metric { border: 1px solid #e2e8f0; background: #ffffff; border-radius: 16px; padding: 16px; text-align: center; display: flex; flex-direction: column; justify-content: center; min-height: 90px; box-shadow: 0 1px 2px 0 rgb(0 0 0 / 0.02); transition: transform 0.2s, box-shadow 0.2s; }
    .metric:hover { transform: translateY(-2px); box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.05); }
    .metric .big { font-size: 26px; font-weight: 800; color: #0f172a; line-height: 1.1; }
    .metric .label { margin-top: 6px; font-size: 11px; line-height: 1.4; text-transform: uppercase; letter-spacing: 0.5px; color: #64748b; font-weight: 700; }
    .metric.hot .big { color: #ea580c; }
    .metric.risk .big { color: #dc2626; }
    .metric.good .big { color: #16a34a; }
    
    .chips { margin: 12px 0 -4px; display: flex; flex-wrap: wrap; gap: 6px; }
    .chip { display: inline-block; padding: 5px 12px; border-radius: 9999px; background: #f1f5f9; color: #334155; font-size: 12px; font-weight: 600; border: 1px solid #e2e8f0; }
    .chip.warn { background: #fef3c7; color: #92400e; border-color: #fde68a; }
    .chip.red { background: #fee2e2; color: #991b1b; border-color: #fca5a5; }
    .chip.green { background: #dcfce7; color: #15803d; border-color: #bbf7d0; }
    
    .timeline-table { width: 100%; display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; border-collapse: separate; margin: 16px 0; }
    .timeline-table tbody, .timeline-table tr { display: contents; }
    .timeline-table td { display: block; background: #f8fafc; border: 1px solid #e2e8f0; border-top: 4px solid #0284c7; border-radius: 16px; padding: 16px; transition: border-color 0.2s; }
    .timeline-table td:hover { border-color: #cbd5e1; }
    .timeline-table strong { font-size: 11px; text-transform: uppercase; color: #0284c7; letter-spacing: 0.5px; display: block; margin-bottom: 6px; font-weight: 800; }
    .timeline-table .dates { font-size: 14px; font-weight: 700; color: #0f172a; margin: 4px 0 8px; }
    .timeline-table .keys { font-size: 13.5px; line-height: 1.5; color: #334155; }
    
    .barbox { border: 1px solid #e2e8f0; border-radius: 16px; padding: 20px; background: #ffffff; box-shadow: 0 1px 2px 0 rgb(0 0 0 / 0.02); }
    .barrow { margin: 12px 0; }
    .barlabel { display: flex; justify-content: space-between; font-size: 12px; font-weight: 700; color: #475569; margin-bottom: 6px; }
    .barlabel span { display: inline-block; }
    .barlabel .right { text-align: right; font-weight: 800; color: #0f172a; }
    .track { height: 10px; background: #f1f5f9; border-radius: 999px; overflow: hidden; }
    .fill { height: 10px; border-radius: 999px; background: #0284c7; }
    .fill.orange { background: #d97706; }
    .fill.red { background: #dc2626; }
    .fill.green { background: #16a34a; }
    .fill.gray { background: #64748b; }
    .caption { font-size: 12px; color: #64748b; line-height: 1.5; margin-top: 12px; }
    
    .region { border: 1px solid #e2e8f0; border-radius: 16px; padding: 18px; background: #ffffff; box-shadow: 0 1px 2px 0 rgb(0 0 0 / 0.02); transition: border-color 0.2s; }
    .region:hover { border-color: #cbd5e1; }
    .region h4 { margin: 0 0 8px; font-size: 14px; color: #0f172a; font-weight: 800; }
    .region .numbers { font-size: 20px; color: #d97706; font-weight: 800; margin-bottom: 8px; }
    .region p { margin: 0; font-size: 14px; line-height: 1.55; color: #475569; }
    
    .conf { display: flex; align-items: stretch; border: 1px solid #e2e8f0; border-radius: 16px; overflow: hidden; background: #ffffff; box-shadow: 0 1px 2px 0 rgb(0 0 0 / 0.02); }
    .conf-score { width: 110px; display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 16px; background: #f0fdf4; border-right: 1px solid #e2e8f0; flex-shrink: 0; text-align: center; }
    .conf-score.conf-badge-orange { background: #fffbeb; border-right-color: #fef3c7; }
    .conf-score.conf-badge-red { background: #fef2f2; border-right-color: #fee2e2; }
    .conf-score .big { font-size: 32px; font-weight: 800; color: #16a34a; line-height: 1; }
    .conf-score .big.conf-text-orange { color: #d97706; }
    .conf-score .big.conf-text-red { color: #dc2626; }
    .conf-text { padding: 16px 20px; font-size: 14px; line-height: 1.55; color: #334155; display: flex; align-items: center; }
    
    .listbox { border-left: 4px solid #ea580c; background: #fff7ed; border-radius: 16px; padding: 18px 20px; border: 1px solid #ffedd5; border-left-width: 5px; }
    .listbox ul { margin: 0; padding-left: 20px; }
    .listbox li { font-size: 14px; line-height: 1.55; color: #7c2d12; margin: 6px 0; }
    
    .scenario { border: 1px solid #e2e8f0; border-radius: 16px; padding: 18px; margin: 12px 0; background: #ffffff; box-shadow: 0 1px 2px 0 rgb(0 0 0 / 0.02); transition: transform 0.15s; }
    .scenario:hover { transform: scale(1.005); }
    .scenario.major { border-left: 5px solid #16a34a; }
    .scenario.medium { border-left: 5px solid #ea580c; }
    .scenario.minor { border-left: 5px solid #dc2626; }
    .scenario-head { display: flex; justify-content: space-between; align-items: center; }
    .scenario-head h4 { margin: 0; font-size: 14px; color: #0f172a; font-weight: 800; }
    .pct { font-size: 16px; font-weight: 800; color: #0f172a; }
    .scenario.major .pct { color: #16a34a; }
    .scenario.medium .pct { color: #ea580c; }
    .scenario.minor .pct { color: #dc2626; }
    .scenario p { font-size: 14px; line-height: 1.55; color: #475569; margin: 10px 0 0; }
    
    .takeaway { background: #f0fdf4; border: 1px solid #bbf7d0; border-left: 5px solid #16a34a; border-radius: 16px; padding: 20px; }
    .takeaway b { font-size: 15px; color: #14532d; display: block; margin-bottom: 8px; font-weight: 800; }
    .takeaway ul { margin: 0; padding-left: 20px; }
    .takeaway li { font-size: 14.5px; line-height: 1.55; color: #166534; margin: 6px 0; }
    
    .detail { margin-top: 14px; border: 1px solid #e2e8f0; border-radius: 16px; background: #f8fafc; padding: 16px; }
    .detail-title { font-size: 11px; text-transform: uppercase; letter-spacing: 1px; font-weight: 800; color: #64748b; margin-bottom: 6px; }
    .detail p { font-size: 13.5px; line-height: 1.55; color: #475569; margin: 0; }
    
    .social { border: 1px solid #e2e8f0; border-radius: 18px; overflow: hidden; background: #ffffff; margin-bottom: 20px; box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.05); }
    .social-head { color: #ffffff; padding: 14px 20px; font-size: 14px; font-weight: 800; display: flex; align-items: center; gap: 8px; }
    .social-body { padding: 20px; font-size: 14.5px; line-height: 1.6; color: #334155; white-space: pre-wrap; font-family: system-ui, sans-serif; }
    .social-body strong { font-weight: 700; color: #0f172a; }
    .copy-note { display: flex; justify-content: space-between; align-items: center; font-size: 12px; color: #64748b; background: #f8fafc; padding: 12px 20px; border-top: 1px solid #e2e8f0; }
    .copy-btn-modern { background: #1e293b; border: none; color: #ffffff; font-size: 11px; font-weight: 700; padding: 6px 16px; border-radius: 8px; cursor: pointer; text-transform: uppercase; letter-spacing: 0.5px; transition: background 0.15s, transform 0.1s; }
    .copy-btn-modern:hover { background: #0f172a; }
    .copy-btn-modern:active { transform: scale(0.97); }
    
    .footer { padding: 24px 32px; background: #f8fafc; color: #64748b; font-size: 12px; line-height: 1.6; text-align: center; border-top: 1px solid #e2e8f0; }
    .source-note { font-size: 12px; color: #64748b; line-height: 1.5; margin-top: 16px; }
 
    @media (max-width: 700px) {
      body { background: #f1f5f9; }
      .wrap { margin: 0; border-radius: 0; border: none; box-shadow: none; }
      .header { padding: 32px 20px; }
      .hero-title { font-size: 26px; }
      .pad { padding: 20px 16px; }
      .week { border-radius: 16px; margin-top: 16px; }
      .week-head { padding: 20px 16px; }
      .week-head h2 { font-size: 19px; }
      .section { margin-top: 28px; }
      .grid2, .grid3, .grid4 { grid-template-columns: 1fr; gap: 12px; }
      .timeline-table { grid-template-columns: 1fr; gap: 10px; }
      .timeline-table td { padding: 14px; }
      .conf { flex-direction: column; }
      .conf-score { width: auto; border-right: none; border-bottom: 1px solid #e2e8f0; padding: 16px 20px; }
      .conf-text { padding: 16px 20px; }
      .social-body { padding: 16px; }
    }
    """

    weeks_html = ""
    for w_idx, w_res in enumerate(results):
        data = w_res["data"]
        downloaded_images = w_res["images"]
        
        # Encodage des graphiques
        html_images_block = ""
        for idx, img_path in enumerate(downloaded_images):
            try:
                with open(img_path, "rb") as f_img:
                    img_b64 = base64.b64encode(f_img.read()).decode('ascii')
                ext = img_path.split('.')[-1]
                html_images_block += f"""
                <div class="meteo-image-card" style="margin-top: 15px; text-align: center;">
                    <span style="font-size: 12px; font-weight: bold; color: #60758a; display: block; margin-bottom: 5px;">📈 Modélisation Météo {idx+1}</span>
                    <img src="data:image/{ext};base64,{img_b64}" alt="Graphique Météo {idx+1}" style="max-width: 100%; border-radius: 12px; border: 1px solid #dce6f0;">
                </div>
                """
            except Exception as e:
                print(f"Erreur encodage base64 pour {img_path} : {e}")
        
        if html_images_block:
            html_images_block = f"""
            <div class="section-title">📊 MODÉLISATIONS & GRAPHIQUES DE TENDANCE</div>
            <div class="meteo-images-container">{html_images_block}</div>
            """
        
        express = data.get("express", {})
        timeline = data.get("timeline", {})
        regional = data.get("regional", {})
        conf = data.get("confidence", {})
        scenarios = data.get("scenarios", {})
        social = data.get("social_pack", {})

        # Pré-calculer les valeurs social (évite les backslash dans f-string, interdit en Python <3.12)
        nl = "\n"
        social_linkedin = social.get('linkedin', '').replace('<br>', nl).replace('<br/>', nl)
        social_facebook = social.get('facebook', '').replace('<br>', nl).replace('<br/>', nl)
        social_twitter = social.get('twitter', '').replace('<br>', nl).replace('<br/>', nl)
        social_tiktok = social.get('tiktok', '').replace('<br>', nl).replace('<br/>', nl)
        social_instagram = social.get('instagram', '').replace('<br>', nl).replace('<br/>', nl)

        # Couleur dynamique du badge de confiance
        conf_score_raw = conf.get('score', '4/5')
        conf_class = "conf-badge-green"
        if "3/" in conf_score_raw:
            conf_class = "conf-badge-orange"
        elif "1/" in conf_score_raw or "2/" in conf_score_raw:
            conf_class = "conf-badge-red"

        # Traitement des puces "À Retenir"
        takeaways_raw = data.get("key_takeaways", "")
        takeaways_items = [t.strip("-* ").strip() for t in takeaways_raw.split("\n") if t.strip()]
        takeaways_li_html = "".join([f"<li>{t}</li>" for t in takeaways_items if t])
        if not takeaways_li_html:
            takeaways_li_html = "<li>Synthèse des prévisions établie avec succès.</li>"

        # Ajustement dynamique des classes de confiance
        conf_bg_class = ""
        conf_text_class = ""
        conf_color_hex = "#087443"
        if "3/" in conf_score_raw:
            conf_bg_class = "conf-badge-orange"
            conf_text_class = "conf-text-orange"
            conf_color_hex = "#a95c00"
        elif "1/" in conf_score_raw or "2/" in conf_score_raw:
            conf_bg_class = "conf-badge-red"
            conf_text_class = "conf-text-red"
            conf_color_hex = "#991b1b"

        # Traitement des incertitudes
        uncertainties_raw = data.get("key_uncertainties", "") + "\n" + data.get("monitoring_points", "")
        uncertainties_items = [u.strip("-* ").strip() for u in uncertainties_raw.split("\n") if u.strip()]
        uncertainties_li_html = "".join([f"<li>{u}</li>" for u in uncertainties_items if u])
        if not uncertainties_li_html:
            uncertainties_li_html = "<li>Aucun élément d'incertitude particulier signalé.</li>"

        # Couleur d'alerte pour le résumé express (basé sur la confiance ou la sévérité)
        alert_cls = "blue"
        if "canicule" in express.get('summary', '').lower() or "extreme" in express.get('summary', '').lower():
            alert_cls = "orange"
        if "4/" in conf_score_raw or "5/" in conf_score_raw:
            if "canicule" in express.get('summary', '').lower():
                alert_cls = "orange"
            else:
                alert_cls = "green"

        divider = '<div style="margin: 40px 0; border-top: 2px dashed #cfdce8;"></div>' if w_idx > 0 else ""
        weeks_html += f"""
        {divider}
        
        <div class="week">
            <div class="week-head">
                <h2>📅 {data.get('title_line1', 'SEMAINE')}</h2>
                <p>{data.get('title_line2', 'Synthèse des prévisions')}</p>
            </div>
            
            <div class="pad">
                <!-- 1. Lecture immédiate -->
                <div class="alert {alert_cls}">
                    <div class="eyebrow">Lecture immédiate · moins de 10 secondes</div>
                    <h3>{express.get('summary', '')}</h3>
                    <p>🎯 Confiance globale : {conf_score_raw} — {conf.get('desc', '')}</p>
                </div>

                <!-- 2. Les Chiffres Clés (KPI) -->
                <div class="section-title">Chiffres clés de la période</div>
                <div class="grid4">
                    <div class="cell"><div class="metric"><div class="big" style="font-size: 22px; padding-top: 4px;">{express.get('trend', '-')}</div><div class="label">Temps</div></div></div>
                    <div class="cell"><div class="metric"><div class="big" style="font-size: 22px; padding-top: 4px;">{express.get('temperatures', '-')}</div><div class="label">Températures</div></div></div>
                    <div class="cell"><div class="metric"><div class="big" style="font-size: 22px; padding-top: 4px;">{express.get('precipitations', '-')}</div><div class="label">Pluies</div></div></div>
                    <div class="cell"><div class="metric risk"><div class="big" style="font-size: 22px; padding-top: 4px; color:#b91c1c;">{express.get('main_risk', 'Aucun')}</div><div class="label">Risque principal</div></div></div>
                </div>

                <!-- 3. Chronologie visuelle -->
                <div class="section">
                    <div class="section-title">Chronologie visuelle</div>
                    <table class="timeline-table" role="presentation">
                        <tr>
                            <td><strong>Début de semaine</strong><div class="keys">{timeline.get('early', '-')}</div></td>
                            <td><strong>Milieu de semaine</strong><div class="keys">{timeline.get('mid', '-')}</div></td>
                            <td><strong>Fin de semaine</strong><div class="keys">{timeline.get('late', '-')}</div></td>
                            <td><strong>Week-end</strong><div class="keys">{timeline.get('weekend', '-')}</div></td>
                        </tr>
                    </table>
                </div>

                <!-- 4. Synthèse Régionale -->
                <div class="section">
                    <div class="section-title">Synthèse régionale · zones clés</div>
                    <div class="grid3">
                        <div class="cell"><div class="region"><h4>📍 Hauts-de-France & Nord</h4><p>{regional.get('hdf_north', '-')}</p></div></div>
                        <div class="cell"><div class="region"><h4>🌊 Façade Atlantique</h4><p>{regional.get('atlantic', '-')}</p></div></div>
                        <div class="cell"><div class="region"><h4>🏙️ Régions Centrales</h4><p>{regional.get('central', '-')}</p></div></div>
                    </div>
                    <div class="grid3" style="margin-top: 10px;">
                        <div class="cell"><div class="region"><h4>☀️ Moitié Sud</h4><p>{regional.get('south', '-')}</p></div></div>
                        <div class="cell"><div class="region"><h4>🏖️ Pourtour Méditerranéen</h4><p>{regional.get('mediterranean', '-')}</p></div></div>
                        <div class="cell"><div class="region"><h4>⛰️ Reliefs & Montagnes</h4><p>{regional.get('mountains', '-')}</p></div></div>
                    </div>
                </div>

                <!-- 5. Confiance & Incertitudes -->
                <div class="section">
                    <div class="section-title">Confiance et incertitudes</div>
                    <div class="conf">
                        <div class="conf-score {conf_bg_class}"><div class="big {conf_text_class}">{conf_score_raw}</div><div style="font-size:10px;font-weight:800;color:{conf_color_hex}">CONFIANCE</div></div>
                        <div class="conf-text"><b>Consensus des modèles :</b> {conf.get('desc', '')}</div>
                    </div>
                    <div class="listbox" style="margin-top:12px">
                        <ul>
                            {uncertainties_li_html}
                        </ul>
                    </div>
                </div>

                <!-- 6. Les 3 Scénarios -->
                <div class="section">
                    <div class="section-title">Trois scénarios atmosphériques</div>
                    <div class="scenario major">
                        <div class="scenario-head"><h4>🟢 {scenarios.get('majoritaire', {}).get('title', 'Scénario Majoritaire')}</h4><div class="pct">{scenarios.get('majoritaire', {}).get('prob', '65%')}</div></div>
                        <div class="track" style="margin: 6px 0;"><div class="fill green" style="width:{scenarios.get('majoritaire', {}).get('prob', '65%')}"></div></div>
                        <p>{scenarios.get('majoritaire', {}).get('desc', '')}</p>
                    </div>
                    <div class="scenario medium">
                        <div class="scenario-head"><h4>🟡 {scenarios.get('median', {}).get('title', 'Scénario Alternatif')}</h4><div class="pct">{scenarios.get('median', {}).get('prob', '25%')}</div></div>
                        <div class="track" style="margin: 6px 0;"><div class="fill orange" style="width:{scenarios.get('median', {}).get('prob', '25%')}"></div></div>
                        <p>{scenarios.get('median', {}).get('desc', '')}</p>
                    </div>
                    <div class="scenario minor">
                        <div class="scenario-head"><h4>🔴 {scenarios.get('minoritaire', {}).get('title', 'Scénario Minoritaire')}</h4><div class="pct">{scenarios.get('minoritaire', {}).get('prob', '10%')}</div></div>
                        <div class="track" style="margin: 6px 0;"><div class="fill red" style="width:{scenarios.get('minoritaire', {}).get('prob', '10%')}"></div></div>
                        <p>{scenarios.get('minoritaire', {}).get('desc', '')}</p>
                    </div>
                </div>

                <!-- 7. À retenir -->
                <div class="section">
                    <div class="takeaway">
                        <b>À retenir en 20 secondes</b>
                        <ul>
                            {takeaways_li_html}
                        </ul>
                    </div>
                </div>

                <!-- 8. Modélisations (images) -->
                {html_images_block}

                <!-- 9. Pack Réseaux Sociaux -->
                <div class="section">
                    <div class="section-title">📢 Pack réseaux sociaux (prêt à diffuser)</div>
                    <div class="social">
                        <div class="social-head" style="background:#0a66c2;">🔗 LinkedIn · Storytelling Expert Météo</div>
                        <div class="social-body">{social_linkedin}</div>
                        <div class="copy-note">
                            <button class="copy-btn-modern" onclick="navigator.clipboard.writeText(this.parentNode.parentNode.querySelector('.social-body').innerText); alert('Copié dans le presse-papiers !');">Copier le post LinkedIn</button>
                        </div>
                    </div>
                    <div class="social">
                        <div class="social-head" style="background:#1877f2;">👥 Facebook · Communautaire & Grand Public</div>
                        <div class="social-body">{social_facebook}</div>
                        <div class="copy-note">
                            <button class="copy-btn-modern" onclick="navigator.clipboard.writeText(this.parentNode.parentNode.querySelector('.social-body').innerText); alert('Copié dans le presse-papiers !');">Copier le post Facebook</button>
                        </div>
                    </div>
                    <div class="social">
                        <div class="social-head" style="background:#0f1419;">🐦 X (Twitter) · 280 Caractères max</div>
                        <div class="social-body">{social_twitter}</div>
                        <div class="copy-note">
                            <button class="copy-btn-modern" onclick="navigator.clipboard.writeText(this.parentNode.parentNode.querySelector('.social-body').innerText); alert('Copié dans le presse-papiers !');">Copier le post X</button>
                        </div>
                    </div>
                    <div class="social">
                        <div class="social-head" style="background:linear-gradient(45deg, #f09433, #e6683c, #dc2743, #cc2366, #bc1888);">📸 Instagram · Légende & CTA Bio</div>
                        <div class="social-body">{social_instagram}</div>
                        <div class="copy-note">
                            <button class="copy-btn-modern" onclick="navigator.clipboard.writeText(this.parentNode.parentNode.querySelector('.social-body').innerText); alert('Copié dans le presse-papiers !');">Copier le post Instagram</button>
                        </div>
                    </div>
                    <div class="social">
                        <div class="social-head" style="background:#fe2c55;">🎵 TikTok · Description vidéo</div>
                        <div class="social-body">{social_tiktok}</div>
                        <div class="copy-note">
                            <button class="copy-btn-modern" onclick="navigator.clipboard.writeText(this.parentNode.parentNode.querySelector('.social-body').innerText); alert('Copié la description TikTok !');">Copier la description TikTok</button>
                        </div>
                    </div>
                </div>

            </div>
        </div>
        """

    html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Tendances Moyen Terme</title>
    <style>{style}</style>
</head>
<body>
<div class="wrap">
    <header class="header">
        <div class="kicker">MONSIEUR MÉTÉO</div>
        <h1 class="hero-title">BULLETIN ÉVOLUTION & TENDANCES MÉTÉO</h1>
        <div class="sub">Analyse consolidée du {datetime.datetime.now().strftime('%d/%m/%Y')} · France · Prévisions à 2 semaines</div>
    </header>
    <main class="pad">
        {weeks_html}
    </main>
</div>
</body>
</html>
"""

    output_dir = "bulletins"
    os.makedirs(output_dir, exist_ok=True)

    html_path = "bulletins/FR.html"
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"HTML généré avec succès : {html_path}")

    date_suffix = datetime.datetime.now().strftime('%Y_%m_%d')

    # --- GÉNÉRATION PARALLÈLE DES 13 BULLETINS RÉGIONAUX ---
    # Utiliser les commentaires BRUTS du forum (pas le résumé LLM) pour maximiser la fidélité régionale
    raw_parts = []
    for res in results:
        d = res.get("data", {})
        raw_text = res.get("raw_comments", "")
        week_title = d.get("title_line1", "Prévisions")
        raw_parts.append(f"=== {week_title} — DISCUSSIONS BRUTES DU FORUM ===\n{raw_text}")

    # all_raw_context = les vraies discussions des prévisionnistes, source directe
    all_raw_context = "\n\n".join(raw_parts)
    topic_title_for_regions = " & ".join([r["data"].get("title_line1", "Prévisions") for r in results])
    # Bug fix: passer le contexte des DEUX semaines aux régions, pas seulement la semaine en cours
    # Aussi injecter la date ISO et la saison pour éviter les hallucinations (neige en été, etc.)
    saison_actuelle = ["hiver", "printemps", "été", "automne"][(now.month % 12 // 3)]
    date_context_for_regions = (
        f"Date actuelle de génération : {today_str} ({now.strftime('%Y-%m-%d')}) — Saison : {saison_actuelle.upper()} EN FRANCE.\n"
        f"ATTENTION ABSOLUE : Nous sommes en {saison_actuelle.upper()}. Toute mention de neige en plaine, de gel sévère ou de conditions hivernales est STRICTEMENT INTERDITE sauf en altitude (>1500m) si les sources le mentionnent explicitement.\n"
        f"Semaine en cours : {semaine_cours_str} (jours restants à prévoir : {jours_restants_cours_str}).\n"
        f"Semaine suivante : {semaine_suivante_str} (semaine complète à prévoir)."
    )

    def gen_region(r_key, r_info):
        r_name, r_abbr = r_info
        # Injection des commentaires bruts du forum directement au LLM régional
        return process_region_query(r_key, r_name, all_raw_context, topic_title_for_regions, date_context_for_regions, 0)

    print("\n--- Génération parallèle des 13 bulletins régionaux ---")
    regions_data = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=13) as executor:
        futures = {executor.submit(gen_region, k, v): k for k, v in REGIONS_CONFIG.items()}
        for future in concurrent.futures.as_completed(futures):
            k, r_data = future.result()
            regions_data[k] = r_data

    # Générer le HTML régional dans le dossier bulletins/ sous le nom abrégé de la région
    for r_key, (r_name, r_abbr) in REGIONS_CONFIG.items():
        r_data = regions_data.get(r_key)
        filename_region = f"bulletins/{r_abbr}"

        if not r_data:
            print(f"[{r_name}] Bulletin manquant — fichier minimal généré.")
            r_data = {
                "title_line1": f"Semaine — {r_name}",
                "title_line2": "Information non précisée dans les sources.",
                "region_name": r_name,
                "express": {"summary": "Information non précisée.", "trend": "-", "temperatures": "-", "precipitations": "-", "main_risk": "-"},
                "confidence": {"score": "3/5", "desc": "Données insuffisantes pour cette région."},
                "timeline": {"early": "-", "mid": "-", "late": "-", "weekend": "-"},
                "regional": {"hdf_north": "-", "atlantic": "-", "central": "-", "south": "-", "mediterranean": "-", "mountains": "-"},
                "scenarios": {
                    "majoritaire": {"prob": "65%", "title": "Scénario Majoritaire", "desc": "Information non précisée dans les sources."},
                    "median": {"prob": "25%", "title": "Scénario Alternatif", "desc": "Information non précisée dans les sources."},
                    "minoritaire": {"prob": "10%", "title": "Scénario Minoritaire", "desc": "Information non précisée dans les sources."},
                },
                "key_uncertainties": "- Information non précisée.",
                "monitoring_points": "- Information non précisée.",
                "key_takeaways": "- Information non précisée dans les sources.",
                "social_pack": {"linkedin": "", "facebook": "", "twitter": "", "tiktok": "", "instagram": ""},
                "linkedin_hashtags": f"#Meteo #{r_name.replace(' ', '').replace('-', '')} #France #MonsieurMeteo",
            }

        # Même CSS que le national
        express_r = r_data.get("express", {})
        timeline_r = r_data.get("timeline", {})
        regional_r = r_data.get("regional", {})
        conf_r = r_data.get("confidence", {})
        scenarios_r = r_data.get("scenarios", {})
        social_r = r_data.get("social_pack", {})

        conf_score_r = conf_r.get('score', '4/5')
        conf_class_r = "conf-badge-green"
        if "3/" in conf_score_r:
            conf_class_r = "conf-badge-orange"
        elif "1/" in conf_score_r or "2/" in conf_score_r:
            conf_class_r = "conf-badge-red"

        takeaways_r_raw = r_data.get("key_takeaways", "")
        takeaways_r_items = [t.strip("-* ").strip() for t in takeaways_r_raw.split("\n") if t.strip()]
        takeaways_r_li = "".join([f"<li>{t}</li>" for t in takeaways_r_items if t])
        if not takeaways_r_li:
            takeaways_r_li = "<li>Information non précisée dans les sources pour cette région.</li>"

        # Ajustement des classes régionales
        conf_bg_class_r = ""
        conf_text_class_r = ""
        conf_color_hex_r = "#087443"
        if "3/" in conf_score_r:
            conf_bg_class_r = "conf-badge-orange"
            conf_text_class_r = "conf-text-orange"
            conf_color_hex_r = "#a95c00"
        elif "1/" in conf_score_r or "2/" in conf_score_r:
            conf_bg_class_r = "conf-badge-red"
            conf_text_class_r = "conf-text-red"
            conf_color_hex_r = "#991b1b"

        uncertainties_r_raw = r_data.get("key_uncertainties", "") + "\n" + r_data.get("monitoring_points", "")
        uncertainties_r_items = [u.strip("-* ").strip() for u in uncertainties_r_raw.split("\n") if u.strip()]
        uncertainties_r_li_html = "".join([f"<li>{u}</li>" for u in uncertainties_r_items if u])
        if not uncertainties_r_li_html:
            uncertainties_r_li_html = "<li>Aucun élément d'incertitude particulier signalé.</li>"

        alert_cls_r = "blue"
        if "canicule" in express_r.get('summary', '').lower() or "extreme" in express_r.get('summary', '').lower():
            alert_cls_r = "orange"
        if "4/" in conf_score_r or "5/" in conf_score_r:
            if "canicule" in express_r.get('summary', '').lower():
                alert_cls_r = "orange"
            else:
                alert_cls_r = "green"

        # Pré-calculer les réseaux sociaux régionaux (pour éviter backslash dans f-string)
        nl = "\n"
        social_r_linkedin = social_r.get('linkedin', '').replace('<br>', nl).replace('<br/>', nl)
        social_r_facebook = social_r.get('facebook', '').replace('<br>', nl).replace('<br/>', nl)
        social_r_twitter = social_r.get('twitter', '').replace('<br>', nl).replace('<br/>', nl)
        social_r_tiktok = social_r.get('tiktok', '').replace('<br>', nl).replace('<br/>', nl)
        social_r_instagram = social_r.get('instagram', '').replace('<br>', nl).replace('<br/>', nl)

        region_html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bulletin Météo — {r_name}</title>
    <style>{style}</style>
</head>
<body>
<div class="wrap">
    <header class="header">
        <div class="kicker">MONSIEUR MÉTÉO — BULLETIN RÉGIONAL</div>
        <h1 class="hero-title">📍 {r_name}</h1>
        <div class="sub">Analyse consolidée du {datetime.datetime.now().strftime('%d/%m/%Y')} · Prévisions à 2 semaines</div>
    </header>
    
    <main class="pad">
        <div class="week">
            <div class="week-head">
                <h2>📅 {r_data.get('title_line1', r_name)}</h2>
                <p>{r_data.get('title_line2', '')}</p>
            </div>
            
            <div class="pad">
                <!-- 1. Lecture immédiate -->
                <div class="alert {alert_cls_r}">
                    <div class="eyebrow">Lecture immédiate · moins de 10 secondes</div>
                    <h3>{express_r.get('summary', '')}</h3>
                    <p>🎯 Confiance globale : {conf_score_r} — {conf_r.get('desc', '')}</p>
                </div>
 
                <!-- 2. KPIs -->
                <div class="section-title">Chiffres clés de la période</div>
                <div class="grid4">
                    <div class="cell"><div class="metric"><div class="big" style="font-size: 22px; padding-top: 4px;">{express_r.get('trend', '-')}</div><div class="label">Temps</div></div></div>
                    <div class="cell"><div class="metric"><div class="big" style="font-size: 22px; padding-top: 4px;">{express_r.get('temperatures', '-')}</div><div class="label">Températures</div></div></div>
                    <div class="cell"><div class="metric"><div class="big" style="font-size: 22px; padding-top: 4px;">{express_r.get('precipitations', '-')}</div><div class="label">Pluies</div></div></div>
                    <div class="cell"><div class="metric risk"><div class="big" style="font-size: 22px; padding-top: 4px; color:#b91c1c;">{express_r.get('main_risk', 'Aucun')}</div><div class="label">Risque principal</div></div></div>
                </div>

                <div class="section">
                    <div class="section-title">Chronologie — 2 semaines</div>
                    <table class="timeline-table" role="presentation">
                        <tr>
                            <td><strong>Sem. en cours · Début</strong><div class="keys">{timeline_r.get('early', '-')}</div></td>
                            <td><strong>Sem. en cours · Fin</strong><div class="keys">{timeline_r.get('mid', '-')}</div></td>
                            <td><strong>Sem. suivante · Début</strong><div class="keys">{timeline_r.get('late', '-')}</div></td>
                            <td><strong>Sem. suivante · Fin</strong><div class="keys">{timeline_r.get('weekend', '-')}</div></td>
                        </tr>
                    </table>
                </div>

                <!-- 4. Découpage par secteurs -->
                <div class="section">
                    <div class="section-title">🗺️ Secteurs de {r_name.upper()}</div>
                    <div class="grid3">
                        <div class="cell"><div class="region"><h4>🔹 Secteur Nord / NW</h4><p>{regional_r.get('hdf_north', '-')}</p></div></div>
                        <div class="cell"><div class="region"><h4>🌊 Façade Ouest</h4><p>{regional_r.get('atlantic', '-')}</p></div></div>
                        <div class="cell"><div class="region"><h4>🏙️ Intérieur / Centre</h4><p>{regional_r.get('central', '-')}</p></div></div>
                    </div>
                    <div class="grid3" style="margin-top: 10px;">
                        <div class="cell"><div class="region"><h4>☀️ Secteur Sud</h4><p>{regional_r.get('south', '-')}</p></div></div>
                        <div class="cell"><div class="region"><h4>🏖️ Côtes / Méditerranée</h4><p>{regional_r.get('mediterranean', 'Non applicable')}</p></div></div>
                        <div class="cell"><div class="region"><h4>⛰️ Reliefs / Montagnes</h4><p>{regional_r.get('mountains', 'Non applicable')}</p></div></div>
                    </div>
                </div>

                <!-- 5. Confiance & Incertitudes -->
                <div class="section">
                    <div class="section-title">Confiance et incertitudes</div>
                    <div class="conf">
                        <div class="conf-score {conf_bg_class_r}"><div class="big {conf_text_class_r}">{conf_score_r}</div><div style="font-size:10px;font-weight:800;color:{conf_color_hex_r}">CONFIANCE</div></div>
                        <div class="conf-text"><b>Consensus des modèles :</b> {conf_r.get('desc', '')}</div>
                    </div>
                    <div class="listbox" style="margin-top:12px">
                        <ul>
                            {uncertainties_r_li_html}
                        </ul>
                    </div>
                </div>

                <!-- 6. Les 3 Scénarios -->
                <div class="section">
                    <div class="section-title">Trois scénarios atmosphériques</div>
                    <div class="scenario major">
                        <div class="scenario-head"><h4>🟢 {scenarios_r.get('majoritaire', {}).get('title', 'Scénario Majoritaire')}</h4><div class="pct">{scenarios_r.get('majoritaire', {}).get('prob', '65%')}</div></div>
                        <div class="track" style="margin: 6px 0;"><div class="fill green" style="width:{scenarios_r.get('majoritaire', {}).get('prob', '65%')}"></div></div>
                        <p>{scenarios_r.get('majoritaire', {}).get('desc', '')}</p>
                    </div>
                    <div class="scenario medium">
                        <div class="scenario-head"><h4>🟡 {scenarios_r.get('median', {}).get('title', 'Scénario Alternatif')}</h4><div class="pct">{scenarios_r.get('median', {}).get('prob', '25%')}</div></div>
                        <div class="track" style="margin: 6px 0;"><div class="fill orange" style="width:{scenarios_r.get('median', {}).get('prob', '25%')}"></div></div>
                        <p>{scenarios_r.get('median', {}).get('desc', '')}</p>
                    </div>
                    <div class="scenario minor">
                        <div class="scenario-head"><h4>🔴 {scenarios_r.get('minoritaire', {}).get('title', 'Scénario Minoritaire')}</h4><div class="pct">{scenarios_r.get('minoritaire', {}).get('prob', '10%')}</div></div>
                        <div class="track" style="margin: 6px 0;"><div class="fill red" style="width:{scenarios_r.get('minoritaire', {}).get('prob', '10%')}"></div></div>
                        <p>{scenarios_r.get('minoritaire', {}).get('desc', '')}</p>
                    </div>
                </div>

                <!-- 7. À retenir -->
                <div class="section">
                    <div class="takeaway">
                        <b>À retenir en 20 secondes</b>
                        <ul>
                            {takeaways_r_li}
                        </ul>
                    </div>
                </div>

                <!-- 9. Pack Réseaux Sociaux -->
                <div class="section">
                    <div class="section-title">📢 Pack réseaux sociaux — {r_name}</div>
                    <div class="social">
                        <div class="social-head" style="background:#0a66c2;">🔗 LinkedIn · Storytelling Expert Météo</div>
                        <div class="social-body">{social_r_linkedin}</div>
                        <div class="copy-note">
                            <button class="copy-btn-modern" onclick="navigator.clipboard.writeText(this.parentNode.parentNode.querySelector('.social-body').innerText); alert('Copié dans le presse-papiers !');">Copier le post LinkedIn</button>
                        </div>
                    </div>
                    <div class="social">
                        <div class="social-head" style="background:#1877f2;">👥 Facebook · Communautaire & Grand Public</div>
                        <div class="social-body">{social_r_facebook}</div>
                        <div class="copy-note">
                            <button class="copy-btn-modern" onclick="navigator.clipboard.writeText(this.parentNode.parentNode.querySelector('.social-body').innerText); alert('Copié dans le presse-papiers !');">Copier le post Facebook</button>
                        </div>
                    </div>
                    <div class="social">
                        <div class="social-head" style="background:#0f1419;">🐦 X (Twitter) · 280 Caractères max</div>
                        <div class="social-body">{social_r_twitter}</div>
                        <div class="copy-note">
                            <button class="copy-btn-modern" onclick="navigator.clipboard.writeText(this.parentNode.parentNode.querySelector('.social-body').innerText); alert('Copié dans le presse-papiers !');">Copier le post X</button>
                        </div>
                    </div>
                    <div class="social">
                        <div class="social-head" style="background:linear-gradient(45deg, #f09433, #e6683c, #dc2743, #cc2366, #bc1888);">📸 Instagram · Légende & CTA Bio</div>
                        <div class="social-body">{social_r_instagram}</div>
                        <div class="copy-note">
                            <button class="copy-btn-modern" onclick="navigator.clipboard.writeText(this.parentNode.parentNode.querySelector('.social-body').innerText); alert('Copié dans le presse-papiers !');">Copier le post Instagram</button>
                        </div>
                    </div>
                    <div class="social">
                        <div class="social-head" style="background:#fe2c55;">🎵 TikTok · Description vidéo</div>
                        <div class="social-body">{social_r_tiktok}</div>
                        <div class="copy-note">
                            <button class="copy-btn-modern" onclick="navigator.clipboard.writeText(this.parentNode.parentNode.querySelector('.social-body').innerText); alert('Copié la description TikTok !');">Copier la description TikTok</button>
                        </div>
                    </div>
                </div>

            </div>
        </div>
    </main>
</div>
</body>
</html>"""

        with open(filename_region, "w", encoding="utf-8") as f_r:
            f_r.write(region_html)
        print(f"Bulletin régional généré : {filename_region}")

    # --- ENVOI EMAIL SMTP (National inline + 14 pièces jointes abrégées) ---
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
    subject_week_names = " & ".join([r["data"].get("title_line1", "Semaine").split("-")[0].strip() for r in results])
    subject = f"Tendances de la semaine - {subject_week_names}"
    subject = unicodedata.normalize('NFKD', subject).encode('ASCII', 'ignore').decode('ASCII')

    msg = MIMEMultipart('mixed')
    msg['From'] = f"Meteo Climat Pro <{sender}>"
    msg['To'] = ", ".join(recipients)
    msg['Subject'] = subject
    msg['Date'] = formatdate(localtime=True)
    msg['Reply-To'] = "gregory.langlet@sfr.fr"

    msg_alt = MIMEMultipart('alternative')
    msg.attach(msg_alt)

    text_body = "Bonjour,\n\nVeuillez trouver le bulletin national France en ligne ci-dessous, et les 13 bulletins régionaux en pièces jointes (FR.html, HDF.html, IDF.html, PACA.html...).\n\nCordialement,\nMonsieur Météo"
    msg_alt.attach(MIMEText(text_body, 'plain', 'utf-8'))
    # Clean the HTML specifically for the email body (remove JavaScript onclick buttons)
    msg_alt.attach(MIMEText(clean_html_for_email(html), 'html', 'utf-8'))

    # Bulletin national FR.html en pièce jointe (contient tous les boutons interactifs intacts)
    part_fr = MIMEBase('text', 'html', charset='utf-8')
    part_fr.set_payload(html.encode('utf-8'))
    encoders.encode_base64(part_fr)
    part_fr.add_header('Content-Disposition', 'attachment', filename="FR.html")
    msg.attach(part_fr)

    # 13 bulletins régionaux en pièces jointes sous leurs noms d'abréviations directes
    for r_key, (r_name, r_abbr) in REGIONS_CONFIG.items():
        fn = f"bulletins/{r_abbr}"
        try:
            with open(fn, "r", encoding="utf-8") as f_r:
                r_html_content = f_r.read()
            part_r = MIMEBase('text', 'html', charset='utf-8')
            part_r.set_payload(r_html_content.encode('utf-8'))
            encoders.encode_base64(part_r)
            part_r.add_header('Content-Disposition', 'attachment', filename=r_abbr)
            msg.attach(part_r)
        except Exception as e:
            print(f"Erreur attachement {r_abbr} : {e}")

    print(f"[SMTP] Envoi via Gmail à {', '.join(recipients)}...")
    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=45) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(gmail_email, gmail_password)
            server.sendmail(gmail_email, recipients, msg.as_bytes())
        print("[SMTP] E-mail envoyé avec succès !")
    except Exception as e:
        print(f"[SMTP] Erreur d'envoi : {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
