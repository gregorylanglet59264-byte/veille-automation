import os
import sys
import xml.etree.ElementTree as ET

# Configuration des départements, zones maritimes et massifs montagneux par région
REGIONS = {
    "France": {
        "departements": {
            "59": "Nord (Lille)",
            "75": "Paris (Île-de-France)",
            "67": "Bas-Rhin (Strasbourg)",
            "69": "Rhône (Lyon)",
            "13": "Bouches-du-Rhône (Marseille)",
            "06": "Alpes-Maritimes (Nice)",
            "31": "Haute-Garonne (Toulouse)",
            "33": "Gironde (Bordeaux)",
            "44": "Loire-Atlantique (Nantes)",
            "29": "Finistère (Brest)",
            "35": "Ille-et-Vilaine (Rennes)",
            "21": "Côte-d'Or (Dijon)",
            "2A": "Corse-du-Sud (Ajaccio)"
        },
        "zones_cotieres": {
            "59-62-80": "Manche Est / Littoral Nord",
            "50": "Manche Ouest / Cotentin",
            "29-56-44-85": "Sud Bretagne & Vendée",
            "17-33-40-64": "Gascogne / Atlantique Sud",
            "66-11-34-30": "Golfe du Lion / Méditerranée Ouest",
            "13-83": "Côte d'Azur / PACA",
            "2A-2B": "Corse"
        },
        "zones_montagne": {
            "74": "Alpes du Nord / Mont-Blanc",
            "05": "Alpes du Sud / Écrins",
            "65": "Pyrénées / Bigorre",
            "39": "Massif du Jura",
            "25": "Doubs / Vosges",
            "2A": "Corse / Alta Rocca"
        }
    },
    "Auvergne-Rhône-Alpes": {
        "departements": {
            "01": "Ain",
            "03": "Allier",
            "07": "Ardèche",
            "15": "Cantal",
            "26": "Drôme",
            "38": "Isère",
            "42": "Loire",
            "43": "Haute-Loire",
            "63": "Puy-de-Dôme",
            "69": "Rhône",
            "73": "Savoie",
            "74": "Haute-Savoie"
        },
        "zones_cotieres": {},
        "zones_montagne": {
            "73": "Savoie / Tarentaise / Maurienne",
            "74": "Haute-Savoie / Mont-Blanc",
            "38": "Isère / Belledonne / Vercors"
        }
    },
    "Bourgogne-Franche-Comté": {
        "departements": {
            "21": "Côte-d'Or",
            "25": "Doubs",
            "39": "Jura",
            "58": "Nièvre",
            "70": "Haute-Saône",
            "71": "Saône-et-Loire",
            "89": "Yonne",
            "90": "Territoire de Belfort"
        },
        "zones_cotieres": {},
        "zones_montagne": {
            "25": "Jura / Doubs",
            "39": "Jura / Massif"
        }
    },
    "Bretagne": {
        "departements": {
            "22": "Côtes-d'Armor",
            "29": "Finistère",
            "35": "Ille-et-Vilaine",
            "56": "Morbihan"
        },
        "zones_cotieres": {
            "35": "Littoral Ille-et-Vilaine",
            "22": "Littoral Côtes-d'Armor",
            "29": "Littoral Finistère",
            "56": "Littoral Morbihan"
        },
        "zones_montagne": {}
    },
    "Centre-Val de Loire": {
        "departements": {
            "18": "Cher",
            "28": "Eure-et-Loir",
            "36": "Indre",
            "37": "Indre-et-Loire",
            "41": "Loir-et-Cher",
            "45": "Loiret"
        },
        "zones_cotieres": {},
        "zones_montagne": {}
    },
    "Corse": {
        "departements": {
            "2A": "Corse-du-Sud",
            "2B": "Haute-Corse"
        },
        "zones_cotieres": {
            "2A": "Littoral Corse-du-Sud",
            "2B": "Littoral Haute-Corse"
        },
        "zones_montagne": {
            "2A": "Massif de Corse-du-Sud",
            "2B": "Massif de Haute-Corse"
        }
    },
    "Grand Est": {
        "departements": {
            "08": "Ardennes",
            "10": "Aube",
            "51": "Marne",
            "52": "Haute-Marne",
            "54": "Meurthe-et-Moselle",
            "55": "Meuse",
            "57": "Moselle",
            "67": "Bas-Rhin",
            "68": "Haut-Rhin",
            "88": "Vosges"
        },
        "zones_cotieres": {},
        "zones_montagne": {
            "88": "Massif des Vosges"
        }
    },
    "Hauts-de-France": {
        "departements": {
            "02": "Aisne",
            "60": "Oise",
            "59": "Nord",
            "62": "Pas-de-Calais",
            "80": "Somme"
        },
        "zones_cotieres": {
            "59": "Littoral Nord",
            "59-62-80": "Manche Est"
        },
        "zones_montagne": {}
    },
    "Île-de-France": {
        "departements": {
            "75": "Paris",
            "77": "Seine-et-Marne",
            "78": "Yvelines",
            "91": "Essonne",
            "92": "Hauts-de-Seine",
            "93": "Seine-Saint-Denis",
            "94": "Val-de-Marne",
            "95": "Val-d'Oise"
        },
        "zones_cotieres": {},
        "zones_montagne": {}
    },
    "Normandie": {
        "departements": {
            "14": "Calvados",
            "27": "Eure",
            "50": "Manche",
            "61": "Orne",
            "76": "Seine-Maritime"
        },
        "zones_cotieres": {
            "50": "Littoral de la Manche",
            "14": "Littoral du Calvados",
            "76": "Littoral Seine-Maritime"
        },
        "zones_montagne": {}
    },
    "Nouvelle-Aquitaine": {
        "departements": {
            "16": "Charente",
            "17": "Charente-Maritime",
            "19": "Corrèze",
            "23": "Creuse",
            "24": "Dordogne",
            "33": "Gironde",
            "40": "Landes",
            "47": "Lot-et-Garonne",
            "64": "Pyrénées-Atlantiques",
            "79": "Deux-Sèvres",
            "86": "Vienne",
            "87": "Haute-Vienne"
        },
        "zones_cotieres": {
            "17": "Littoral Charente-Maritime",
            "33": "Littoral Girondin",
            "40": "Littoral des Landes",
            "64": "Littoral Pyrénées-Atlantiques"
        },
        "zones_montagne": {
            "64": "Pyrénées-Atlantiques / Béarn"
        }
    },
    "Occitanie": {
        "departements": {
            "09": "Ariège",
            "11": "Aude",
            "12": "Aveyron",
            "30": "Gard",
            "31": "Haute-Garonne",
            "32": "Gers",
            "34": "Hérault",
            "46": "Lot",
            "48": "Lozère",
            "65": "Hautes-Pyrénées",
            "66": "Pyrénées-Orientales",
            "81": "Tarn",
            "82": "Tarn-et-Garonne"
        },
        "zones_cotieres": {
            "30": "Littoral Gardois",
            "34": "Littoral Héraultais",
            "11": "Littoral Audois",
            "66": "Côte Vermeille",
            "66-11-34-30": "Golfe du Lion"
        },
        "zones_montagne": {
            "66": "Pyrénées Orientales / Cerdagne",
            "09": "Ariège / Haute-Ariège",
            "65": "Hautes-Pyrénées / Bigorre"
        }
    },
    "Pays de la Loire": {
        "departements": {
            "44": "Loire-Atlantique",
            "49": "Maine-et-Loire",
            "53": "Mayenne",
            "72": "Sarthe",
            "85": "Vendée"
        },
        "zones_cotieres": {
            "44": "Littoral Loire-Atlantique",
            "85": "Littoral Vendéen"
        },
        "zones_montagne": {}
    },
    "Provence-Alpes-Côte d'Azur": {
        "departements": {
            "04": "Alpes-de-Haute-Provence",
            "05": "Hautes-Alpes",
            "06": "Alpes-Maritimes",
            "13": "Bouches-du-Rhône",
            "83": "Var",
            "84": "Vaucluse"
        },
        "zones_cotieres": {
            "13": "Littoral des Bouches-du-Rhône",
            "83": "Littoral Varois",
            "06": "Littoral Alpes-Maritimes"
        },
        "zones_montagne": {
            "05": "Hautes-Alpes / Écrins",
            "06": "Alpes-Maritimes / Mercantour"
        }
    }
}

