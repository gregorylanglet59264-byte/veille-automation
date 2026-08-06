"""
generate_bulletins_html.py
Génère 3 fichiers HTML Premium :
- public/bulletin_national.html
- public/bulletin_hdf.html
- public/bulletin_npdc.html
En intégrant les bulletins rédigés (.md), les données marées/plages (tides_marine.json)
et les prévisions sur 14 jours.
"""

import os
import json
import re
import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
PUBLIC_DIR = os.path.join(BASE_DIR, "public")
HDF_DIR = os.path.join(BASE_DIR, "Hauts-de-France")

os.makedirs(PUBLIC_DIR, exist_ok=True)

TIDES_JSON = os.path.join(DATA_DIR, "tides_marine.json")

# Sources primaires : générées en temps réel par run_infoclimat.py
# Fallback : fichiers statiques committés dans Hauts-de-France/
MD_FRANCE = os.path.join(BASE_DIR, "sources_raw_national.md") if os.path.exists(os.path.join(BASE_DIR, "sources_raw_national.md")) else os.path.join(HDF_DIR, "bulletin_france_premium.md")
MD_HDF = os.path.join(BASE_DIR, "sources_raw_hdf.md") if os.path.exists(os.path.join(BASE_DIR, "sources_raw_hdf.md")) else os.path.join(HDF_DIR, "bulletin_hauts_de_france_premium.md")

def read_file(path):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return ""

def load_tides_data():
    if os.path.exists(TIDES_JSON):
        with open(TIDES_JSON, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "tides": {},
        "beaches": {},
        "forecast_14d": [],
        "marine": {"nord_pas_de_calais": {}, "national": {}}
    }

def get_french_date():
    days = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
    months = ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin", "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"]
    today = datetime.date.today()
    return f"{days[today.weekday()]} {today.day} {months[today.month - 1]} {today.year}"

