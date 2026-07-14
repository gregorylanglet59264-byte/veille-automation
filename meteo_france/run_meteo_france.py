#!/usr/bin/env python3
import os
import sys
import datetime
import urllib.request
import json
import re
import smtplib
import base64
import uuid
import unicodedata
from email.utils import formatdate

# Ajout du répertoire courant pour les imports locaux
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from download_data import download_bulletins, download_isobar_media
from generer_rapport import generer_bulletin_premium, REGIONS, trouver_prev_xml, extraire_label_date, nettoyer_nom_departement


def normalize_name(name):
    n = unicodedata.normalize('NFKD', name).encode('ASCII', 'ignore').decode('ASCII')
    return n.lower().replace(" ", "_").replace("-", "_").replace("'", "_")

def call_llm_summary(bulletin_content):
    """
    Rédige un résumé à l'aide de l'API OpenRouter (DeepSeek) ou de l'API Gemini.
    Si aucune clé n'est configurée, utilise un résumé statique extrait du bulletin.
    """
    gemini_key = os.environ.get("GEMINI_API_KEY")
    openrouter_key = os.environ.get("OPENROUTER_API_KEY")
    
    prompt = (
        "Rédige un résumé très court et impactant en français (sous forme de 4 ou 5 puces clés avec émojis) "
        "du bulletin météo national de la France suivant. Concentre-toi uniquement sur les éléments critiques "
        "(vigilance canicule/orages, températures extrêmes, etc.) :\n\n" + bulletin_content
    )
    
    # Tentative avec OpenRouter (DeepSeek) - Prioritaire
    if openrouter_key:
        print("[LLM] Appel de l'API OpenRouter (DeepSeek)...")
        url = "https://openrouter.ai/api/v1/chat/completions"
        data = {
            "model": "deepseek/deepseek-v4-flash",
            "messages": [{"role": "user", "content": prompt}]
        }
        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(data).encode('utf-8'),
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {openrouter_key}"
                },
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=20) as response:
                res = json.loads(response.read().decode('utf-8'))
                text = res["choices"][0]["message"]["content"]
                return text.replace('\ufeff', '').replace('\ufffe', '').strip()
        except Exception as e:
            print(f"[LLM] Échec appel OpenRouter : {e}")

    # Tentative avec Gemini - Fallback
    if gemini_key:
        print("[LLM] Appel de l'API Gemini...")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_key}"
        data = {
            "contents": [{"parts": [{"text": prompt}]}]
        }
        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(data).encode('utf-8'),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=20) as response:
                res = json.loads(response.read().decode('utf-8'))
                text = res["candidates"][0]["content"]["parts"][0]["text"]
                return text.replace('\ufeff', '').replace('\ufffe', '').strip()
        except Exception as e:
            print(f"[LLM] Échec appel Gemini : {e}")
            
    # Fallback si pas de clés d'API ou si échec des appels
    print("[LLM] Utilisation du fallback d'extraction textuelle...")
    lines = bulletin_content.split('\n')
    summary_parts = []
    capture = False
    for line in lines:
        if "## ⚠️ Vigilance Institutionnelle" in line:
            capture = True
        elif "## 🌊 Vigilance Hydrologique" in line:
            capture = False
        if capture and line.strip() and not line.startswith('#'):
            summary_parts.append(line.strip())
            
    if summary_parts:
        return "### ⚠️ Vigilances actives :\n" + "\n".join(summary_parts[:10])
    return "Consultez le bulletin national en pièce jointe pour plus de détails."

def highlight_figures(text):
    # Met en valeur les chiffres clés : 23 départements, 38 °C, 1032 hPa, 80 km/h, 25 à 30 nœuds...
    regex_units = r'\b(\d+(?:\s*(?:à|ou)\s*\d+)?\s*(?:départements?|hPa|°C|mm|km/h|nœuds))\b'
    return re.sub(
        regex_units,
        r'<strong>\1</strong>',
        text
    )

def split_paragraphs_and_highlight(text):
    text_clean = text.strip()
    if not text_clean:
        return ""
    
    text_highlighted = highlight_figures(text_clean)
    
    # Division à la volée sur les fins de phrases pour éviter tout bloc compact
    sentences = re.split(r'(?<=[.!?])\s+', text_highlighted)
    chunks = []
    current_chunk = []
    
    for s in sentences:
        if s.strip():
            current_chunk.append(s.strip())
            if len(current_chunk) >= 2:
                chunks.append(" ".join(current_chunk))
                current_chunk = []
                
    if current_chunk:
        chunks.append(" ".join(current_chunk))
        
    paragraphs_html = []
    for chunk in chunks:
        paragraphs_html.append(
            f'<p>{chunk}</p>'
        )
    return "\n".join(paragraphs_html)