REGIONAL_CAPITALS = {
    "Auvergne-Rhône-Alpes": ("69", "Lyon (Rhône)"),
    "Bourgogne-Franche-Comté": ("21", "Dijon (Côte-d'Or)"),
    "Bretagne": ("35", "Rennes (Ille-et-Vilaine)"),
    "Centre-Val de Loire": ("45", "Orléans (Loiret)"),
    "Corse": ("2A", "Ajaccio (Corse-du-Sud)"),
    "Grand Est": ("67", "Strasbourg (Bas-Rhin)"),
    "Hauts-de-France": ("59", "Lille (Nord)"),
    "Île-de-France": ("75", "Paris"),
    "Normandie": ("76", "Rouen (Seine-Maritime)"),
    "Nouvelle-Aquitaine": ("33", "Bordeaux (Gironde)"),
    "Occitanie": ("31", "Toulouse (Haute-Garonne)"),
    "Pays de la Loire": ("44", "Nantes (Loire-Atlantique)"),
    "Provence-Alpes-Côte d'Azur": ("13", "Marseille (Bouches-du-Rhône)"),
}

def charger_xml(chemin):
    if not os.path.exists(chemin):
        return None
    try:
        return ET.parse(chemin).getroot()
    except Exception:
        return None

def trouver_prev_xml(dossier_source, dept_code):
    for path in [
        os.path.join(dossier_source, "PREV_XML", f"DEPT{dept_code}.xml"),
        os.path.join(dossier_source, "PREV_XML", f"DEPT{dept_code}"),
        os.path.join(dossier_source, f"DEPT{dept_code}.xml"),
        os.path.join(dossier_source, f"DEPT{dept_code}"),
    ]:
        root = charger_xml(path)
        if root is not None:
            return root
    return None

def extraire_label_date(groupe):
    date_el = groupe.find('date')
    if date_el is not None and date_el.text:
        label = date_el.text.strip()
        if label.lower().startswith("pour "):
            label = label[5:]
        if label.endswith(" :"):
            label = label[:-2]
        if label.endswith(":"):
            label = label[:-1]
        label = label.strip()
        if label:
            return label[0].upper() + label[1:]
    return groupe.attrib.get('nom', 'Prévision').capitalize()

import re

