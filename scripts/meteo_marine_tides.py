"""
meteo_marine_tides.py
Sources exactes par bulletin (selon prompt original) :

BULLETIN NATIONAL :
  - Vigilance France      : https://vigilance.meteofrance.com/fr
  - Marine Brest          : https://meteofrance.com/previsions-meteo-marine/brest/292219
  - Marine Marseille      : https://meteofrance.com/previsions-meteo-marine/marseille/132551
  - Marine Arcachon       : https://meteofrance.com/previsions-meteo-marine/arcachon/330090
  - Plages                : https://meteofrance.com/meteo-des-plages
  - Eau mer               : https://fr.seatemperature.org/
  - Marées Brest          : https://maree.info/62

BULLETIN HDF (Hauts-de-France) :
  - Vigilance Nord        : https://vigilance.meteofrance.com/fr/nord
  - Vigilance PdC         : https://vigilance.meteofrance.com/fr/pas-de-calais
  - Vigilance Somme       : https://vigilance.meteofrance.com/fr/somme
  - Vigilance Oise        : https://vigilance.meteofrance.com/fr/oise
  - Vigilance Aisne       : https://vigilance.meteofrance.com/fr/aisne
  - Marine Dunkerque      : https://meteofrance.com/previsions-meteo-marine/dunkerque/591831
  - Marine Boulogne       : https://meteofrance.com/previsions-meteo-marine/boulogne-sur-mer/621601
  - Eau mer HDF           : https://fr.seatemperature.org/ (Dunkerque, Calais, Boulogne, Le Touquet)
  - Marées Côte d'Opale   : https://maree.info/80 (Dunkerque), /78 (Calais), /79 (Boulogne), /82 (Le Touquet)

BULLETIN NPDC (Nord-Pas-de-Calais) :
  - Vigilance Nord        : https://vigilance.meteofrance.com/fr/nord
  - Vigilance PdC         : https://vigilance.meteofrance.com/fr/pas-de-calais
  - Marine Dunkerque      : https://meteofrance.com/previsions-meteo-marine/dunkerque/591831
  - Marine Boulogne       : https://meteofrance.com/previsions-meteo-marine/boulogne-sur-mer/621601
  - Eau mer NPDC          : https://fr.seatemperature.org/ (Dunkerque, Calais, Boulogne, Le Touquet)
  - Marées Côte d'Opale   : https://maree.info/80 (Dunkerque), /78 (Calais), /79 (Boulogne), /82 (Le Touquet)

Génère data/tides_marine.json avec toutes les sections.
"""

import json, os, re, urllib.request, datetime
from html.parser import HTMLParser

BASE_DIR    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR    = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)
OUTPUT_JSON = os.path.join(DATA_DIR, "tides_marine.json")
SOURCES_NAT = os.path.join(BASE_DIR, "sources_raw_national.md")
SOURCES_HDF = os.path.join(BASE_DIR, "sources_raw_hdf.md")

UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'

def fetch(url, timeout=12):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': UA})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read().decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"  Notice {url[:70]}: {e}")
        return ""

def read_file(path):
    return open(path, encoding='utf-8').read() if os.path.exists(path) else ""

class Strip(HTMLParser):
    def __init__(self): super().__init__(); self.out=[]; self._s=False
    def handle_starttag(self, t, a):
        if t in ('script','style'): self._s=True
    def handle_endtag(self, t):
        if t in ('script','style'): self._s=False
    def handle_data(self, d):
        if not self._s and d.strip(): self.out.append(d.strip())

def html_text(html):
    p = Strip(); p.feed(html); return " ".join(p.out)

# ─────────────────────────────────────────────────────────────────────────────
# VIGILANCE → vigilance.meteofrance.com/fr/<dept>
# ─────────────────────────────────────────────────────────────────────────────

VIGILANCE_URLS = {
    # Bulletins HDF & NPDC
    "nord":          "https://vigilance.meteofrance.com/fr/nord",
    "pas-de-calais": "https://vigilance.meteofrance.com/fr/pas-de-calais",
    "somme":         "https://vigilance.meteofrance.com/fr/somme",
    "oise":          "https://vigilance.meteofrance.com/fr/oise",
    "aisne":         "https://vigilance.meteofrance.com/fr/aisne",
    # Bulletin National
    "france":        "https://vigilance.meteofrance.com/fr",
}