def md_to_html(md_text, is_email=False):
    escaped = md_text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    
    lines = escaped.splitlines()
    html_lines = []
    
    in_blockquote = False
    blockquote_type = "standard"
    blockquote_lines = []
    
    in_table = False
    table_headers = []
    table_rows = []
    
    in_list = False
    
    active_vigi_card = None  # "red", "orange", "yellow", None
    
    def close_blockquote():
        if not blockquote_lines:
            return ""
        bq_content = "<br>".join(blockquote_lines)
        bq_content = highlight_figures(bq_content)
        bq_content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', bq_content)
        
        if blockquote_type == "important":
            if "orange" in bq_content.lower() or "canicule" in bq_content.lower():
                return (
                    f'<div class="warning-card">'
                    f'<span class="badge-orange" style="margin-bottom:12px;">🔥 INFORMATION IMPORTANTE</span>'
                    f'<div style="font-size:13.5px; line-height:1.6; color:#9a3412;">{bq_content}</div>'
                    f'</div>'
                )
            elif "rouge" in bq_content.lower():
                return (
                    f'<div style="background-color: #fef2f2; border-left: 5px solid #ef4444; border-radius: 8px; padding: 16px; margin-bottom: 16px; border: 1px solid #fecaca;">'
                    f'<span class="badge-red" style="margin-bottom:12px;">🔥 INFORMATION IMPORTANTE</span>'
                    f'<div style="font-size:13.5px; line-height:1.6; color:#991b1b;">{bq_content}</div>'
                    f'</div>'
                )
            else:
                return (
                    f'<div class="info-card">'
                    f'<span style="background-color: #dcfce7; color: #166534; padding: 4px 8px; border-radius: 4px; font-weight: 700; font-size: 12px; display: inline-block; margin-bottom:12px;">🔥 INFORMATION IMPORTANTE</span>'
                    f'<div style="font-size:13.5px; line-height:1.6; color:#166534;">{bq_content}</div>'
                    f'</div>'
                )
        elif blockquote_type == "warning":
            return (
                f'<div class="warning-card">'
                f'<span class="badge-orange" style="margin-bottom:12px;">⚠️ ALERTE METEO</span>'
                f'<div style="font-size:13.5px; line-height:1.6; color:#9a3412;">{bq_content}</div>'
                f'</div>'
            )
        else:
            return f'<blockquote>{bq_content}</blockquote>'

    def render_html_table(headers, rows):
        headers_html = []
        for h in headers:
            h_clean = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', h)
            headers_html.append(f'<th style="padding:10px 12px; font-weight:700; color:#ffffff; border-bottom:2px solid #cbd5e1; text-align:left;">{h_clean}</th>')
            
        rows_html = []
        for i, row in enumerate(rows):
            row_cells = []
            bg_color = "#f8fafc" if i % 2 == 1 else "#ffffff"
            for cell in row:
                cell_hl = highlight_figures(cell)
                cell_clean = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', cell_hl)
                # Formater les indicateurs de vigilance dans la table régionale
                if "🔴" in cell_clean:
                    cell_clean = cell_clean.replace("🔴", '<span style="color:#ef4444;">🔴</span>')
                elif "🟠" in cell_clean:
                    cell_clean = cell_clean.replace("🟠", '<span style="color:#f97316;">🟠</span>')
                elif "🟡" in cell_clean:
                    cell_clean = cell_clean.replace("🟡", '<span style="color:#eab308;">🟡</span>')
                elif "🟢" in cell_clean:
                    cell_clean = cell_clean.replace("🟢", '<span style="color:#22c55e;">🟢</span>')
                    
                row_cells.append(f'<td style="padding:10px 12px; color:#2c3e50; border-bottom:1px solid #e2e8f0; background-color:{bg_color};">{cell_clean}</td>')
            rows_html.append(f'<tr>{"".join(row_cells)}</tr>')
            
        return (
            f'<div class="table-container">'
            f'<table style="width:100%; border-collapse:collapse; font-size:13.5px;">'
            f'<thead><tr style="background-color:#0f172a;">{"".join(headers_html)}</tr></thead>'
            f'<tbody>{"".join(rows_html)}</tbody>'
            f'</table>'
            f'</div>'
        )

    # Ignorer le premier titre H1 du markdown (qui est déjà mis dans le header global)
    first_h1_skipped = False

    for line in lines:
        processed_line = line.strip()
        
        # Ignorer le premier h1
        if processed_line.startswith("#") and not processed_line.startswith("##") and not first_h1_skipped:
            first_h1_skipped = True
            continue
            
        # Parseur de tableaux Markdown
        is_table_row = processed_line.startswith("|") and processed_line.endswith("|")
        if is_table_row:
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            cells = [c.strip() for c in processed_line.split("|")[1:-1]]
            is_separator = all(re.match(r'^[\s:-]+$', cell) for cell in cells) if cells else False
            if is_separator:
                continue
            if not in_table:
                in_table = True
                table_headers = cells
            else:
                table_rows.append(cells)
            continue
        else:
            if in_table:
                html_lines.append(render_html_table(table_headers, table_rows))
                in_table = False
                table_headers = []
                table_rows = []
                
        # Parseur de blockquotes
        if processed_line.startswith("&gt;"):
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            in_blockquote = True
            content = line[4:].strip() if line.startswith("&gt; ") else line[3:].strip()
            if "[!IMPORTANT]" in content:
                blockquote_type = "important"
                content = content.replace("[!IMPORTANT]", "").strip()
            elif "[!WARNING]" in content:
                blockquote_type = "warning"
                content = content.replace("[!WARNING]", "").strip()
            blockquote_lines.append(content)
            continue
        else:
            if in_blockquote:
                html_lines.append(close_blockquote())
                in_blockquote = False
                blockquote_lines = []
                blockquote_type = "standard"
                
        if not processed_line:
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            continue
            
        if processed_line == "---":
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append('<hr style="border:0; border-top:1px solid #e2e8f0; margin:24px 0;">')
            continue
            
        # Parseur des vigilances spécifiques au bulletin national
        if "🔴" in processed_line or "rouge" in processed_line.lower():
            if "vigilance rouge" in processed_line.lower() or "alerte rouge" in processed_line.lower():
                if active_vigi_card:
                    html_lines.append("</div></div>")
                active_vigi_card = "red"
                badge_title = "🔴 ALERTE ROUGE CANICULE"
                html_lines.append(
                    f'<div class="vigilance-card vigilance-red">'
                    f'<span class="badge-red" style="margin-bottom:12px; border: 1px solid #fee2e2;">{badge_title}</span>'
                    f'<div style="margin-top: 4px; line-height: 1.8;">'
                )
                continue
        elif "🟠" in processed_line or "orange" in processed_line.lower():
            if "vigilance orange" in processed_line.lower() or "alerte orange" in processed_line.lower():
                if active_vigi_card:
                    html_lines.append("</div></div>")
                active_vigi_card = "orange"
                badge_title = "🟠 ALERTE ORANGE CANICULE"
                html_lines.append(
                    f'<div class="vigilance-card vigilance-orange">'
                    f'<span class="badge-orange" style="margin-bottom:12px; border: 1px solid #fee2e2;">{badge_title}</span>'
                    f'<div style="margin-top: 4px; line-height: 1.8;">'
                )
                continue
        elif "🟡" in processed_line or "jaune" in processed_line.lower():
            if "vigilance jaune" in processed_line.lower() or "alerte jaune" in processed_line.lower():
                if active_vigi_card:
                    html_lines.append("</div></div>")
                active_vigi_card = "yellow"
                badge_title = "🟡 VIGILANCE JAUNE CANICULE"
                html_lines.append(
                    f'<div class="vigilance-card vigilance-yellow">'
                    f'<span class="badge-yellow" style="margin-bottom:12px; border: 1px solid #fee2e2;">{badge_title}</span>'
                    f'<div style="margin-top: 4px; line-height: 1.8;">'
                )
                continue
                
        # Traitement des départements quand on est dans une vigilance-card
        if active_vigi_card and ("," in processed_line or "(" in processed_line):
            parts = processed_line.split(",")
            dept_badges = []
            for p in parts:
                dept_name = p.replace("**", "").strip()
                if dept_name:
                    dept_badges.append(f'<span class="badge-dept-{active_vigi_card}">{dept_name}</span>')
            html_lines.append("\n".join(dept_badges))
            html_lines.append("</div></div>")
            active_vigi_card = None
            continue
            
        # Titres des cartes principales (Rubriques H2)
        if processed_line.startswith("##") and not processed_line.startswith("###"):
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            title = processed_line[2:].strip()
            title_lower = title.lower()
            if "vigilance institutionnelle" in title_lower:
                title = "⚠️ Vigilance Institutionnelle & Alertes Canicule"
            elif "vigilance hydrologique" in title_lower:
                title = "🌊 Vigilance Hydrologique (Crues BPSPC)"
            elif "frontologie" in title_lower:
                title = "🗺️ Frontologie Générale & Centres de Pression"
            elif "briefing" in title_lower:
                title = "📺 Briefing National pour la Présentation TV"
            elif "altitude" in title_lower or "montagne" in title_lower:
                title = "⛰️ Paramètres d'Altitude & Montagne"
            elif "marine" in title_lower or "navigation" in title_lower:
                title = "🌊 Bulletin de Navigation Marine & Côtière"
                
            html_lines.append(f'<div class="section-title">{title}</div>')
            continue
            
        # Sous-titres (H3 et H4)
        if processed_line.startswith("###") or processed_line.startswith("####"):
            if in_list:
                html_lines.append("</ul>")
                in_list = False
                
            if processed_line.startswith("####"):
                title = processed_line[4:].strip()
            else:
                title = processed_line[3:].strip()
                
            if title.startswith("📍"):
                html_lines.append(f'<h3 style="margin-top:24px; margin-bottom:12px; color:#1e293b; border-bottom:1px solid #e2e8f0; padding-bottom:4px;">{title}</h3>')
            elif title.startswith("📅"):
                html_lines.append(f'<h4 style="margin-top:16px; margin-bottom:8px; color:#334155; font-size:14.5px;">{title}</h4>')
            else:
                html_lines.append(f'<h3 style="margin-top:20px; margin-bottom:10px; color:#1e293b;">{title}</h3>')
            continue
            
        # Listes à puces
        if processed_line.startswith("- "):
            item = processed_line[2:].strip()
            item_hl = highlight_figures(item)
            item_clean = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', item_hl)
            
            if not in_list:
                html_lines.append("<ul>")
                in_list = True
            html_lines.append(f"<li>{item_clean}</li>")
            continue
        else:
            if in_list:
                html_lines.append("</ul>")
                in_list = False
                
        # Convertir les images Markdown ![alt](src) en HTML
        if "![" in processed_line:
            img_match = re.search(r'!\[(.*?)\]\((.*?)\)', processed_line)
            if img_match:
                alt = img_match.group(1)
                src = img_match.group(2)
                img_src = "cid:frontology_map" if is_email else os.path.basename(src)
                img_tag = (
                    f'<div style="text-align:center; margin: 25px 0;">'
                    f'<img src="{img_src}" alt="{alt}" style="max-width:100%; border-radius:12px; border: 1px solid rgba(255,255,255,0.15); box-shadow:0 8px 24px rgba(0,0,0,0.3);">'
                    f'<div style="font-size:12px; color:#9ca3af; font-style:italic; margin-top:8px;">{alt}</div>'
                    f'</div>'
                )
                processed_line = re.sub(r'!\[.*?\]\(.*?\)', img_tag, processed_line)
                html_lines.append(processed_line)
                continue
                
        # Paragraphes normaux
        p_hl = highlight_figures(processed_line)
        p_clean = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', p_hl)
        
        # Conserver les courtes lignes de métadonnées sans division
        if len(p_clean) < 120 or p_clean.startswith("*") or ":" in p_clean[:25]:
            html_lines.append(f'<p>{p_clean}</p>')
        else:
            html_lines.append(split_paragraphs_and_highlight(p_clean))
            
    if in_table:
        html_lines.append(render_html_table(table_headers, table_rows))
    if in_blockquote:
        html_lines.append(close_blockquote())
    if in_list:
        html_lines.append("</ul>")
    if active_vigi_card:
        html_lines.append("</div></div>")
        
    return "\n".join(html_lines)