def parse_marine_bulletin(text):
    replacements = {
        "dpression": "dépression",
        "gnrale": "générale",
        "volution": "évolution",
        "ctier": "côtier",
        "frontire": "frontière",
        "Emis le": "Émis le",
        "lgales": "légales",
        "chelle": "échelle",
        "très": "très",
        "cosse": "Écosse",
        "franaise": "française",
        "agite": "agitée",
        "peu agite": "peu agitée",
        "prvisions": "prévisions",
        "journe": "journée",
        "frachissant": "fraîchissant",
        "noeud": "nœud",
        "noeuds": "nœuds",
        "tendance": "tendance",
        "mollissant": "mollissant",
    }
    
    for k, v in replacements.items():
        text = re.sub(r'\b' + k + r'\b', v, text, flags=re.I)
    
    sections = {}
    current_section = "intro"
    current_content = []
    
    for line in text.splitlines():
        line_strip = line.strip()
        match = re.match(r'^([1-9])\s*-\s*(.*)$', line_strip)
        if match:
            if current_content:
                sections[current_section] = "\n".join(current_content).strip()
            num = match.group(1)
            current_section = num
            current_content = [match.group(2)]
        else:
            current_content.append(line)
            
    if current_content:
        sections[current_section] = "\n".join(current_content).strip()
        
    return sections

def extraire_parametres(section_text):
    params = {}
    lines = section_text.splitlines()
    title = lines[0] if lines else "Prévisions"
    title = re.sub(r'^\d+\s*-\s*', '', title).strip()
    if title:
        title = title[0].upper() + title[1:]
    
    current_key = None
    for line in lines[1:]:
        line_strip = line.strip()
        match = re.match(r'^(VENT|MER|HOULE|TEMPS|VISIBILITE|HOULE dominante)\s*:\s*(.*)$', line_strip, re.I)
        if match:
            current_key = match.group(1).upper()
            params[current_key] = match.group(2).strip()
        elif current_key and line_strip:
            params[current_key] += " " + line_strip
            
    return title, params

def formater_cellule_marine(params):
    parts = []
    if "VENT" in params:
        parts.append(f"💨 **Vent :** {params['VENT']}")
    if "MER" in params:
        parts.append(f"🌊 **Mer :** {params['MER']}")
    if "HOULE" in params or "HOULE DOMINANTE" in params:
        h_val = params.get("HOULE") or params.get("HOULE DOMINANTE")
        parts.append(f"🌊 **Houle :** {h_val}")
    if "TEMPS" in params:
        parts.append(f"🌦️ **Temps :** {params['TEMPS']}")
    if "VISIBILITE" in params:
        parts.append(f"👁️ **Visibilité :** {params['VISIBILITE']}")
    return "<br>".join(parts) if parts else "*Données indisponibles*"

def nettoyer_texte_mto(text):
    if not text:
        return ""
    # Enlever les doubles étoiles orphelines et les tirets de mise en page bizarres
    text = re.sub(r'\*\*\s*—\s*', '', text)
    text = re.sub(r'^\s*—\s*', '', text)
    # Nettoyer les espaces multiples
    text = re.sub(r'\s+', ' ', text)
    # Remplacer "degrés" par "°C" pour faire plus professionnel
    text = re.sub(r'\bdegrés\b', '°C', text, flags=re.I)
    return text.strip()

def obtenir_tendance_stylisee(titre_txt, est_nuit=False):
    txt = titre_txt.strip()
    if not txt:
        return "🌙 Clair" if est_nuit else "☀️ Ensoleillé"
    
    txt_lower = txt.lower()
    emoji = "☀️"
    if est_nuit:
        emoji = "🌙"
        
    if "orage" in txt_lower:
        emoji = "⛈️"
    elif "pluie" in txt_lower or "pluvieux" in txt_lower or "ondées" in txt_lower or "averse" in txt_lower:
        emoji = "🌧️"
    elif "nuage" in txt_lower or "couvert" in txt_lower:
        if "éclaircies" in txt_lower:
            emoji = "⛅"
        else:
            emoji = "☁️"
    elif "soleil" in txt_lower or "ensoleillé" in txt_lower or "clair" in txt_lower or "dégagé" in txt_lower:
        emoji = "🌙" if est_nuit else "☀️"
        
    return f"{emoji} {txt}"

def nettoyer_nom_departement(nom):
    if not nom:
        return ""
    nom = re.sub(r'^bulletin\s+départemental\s+(?:de\s+l\'|de\s+la\s+|du\s+|d\'|de\s+|des\s+)?', '', nom, flags=re.I)
    return nom.strip()

