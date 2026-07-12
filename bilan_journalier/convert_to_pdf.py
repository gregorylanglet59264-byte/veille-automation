# -*- coding: utf-8 -*-
"""
convert_to_pdf.py
═══════════════════════════════════════════════════════════════════════════════
Convertit un rapport Markdown en HTML puis l'imprime en PDF de haute qualité
en utilisant Google Chrome installé en mode headless (sans interface).
═══════════════════════════════════════════════════════════════════════════════
"""

import os, subprocess, re

def md_to_html(md_path, html_path, title="Rapport"):
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Nettoyage des blocs d'intégration NotebookLM (prompts de secours) pour ne garder que l'article propre
    content = content.split("### 📝 Prompts de secours")[0]

    # Convertir sommairement le Markdown en HTML (titres, listes, gras, alertes)
    # Titres
    html = re.sub(r'^# (.*?)$', r'<h1>\1</h1>', content, flags=re.MULTILINE)
    html = re.sub(r'^## (.*?)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
    html = re.sub(r'^### (.*?)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
    
    # Blocs d'alertes IMPORTANT/WARNING/CAUTION
    # Motif: > [!IMPORTANT]\n> Contenu
    # On va d'abord convertir les lignes de citation simples
    # Mais les alertes github style méritent un style spécial
    html = re.sub(r'>\s*\[!IMPORTANT\]\s*\n>\s*(.*?)$', r'<div class="alert alert-important"><strong>Important :</strong> \1</div>', html, flags=re.MULTILINE|re.IGNORECASE)
    html = re.sub(r'>\s*\[!NOTE\]\s*\n>\s*(.*?)$', r'<div class="alert alert-note"><strong>Note :</strong> \1</div>', html, flags=re.MULTILINE|re.IGNORECASE)
    
    # Lignes de citation classiques
    html = re.sub(r'^>\s*(.*?)$', r'<blockquote>\1</blockquote>', html, flags=re.MULTILINE)

    # Gras
    html = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html)
    # Italique
    html = re.sub(r'\*(.*?)\*', r'<em>\1</em>', html)
    
    # Listes à puces
    # Remplacer les lignes qui commencent par * ou - en <li>
    # Pour faire simple et propre, on va traiter ligne par ligne
    lines = html.split('\n')
    in_list = False
    in_table = False
    new_lines = []
    
    for line in lines:
        # Traitement des tables simples
        if line.strip().startswith('|'):
            if not in_table:
                in_table = True
                new_lines.append('<table class="table">')
            # Extraire les cellules
            cells = [c.strip() for c in line.split('|')[1:-1]]
            if len(cells) > 0:
                # Éviter la ligne de séparation |---|---|
                if all(re.match(r'^[-:]+$', c) for c in cells):
                    continue
                tag = 'th' if len(new_lines) == len([l for l in new_lines if not l.startswith('<table')]) + 1 else 'td'
                row_html = '<tr>' + ''.join(f'<{tag}>{c}</{tag}>' for c in cells) + '</tr>'
                new_lines.append(row_html)
            continue
        elif in_table:
            in_table = False
            new_lines.append('</table>')

        # Traitement des listes à puces
        bullet_match = re.match(r'^[\*\-\+]\s+(.*?)$', line.strip())
        if bullet_match:
            if not in_list:
                in_list = True
                new_lines.append('<ul>')
            new_lines.append(f'<li>{bullet_match.group(1)}</li>')
        else:
            if in_list:
                in_list = False
                new_lines.append('</ul>')
            
            # Paragraphes simples (éviter les lignes vides et les balises déjà HTML)
            stripped = line.strip()
            if stripped and not stripped.startswith('<') and not stripped.endswith('>'):
                new_lines.append(f'<p>{stripped}</p>')
            else:
                new_lines.append(line)
                
    if in_list:
        new_lines.append('</ul>')
    if in_table:
        new_lines.append('</table>')
        
    html_body = '\n'.join(new_lines)

    # Template HTML haut de gamme (Style minimaliste, typographie élégante, adapté pour impression PDF)
    styled_html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=Plus+Jakarta+Sans:ital,wght@0,300;0,400;0,600;1,400&display=swap');
        
        body {{
            font-family: 'Plus Jakarta Sans', sans-serif;
            color: #1e293b;
            line-height: 1.6;
            max-width: 800px;
            margin: 40px auto;
            padding: 0 20px;
            background-color: #ffffff;
        }}
        
        h1, h2, h3 {{
            font-family: 'Outfit', sans-serif;
            color: #0f172a;
            font-weight: 800;
        }}
        
        h1 {{
            font-size: 2.2rem;
            border-bottom: 2px solid #f1f5f9;
            padding-bottom: 15px;
            margin-top: 0;
            color: #dc2626; /* Rouge incendie pour le sujet */
        }}
        
        h2 {{
            font-size: 1.5rem;
            margin-top: 30px;
            border-left: 4px solid #ef4444;
            padding-left: 12px;
        }}
        
        h3 {{
            font-size: 1.15rem;
            margin-top: 20px;
            color: #475569;
        }}
        
        p {{
            margin-bottom: 1.25rem;
            font-size: 1.05rem;
            font-weight: 300;
        }}
        
        ul {{
            margin-bottom: 1.5rem;
            padding-left: 20px;
        }}
        
        li {{
            margin-bottom: 0.5rem;
            font-size: 1.05rem;
            font-weight: 300;
        }}
        
        strong {{
            font-weight: 600;
            color: #0f172a;
        }}
        
        /* Bloc alertes premium */
        .alert {{
            padding: 15px 20px;
            border-radius: 8px;
            margin: 20px 0;
            font-size: 1rem;
        }}
        
        .alert-important {{
            background-color: #fef2f2;
            border-left: 4px solid #ef4444;
            color: #991b1b;
        }}
        
        .alert-note {{
            background-color: #f0f9ff;
            border-left: 4px solid #0284c7;
            color: #075985;
        }}
        
        blockquote {{
            border-left: 4px solid #e2e8f0;
            padding-left: 15px;
            margin: 20px 0;
            font-style: italic;
            color: #64748b;
        }}
        
        /* Tableaux */
        .table {{
            width: 100%;
            border-collapse: collapse;
            margin: 30px 0;
            font-size: 0.95rem;
        }}
        
        .table th, .table td {{
            padding: 12px 15px;
            text-align: left;
            border-bottom: 1px solid #e2e8f0;
        }}
        
        .table th {{
            background-color: #f8fafc;
            color: #475569;
            font-weight: 600;
        }}
        
        .table tr:hover {{
            background-color: #f8fafc;
        }}
        
        /* Suppression des éléments non-imprimables */
        @media print {{
            body {{
                margin: 20px;
                font-size: 12pt;
            }}
            
            /* Eviter de couper les sections importantes au milieu d'une page */
            h1, h2, h3, table, .alert {{
                page-break-inside: avoid;
            }}
        }}
    </style>
</head>
<body>
    {html_body}
</body>
</html>
"""
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(styled_html)

def convert_html_to_pdf(html_path, pdf_path):
    # Résoudre les chemins absolus et formuler l'URL de fichier pour Chrome
    abs_html = os.path.abspath(html_path)
    abs_pdf = os.path.abspath(pdf_path)
    html_url = f"file:///{abs_html.replace(os.sep, '/')}"

    # Chercher le chemin de Google Chrome (Windows / Linux)
    chrome_exe = None
    if os.name == 'posix':
        import shutil
        chrome_exe = shutil.which("google-chrome") or shutil.which("google-chrome-stable") or shutil.which("chromium-browser") or shutil.which("chromium")
    else:
        chrome_paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            os.path.expandvars(r"%LocalAppData%\Google\Chrome\Application\chrome.exe")
        ]
        for path in chrome_paths:
            if os.path.exists(path):
                chrome_exe = path
                break
            
    if not chrome_exe:
        print("Erreur : Impossible de trouver Google Chrome sur votre systeme.")
        return False
        
    print(f"Google Chrome trouve : {chrome_exe}")
    
    # Commande Chrome Headless pour imprimer en PDF
    cmd = [
        chrome_exe,
        "--headless",
        "--disable-gpu",
        "--no-sandbox",
        f"--print-to-pdf={abs_pdf}",
        html_url
    ]
    
    try:
        # Lancer le processus Chrome
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        if os.path.exists(abs_pdf):
            print(f"Succes : Le fichier PDF a ete genere avec succes sous : {abs_pdf}")
            return True
        else:
            print("Erreur : Le fichier PDF n'a pas ete cree.")
            return False
    except Exception as e:
        print(f"Erreur lors du lancement de Chrome : {e}")
        return False

if __name__ == "__main__":
    import sys
    md_file = "rapports/regle_330_incendies.md"
    if len(sys.argv) > 1:
        md_file = sys.argv[1]

    html_file = md_file.replace(".md", ".html")
    pdf_file = md_file.replace(".md", ".pdf")

    title = os.path.basename(md_file).replace("_", " ").replace(".md", "").title()

    print(f"--- Etape 1 : Conversion de {md_file} en HTML Premium ---")
    md_to_html(md_file, html_file, title=title)

    print("\n--- Etape 2 : Impression en PDF via Google Chrome Headless ---")
    success = convert_html_to_pdf(html_file, pdf_file)

    if success:
        # Nettoyer le fichier HTML intermediaire
        try:
            os.remove(html_file)
            print("Nettoyage du fichier HTML intermediaire effectue.")
        except:
            pass