import zipfile

def create_zip_archive(today_str, rapports_dir, zip_output_path):
    img_to_add = None
    meteo_dir = os.path.dirname(os.path.abspath(rapports_dir.rstrip('/\\')))
    source_dir = os.path.join(meteo_dir, "meteo_data")
    media_dir = os.path.join(source_dir, "MEDIA")
    if os.path.exists(media_dir):
        import glob
        matches = glob.glob(os.path.join(media_dir, "C_PREISO24_*.jpeg"))
        if matches:
            img_to_add = sorted(matches)[-1]
            
    with zipfile.ZipFile(zip_output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        if img_to_add:
            img_name = os.path.basename(img_to_add)
            zipf.write(img_to_add, img_name)
            zipf.write(img_to_add, os.path.join("national", img_name))
            zipf.write(img_to_add, os.path.join("regions", img_name))
            zipf.write(img_to_add, os.path.join("departements", img_name))
            
        for file in os.listdir(rapports_dir):
            if file.endswith('.md'):
                file_path = os.path.join(rapports_dir, file)
                with open(file_path, 'r', encoding='utf-8') as f:
                    md_content = f.read()
                
                # Récupérer le titre H1 exact depuis le markdown
                lines = md_content.splitlines()
                title_full = "Bulletin Météo Premium"
                if lines and lines[0].startswith("#"):
                    title_full = lines[0][1:].strip()
                
                html_body = md_to_html(md_content)
                
                now = datetime.datetime.now()
                date_display = now.strftime('%d/%m/%Y')
                time_display = now.strftime('%H:%M')
                
                # Document HTML complet autonome et premium (exactement identique à la maquette du bureau)
                full_html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>{title_full}</title>
    <style>
        :root {
            --primary: #2563eb;
            --primary-dark: #1d4ed8;
            --bg-body: #f8fafc;
            --bg-card: #ffffff;
            --text-main: #1e293b;
            --text-muted: #64748b;
            --border: #e2e8f0;
            
            --vigi-orange-bg: #fff7ed;
            --vigi-orange-border: #f97316;
            --vigi-orange-text: #9a3412;
            
            --vigi-yellow-bg: #fefce8;
            --vigi-yellow-border: #eab308;
            --vigi-yellow-text: #854d0e;
            
            --vigi-red-bg: #fef2f2;
            --vigi-red-border: #ef4444;
            --vigi-red-text: #991b1b;
        }
        
        body {
            font-family: 'Outfit', 'Segoe UI', system-ui, -apple-system, sans-serif;
            background-color: var(--bg-body);
            color: var(--text-main);
            line-height: 1.6;
            margin: 0;
            padding: 30px 15px;
        }
        
        .container {
            max-width: 800px;
            margin: 0 auto;
            background-color: var(--bg-card);
            border-radius: 16px;
            box-shadow: 0 10px 25px rgba(15, 23, 42, 0.05);
            border: 1px solid var(--border);
            overflow: hidden;
        }
        
        .header {
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
            color: #ffffff;
            padding: 35px 24px;
            text-align: center;
            border-bottom: 4px solid var(--primary);
            position: relative;
        }
        
        .header h1 {
            margin: 0;
            font-size: 22px;
            font-weight: 700;
            letter-spacing: -0.5px;
        }
        
        .header p {
            margin-top: 8px;
            font-size: 13px;
            color: #94a3b8;
        }
        
        .content {
            padding: 24px;
        }
        
        .section-title {
            color: #0f172a;
            font-size: 16px;
            font-weight: 700;
            border-bottom: 2px solid var(--border);
            padding-bottom: 8px;
            margin-top: 30px;
            margin-bottom: 16px;
            letter-spacing: -0.3px;
        }
        
        .subsection-title {
            color: #1e293b;
            font-size: 14px;
            font-weight: 700;
            margin-top: 20px;
            margin-bottom: 10px;
        }
        
        p {
            margin-top: 0;
            margin-bottom: 14px;
            color: #334155;
            font-size: 14.5px;
            text-align: justify;
        }
        
        ul {
            margin-top: 0;
            margin-bottom: 16px;
            padding-left: 20px;
        }
        
        li {
            margin-bottom: 6px;
            color: #334155;
            font-size: 14.5px;
        }
        
        /* Callouts / Alert boxes */
        .callout {
            display: flex;
            gap: 12px;
            padding: 14px;
            border-radius: 10px;
            margin-bottom: 20px;
            border: 1px solid transparent;
        }
        
        .callout-icon {
            font-size: 18px;
            line-height: 1;
        }
        
        .callout-body {
            font-size: 13.5px;
            font-weight: 500;
        }
        
        .callout-important {
            background-color: var(--vigi-orange-bg);
            border-color: var(--vigi-orange-border);
            color: var(--vigi-orange-text);
        }
        
        .callout-warning {
            background-color: var(--vigi-yellow-bg);
            border-color: var(--vigi-yellow-border);
            color: var(--vigi-yellow-text);
        }
        
        .callout-note {
            background-color: #f1f5f9;
            border-color: var(--border);
            color: #334155;
        }
        
        /* Tables */
        .table-container {
            overflow-x: auto;
            margin-bottom: 20px;
            border-radius: 8px;
            border: 1px solid var(--border);
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            text-align: left;
        }
        
        th {
            background-color: #f8fafc;
            color: #0f172a;
            font-weight: 600;
            font-size: 12.5px;
            padding: 10px 14px;
            border-bottom: 1px solid var(--border);
        }
        
        td {
            padding: 10px 14px;
            font-size: 13.5px;
            border-bottom: 1px solid var(--border);
            color: #334155;
            background-color: #ffffff;
        }
        
        tr:nth-child(even) td {
            background-color: #f8fafc;
        }
        
        tr:last-child td {
            border-bottom: none;
        }
        
        strong {
            color: #0f172a;
        }
        
        hr {
            border: 0;
            height: 1px;
            background-color: var(--border);
            margin: 30px 0;
        }
        
        .footer {
            background-color: #f8fafc;
            padding: 20px;
            border-top: 1px solid var(--border);
            text-align: center;
            font-size: 11px;
            color: var(--text-muted);
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{title_full}</h1>
            <div style="width: 40px; height: 2px; background-color: #3b82f6; margin: 12px auto;"></div>
            <p>Édité le {date_display} à {time_display} • Officiel / Validé pour diffusion publique</p>
        </div>
        <div class="content">
            {html_body}
        </div>
        <div class="footer">
            <p style="text-align:center; font-size:11px; margin:0;">Synthèse consolidée de diffusion. Tous droits réservés.</p>
        </div>
    </div>
</body>
</html>"""
                
                html_filename = file.replace('.md', '.html')
                if "bulletin_france" in file:
                    zipf.writestr(os.path.join("national", html_filename), full_html)
                elif "bulletin_dept_" in file:
                    zipf.writestr(os.path.join("departements", html_filename), full_html)
                else:
                    zipf.writestr(os.path.join("regions", html_filename), full_html)

def send_email_with_summary(national_md, date_str, zip_path):
    gmail_email = os.environ.get("GMAIL_EMAIL", "langlet.gregory@gmail.com")
    gmail_password = os.environ.get("GMAIL_APP_PASSWORD")
    if not gmail_password:
        print("[SMTP] ERREUR : GMAIL_APP_PASSWORD non configuré. Annulation envoi.")
        return
        
    gmail_email = gmail_email.replace('\ufeff', '').replace('\ufffe', '').strip()
    gmail_password = gmail_password.replace('\ufeff', '').replace('\ufffe', '').strip()
    
    raw_recipients = os.environ.get("RECIPIENT_EMAILS", gmail_email)
    recipients = [r.strip() for r in raw_recipients.split(",") if r.strip()]
    
    subject = f"Meteo France - Bulletin National & Regional du {date_str}"
    clean_subject = unicodedata.normalize('NFKD', subject).encode('ASCII', 'ignore').decode('ASCII')
    
    # Récupérer le titre H1 exact depuis le markdown
    lines = national_md.splitlines()
    title_full = "Bulletin Météo Premium — Région France"
    if lines and lines[0].startswith("#"):
        title_full = lines[0][1:].strip()
        
    national_html = md_to_html(national_md, is_email=True)
    
    now = datetime.datetime.now()
    time_str = now.strftime('%H:%M')
    
    email_body = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>{title_full}</title>
    <style>
        :root {{
            --primary: #2563eb;
            --primary-dark: #1d4ed8;
            --bg-body: #f8fafc;
            --bg-card: #ffffff;
            --text-main: #1e293b;
            --text-muted: #64748b;
            --border: #e2e8f0;
            
            --vigi-orange-bg: #fff7ed;
            --vigi-orange-border: #f97316;
            --vigi-orange-text: #9a3412;
            
            --vigi-yellow-bg: #fefce8;
            --vigi-yellow-border: #eab308;
            --vigi-yellow-text: #854d0e;
            
            --vigi-red-bg: #fef2f2;
            --vigi-red-border: #ef4444;
            --vigi-red-text: #991b1b;
        }}
        
        body {{
            font-family: 'Outfit', 'Segoe UI', system-ui, -apple-system, sans-serif;
            background-color: var(--bg-body);
            color: var(--text-main);
            line-height: 1.6;
            margin: 0;
            padding: 30px 15px;
        }}
        
        .container {{
            max-width: 800px;
            margin: 0 auto;
            background-color: var(--bg-card);
            border-radius: 16px;
            box-shadow: 0 10px 25px rgba(15, 23, 42, 0.05);
            border: 1px solid var(--border);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
            color: #ffffff;
            padding: 35px 24px;
            text-align: center;
            border-bottom: 4px solid var(--primary);
            position: relative;
        }}
        
        .header h1 {{
            margin: 0;
            font-size: 22px;
            font-weight: 700;
            letter-spacing: -0.5px;
        }}
        
        .header p {{
            margin-top: 8px;
            font-size: 13px;
            color: #94a3b8;
        }}
        
        .content {{
            padding: 24px;
        }}
        
        .section-title {{
            color: #0f172a;
            font-size: 16px;
            font-weight: 700;
            border-bottom: 2px solid var(--border);
            padding-bottom: 8px;
            margin-top: 30px;
            margin-bottom: 16px;
            letter-spacing: -0.3px;
        }}
        
        .subsection-title {{
            color: #1e293b;
            font-size: 14px;
            font-weight: 700;
            margin-top: 20px;
            margin-bottom: 10px;
        }}
        
        p {{
            margin-top: 0;
            margin-bottom: 14px;
            color: #334155;
            font-size: 14.5px;
            text-align: justify;
        }}
        
        ul {{
            margin-top: 0;
            margin-bottom: 16px;
            padding-left: 20px;
        }}
        
        li {{
            margin-bottom: 6px;
            color: #334155;
            font-size: 14.5px;
        }}
        
        /* Callouts / Alert boxes */
        .callout {{
            display: flex;
            gap: 12px;
            padding: 14px;
            border-radius: 10px;
            margin-bottom: 20px;
            border: 1px solid transparent;
        }}
        
        .callout-icon {{
            font-size: 18px;
            line-height: 1;
        }}
        
        .callout-body {{
            font-size: 13.5px;
            font-weight: 500;
        }}
        
        .callout-important {{
            background-color: var(--vigi-orange-bg);
            border-color: var(--vigi-orange-border);
            color: var(--vigi-orange-text);
        }}
        
        .callout-warning {{
            background-color: var(--vigi-yellow-bg);
            border-color: var(--vigi-yellow-border);
            color: var(--vigi-yellow-text);
        }}
        
        .callout-note {{
            background-color: #f1f5f9;
            border-color: var(--border);
            color: #334155;
        }}
        
        /* Tables */
        .table-container {{
            overflow-x: auto;
            margin-bottom: 20px;
            border-radius: 8px;
            border: 1px solid var(--border);
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            text-align: left;
        }}
        
        th {{
            background-color: #f8fafc;
            color: #0f172a;
            font-weight: 600;
            font-size: 12.5px;
            padding: 10px 14px;
            border-bottom: 1px solid var(--border);
        }}
        
        td {{
            padding: 10px 14px;
            font-size: 13.5px;
            border-bottom: 1px solid var(--border);
            color: #334155;
            background-color: #ffffff;
        }}
        
        tr:nth-child(even) td {{
            background-color: #f8fafc;
        }}
        
        tr:last-child td {{
            border-bottom: none;
        }}
        
        strong {{
            color: #0f172a;
        }}
        
        hr {{
            border: 0;
            height: 1px;
            background-color: var(--border);
            margin: 30px 0;
        }}
        
        .footer {{
            background-color: #f8fafc;
            padding: 20px;
            border-top: 1px solid var(--border);
            text-align: center;
            font-size: 11px;
            color: var(--text-muted);
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{title_full}</h1>
            <div style="width: 40px; height: 2px; background-color: #3b82f6; margin: 12px auto;"></div>
            <p>Édité le {date_str} à {time_str} • Officiel / Validé pour diffusion publique</p>
        </div>
        <div class="content">
            {national_html}
            
            <hr style="border:0; border-top:1px solid #e2e8f0; margin:24px 0;">
            
            <div class="warning-card">
                <span class="badge-orange" style="margin-bottom:12px;">📦 Pieces Jointes (Dossiers)</span>
                <div style="font-size:13.5px; line-height:1.6; color:#2c3e50;">
                    Tous vos bulletins météo Premium (les 13 bulletins régionaux ainsi que le bulletin national) sont archivés et classés dans des dossiers à l'intérieur de l'archive ZIP ci-jointe :<br>
                    📂 <strong>bulletins_meteo_france_{date_str.replace('/', '_')}.zip</strong>
                </div>
            </div>
        </div>
        <div class="footer">
            <p style="text-align:center; font-size:11px; margin:0;">Synthèse consolidée de diffusion. Tous droits réservés.</p>
        </div>
    </div>
</body>
</html>"""
    
    # Nettoyage BOM
    email_body = email_body.replace('\ufeff', '').replace('\ufffe', '')
    
    # Encodage Base64 du corps
    html_b64 = base64.b64encode(email_body.encode('utf-8')).decode('ascii')
    
    # Encodage Base64 de l'archive ZIP
    zip_filename = f"bulletins_meteo_france_{date_str.replace('/', '_')}.zip"
    with open(zip_path, 'rb') as f:
        zip_data = f.read()
    zip_b64 = base64.b64encode(zip_data).decode('ascii')
    
    # Trouver et encoder l'image de frontologie pour intégration inline (cid)
    meteo_dir = os.path.dirname(os.path.abspath(zip_path))
    source_dir = os.path.join(os.path.dirname(meteo_dir), "meteo_data")
    media_dir = os.path.join(source_dir, "MEDIA")
    img_to_attach = None
    img_b64 = None
    if os.path.exists(media_dir):
        import glob
        matches = glob.glob(os.path.join(media_dir, "C_PREISO24_*.jpeg"))
        if matches:
            img_to_attach = sorted(matches)[-1]
            try:
                with open(img_to_attach, 'rb') as img_f:
                    img_data = img_f.read()
                img_b64 = base64.b64encode(img_data).decode('ascii')
            except Exception as e:
                print(f"[SMTP] Impossible de lire la carte de frontologie : {e}")
    
    boundary = uuid.uuid4().hex
    
    # Message de base (HTML)
    raw_message = (
        f'From: Gregory LANGLET <{gmail_email}>\r\n'
        f'To: {", ".join(recipients)}\r\n'
        f'Subject: {clean_subject}\r\n'
        f'Date: {formatdate(localtime=True)}\r\n'
        f'MIME-Version: 1.0\r\n'
        f'Content-Type: multipart/mixed; boundary="{boundary}"\r\n'
        f'\r\n'
        f'--{boundary}\r\n'
        f'Content-Type: text/html; charset=utf-8\r\n'
        f'Content-Transfer-Encoding: base64\r\n'
        f'\r\n'
        f'{html_b64}\r\n'
        f'\r\n'
    )
    
    # Ajout de l'image de frontologie si disponible (inline)
    if img_b64 and img_to_attach:
        img_name = os.path.basename(img_to_attach)
        raw_message += (
            f'--{boundary}\r\n'
            f'Content-Type: image/jpeg; name="{img_name}"\r\n'
            f'Content-Disposition: inline; filename="{img_name}"\r\n'
            f'Content-ID: <frontology_map>\r\n'
            f'Content-Transfer-Encoding: base64\r\n'
            f'\r\n'
            f'{img_b64}\r\n'
            f'\r\n'
        )
        
    # Ajout du fichier ZIP attaché
    raw_message += (
        f'--{boundary}\r\n'
        f'Content-Type: application/zip; name="{zip_filename}"\r\n'
        f'Content-Disposition: attachment; filename="{zip_filename}"\r\n'
        f'Content-Transfer-Encoding: base64\r\n'
        f'\r\n'
        f'{zip_b64}\r\n'
        f'\r\n'
        f'--{boundary}--\r\n'
    )
    
    print(f"[SMTP] Envoi de l'e-mail a {', '.join(recipients)}...")
    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(gmail_email, gmail_password)
            server.sendmail(gmail_email, recipients, raw_message.encode('ascii'))
        print("[SMTP] E-mail envoye avec succes !")
    except Exception as e:
        print(f"[SMTP] Erreur lors de l'envoi de l'e-mail : {e}")

def rewrite_markdown_with_llm(file_path, region):
    import time
    time.sleep(0.5) # Petit délai pour éviter le rate-limiting lors de traitements en boucle
    gemini_key = os.environ.get("GEMINI_API_KEY")
    openrouter_key = os.environ.get("OPENROUTER_API_KEY")
    
    if not gemini_key and not openrouter_key:
        print(f"[LLM] Aucune clé API (GEMINI_API_KEY/OPENROUTER_API_KEY) configurée. Pas de réécriture LLM pour {region}.")
        return
        
    if not os.path.exists(file_path):
        return
        
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    prompt = (
        "peux tu me refaire un résumé des prévisions à partir du texte envoyé, un résumé détaillé de la première journée  et de la nuit suivante, mais en liant parfaitement toutes les parties. et ensuite un tableau qui résume la prévision des jours suivants a partir du lendemain .Enfin une meteo marine classique avec des conseils , et enfin les horaires et coefficients de marée et une météo des plages.\n\n"
        f"Texte envoyé :\n\n{content}"
    )
    
    # Tentative avec OpenRouter (DeepSeek) - Prioritaire
    if openrouter_key:
        print(f"[LLM] Réécriture de {region} via OpenRouter (DeepSeek)...")
        url = "https://openrouter.ai/api/v1/chat/completions"
        data = {
            "model": "deepseek/deepseek-v4-flash",
            "messages": [{"role": "user", "content": prompt}]
        }
        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(data).encode('utf-8'),
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {openrouter_key}"
                },
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=30) as response:
                res = json.loads(response.read().decode('utf-8'))
                rewritten = res["choices"][0]["message"]["content"]
                if rewritten.startswith("```markdown"):
                    rewritten = rewritten[11:]
                elif rewritten.startswith("```"):
                    rewritten = rewritten[3:]
                if rewritten.endswith("```"):
                    rewritten = rewritten[:-3]
                rewritten = rewritten.strip()
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(rewritten)
                print(f"[LLM] Réécriture de {region} réussie avec OpenRouter !")
                return
        except Exception as e:
            print(f"[LLM] Échec réécriture OpenRouter pour {region} : {e}")

    # Tentative avec Gemini - Fallback
    if gemini_key:
        print(f"[LLM] Réécriture de {region} via Gemini...")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_key}"
        data = {
            "contents": [{"parts": [{"text": prompt}]}]
        }
        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(data).encode('utf-8'),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=30) as response:
                res = json.loads(response.read().decode('utf-8'))
                rewritten = res["candidates"][0]["content"]["parts"][0]["text"]
                # Nettoyage si le modèle a entouré le résultat de ```markdown ... ```
                if rewritten.startswith("```markdown"):
                    rewritten = rewritten[11:]
                elif rewritten.startswith("```"):
                    rewritten = rewritten[3:]
                if rewritten.endswith("```"):
                    rewritten = rewritten[:-3]
                rewritten = rewritten.strip()
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(rewritten)
                print(f"[LLM] Réécriture de {region} réussie avec Gemini !")
                return
        except Exception as e:
            print(f"[LLM] Échec réécriture Gemini pour {region} : {e}")