def md_to_html(md):
    if not md:
        return ""
    lines = md.split('\n')
    out = []
    in_table = False
    table_lines = []
    in_list = False
    
    def flush_table(t_lines):
        if not t_lines:
            return ''
        h = '<table><thead>'
        t_lines = [l for l in t_lines if not re.match(r'^\s*\|?\s*:?-+:?\s*\|', l)]
        for idx, line in enumerate(t_lines):
            cells = [c.strip() for c in line.strip('|').split('|')]
            tag = 'th' if idx == 0 else 'td'
            row_html = ''.join(f'<{tag}>{c}</{tag}>' for c in cells)
            if idx == 0:
                h += f'<tr>{row_html}</tr></thead><tbody>'
            else:
                h += f'<tr>{row_html}</tr>'
        h += '</tbody></table>'
        return h

    for line in lines:
        l = line.strip()
        if l.startswith('|'):
            if in_list:
                out.append('</ul>')
                in_list = False
            table_lines.append(l)
            in_table = True
            continue
        elif in_table:
            out.append(flush_table(table_lines))
            table_lines = []
            in_table = False
            
        if not l:
            if in_list:
                out.append('</ul>')
                in_list = False
            continue
        elif l.startswith('### '):
            if in_list: out.append('</ul>'); in_list = False
            out.append(f'<h3 style="color:var(--primary); margin-top:16px; font-size:1.15em;">{l[4:]}</h3>')
        elif l.startswith('## '):
            if in_list: out.append('</ul>'); in_list = False
            out.append(f'<h2 style="color:var(--text); border-bottom:1px solid var(--border); padding-bottom:6px; margin-top:24px; font-size:1.3em;">{l[3:]}</h2>')
        elif l.startswith('# '):
            if in_list: out.append('</ul>'); in_list = False
            out.append(f'<h1 style="color:var(--primary); margin-bottom:12px; font-size:1.5em;">{l[2:]}</h1>')
        elif l.startswith('> '):
            if in_list: out.append('</ul>'); in_list = False
            txt = l[2:].replace('[!IMPORTANT]', '⚠️').replace('[!NOTE]', 'ℹ️').replace('[!WARNING]', '⚠️')
            out.append(f'<div class="alert-box" style="margin:10px 0;"><p>{txt}</p></div>')
        elif l.startswith('- ') or l.startswith('* '):
            if not in_list:
                out.append('<ul style="padding-left:20px; margin-bottom:12px;">')
                in_list = True
            out.append(f'<li>{l[2:]}</li>')
        else:
            if in_list:
                out.append('</ul>')
                in_list = False
            out.append(f'<p style="margin-bottom:8px; line-height:1.6;">{l}</p>')

    if in_list:
        out.append('</ul>')
    if in_table:
        out.append(flush_table(table_lines))
        
    res = '\n'.join(out)
    res = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', res)
    return res

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
  <style>
    :root {{
      --bg: #0b1329;
      --card-bg: rgba(22, 33, 62, 0.85);
      --text: #f0f4f8;
      --text-muted: #94a3b8;
      --primary: #38bdf8;
      --accent: #0284c7;
      --border: rgba(255, 255, 255, 0.12);
      --success: #22c55e;
      --warning: #eab308;
      --danger: #ef4444;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
      background: radial-gradient(circle at 10% 20%, #0f172a 0%, #020617 90%);
      color: var(--text);
      line-height: 1.6;
      padding: 20px;
    }}
    .container {{
      max-width: 1000px;
      margin: 0 auto;
    }}
    .header {{
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: 24px;
      text-align: center;
      margin-bottom: 24px;
      backdrop-filter: blur(12px);
      box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
    }}
    .header h1 {{
      font-size: 2rem;
      color: var(--primary);
      margin-bottom: 8px;
    }}
    .header .date {{
      color: var(--text-muted);
      font-size: 0.95rem;
    }}
    .nav-bar {{
      display: flex;
      justify-content: center;
      gap: 12px;
      margin-bottom: 24px;
      flex-wrap: wrap;
    }}
    .nav-btn {{
      padding: 10px 20px;
      border-radius: 12px;
      background: var(--card-bg);
      border: 1px solid var(--border);
      color: var(--text);
      text-decoration: none;
      font-weight: 600;
      font-size: 0.9rem;
      transition: all 0.2s ease;
    }}
    .nav-btn:hover, .nav-btn.active {{
      background: var(--accent);
      color: #fff;
      border-color: var(--primary);
      box-shadow: 0 4px 12px rgba(2, 132, 199, 0.4);
    }}
    .section {{
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: 24px;
      margin-bottom: 24px;
      backdrop-filter: blur(12px);
    }}
    .section-title {{
      font-size: 1.25rem;
      color: var(--primary);
      border-bottom: 2px solid var(--border);
      padding-bottom: 12px;
      margin-bottom: 16px;
      display: flex;
      align-items: center;
      gap: 10px;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      margin-top: 12px;
      font-size: 0.9rem;
    }}
    th, td {{
      padding: 10px 12px;
      text-align: left;
      border-bottom: 1px solid var(--border);
    }}
    th {{
      background: rgba(255, 255, 255, 0.05);
      color: var(--primary);
      font-weight: 600;
    }}
    tr:hover {{
      background: rgba(255, 255, 255, 0.02);
    }}
    .badge {{
      display: inline-block;
      padding: 4px 8px;
      border-radius: 6px;
      font-size: 0.8rem;
      font-weight: 600;
    }}
    .badge-green {{ background: rgba(34, 197, 94, 0.2); color: #4ade80; border: 1px solid rgba(34, 197, 94, 0.4); }}
    .badge-yellow {{ background: rgba(234, 179, 8, 0.2); color: #facc15; border: 1px solid rgba(234, 179, 8, 0.4); }}
    .badge-red {{ background: rgba(239, 68, 68, 0.2); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.4); }}
    .alert-box {{
      background: rgba(56, 189, 248, 0.1);
      border-left: 4px solid var(--primary);
      padding: 12px 16px;
      border-radius: 0 8px 8px 0;
      margin-bottom: 16px;
    }}
    .footer {{
      text-align: center;
      padding: 20px;
      color: var(--text-muted);
      font-size: 0.85rem;
    }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>{icon} {title}</h1>
      <div class="date"><i class="fa-regular fa-clock"></i> Édition du {date_str}</div>
    </div>

    <div class="nav-bar">
      <a href="bulletin_national.html" class="nav-btn {active_nat}"><i class="fa-solid fa-earth-france"></i> 🌊 Bulletin National</a>
      <a href="bulletin_hdf.html" class="nav-btn {active_hdf}"><i class="fa-solid fa-map-location-dot"></i> 🌾 Hauts-de-France</a>
      <a href="bulletin_npdc.html" class="nav-btn {active_npdc}"><i class="fa-solid fa-water"></i> ⚓ Nord-Pas-de-Calais</a>
      <a href="index.html" class="nav-btn"><i class="fa-solid fa-house"></i> Accueil Synthèse</a>
    </div>

    {content}

    <div class="footer">
      <p>Centrale Météo - Données Météo-France, Infoclimat, maree.info & seatemperature.org</p>
    </div>
  </div>
</body>
</html>
"""

def build_national_html(data, md_content):
    date_str = get_french_date()
    tides = data.get("tides", {})
    beaches = data.get("beaches", {})
    forecast14 = data.get("forecast_14d", [])

    brest_tide = tides.get("Brest", {"pm": "06:12 & 18:35", "bm": "00:45 & 13:10", "coeff": "61 / 57"})

    tides_table = f"""
    <table>
      <thead>
        <tr>
          <th>Port Référent</th>
          <th>Pleines Mers (PM) ⬆️</th>
          <th>Basses Mers (BM) ⬇️</th>
          <th>Coefficients 📈</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td>🚢 <strong>Brest (Atlantique)</strong></td>
          <td>{brest_tide['pm']}</td>
          <td>{brest_tide['bm']}</td>
          <td><strong>{brest_tide['coeff']}</strong></td>
        </tr>
      </tbody>
    </table>
    """

    nat_beaches = [
      ("🏖️ Manche / Côte d'Opale", beaches.get("Manche / Côte d'Opale", {})),
      ("🏖️ Bretagne (Nord & Sud)", beaches.get("Bretagne (Nord & Sud)", {})),
      ("🏖️ Atlantique (Vendée à Landes)", beaches.get("Atlantique (Vendée à Landes)", {})),
      ("🏖️ Côte Basque (Biarritz)", beaches.get("Côte Basque (Biarritz)", {})),
      ("🏖️ Méditerranée (Languedoc/PACA)", beaches.get("Méditerranée (Languedoc/PACA)", {})),
      ("🏖️ Corse (Ajaccio / Bastia)", beaches.get("Corse (Ajaccio / Bastia)", {}))
    ]

    beaches_rows = ""
    for name, binfo in nat_beaches:
        water = binfo.get("water", "–")
        flag = binfo.get("flag", "🟢 Vert (Baignade autorisée)")
        uv = binfo.get("uv", "–")
        beaches_rows += f"""
        <tr>
          <td>{name}</td>
          <td><strong>{water}</strong></td>
          <td><span class="badge badge-green">{flag}</span></td>
          <td><strong>{uv}</strong></td>
        </tr>
        """

    beaches_table = f"""
    <table>
      <thead>
        <tr>
          <th>Façade Littorale</th>
          <th>Eau 🌊</th>
          <th>Baignade & Drapeau 🚩</th>
          <th>Indice UV ☀️</th>
        </tr>
      </thead>
      <tbody>
        {beaches_rows}
      </tbody>
    </table>
    """

    forecast_rows = ""
    for item in forecast14:
        forecast_rows += f"""
        <tr>
          <td><strong>{item['day_name']}</strong></td>
          <td>{item['weather']}</td>
          <td>{item['temp']}</td>
          <td>{item['confidence']}</td>
        </tr>
        """

    forecast_table = f"""
    <table>
      <thead>
        <tr>
          <th>Jour</th>
          <th>Temps Sensible 🌤️</th>
          <th>Températures / Tendance 🌡️</th>
          <th>Indice Confiance</th>
        </tr>
      </thead>
      <tbody>
        {forecast_rows}
      </tbody>
    </table>
    """

    rendered_md = md_to_html(md_content)

    content = f"""
    <div class="section">
      <div class="section-title"><i class="fa-solid fa-file-lines"></i> 1. Bulletin Météo National & Expertise</div>
      {rendered_md if rendered_md else '<p>Bulletin en cours de génération...</p>'}
    </div>

    <div class="section">
      <div class="section-title"><i class="fa-solid fa-water"></i> 2. Marées & Météo des Plages Nationales</div>
      <h4 style="margin-top: 10px; color: var(--primary);">Horaires et Coefficients de Marée (Brest)</h4>
      {tides_table}

      <h4 style="margin-top: 20px; color: var(--primary);">Synthèse Météo des Plages & Eau de Mer</h4>
      {beaches_table}
    </div>

    <div class="section">
      <div class="section-title"><i class="fa-solid fa-calendar-days"></i> 3. Tendance à 14 Jours (France)</div>
      {forecast_table}
    </div>
    """

    return HTML_TEMPLATE.format(
        title="Bulletin Météo National Premium",
        icon="🇫🇷",
        date_str=date_str,
        active_nat="active",
        active_hdf="",
        active_npdc="",
        content=content
    )

def build_hdf_html(data, md_content):
    date_str = get_french_date()
    tides = data.get("tides", {})
    beaches = data.get("beaches", {})
    forecast14 = data.get("forecast_14d", [])

    ports_hdf = ["Dunkerque", "Boulogne-sur-Mer", "Saint-Valery-sur-Somme"]
    tides_rows = ""
    for p in ports_hdf:
        tinfo = tides.get(p, {"pm": "–", "bm": "–", "coeff": "–"})
        tides_rows += f"""
        <tr>
          <td>🚢 <strong>{p}</strong></td>
          <td>{tinfo['pm']}</td>
          <td>{tinfo['bm']}</td>
          <td><strong>{tinfo['coeff']}</strong></td>
        </tr>
        """

    tides_table = f"""
    <table>
      <thead>
        <tr>
          <th>Port Référent</th>
          <th>Pleines Mers (PM) ⬆️</th>
          <th>Basses Mers (BM) ⬇️</th>
          <th>Coefficients 📈</th>
        </tr>
      </thead>
      <tbody>
        {tides_rows}
      </tbody>
    </table>
    """

    beaches_hdf_keys = [
        "Malo-les-Bains / Dunkerque",
        "Calais / Sangatte",
        "Wissant / Cap Blanc-Nez",
        "Wimereux / Boulogne",
        "Le Touquet-Paris-Plage",
        "Baie de Somme (Cayeux / Crotoy)"
    ]

    beaches_rows = ""
    for name in beaches_hdf_keys:
        binfo = beaches.get(name, {})
        water = binfo.get("water", "–")
        flag = binfo.get("flag", "🟢 Vert (Baignade autorisée)")
        uv = binfo.get("uv", "–")
        beaches_rows += f"""
        <tr>
          <td>🏖️ {name}</td>
          <td><strong>{water}</strong></td>
          <td><span class="badge badge-green">{flag}</span></td>
          <td><strong>{uv}</strong></td>
        </tr>
        """

    beaches_table = f"""
    <table>
      <thead>
        <tr>
          <th>Station Littorale</th>
          <th>Eau 🌊</th>
          <th>Baignade & Drapeau 🚩</th>
          <th>Indice UV ☀️</th>
        </tr>
      </thead>
      <tbody>
        {beaches_rows}
      </tbody>
    </table>
    """

    forecast_rows = ""
    for item in forecast14:
        forecast_rows += f"""
        <tr>
          <td><strong>{item['day_name']}</strong></td>
          <td>{item['weather']}</td>
          <td>{item['temp']}</td>
          <td>{item['confidence']}</td>
        </tr>
        """

    forecast_table = f"""
    <table>
      <thead>
        <tr>
          <th>Jour</th>
          <th>Temps Sensible 🌤️</th>
          <th>Températures / Tendance 🌡️</th>
          <th>Indice Confiance</th>
        </tr>
      </thead>
      <tbody>
        {forecast_rows}
      </tbody>
    </table>
    """

    rendered_md = md_to_html(md_content)

    content = f"""
    <div class="section">
      <div class="section-title"><i class="fa-solid fa-file-lines"></i> 1. Bulletin Météo Hauts-de-France & Expertise</div>
      {rendered_md if rendered_md else '<p>Bulletin régional en cours de génération...</p>'}
    </div>

    <div class="section">
      <div class="section-title"><i class="fa-solid fa-water"></i> 2. Marées & Météo des Plages Hauts-de-France</div>
      <h4 style="margin-top: 10px; color: var(--primary);">Horaires et Coefficients de Marée</h4>
      {tides_table}

      <h4 style="margin-top: 20px; color: var(--primary);">Tableau Météo des Plages & Eau de Mer</h4>
      {beaches_table}
    </div>

    <div class="section">
      <div class="section-title"><i class="fa-solid fa-calendar-days"></i> 3. Tendance Régionale à 14 Jours</div>
      {forecast_table}
    </div>
    """

    return HTML_TEMPLATE.format(
        title="Bulletin Météo Hauts-de-France",
        icon="🌾",
        date_str=date_str,
        active_nat="",
        active_hdf="active",
        active_npdc="",
        content=content
    )

def build_npdc_html(data, md_content):
    date_str = get_french_date()
    tides = data.get("tides", {})
    beaches = data.get("beaches", {})
    forecast14 = data.get("forecast_14d", [])

    ports_npdc = ["Dunkerque", "Calais", "Boulogne-sur-Mer", "Le Touquet"]
    tides_rows = ""
    for p in ports_npdc:
        tinfo = tides.get(p, {"pm": "–", "bm": "–", "coeff": "–"})
        tides_rows += f"""
        <tr>
          <td>🚢 <strong>{p} (62/59)</strong></td>
          <td>{tinfo['pm']}</td>
          <td>{tinfo['bm']}</td>
          <td><strong>{tinfo['coeff']}</strong></td>
        </tr>
        """

    tides_table = f"""
    <table>
      <thead>
        <tr>
          <th>Port Référent</th>
          <th>Pleines Mers (PM) ⬆️</th>
          <th>Basses Mers (BM) ⬇️</th>
          <th>Coefficients 📈</th>
        </tr>
      </thead>
      <tbody>
        {tides_rows}
      </tbody>
    </table>
    """

    beaches_npdc_keys = [
        "Malo-les-Bains / Dunkerque",
        "Gravelines / Petit-Fort",
        "Calais / Sangatte",
        "Wissant / Cap Blanc-Nez",
        "Wimereux / Boulogne",
        "Hardelot-Plage",
        "Le Touquet-Paris-Plage",
        "Stella / Merlimont / Berck"
    ]

    beaches_rows = ""
    for name in beaches_npdc_keys:
        binfo = beaches.get(name, {})
        water = binfo.get("water", "–")
        flag = binfo.get("flag", "🟢 Vert (Baignade autorisée)")
        uv = binfo.get("uv", "–")
        beaches_rows += f"""
        <tr>
          <td>🏖️ {name}</td>
          <td><strong>{water}</strong></td>
          <td><span class="badge badge-green">{flag}</span></td>
          <td><strong>{uv}</strong></td>
        </tr>
        """

    beaches_table = f"""
    <table>
      <thead>
        <tr>
          <th>Station Littorale (59 & 62)</th>
          <th>Eau 🌊</th>
          <th>Baignade & Drapeau 🚩</th>
          <th>Indice UV ☀️</th>
        </tr>
      </thead>
      <tbody>
        {beaches_rows}
      </tbody>
    </table>
    """

    forecast_rows = ""
    for item in forecast14:
        forecast_rows += f"""
        <tr>
          <td><strong>{item['day_name']}</strong></td>
          <td>{item['weather']}</td>
          <td>{item['temp']}</td>
          <td>{item['confidence']}</td>
        </tr>
        """

    forecast_table = f"""
    <table>
      <thead>
        <tr>
          <th>Jour</th>
          <th>Temps Sensible 🌤️</th>
          <th>Températures / Tendance 🌡️</th>
          <th>Indice Confiance</th>
        </tr>
      </thead>
      <tbody>
        {forecast_rows}
      </tbody>
    </table>
    """

    rendered_md = md_to_html(md_content)

    content = f"""
    <div class="section">
      <div class="section-title"><i class="fa-solid fa-file-lines"></i> 1. Bulletin Météo Nord-Pas-de-Calais & Expertise</div>
      {rendered_md if rendered_md else '<p>Bulletin Nord-Pas-de-Calais en cours de génération...</p>'}
    </div>

    <div class="section">
      <div class="section-title"><i class="fa-solid fa-water"></i> 2. Marées & Météo des Plages Nord-Pas-de-Calais</div>
      <h4 style="margin-top: 10px; color: var(--primary);">Horaires et Coefficients de Marée Côte d'Opale</h4>
      {tides_table}

      <h4 style="margin-top: 20px; color: var(--primary);">Tableau Météo des Plages & Eau de Mer</h4>
      {beaches_table}
    </div>

    <div class="section">
      <div class="section-title"><i class="fa-solid fa-calendar-days"></i> 3. Tendance Nord-Pas-de-Calais à 14 Jours</div>
      {forecast_table}
    </div>
    """

    return HTML_TEMPLATE.format(
        title="Bulletin Météo Nord-Pas-de-Calais",
        icon="⚓",
        date_str=date_str,
        active_nat="",
        active_hdf="",
        active_npdc="active",
        content=content
    )

def main():
    print("Generating HTML weather bulletins...")
    data = load_tides_data()
    md_france = read_file(MD_FRANCE)
    md_hdf = read_file(MD_HDF)

    html_nat = build_national_html(data, md_france)
    html_hdf = build_hdf_html(data, md_hdf)
    html_npdc = build_npdc_html(data, md_hdf)

    out_nat = os.path.join(PUBLIC_DIR, "bulletin_national.html")
    out_hdf = os.path.join(PUBLIC_DIR, "bulletin_hdf.html")
    out_npdc = os.path.join(PUBLIC_DIR, "bulletin_npdc.html")

    with open(out_nat, "w", encoding="utf-8") as f:
        f.write(html_nat)
    with open(out_hdf, "w", encoding="utf-8") as f:
        f.write(html_hdf)
    with open(out_npdc, "w", encoding="utf-8") as f:
        f.write(html_npdc)

    print("HTML bulletins created successfully:")
    print(f" - {out_nat}")
    print(f" - {out_hdf}")
    print(f" - {out_npdc}")

if __name__ == "__main__":
    main()
