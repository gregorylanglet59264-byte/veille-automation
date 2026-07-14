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
from download_data import download_bulletins
from generer_rapport import generer_bulletin_premium, REGIONS

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
    
    # Tentative avec Gemini
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

    # Tentative avec OpenRouter (DeepSeek)
    if openrouter_key:
        print("[LLM] Appel de l'API OpenRouter (DeepSeek)...")
        url = "https://openrouter.ai/api/v1/chat/completions"
        data = {
            "model": "deepseek/deepseek-chat",
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

def md_to_html(md_text):
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
            return (
                f'<div class="info-card">'
                f'<span class="badge-red" style="margin-bottom:12px;">🔥 INFORMATION IMPORTANTE</span>'
                f'<div style="font-size:13.5px; line-height:1.6;">{bq_content}</div>'
                f'</div>'
            )
        elif blockquote_type == "warning":
            return (
                f'<div class="warning-card">'
                f'<span class="badge-orange" style="margin-bottom:12px;">⚠️ ALERTE METEO</span>'
                f'<div style="font-size:13.5px; line-height:1.6;">{bq_content}</div>'
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
    with zipfile.ZipFile(zip_output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
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
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            line-height: 1.6;
            color: #2c3e50;
            background-color: #f4f6f8;
            margin: 0;
            padding: 0;
        }}
        .container {{
            max-width: 720px;
            margin: 30px auto;
            background-color: #ffffff;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
            border: 1px solid #e1e8ed;
        }}
        .header {{
            background: linear-gradient(135deg, #0f172a, #1e293b);
            color: #ffffff;
            padding: 35px 24px;
            text-align: center;
            border-bottom: 3px solid #3b82f6;
        }}
        .header h1 {{
            margin: 0;
            font-size: 22px;
            font-weight: 700;
            letter-spacing: 0.5px;
        }}
        .header p {{
            margin: 8px 0 0 0;
            font-size: 13px;
            opacity: 0.8;
        }}
        .content {{
            padding: 24px;
        }}
        .section-title {{
            color: #1e293b;
            font-size: 16px;
            font-weight: 700;
            border-bottom: 2px solid #f1f5f9;
            padding-bottom: 6px;
            margin-top: 30px;
            margin-bottom: 14px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .badge-red {{
            background-color: #fef2f2;
            color: #991b1b;
            padding: 4px 8px;
            border-radius: 4px;
            font-weight: 700;
            font-size: 12px;
            display: inline-block;
        }}
        .badge-orange {{
            background-color: #fff7ed;
            color: #9a3412;
            padding: 4px 8px;
            border-radius: 4px;
            font-weight: 700;
            font-size: 12px;
            display: inline-block;
        }}
        .badge-yellow {{
            background-color: #fef9c3;
            color: #854d0e;
            padding: 4px 8px;
            border-radius: 4px;
            font-weight: 700;
            font-size: 12px;
            display: inline-block;
        }}
        .vigilance-card {{
            border-radius: 8px;
            padding: 16px;
            margin-bottom: 16px;
            border: 1px solid #e2e8f0;
        }}
        .vigilance-red {{
            background-color: #fef2f2;
            border-left: 5px solid #ef4444;
        }}
        .vigilance-orange {{
            background-color: #fff7ed;
            border-left: 5px solid #f97316;
        }}
        .vigilance-yellow {{
            background-color: #fef9c3;
            border-left: 5px solid #eab308;
        }}
        .badge-dept-red {{
            display: inline-block;
            background-color: #fee2e2;
            color: #991b1b;
            padding: 2px 8px;
            margin: 2px 1px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: 600;
            border: 1px solid #fecaca;
        }}
        .badge-dept-orange {{
            display: inline-block;
            background-color: #ffedd5;
            color: #c2410c;
            padding: 2px 8px;
            margin: 2px 1px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: 600;
            border: 1px solid #fed7aa;
        }}
        .badge-dept-yellow {{
            display: inline-block;
            background-color: #fef9c3;
            color: #854d0e;
            padding: 2px 8px;
            margin: 2px 1px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: 600;
            border: 1px solid #fef08a;
        }}
        .info-card {{
            background-color: #f0fdf4;
            border-left: 5px solid #22c55e;
            border-radius: 8px;
            padding: 16px;
            margin-bottom: 16px;
            border-top: 1px solid #bbf7d0;
            border-right: 1px solid #bbf7d0;
            border-bottom: 1px solid #bbf7d0;
        }}
        .warning-card {{
            background-color: #fffbeb;
            border-left: 5px solid #f59e0b;
            border-radius: 8px;
            padding: 16px;
            margin-bottom: 16px;
            border-top: 1px solid #fef3c7;
            border-right: 1px solid #fef3c7;
            border-bottom: 1px solid #fef3c7;
        }}
        .table-container {{
            margin-bottom: 20px;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 5px rgba(0,0,0,0.02);
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 13.5px;
        }}
        th {{
            background-color: #0f172a;
            color: #ffffff;
            padding: 10px 12px;
            text-align: left;
            font-weight: 700;
            border-bottom: 2px solid #cbd5e1;
        }}
        td {{
            padding: 10px 12px;
            border-bottom: 1px solid #e2e8f0;
            background-color: #ffffff;
        }}
        tr:nth-child(even) td {{
            background-color: #f8fafc;
        }}
        .footer {{
            background-color: #f8fafc;
            padding: 20px;
            text-align: center;
            font-size: 11px;
            color: #64748b;
            border-top: 1px solid #e2e8f0;
        }}
        blockquote {{
            background-color: #f8fafc;
            border-left: 4px solid #cbd5e1;
            padding: 8px 16px;
            margin: 0 0 16px 0;
            font-style: italic;
            color: #475569;
        }}
        p {{
            margin: 0 0 12px 0;
            text-align: justify;
            line-height: 1.5;
            font-size: 14.5px;
        }}
        ul {{
            margin: 0 0 16px 0;
            padding-left: 20px;
        }}
        li {{
            margin-bottom: 6px;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div style="font-size: 11px; font-weight: 800; letter-spacing: 2px; color: #3b82f6; text-transform: uppercase; margin-bottom: 8px;">MONSIEUR MÉTÉO</div>
            <h1>{title_full}</h1>
            <div style="width: 40px; height: 2px; background-color: #3b82f6; margin: 12px auto;"></div>
            <p>Édité le {date_display} à {time_display} • Officiel / Validé pour diffusion publique</p>
        </div>
        <div class="content">
            {html_body}
        </div>
        <div class="footer">
            <p style="text-align:center; font-size:11px; margin:0;">Météo-France Officiel — Synthèse consolidée de diffusion. Tous droits réservés.</p>
        </div>
    </div>
</body>
</html>"""
                
                html_filename = file.replace('.md', '.html')
                if "bulletin_france" in file:
                    zipf.writestr(html_filename, full_html)
                else:
                    zipf.writestr(os.path.join("bulletins_regionaux", html_filename), full_html)

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
        
    national_html = md_to_html(national_md)
    
    now = datetime.datetime.now()
    time_str = now.strftime('%H:%M')
    
    email_body = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>{title_full}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            line-height: 1.6;
            color: #2c3e50;
            background-color: #f4f6f8;
            margin: 0;
            padding: 0;
        }}
        .container {{
            max-width: 720px;
            margin: 30px auto;
            background-color: #ffffff;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
            border: 1px solid #e1e8ed;
        }}
        .header {{
            background: linear-gradient(135deg, #0f172a, #1e293b);
            color: #ffffff;
            padding: 35px 24px;
            text-align: center;
            border-bottom: 3px solid #3b82f6;
        }}
        .header h1 {{
            margin: 0;
            font-size: 22px;
            font-weight: 700;
            letter-spacing: 0.5px;
        }}
        .header p {{
            margin: 8px 0 0 0;
            font-size: 13px;
            opacity: 0.8;
        }}
        .content {{
            padding: 24px;
        }}
        .section-title {{
            color: #1e293b;
            font-size: 16px;
            font-weight: 700;
            border-bottom: 2px solid #f1f5f9;
            padding-bottom: 6px;
            margin-top: 30px;
            margin-bottom: 14px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .badge-red {{
            background-color: #fef2f2;
            color: #991b1b;
            padding: 4px 8px;
            border-radius: 4px;
            font-weight: 700;
            font-size: 12px;
            display: inline-block;
        }}
        .badge-orange {{
            background-color: #fff7ed;
            color: #9a3412;
            padding: 4px 8px;
            border-radius: 4px;
            font-weight: 700;
            font-size: 12px;
            display: inline-block;
        }}
        .badge-yellow {{
            background-color: #fef9c3;
            color: #854d0e;
            padding: 4px 8px;
            border-radius: 4px;
            font-weight: 700;
            font-size: 12px;
            display: inline-block;
        }}
        .vigilance-card {{
            border-radius: 8px;
            padding: 16px;
            margin-bottom: 16px;
            border: 1px solid #e2e8f0;
        }}
        .vigilance-red {{
            background-color: #fef2f2;
            border-left: 5px solid #ef4444;
        }}
        .vigilance-orange {{
            background-color: #fff7ed;
            border-left: 5px solid #f97316;
        }}
        .vigilance-yellow {{
            background-color: #fef9c3;
            border-left: 5px solid #eab308;
        }}
        .badge-dept-red {{
            display: inline-block;
            background-color: #fee2e2;
            color: #991b1b;
            padding: 2px 8px;
            margin: 2px 1px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: 600;
            border: 1px solid #fecaca;
        }}
        .badge-dept-orange {{
            display: inline-block;
            background-color: #ffedd5;
            color: #c2410c;
            padding: 2px 8px;
            margin: 2px 1px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: 600;
            border: 1px solid #fed7aa;
        }}
        .badge-dept-yellow {{
            display: inline-block;
            background-color: #fef9c3;
            color: #854d0e;
            padding: 2px 8px;
            margin: 2px 1px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: 600;
            border: 1px solid #fef08a;
        }}
        .info-card {{
            background-color: #f0fdf4;
            border-left: 5px solid #22c55e;
            border-radius: 8px;
            padding: 16px;
            margin-bottom: 16px;
            border-top: 1px solid #bbf7d0;
            border-right: 1px solid #bbf7d0;
            border-bottom: 1px solid #bbf7d0;
        }}
        .warning-card {{
            background-color: #fffbeb;
            border-left: 5px solid #f59e0b;
            border-radius: 8px;
            padding: 16px;
            margin-bottom: 16px;
            border-top: 1px solid #fef3c7;
            border-right: 1px solid #fef3c7;
            border-bottom: 1px solid #fef3c7;
        }}
        .table-container {{
            margin-bottom: 20px;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 5px rgba(0,0,0,0.02);
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 13.5px;
        }}
        th {{
            background-color: #0f172a;
            color: #ffffff;
            padding: 10px 12px;
            text-align: left;
            font-weight: 700;
            border-bottom: 2px solid #cbd5e1;
        }}
        td {{
            padding: 10px 12px;
            border-bottom: 1px solid #e2e8f0;
            background-color: #ffffff;
        }}
        tr:nth-child(even) td {{
            background-color: #f8fafc;
        }}
        .footer {{
            background-color: #f8fafc;
            padding: 20px;
            text-align: center;
            font-size: 11px;
            color: #64748b;
            border-top: 1px solid #e2e8f0;
        }}
        blockquote {{
            background-color: #f8fafc;
            border-left: 4px solid #cbd5e1;
            padding: 8px 16px;
            margin: 0 0 16px 0;
            font-style: italic;
            color: #475569;
        }}
        p {{
            margin: 0 0 12px 0;
            text-align: justify;
            line-height: 1.5;
            font-size: 14.5px;
        }}
        ul {{
            margin: 0 0 16px 0;
            padding-left: 20px;
        }}
        li {{
            margin-bottom: 6px;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div style="font-size: 11px; font-weight: 800; letter-spacing: 2px; color: #3b82f6; text-transform: uppercase; margin-bottom: 8px;">MONSIEUR MÉTÉO</div>
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
            <p style="text-align:center; font-size:11px; margin:0;">Météo-France Officiel — Synthèse consolidée de diffusion. Tous droits réservés.</p>
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
    
    boundary = uuid.uuid4().hex
    
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

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    meteo_dir = os.path.join(base_dir, "meteo_france")
    source_dir = os.path.join(meteo_dir, "meteo_data")
    
    # 1. Télécharger les bulletins
    print("=== Etape 1 : Telechargement des bulletins XML ===")
    download_bulletins("PREV_XML", source_dir)
    download_bulletins("COTE2", source_dir)
    
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
            
            # Si c'est le bulletin national, on garde le contenu
            if region == "France":
                if os.path.exists(output_file):
                    with open(output_file, 'r', encoding='utf-8') as f:
                        national_content = f.read()
        except Exception as e:
            print(f"[ERREUR] Echec de la generation pour {region} : {e}")
            
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