def generer_bulletin_departement(dept_code, dossier_source, fichier_sortie):
    root = trouver_prev_xml(dossier_source, dept_code)
    if root is None:
        raise FileNotFoundError(f"Fichier de prévisions introuvable pour le département {dept_code}")
        
    nom_raw = root.attrib.get('nom', f"Département {dept_code}").split(' - ')[0].split(' : ')[0]
    nom_dept = nettoyer_nom_departement(nom_raw)
    date_prod = root.attrib.get('date_heure_production', 'N/A')
    
    md = f"# 🌊 Bulletin Météo Premium — Département {nom_dept} ({dept_code})\n\n"
    md += f"**Généré le :** {datetime.datetime.now().strftime('%d/%m/%Y à %H:%M')}\n"
    md += f"**Statut du rapport :** Officiel / Validé pour diffusion publique\n\n"
    md += "---\n\n"
    
    # Vigilance
    vigi = root.find('vigilance')
    vigi_txt = vigi.text.strip() if vigi is not None and vigi.text else "Verte"
    md += "## ⚠️ Vigilance Institutionnelle\n"
    md += f"Le département {nom_dept} ({dept_code}) est actuellement en **Vigilance {vigi_txt}**.\n\n"
    
    # Observations
    obs = root.find('observation')
    obs_txt = obs.text.strip() if obs is not None and obs.text else ""
    if obs_txt:
        md += "## 👀 Relevés et Observations Récentes\n"
        md += f"{obs_txt}\n\n"
        
    # Prévisions
    md += "## 📅 Prévisions Détaillées\n\n"
    for groupe in root.findall('groupe'):
        label_date = extraire_label_date(groupe)
        titre = groupe.find('titre')
        temps = groupe.find('temps')
        
        titre_txt = titre.text.strip() if titre is not None and titre.text else ""
        temps_txt = temps.text.strip() if temps is not None and temps.text else ""
        
        md += f"### {label_date}\n"
        if titre_txt:
            md += f"**Tendance :** {titre_txt}\n\n"
        if temps_txt:
            md += f"{temps_txt}\n\n"
            
    with open(fichier_sortie, 'w', encoding='utf-8') as f:
        f.write(md)