def scrape_vigilance(dept):
    t = html_text(fetch(VIGILANCE_URLS[dept], timeout=10)).lower()
    if not t:                  return "🟢 Vert (données indisponibles)"
    if "rouge"  in t:          return "🔴 Vigilance Rouge"
    if "orange" in t:          return "🟠 Vigilance Orange"
    if "jaune"  in t:          return "🟡 Vigilance Jaune"
    return "🟢 Vigilance Verte"

def get_vigilance_national():
    print("  Vigilance France...")
    return {"france": scrape_vigilance("france")}

def get_vigilance_hdf():
    result = {}
    for dept in ["nord", "pas-de-calais", "somme", "oise", "aisne"]:
        print(f"  Vigilance {dept}...")
        result[dept] = scrape_vigilance(dept)
    return result

def get_vigilance_npdc():
    result = {}
    for dept in ["nord", "pas-de-calais"]:
        print(f"  Vigilance {dept}...")
        result[dept] = scrape_vigilance(dept)
    return result

# ─────────────────────────────────────────────────────────────────────────────
# MARINE → meteofrance.com/previsions-meteo-marine/<port>/<id>
# ─────────────────────────────────────────────────────────────────────────────

MARINE_MF_URLS = {
    # Bulletins HDF & NPDC
    "Dunkerque":        "https://meteofrance.com/previsions-meteo-marine/dunkerque/591831",
    "Boulogne-sur-Mer": "https://meteofrance.com/previsions-meteo-marine/boulogne-sur-mer/621601",
    # Bulletin National
    "Brest":            "https://meteofrance.com/previsions-meteo-marine/brest/292219",
    "Marseille":        "https://meteofrance.com/previsions-meteo-marine/marseille/132551",
    "Arcachon":         "https://meteofrance.com/previsions-meteo-marine/arcachon/330090",
}

def scrape_marine_mf(port):
    url = MARINE_MF_URLS.get(port, "")
    if not url: return ""
    t = html_text(fetch(url, timeout=10))
    vent = re.search(r'(vent|wind)[^\.]{0,150}', t, re.IGNORECASE)
    mer  = re.search(r'(mer|houle|vague)[^\.]{0,150}', t, re.IGNORECASE)
    parts = []
    if vent: parts.append(vent.group(0).strip()[:120])
    if mer:  parts.append(mer.group(0).strip()[:120])
    return " — ".join(parts) if parts else t[:250]

# ─────────────────────────────────────────────────────────────────────────────
# PLAGES → meteofrance.com/meteo-des-plages (résumé national)
# ─────────────────────────────────────────────────────────────────────────────

def scrape_meteo_plages():
    t = html_text(fetch("https://meteofrance.com/meteo-des-plages", timeout=10))
    air   = re.search(r'air[^\d]{0,10}(\d{1,2})\s*°', t, re.IGNORECASE)
    water = re.search(r'eau[^\d]{0,10}(\d{1,2})\s*°', t, re.IGNORECASE)
    flag  = re.search(r'(vert|jaune|rouge|interdit|surveil)', t, re.IGNORECASE)
    return {
        "air":   f"{air.group(1)}°C"   if air   else "–",
        "water": f"{water.group(1)}°C" if water else "–",
        "flag":  flag.group(0).capitalize() if flag else "🔵 Voir meteofrance.com/meteo-des-plages",
        "source": "https://meteofrance.com/meteo-des-plages"
    }

# ─────────────────────────────────────────────────────────────────────────────
# TEMPÉRATURE EAU → fr.seatemperature.org
# Slugs par bulletin
# ─────────────────────────────────────────────────────────────────────────────

# Bulletin NPDC (Côte d'Opale uniquement)
SEA_NPDC = {
    "Malo-les-Bains / Dunkerque":      "europe/france/dunkerque",
    "Calais / Sangatte":               "europe/france/calais",
    "Wissant / Cap Blanc-Nez":         "europe/france/wissant",
    "Wimereux / Boulogne":             "europe/france/boulogne-sur-mer",
    "Hardelot-Plage":                  "europe/france/neufchatel-hardelot",
    "Le Touquet-Paris-Plage":          "europe/france/le-touquet-paris-plage",
    "Stella / Merlimont / Berck":      "europe/france/berck",
    "Baie de Somme (Cayeux / Crotoy)": "europe/france/cayeux-sur-mer",
}