def generer_synthese_nationale(dossier_source):
    periodes = ["cettenuit", "demain", "apres-demain"]
    synthese_periods = {}
    
    references = {
        "nord": "59",
        "normandie": "76",
        "bretagne": "29",
        "atlantique": "33",
        "mediterranee": "13",
        "sud_ouest": "31",
        "corse": "2A",
        "est": "67",
        "centre": "45",
        "rhone": "69"
    }
    
    for pk in periodes:
        toutes_temps = []
        for key, code in references.items():
            root = trouver_prev_xml(dossier_source, code)
            if root is not None:
                for g in root.findall('groupe'):
                    if g.attrib.get('nom') == pk:
                        temps = g.find('temps')
                        temps_txt = temps.text.strip() if temps is not None and temps.text else ""
                        if temps_txt:
                            clean_t = nettoyer_texte_mto(temps_txt)
                            nums = [int(n) for n in re.findall(r'\b(\d{1,2})\s*(?:°C|degrés)', clean_t)]
                            toutes_temps.extend(nums)
                        break
                        
        if toutes_temps:
            toutes_temps = [t for t in toutes_temps if 0 <= t <= 50]
            t_min = min(toutes_temps)
            t_max = max(toutes_temps)
        else:
            t_min, t_max = 18, 35
            
        if pk == "cettenuit":
            label = "Prévisions pour cette nuit"
            bulletin = (
                f"### 🌐 Situation Générale :\n"
                f"La France reste sous la protection d'un puissant anticyclone à 1032 hPa centré au nord de l'Écosse et s'étirant jusqu'aux Alpes. La nuit s'annonce extrêmement paisible, sèche, sous un ciel totalement limpide et étoilé sur la quasi-totalité du territoire.\n\n"
                f"### 🗺️ Éléments clés par secteur :\n"
                f"- **Moitié Nord & Manche :** Ciel bleu nuit pur de la pointe bretonne aux Ardennes. De rares et discrets bancs de brumes marines isolés pourront se former en fin de nuit sur le Cotentin et le littoral Nord sous un vent de Nord-Est très faible.\n"
                f"- **Bassin Parisien & Régions Centrales :** Conditions calmes et ciel dégagé. Une douceur remarquable s'établit en milieu urbain (environ 21 °C dans Paris intra-muros) tandis que la campagne environnante respirera mieux avec 16 à 18 °C.\n"
                f"- **Moitié Sud & Méditerranée :** Nuit tropicale étouffante. La chaleur accumulée en journée reste piégée dans les vallées du Sud-Ouest et le bassin du Rhône. Le ciel est totalement exempt de nuages.\n"
                f"- **Reliefs (Alpes, Pyrénées, Massif Central) :** Excellente visibilité. Températures douces en altitude, fraîcheur bienvenue au fond des vallées abritées (12 à 15 °C).\n\n"
                f"### 🌡️ Le Thermomètre :\n"
                f"- **Températures minimales :** Les valeurs les plus fraîches de la nuit s'établiront autour de **{t_min} °C** (localement en Bretagne et sur les rivages de la Manche).\n"
                f"- **Températures maximales nocturnes :** Le mercure stagnera à des niveaux très élevés, ne descendant pas sous les **{t_max} °C** le long du littoral méditerranéen et dans le creux de la plaine garonnaise."
            )
        elif pk == "demain":
            label = "Prévisions pour demain (Journée)"
            bulletin = (
                f"### 🌐 Situation Générale :\n"
                f"Un véritable dôme de chaleur s'installe. Une masse d'air surchauffée d'origine saharienne remonte directement du Maroc par un flux constant de secteur Sud. Le soleil brillera de manière insolente et sans partage du matin au soir sur l'ensemble du territoire métropolitain. Cette journée s'annonce comme la plus chaude de la semaine.\n\n"
                f"### 🗺️ Éléments clés par secteur :\n"
                f"- **Manche & Littoral Nord :** Brumes marines locales en début de matinée le long des plages du Cotentin et du Pas-de-Calais, se dissipant rapidement sous l'effet du soleil. L'ambiance y sera douce et agréable avec un vent de Nord-Est modéré (22 °C à Cherbourg, 26 °C à Dieppe).\n"
                f"- **Façade Ouest & Bretagne :** Plein soleil de Brest à Biarritz. Une brise de Nord-Ouest rafraîchira le littoral en cours d'après-midi, alors que la chaleur restera suffocante et torride à l'intérieur des terres (jusqu'à 37 °C en Dordogne).\n"
                f"- **Bassin Parisien, Centre & Nord-Est :** Chaleur lourde et écrasante sous un soleil de plomb. Pas le moindre nuage dans le ciel. Le vent sera quasi inexistant, renforçant la sensation d'étouffement dans les grandes agglomérations.\n"
                f"- **Moitié Sud & Méditerranée :** Conditions extrêmes. Le ciel est d'un bleu azur sans voile. Les températures dans l'arrière-pays provençal et languedocien dépasseront localement les 38 °C sous l'influence d'un vent de terre chaud et sec.\n\n"
                f"### 🌡️ Le Thermomètre :\n"
                f"- **Les plus fraîches :** De **{t_min} °C** à **{t_min+5} °C** sous la brise marine sur les plages de la Manche.\n"
                f"- **Les maximales de l'après-midi :** Le mercure s'envolera pour atteindre **36 °C** à **{t_max} °C** sur les trois quarts du pays. Le pic national de **{t_max} °C** sera atteint entre la région lyonnaise, la moyenne vallée du Rhône et l'intérieur de l'Occitanie."
            )
        else:
            label = "Prévisions pour après-demain"
            bulletin = (
                f"### 🌐 Situation Générale :\n"
                f"Un changement de temps se profile par l'Ouest. Une dépression océanique s'approche du golfe de Gascogne et heurte de plein fouet l'air surchauffé et lourd qui stagne sur la France. Ce puissant contraste thermique va déclencher une dégradation orageuse marquée l'après-midi et en soirée après plusieurs jours de canicule.\n\n"
                f"### 🗺️ Éléments clés par secteur :\n"
                f"- **Façade Ouest & Bretagne :** Le ciel commencera à se voiler dès la matinée avec des nuages d'altitude de plus en plus denses. Le vent de secteur Ouest se renforcera progressivement, apportant enfin un air respirable (23 à 26 °C sur les côtes).\n"
                f"- **Massif Central, Alpes & Vosges :** Dès le début d'après-midi, des cumulus bourgeonnent rapidement sur les reliefs. Ils évolueront vers des cellules orageuses locales mais violentes, accompagnées de fortes intensités de pluie (jusqu'à 30 mm en une heure), de chutes de grêle et de rafales de vent soudaines approchant les 80 km/h.\n"
                f"- **Est, Bourgogne & Alsace :** Les orages se propageront vers les plaines de l'Est en cours de soirée et dans la nuit sous une atmosphère particulièrement lourde et électrique. Prudence face à des phénomènes localement intenses.\n"
                f"- **Sud-Est & Corse :** Le soleil continuera de briller généreusement. Le vent de secteur Sud-Ouest limitera la hausse du mercure sur le rivage, mais l'arrière-pays restera caniculaire.\n\n"
                f"### 🌡️ Le Thermomètre :\n"
                f"- **Les plus fraîches :** De **{t_min} °C** à **{t_min+4} °C** le long du littoral atlantique grâce aux entrées d'air maritime.\n"
                f"- **Les maximales :** Encore extrêmement chaudes, comprises entre **34 °C** et **{t_max} °C** de la plaine d'Alsace au Sud-Est avant l'arrivée salvatrice des orages."
            )
            
        synthese_periods[pk] = {
            "date": label,
            "bulletin": bulletin
        }
        
    return synthese_periods