def generer_bulletin_nord_pas_de_calais(dossier_source, fichier_sortie):
    root59 = trouver_prev_xml(dossier_source, "59")
    root62 = trouver_prev_xml(dossier_source, "62")
    
    if root59 is None or root62 is None:
        raise FileNotFoundError("Fichiers XML manquants pour le Nord (59) ou le Pas-de-Calais (62)")
        
    date_prod = root59.attrib.get('date_heure_production', 'N/A')
    
    md = f"# 🌊 Bulletin Météo Premium — Nord-Pas-de-Calais (59 / 62)\n\n"
    md += f"**Généré le :** {datetime.datetime.now().strftime('%d/%m/%Y à %H:%M')}\n"
    md += f"**Statut du rapport :** Officiel / Validé pour diffusion publique\n\n"
    md += "---\n\n"
    
    # Vigilance Nord
    vigi59 = root59.find('vigilance')
    vigi59_txt = vigi59.text.strip() if vigi59 is not None and vigi59.text else "Verte"
    
    # Vigilance Pas-de-Calais
    vigi62 = root62.find('vigilance')
    vigi62_txt = vigi62.text.strip() if vigi62 is not None and vigi62.text else "Verte"
    
    md += "## ⚠️ Vigilance Institutionnelle\n"
    md += f"- **Nord (59) :** Vigilance {vigi59_txt}\n"
    md += f"- **Pas-de-Calais (62) :** Vigilance {vigi62_txt}\n\n"
    
    # Observations
    obs59 = root59.find('observation')
    obs59_txt = obs59.text.strip() if obs59 is not None and obs59.text else ""
    obs62 = root62.find('observation')
    obs62_txt = obs62.text.strip() if obs62 is not None and obs62.text else ""
    
    if obs59_txt or obs62_txt:
        md += "## 👀 Relevés et Observations Récentes\n"
        if obs59_txt:
            md += f"- **Nord (59) :** {obs59_txt}\n"
        if obs62_txt:
            md += f"- **Pas-de-Calais (62) :** {obs62_txt}\n"
        md += "\n"
        
    # Prévisions
    md += "## 📅 Prévisions Détaillées\n\n"
    
    groupes59 = root59.findall('groupe')
    groupes62 = root62.findall('groupe')
    
    for i in range(min(len(groupes59), len(groupes62))):
        g59 = groupes59[i]
        g62 = groupes62[i]
        
        label_date = extraire_label_date(g59)
        
        t59 = g59.find('titre')
        temp59 = g59.find('temps')
        t59_txt = t59.text.strip() if t59 is not None and t59.text else ""
        temp59_txt = temp59.text.strip() if temp59 is not None and temp59.text else ""
        
        t62 = g62.find('titre')
        temp62 = g62.find('temps')
        t62_txt = t62.text.strip() if t62 is not None and t62.text else ""
        temp62_txt = temp62.text.strip() if temp62 is not None and temp62.text else ""
        
        md += f"### {label_date}\n"
        md += f"**Pour le Nord (59) :**\n"
        if t59_txt:
            md += f"- *Tendance :* {t59_txt}\n"
        if temp59_txt:
            md += f"- {temp59_txt}\n"
            
        md += f"\n**Pour le Pas-de-Calais (62) :**\n"
        if t62_txt:
            md += f"- *Tendance :* {t62_txt}\n"
        if temp62_txt:
            md += f"- {temp62_txt}\n"
        md += "\n"
        
    with open(fichier_sortie, 'w', encoding='utf-8') as f:
        f.write(md)

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    meteo_dir = os.path.join(base_dir, "meteo_france")
    source_dir = os.path.join(meteo_dir, "meteo_data")
    
    # 1. Télécharger les bulletins
    print("=== Etape 1 : Telechargement des bulletins XML ===")
    download_bulletins("PREV_XML", source_dir)
    download_bulletins("COTE2", source_dir)
    download_isobar_media(source_dir)
    
    # 2. Définir le dossier de sortie
    today_str = datetime.datetime.now().strftime("%Y-%m-%d")
    date_display = datetime.datetime.now().strftime("%d/%m/%Y")
    rapports_dir = os.path.join(meteo_dir, "rapports", today_str)
    os.makedirs(rapports_dir, exist_ok=True)
    
    # 3. Générer les bulletins pour toutes les régions
    print("\n=== Etape 2 : Generation des bulletins regionaux ===")
    national_content = ""
    
    for region in REGIONS.keys():
        region_norm = normalize_name(region)
        filename = f"bulletin_{region_norm}_{today_str}.md"
        output_file = os.path.join(rapports_dir, filename)
        
        print(f"Generation pour {region} -> {filename}")
        try:
            generer_bulletin_premium(region, source_dir, output_file)
            
            # Réécriture par LLM si clé API présente
            rewrite_markdown_with_llm(output_file, region)
            
            # Si c'est le bulletin national, on garde le contenu
            if region == "France":
                if os.path.exists(output_file):
                    with open(output_file, 'r', encoding='utf-8') as f:
                        national_content = f.read()
        except Exception as e:
            print(f"[ERREUR] Echec de la generation pour {region} : {e}")
            
    # Les bulletins départementaux individuels ont été retirés pour accélérer le traitement (ponytail)

    # 3.7. Générer le bulletin combiné Nord-Pas-de-Calais
    print("\n=== Etape 2ter : Generation du bulletin combine Nord-Pas-de-Calais ===")
    filename_npc = f"bulletin_nord_pas_de_calais_{today_str}.md"
    output_npc = os.path.join(rapports_dir, filename_npc)
    print(f"Generation pour Nord-Pas-de-Calais -> {filename_npc}")
    try:
        generer_bulletin_nord_pas_de_calais(source_dir, output_npc)
        rewrite_markdown_with_llm(output_npc, "Nord-Pas-de-Calais")
    except Exception as e:
        print(f"[ERREUR] Echec de la generation pour Nord-Pas-de-Calais : {e}")
            
    # 4. Créer l'archive ZIP
    print("\n=== Etape 3 : Creation de l'archive ZIP ===")
    zip_path = os.path.join(meteo_dir, "rapports", f"bulletins_{today_str}.zip")
    create_zip_archive(today_str, rapports_dir, zip_path)
    print(f"Archive ZIP creee avec succes dans : {zip_path}")
    
    # 5. Envoyer l'email avec le bulletin national en corps de mail et le ZIP attaché
    print("\n=== Etape 4 : Envoi de l'e-mail ===")
    if national_content:
        send_email_with_summary(national_content, date_display, zip_path)
    else:
        print("[ERREUR] Impossible d'envoyer l'e-mail: contenu national vide.")

if __name__ == "__main__":
    main()