# Bulletin HDF = NPDC + Baie de Somme (déjà inclus)
SEA_HDF = SEA_NPDC  # identique

# Bulletin National = toutes les façades
SEA_NATIONAL = {
    **SEA_NPDC,
    "Manche / Côte d'Opale":        "europe/france/cherbourg",
    "Bretagne (Nord & Sud)":         "europe/france/brest",
    "Atlantique (Vendée à Landes)":  "europe/france/arcachon",
    "Côte Basque (Biarritz)":        "europe/france/biarritz",
    "Méditerranée (Languedoc/PACA)": "europe/france/marseille",
    "Corse (Ajaccio / Bastia)":      "europe/france/ajaccio",
}

def scrape_water_temp(slug):
    html = fetch(f"https://fr.seatemperature.org/{slug}.htm")
    m = re.search(r'(\d{1,2}\.?\d?)\s*°C', html)
    return f"{m.group(1)}°C" if m else "–"

def get_sea_temps(slugs_dict):
    return {name: scrape_water_temp(slug) for name, slug in slugs_dict.items()}

# ─────────────────────────────────────────────────────────────────────────────
# MARÉES → maree.info (IDs du prompt, par bulletin)
# ─────────────────────────────────────────────────────────────────────────────

# Bulletin NPDC & HDF : Dunkerque/80, Calais/78, Boulogne/79, Le Touquet/82
MAREE_NPDC = {"Dunkerque": 80, "Calais": 78, "Boulogne-sur-Mer": 79, "Le Touquet": 82}
# HDF ajoute Saint-Valery
MAREE_HDF  = {**MAREE_NPDC, "Saint-Valery-sur-Somme": 83}
# National ajoute Brest
MAREE_NAT  = {**MAREE_HDF, "Brest": 62}

def scrape_tide(port_id):
    html = fetch(f"https://maree.info/{port_id}")
    if not html: return {"pm": "–", "bm": "–", "coeff": "–"}
    p = Strip(); p.feed(html); lines = p.out
    pm, bm, co = [], [], []
    for i, l in enumerate(lines):
        if ('PM' in l or 'Pleine' in l) and len(pm) < 2:
            for j in lines[i:i+5]:
                m = re.search(r'(\d{1,2}h\d{2})', j)
                if m: pm.append(m.group(1).replace('h',':')); break
        if ('BM' in l or 'Basse' in l) and len(bm) < 2:
            for j in lines[i:i+5]:
                m = re.search(r'(\d{1,2}h\d{2})', j)
                if m: bm.append(m.group(1).replace('h',':')); break
        if re.match(r'^\d{2,3}$', l) and 20 <= int(l) <= 120 and len(co) < 2:
            co.append(l)
    return {"pm": " & ".join(pm) if pm else "–",
            "bm": " & ".join(bm) if bm else "–",
            "coeff": " / ".join(co) if co else "–"}

def get_tides(ports_dict):
    return {name: (print(f"  Marées {name} (maree.info/{pid})...") or scrape_tide(pid))
            for name, pid in ports_dict.items()}

# ─────────────────────────────────────────────────────────────────────────────
# PRÉVISIONS 14J → sources_raw (MF XML + Infoclimat forums)
# ─────────────────────────────────────────────────────────────────────────────

def extract_marine_xml(text, dept_tag):
    if not text: return ""
    for pat in [
        rf'BULLETIN MARINE.*?\[{re.escape(dept_tag)}\](.*?)(?====|Prochain bulletin)',
        rf'c[oô]tier.*?bande(.*?)(?:Prochain bulletin|===)',
    ]:
        m = re.search(pat, text, re.DOTALL | re.IGNORECASE)
        if m:
            raw = re.sub(r'\s+', ' ', m.group(1)).strip()
            vent = re.search(r'VENT\s*:\s*([^\.]{10,150})', raw, re.IGNORECASE)
            mer  = re.search(r'MER\s*:\s*([^\.]{10,120})',  raw, re.IGNORECASE)
            out = []
            if vent: out.append(f"Vent : {vent.group(1).strip()}")
            if mer:  out.append(f"Mer : {mer.group(1).strip()}")
            return " — ".join(out) if out else raw[:300]
    return ""