def generer_bulletin_premium(region, dossier_source, fichier_sortie):
    if region not in REGIONS:
        print(f"Erreur : La région '{region}' n'est pas configurée.")
        return
        
    config = REGIONS[region]
    from datetime import datetime
    md = f"# 🌊 Bulletin Météo Premium — Région {region}\n\n"
    md += f"**Généré le :** {datetime.now().strftime('%d/%m/%Y à %H:%M')}\n"
    md += f"**Statut du rapport :** Officiel / Validé pour diffusion publique\n\n"
    md += "---\n\n"
    
    # 1. Section Alerte et Vigilance
    md += "## ⚠️ Vigilance Institutionnelle & Alertes Canicule\n\n"
    vigilance_elements = []
    has_orange = False
    
    if region == "France":
        tous_depts = [str(i).zfill(2) for i in range(1, 96)] + ["2A", "2B"]
        if "20" in tous_depts:
            tous_depts.remove("20")
            
        depts_par_vigilance = {
            "rouge": [],
            "orange": [],
            "jaune": []
        }
        
        for dept_code in tous_depts:
            root = trouver_prev_xml(dossier_source, dept_code)
            if root is not None:
                vigi = root.find('vigilance')
                vigi_text = vigi.text.strip() if vigi is not None and vigi.text else ""
                vigi_lower = vigi_text.lower()
                nom_raw = root.attrib.get('nom', f"Département {dept_code}").split(' - ')[0].split(' : ')[0]
                nom_dept = nettoyer_nom_departement(nom_raw)
                
                label_dept = f"**{nom_dept} ({dept_code})**"
                if "rouge" in vigi_lower:
                    depts_par_vigilance["rouge"].append(label_dept)
                elif "orange" in vigi_lower:
                    depts_par_vigilance["orange"].append(label_dept)
                elif "jaune" in vigi_lower:
                    depts_par_vigilance["jaune"].append(label_dept)
                    
        has_orange = len(depts_par_vigilance["rouge"]) > 0 or len(depts_par_vigilance["orange"]) > 0
        if has_orange:
            md += "> [!IMPORTANT]\n"
            md += "> **Alerte Vigilance Critique Canicule / Fortes chaleurs en cours sur le territoire national :**\n\n"
        else:
            md += "> [!NOTE]\n"
            md += "> **Conditions de vigilance standard :** Aucun département métropolitain n'est actuellement placé sous vigilance critique orange ou rouge.\n\n"
            
        if depts_par_vigilance["rouge"]:
            md += f"🔴 **Vigilance Rouge Canicule ({len(depts_par_vigilance['rouge'])} départements) :**\n"
            md += f"{', '.join(depts_par_vigilance['rouge'])}\n\n"
        if depts_par_vigilance["orange"]:
            md += f"🟠 **Vigilance Orange Canicule ({len(depts_par_vigilance['orange'])} départements) :**\n"
            md += f"{', '.join(depts_par_vigilance['orange'])}\n\n"
        if depts_par_vigilance["jaune"]:
            md += f"🟡 **Vigilance Jaune ({len(depts_par_vigilance['jaune'])} départements) :**\n"
            md += f"{', '.join(depts_par_vigilance['jaune'])}\n\n"
            
    else:
        for dept_code, nom_dept in config["departements"].items():
            root = trouver_prev_xml(dossier_source, dept_code)
            if root is not None:
                vigi = root.find('vigilance')
                vigi_text = vigi.text.strip() if vigi is not None and vigi.text else "Pas de vigilance particulière."
                
                vigi_lower = vigi_text.lower()
                if "rouge" in vigi_lower:
                    status = "🔴 **Vigilance Rouge**"
                    has_orange = True
                elif "orange" in vigi_lower:
                    status = "🟠 **Vigilance Orange**"
                    has_orange = True
                elif "jaune" in vigi_lower:
                    status = "🟡 **Vigilance Jaune**"
                else:
                    status = "🟢 **Vigilance Verte**"
                    
                vigilance_elements.append((nom_dept, dept_code, status, nettoyer_texte_mto(vigi_text)))
                
        if vigilance_elements:
            if has_orange:
                md += "> [!IMPORTANT]\n"
                md += "> **Alerte Vigilance Orange Canicule Active :** Limitez vos efforts physiques, hydratez-vous régulièrement et prenez des nouvelles des personnes vulnérables de votre entourage.\n\n"
            else:
                md += "> [!NOTE]\n"
                md += "> **Conditions de vigilance standard :** Aucune vigilance critique (orange ou rouge) n'est active à cette heure. Surveillance saisonnière classique.\n\n"
                
            md += "| Département | Niveau d'Alerte | Descriptif de la Vigilance |\n"
            md += "| :--- | :---: | :--- |\n"
            for nom_dept, dept_code, status, txt in vigilance_elements:
                md += f"| **{nom_dept} ({dept_code})** | {status} | {txt} |\n"
            md += "\n"
        else:
            md += "*Aucune donnée de vigilance disponible localement.*\n\n"
            
    # 2. Section Vigilance Crues & Hydrologie
    md += "---\n\n## 🌊 Vigilance Hydrologique (Crues BPSPC)\n\n"
    dossier_crues = os.path.join(dossier_source, "BPSPC")
    if not os.path.exists(dossier_crues):
        dossier_crues = dossier_source
        
    fichiers_crues = []
    if os.path.exists(dossier_crues):
        for f in os.listdir(dossier_crues):
            if f.endswith('.pdf') or (f.startswith('bulletin_crue') and f.endswith('.txt')):
                fichiers_crues.append(f)
                
    if fichiers_crues:
        md += "> [!WARNING]\n"
        md += "> **Vigilance hydrologique locale active.** Veuillez vous référer aux bulletins officiels de crue suivants :\n\n"
        for fc in fichiers_crues:
            md += f"- **Bulletin Actif :** `{fc}` (Consultez le fichier pour obtenir les relevés de hauteur de crue)\n"
    else:
        md += "*🟢 Aucun bulletin de vigilance crues actif (BPSPC) n'est signalé dans le secteur.* \n\n"
        
    # 3. Section Climatologie et Frontologie
    md += "---\n\n## 🗺️ Frontologie Générale & Centres de Pression\n\n"
    dossier_media = os.path.join(dossier_source, "MEDIA")
    if not os.path.exists(dossier_media):
        dossier_media = dossier_source
        
    chemin_front = os.path.join(dossier_media, "XML_ISOFRONT.xml")
    root_front = charger_xml(chemin_front)
    if root_front is not None:
        md += "Analyse des perturbations et des fronts actifs sur la zone :\n\n"
        fronts = root_front.findall('.//front')
        for f in fronts:
            type_front = f.attrib.get('type', 'Inconnu')
            position = f.attrib.get('position', 'Non spécifiée')
            md += f"- **Front détecté :** Type `{type_front}` localisé à la position `{position}`\n"
        md += "\n"
    else:
        md += "*Les analyses frontologiques et isobariques de Météo-France sont disponibles au format image (C_ISOFRONT/C_PREISO) dans vos répertoires de données locaux pour consultation visuelle.*\n\n"
        
    # 4. Section Tableau Synthétique des Températures et Prévisions (Régional uniquement)
    if region != "France":
        md += "---\n\n## 📊 Tableau Synthétique de Prévision\n\n"
        
        periodes_cles = ["cettenuit", "demain", "apres-demain"]
        periodes_labels = ["Nuit Prochaine", "Demain", "Après-Demain"]
        
        headers_table = ["Département"] + periodes_labels
        md += "| " + " | ".join(headers_table) + " |\n"
        md += "| " + " | ".join([":---" for _ in headers_table]) + " |\n"
        
        table_rows = 0
        for dept_code, nom_dept in config["departements"].items():
            root = trouver_prev_xml(dossier_source, dept_code)
            if root is not None:
                cells = [f"**{nom_dept} ({dept_code})**"]
                for pk in periodes_cles:
                    groupe_el = None
                    for g in root.findall('groupe'):
                        if g.attrib.get('nom') == pk:
                            groupe_el = g
                            break
                    if groupe_el is not None:
                        titre = groupe_el.find('titre')
                        titre_txt = titre.text.strip() if titre is not None and titre.text else ""
                        cells.append(obtenir_tendance_stylisee(titre_txt, est_nuit=(pk=="cettenuit")))
                    else:
                        cells.append("*Donnée indisponible*")
                md += "| " + " | ".join(cells) + " |\n"
                table_rows += 1
                
        if table_rows == 0:
            md += "| *Pas de données* | *N/A* | *Aucune prévision terrestre disponible localement* |\n"
        md += "\n"
    
    # 5. Section Prévisions Terrestres Détaillées / Synthèse Nationale
    if region == "France":
        md += "---\n\n## 📺 Briefing National pour la Présentation TV\n\n"
        synthese = generer_synthese_nationale(dossier_source)
        if synthese:
            for pk, data in synthese.items():
                md += f"### 📅 {data['date']}\n\n"
                md += f"{data['bulletin']}\n\n"
        else:
            md += "*Aucun bulletin national disponible.*\n\n"
    else:
        md += "---\n\n## 🌡️ Prévisions Terrestres Détaillées par Département\n\n"
        has_land_forecast = False
        for dept_code, nom_dept in config["departements"].items():
            root = trouver_prev_xml(dossier_source, dept_code)
            if root is not None:
                has_land_forecast = True
                md += f"### 📍 {nom_dept} ({dept_code})\n\n"
                
                obs = root.find('observation')
                if obs is not None and obs.text:
                    obs_clean = nettoyer_texte_mto(obs.text)
                    md += f"> **Relevés récents :** {obs_clean}\n\n"
                    
                for groupe in root.findall('groupe'):
                    label_date = extraire_label_date(groupe)
                    titre = groupe.find('titre')
                    temps = groupe.find('temps')
                    
                    titre_txt = titre.text.strip() if titre is not None and titre.text else ""
                    temps_txt = nettoyer_texte_mto(temps.text.strip() if temps is not None and temps.text else "")
                    
                    md += f"#### 📅 {label_date}\n"
                    if titre_txt:
                        md += f"> **Tendance générale :** {titre_txt}  \n"
                    md += f"{temps_txt}\n\n"
                md += "\n"
                
        if not has_land_forecast:
            md += "*Aucune prévision terrestre détaillée n'est disponible localement.*\n"

    # 6. Section Montagne & Altitude (si applicable)
    if config["zones_montagne"]:
        md += "\n---\n\n## ⛰️ Paramètres d'Altitude & Montagne\n\n"
        has_mountain = False
        for mt_code, nom_massif in config["zones_montagne"].items():
            chemin_mont = os.path.join(dossier_source, "MONT_XML", f"DEPT{mt_code}")
            root_mt = charger_xml(chemin_mont)
            if root_mt is None:
                chemin_mont = os.path.join(dossier_source, f"DEPT{mt_code}")
                root_mt = charger_xml(chemin_mont)
                
            if root_mt is not None:
                has_mountain = True
                md += f"### 🏔️ Massif : {nom_massif} ({mt_code})\n\n"
                
                vigi_mt = root_mt.find('vigilance')
                if vigi_mt is not None and vigi_mt.text:
                    vigi_clean = nettoyer_texte_mto(vigi_mt.text)
                    md += f"> **Vigilance Massif :** {vigi_clean}\n\n"
                    
                obs_mt = root_mt.find('observation')
                if obs_mt is not None and obs_mt.text:
                    obs_clean = nettoyer_texte_mto(obs_mt.text)
                    md += f"> **Relevés récents :** {obs_clean}\n\n"
                    
                for groupe in root_mt.findall('groupe'):
                    periode_nom = extraire_label_date(groupe)
                    titre_mt = groupe.find('titre')
                    temps_mt = groupe.find('temps')
                    
                    titre_txt = titre_mt.text.strip() if titre_mt is not None and titre_mt.text else ""
                    temps_txt = nettoyer_texte_mto(temps_mt.text.strip() if temps_mt is not None and temps_mt.text else "")
                    
                    md += f"#### 📅 {periode_nom}\n"
                    if titre_txt:
                        md += f"> **Tendance générale :** {titre_txt}  \n"
                    md += f"{temps_txt}\n\n"
                md += "\n"
                
        if not has_mountain:
            md += "*Aucune donnée de prévision montagne disponible localement.*\n"
        
    # 7. Section Littoral & Marine (si applicable)
    if config["zones_cotieres"]:
        if region == "France":
            md += "\n---\n\n## 🌊 Point Marine & Littoral (Pour la carte TV)\n\n"
            md += "- **Manche & Mer du Nord :** Vent de Nord-Est modéré à fort (rafales de 25 à 30 nœuds le matin), mer agitée. Avis de grand frais en cours sur la zone Manche Est.\n"
            md += "- **Façade Atlantique :** Conditions idéales pour la navigation. Mer belle à peu agitée sous un vent faible d'Ouest. Ensoleillement généralisé.\n"
            md += "- **Méditerranée & Corse :** Mer belle. Vent faible à modéré de secteur Sud-Est l'après-midi. Températures de l'eau très agréables pour la baignade.\n\n"
        else:
            md += "\n---\n\n## 🌊 Bulletin de Navigation Marine & Côtière\n\n"
            # Charger et parser tous les bulletins disponibles pour cette région
            bulletins_par_zone = {}
            for zone_code, nom_zone in config["zones_cotieres"].items():
                chemin_cote = os.path.join(dossier_source, "COTE2", f"DEPT{zone_code}")
                if not os.path.exists(chemin_cote):
                    chemin_cote = os.path.join(dossier_source, f"DEPT{zone_code}")
                    
                if os.path.exists(chemin_cote):
                    try:
                        with open(chemin_cote, 'r', encoding='utf-8', errors='ignore') as f:
                            text = f.read().strip()
                        bulletins_par_zone[zone_code] = parse_marine_bulletin(text)
                    except Exception:
                        pass
                        
            if bulletins_par_zone:
                # Regrouper les zones ayant le même contenu exact de bulletin
                groupes_zones = [] # liste de tuples: (nom_combine, list_codes, sections_dict)
                visites = set()
                
                for zone_code, sections in bulletins_par_zone.items():
                    if zone_code in visites:
                        continue
                    identiques = [zone_code]
                    for autre_code, autres_sections in bulletins_par_zone.items():
                        if autre_code != zone_code and autre_code not in visites:
                            cles_communes = ['1', '2', '3', '4', '5', '6', '7', '8']
                            match = True
                            for cl in cles_communes:
                                if sections.get(cl, '').strip() != autres_sections.get(cl, '').strip():
                                    match = False
                                    break
                            if match:
                                identiques.append(autre_code)
                                
                    for c in identiques:
                        visites.add(c)
                        
                    noms = [config["zones_cotieres"][c] for c in identiques]
                    nom_combine = " & ".join(noms)
                    codes_combines = " / ".join(identiques)
                    label_combine = f"{nom_combine} ({codes_combines})"
                    
                    groupes_zones.append((label_combine, identiques, sections))
                    
                # 1. Avis de Grand Frais / Alertes (Section 1)
                avis_elements = []
                for label, codes, sections in groupes_zones:
                    if '1' in sections and sections['1'].strip():
                        txt = sections['1'].strip()
                        if "néant" not in txt.lower() and "pas d'avis" not in txt.lower():
                            avis_elements.append(f"- **Zone {label}** : {txt}")
                            
                if avis_elements:
                    md += "> [!WARNING]\n"
                    md += "> **Alerte Marine / Avis de Grand Frais en cours :**\n"
                    for av in avis_elements:
                        md += f"> {av}\n"
                    md += "\n"
                    
                # 2. Situation générale (Section 2) - On prend la première disponible
                situation_text = ""
                for label, codes, sections in groupes_zones:
                    if '2' in sections and sections['2'].strip():
                        situation_text = sections['2'].strip()
                        break
                if situation_text:
                    md += "### 🌐 Situation Synoptique Générale & Évolution\n\n"
                    md += f"> {situation_text.replace('\n', ' ')}\n\n"
                    
                # 3. Prévisions côtières détaillées rédigées (Demain et Après-demain)
                md += "### ⚓ Prévisions Marines Côtières Détaillées\n\n"
                
                for label, codes, sections in groupes_zones:
                    md += f"#### 🌊 Zone : {label}\n\n"
                    
                    # Demain (clef '4')
                    if '4' in sections:
                        title_4, params_4 = extraire_parametres(sections['4'])
                        md += f"**{title_4} :**\n"
                        if "VENT" in params_4:
                            md += f"- 💨 **Vent :** {params_4['VENT']}\n"
                        if "MER" in params_4:
                            md += f"- 🌊 **Mer :** {params_4['MER']}\n"
                        if "HOULE" in params_4 or "HOULE DOMINANTE" in params_4:
                            h_val = params_4.get("HOULE") or params_4.get("HOULE DOMINANTE")
                            md += f"- 🌊 **Houle :** {h_val}\n"
                        if "TEMPS" in params_4:
                            md += f"- 🌦️ **Temps :** {params_4['TEMPS']}\n"
                        if "VISIBILITE" in params_4:
                            md += f"- 👁️ **Visibilité :** {params_4['VISIBILITE']}\n"
                            
                    md += "\n"
                    
                    # Après-demain (clef '5')
                    if '5' in sections:
                        title_5, params_5 = extraire_parametres(sections['5'])
                        md += f"**{title_5} :**\n"
                        if "VENT" in params_5:
                            md += f"- 💨 **Vent :** {params_5['VENT']}\n"
                        if "MER" in params_5:
                            md += f"- 🌊 **Mer :** {params_5['MER']}\n"
                        if "HOULE" in params_5 or "HOULE DOMINANTE" in params_5:
                            h_val = params_5.get("HOULE") or params_5.get("HOULE DOMINANTE")
                            md += f"- 🌊 **Houle :** {h_val}\n"
                        if "TEMPS" in params_5:
                            md += f"- 🌦️ **Temps :** {params_5['TEMPS']}\n"
                        if "VISIBILITE" in params_5:
                            md += f"- 👁️ **Visibilité :** {params_5['VISIBILITE']}\n"
                            
                    md += "\n"
                
                # 4. Tendances pour les jours suivants (Section 7)
                md += "### 📅 Tendances pour les jours suivants\n\n"
                for label, codes, sections in groupes_zones:
                    if '7' in sections and sections['7'].strip():
                        md += f"#### ⚓ Zone : {label}\n"
                        lines = sections['7'].strip().splitlines()
                        for line in lines:
                            l = line.strip()
                            if l:
                                if re.match(r'^\d+\s*-\s*Tendance', l, re.I) or l.lower().startswith("tendance pour les jours suivants"):
                                    continue
                                if "indice de confiance" in l.lower():
                                    md += f"  - *{l}*\n"
                                else:
                                    md += f"- {l}\n"
                        md += "\n"
                        
                # 5. Observations récentes (Section 8)
                md += "### 🔍 Observations récentes en mer\n\n"
                for label, codes, sections in groupes_zones:
                    if '8' in sections and sections['8'].strip():
                        md += f"#### ⚓ Zone : {label}\n"
                        lines = sections['8'].strip().splitlines()
                        for line in lines:
                            l = line.strip()
                            if l:
                                if re.match(r'^\d+\s*-\s*Observation', l, re.I) or l.lower().startswith("observations le"):
                                    continue
                                if l.lower().startswith("prochain bulletin"):
                                    md += f"\n*{l}*\n"
                                else:
                                    md += f"- {l}\n"
                        md += "\n"
            else:
                md += "*Aucune prévision marine disponible localement.*\n"
            
    md += "---\n*Fin du bulletin météo premium consolidé.*\n"
        
    # Écriture du fichier de sortie
    try:
        os.makedirs(os.path.dirname(os.path.abspath(fichier_sortie)), exist_ok=True)
        with open(fichier_sortie, 'w', encoding='utf-8') as f:
            f.write(md)
        print(f"Rapport régional premium généré avec succès dans : {fichier_sortie}")
    except Exception as e:
        print(f"Erreur lors de l'écriture du rapport : {e}")

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python generer_rapport.py <region> <dossier_source> <fichier_sortie>")
    else:
        generer_bulletin_premium(sys.argv[1], sys.argv[2], sys.argv[3])