def extract_forecast_14d(text_nat, text_hdf):
    today   = datetime.date.today()
    fr_days = ["Lun","Mar","Mer","Jeu","Ven","Sam","Dim"]
    combined = (text_nat or "") + "\n" + (text_hdf or "")
    # Tendances XML MF jour par jour
    xml_days = {}
    for m in re.finditer(
        r'(Lundi|Mardi|Mercredi|Jeudi|Vendredi|Samedi|Dimanche)\s+(\d+)\s+\w+\s+([^\n]{5,200})',
        combined, re.IGNORECASE
    ):
        num = int(m.group(2))
        if num not in xml_days: xml_days[num] = m.group(3).strip()
    # Résumés Infoclimat S1 & S2
    snips = [re.sub(r'\s+',' ',m.group(0)).strip()
             for m in re.finditer(
                 r'(semaine\s*[12]|tendance|chaleur|instable|orage|fra[iî]ch)[^\n]{10,180}',
                 combined, re.IGNORECASE) if len(m.group(0)) > 20]
    sw1 = next((s for s in snips if re.search(r'semaine\s*1',s,re.I)), "")
    sw2 = next((s for s in snips if re.search(r'semaine\s*2',s,re.I)), "")
    itn = re.search(r'oscillant entre ([\d.]+).*?et ([\d.]+).*?°C', combined, re.IGNORECASE)
    itn_t = f"ITN {itn.group(1)}–{itn.group(2)}°C" if itn else "–"
    forecasts = []
    for i in range(14):
        d   = today + datetime.timedelta(days=i)
        lbl = f"{fr_days[d.weekday()]} {d.day}/{d.month:02d}"
        w2  = i >= 7
        xml = xml_days.get(d.day)
        if xml:
            cm   = re.search(r'confiance\s*:\s*(\d)\s*sur\s*5', xml, re.IGNORECASE)
            conf = f"🟢 MF {cm.group(1)}/5" if cm else "🟡 MF 3/5"
            desc = re.sub(r'[Ii]ndice de confiance.*', '', xml).strip()
            src  = "Météo-France XML"
        else:
            s    = sw2 if w2 else sw1
            desc = (s[:90]+"…") if len(s)>90 else s or ("S2 – Infoclimat" if w2 else "S1 – Infoclimat")
            conf = "🔴 Infoclimat 2/5" if w2 else "🟡 Infoclimat 3/5"
            src  = "Infoclimat"
        forecasts.append({"day_name":lbl,"weather":desc,"temp":itn_t if i<7 else "–",
                           "wind":"–","confidence":conf,"source":src})
    return forecasts

# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main():
    print("=== meteo_marine_tides.py ===")
    text_nat = read_file(SOURCES_NAT)
    text_hdf = read_file(SOURCES_HDF)
    print(f"  sources_raw_national : {len(text_nat)} car. | sources_raw_hdf : {len(text_hdf)} car.")

    # ── VIGILANCE par bulletin ──
    print("\n[1/6] Vigilance Météo-France...")
    vig_nat  = get_vigilance_national()
    vig_hdf  = get_vigilance_hdf()
    vig_npdc = get_vigilance_npdc()

    # ── MARINE par bulletin ──
    print("\n[2/6] Marine Météo-France (par bulletin)...")
    # NPDC & HDF
    marine_dunk   = scrape_marine_mf("Dunkerque")    # meteofrance.com/previsions-meteo-marine/dunkerque/591831
    marine_boul   = scrape_marine_mf("Boulogne-sur-Mer")  # /boulogne-sur-mer/621601
    # National
    marine_brest  = scrape_marine_mf("Brest")        # /brest/292219
    marine_arcd   = scrape_marine_mf("Arcachon")     # /arcachon/330090
    marine_mars   = scrape_marine_mf("Marseille")    # /marseille/132551
    # Fallback XML pour méditerranée
    marine_med_xml = extract_marine_xml(text_nat, "DEPT13-83")

    # ── PLAGES nationale ──
    print("\n[3/6] Météo des plages (meteofrance.com/meteo-des-plages)...")
    plages_mf = scrape_meteo_plages()

    # ── TEMPÉRATURE EAU par bulletin ──
    print("\n[4/6] Températures eau (fr.seatemperature.org)...")
    print("  >> Bulletin NPDC/HDF (Côte d'Opale)...")
    sea_npdc = get_sea_temps(SEA_NPDC)
    print("  >> Bulletin National (toutes façades)...")
    sea_extra = get_sea_temps({k:v for k,v in SEA_NATIONAL.items() if k not in SEA_NPDC})
    sea_nat  = {**sea_npdc, **sea_extra}

    # ── MARÉES par bulletin ──
    print("\n[5/6] Marées (maree.info, IDs par bulletin)...")
    print("  >> NPDC : Dunkerque/80, Calais/78, Boulogne/79, Le Touquet/82")
    tides_npdc = get_tides(MAREE_NPDC)
    print("  >> HDF : + Saint-Valery/83")
    tides_hdf  = {**tides_npdc, **get_tides({"Saint-Valery-sur-Somme": 83})}
    print("  >> National : + Brest/62")
    tides_nat  = {**tides_hdf, **get_tides({"Brest": 62})}

    # ── PRÉVISIONS 14J (commun, sources MF XML + Infoclimat) ──
    print("\n[6/6] Prévisions 14j (sources_raw Météo-France XML + Infoclimat)...")
    forecast14 = extract_forecast_14d(text_nat, text_hdf)

    # ── Assemblage JSON par bulletin ──
    def beaches_dict(sea_temps):
        return {name: {"water": wt, "flag": plages_mf.get("flag","🔵 Voir MF"), "uv":"–"}
                for name, wt in sea_temps.items()}

    full_data = {
        # ── Bulletin National ──
        "national": {
            "vigilance":   vig_nat,
            "tides":       tides_nat,
            "beaches":     beaches_dict(sea_nat),
            "marine": {
                "manche":       marine_brest or "Voir meteofrance.com/previsions-meteo-marine/brest/292219",
                "atlantique":   marine_arcd  or "Voir /arcachon/330090",
                "mediterranee": marine_mars  or marine_med_xml or "Voir /marseille/132551",
                "source":       "meteofrance.com/previsions-meteo-marine"
            },
            "plages_mf":   plages_mf,
            "forecast_14d": forecast14,
        },
        # ── Bulletin HDF ──
        "hdf": {
            "vigilance":   vig_hdf,
            "tides":       tides_hdf,
            "beaches":     beaches_dict(sea_npdc),
            "marine": {
                "dunkerque":  marine_dunk or "Voir meteofrance.com/previsions-meteo-marine/dunkerque/591831",
                "boulogne":   marine_boul or "Voir /boulogne-sur-mer/621601",
                "source":     "meteofrance.com/previsions-meteo-marine"
            },
            "plages_mf":   plages_mf,
            "forecast_14d": forecast14,
        },
        # ── Bulletin NPDC ──
        "npdc": {
            "vigilance":   vig_npdc,
            "tides":       tides_npdc,
            "beaches":     beaches_dict(sea_npdc),
            "marine": {
                "dunkerque":  marine_dunk or "Voir meteofrance.com/previsions-meteo-marine/dunkerque/591831",
                "boulogne":   marine_boul or "Voir /boulogne-sur-mer/621601",
                "source":     "meteofrance.com/previsions-meteo-marine"
            },
            "plages_mf":   plages_mf,
            "forecast_14d": forecast14,
        },
        # Rétrocompat : clés plates utilisées par generate_bulletins_html.py
        "tides":       tides_nat,
        "beaches":     beaches_dict(sea_nat),
        "forecast_14d": forecast14,
        "marine": {
            "nord_pas_de_calais": {"dunkerque": marine_dunk, "boulogne": marine_boul,
                                   "source": "meteofrance.com/previsions-meteo-marine"},
            "national": {"manche": marine_brest, "atlantique": marine_arcd,
                         "mediterranee": marine_mars or marine_med_xml,
                         "source": "meteofrance.com/previsions-meteo-marine"}
        }
    }

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(full_data, f, ensure_ascii=False, indent=2)

    print(f"\n✅ {OUTPUT_JSON}")
    print(f"   National : {len(tides_nat)} ports | {len(sea_nat)} plages")
    print(f"   HDF      : {len(tides_hdf)} ports | {len(sea_npdc)} plages")
    print(f"   NPDC     : {len(tides_npdc)} ports | {len(sea_npdc)} plages")
    print(f"   Prévisions 14j : {len(forecast14)} jours (MF XML + Infoclimat)")

if __name__ == "__main__":
    main()
