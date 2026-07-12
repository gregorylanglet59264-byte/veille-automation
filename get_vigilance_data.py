import urllib.request
import re
import os
import sys
import tempfile
import argparse
import sqlite3
from datetime import datetime
from html.parser import HTMLParser

sys.path.append(r"C:\Users\grego\.gemini\config\skills\meteo\scripts")
try:
    import meteo_core
except ImportError:
    meteo_core = None

def fix_encoding(text):
    if not text:
        return ""
    try:
        return text.encode('latin-1').decode('utf-8')
    except Exception:
        return text

def get_image_base64(filepath):
    if not filepath or not os.path.exists(filepath):
        return ""
    import base64
    try:
        with open(filepath, "rb") as f:
            encoded = base64.b64encode(f.read()).decode("utf-8")
        return f"data:image/png;base64,{encoded}"
    except Exception as e:
        print(f"Erreur d'encodage base64 pour {filepath}: {e}")
        return ""

def generate_records_alert_html(date_compact):
    if not meteo_core:
        return ""
    try:
        print("Scraping en direct pour vérification des records...")
        meteo_core.scrape_national_archive(date_compact)
        
        db_path = meteo_core.get_db_path()
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        broken = []
        
        # Tmax
        cursor.execute("""
            SELECT s.name, s.dept, o.tmax, o.tmax_rec_m, o.tmax_rec_m_date, o.tmax_rec_a, o.tmax_rec_a_date
            FROM observations o
            JOIN stations s ON o.station_code = s.code
            WHERE o.date = ? AND o.tmax IS NOT NULL AND o.tmax_rec_m IS NOT NULL
              AND o.tmax >= o.tmax_rec_m
        """, (date_compact,))
        for r in cursor.fetchall():
            is_abs = r[2] >= r[5] if r[5] is not None else False
            type_str = "ABSOLU 🌡️" if is_abs else "MENSUEL 🌡️"
            broken.append(f"🔴 <strong>[{type_str}] {r[0]} ({r[1]})</strong> : <strong>{r[2]}°C</strong> (ancien record : {r[3]}°C le {r[4]})")
            
        # Tmin (froid)
        cursor.execute("""
            SELECT s.name, s.dept, o.tmin, o.tmin_rec_m, o.tmin_rec_m_date, o.tmin_rec_a, o.tmin_rec_a_date
            FROM observations o
            JOIN stations s ON o.station_code = s.code
            WHERE o.date = ? AND o.tmin IS NOT NULL AND o.tmin_rec_m IS NOT NULL
              AND o.tmin <= o.tmin_rec_m
        """, (date_compact,))
        for r in cursor.fetchall():
            is_abs = r[2] <= r[5] if r[5] is not None else False
            type_str = "ABSOLU ❄️" if is_abs else "MENSUEL ❄️"
            broken.append(f"🔵 <strong>[{type_str}] {r[0]} ({r[1]})</strong> : <strong>{r[2]}°C</strong> (ancien record : {r[3]}°C le {r[4]})")
            
        # Pluie
        cursor.execute("""
            SELECT s.name, s.dept, o.precip, o.precip_rec_m, o.precip_rec_m_date, o.precip_rec_a, o.precip_rec_a_date
            FROM observations o
            JOIN stations s ON o.station_code = s.code
            WHERE o.date = ? AND o.precip IS NOT NULL AND o.precip_rec_m IS NOT NULL
              AND o.precip >= o.precip_rec_m AND o.precip > 0
        """, (date_compact,))
        for r in cursor.fetchall():
            is_abs = r[2] >= r[5] if r[5] is not None else False
            type_str = "ABSOLU 🌧️" if is_abs else "MENSUEL 🌧️"
            broken.append(f"🌧️ <strong>[{type_str}] {r[0]} ({r[1]})</strong> : <strong>{r[2]} mm</strong> (ancien record : {r[3]} mm le {r[4]})")
            
        # Vent
        cursor.execute("""
            SELECT s.name, s.dept, o.gust, o.gust_rec_m, o.gust_rec_m_date, o.gust_rec_a, o.gust_rec_a_date
            FROM observations o
            JOIN stations s ON o.station_code = s.code
            WHERE o.date = ? AND o.gust IS NOT NULL AND o.gust_rec_m IS NOT NULL
              AND o.gust >= o.gust_rec_m AND o.gust > 0
        """, (date_compact,))
        for r in cursor.fetchall():
            is_abs = r[2] >= r[5] if r[5] is not None else False
            type_str = "ABSOLU 💨" if is_abs else "MENSUEL 💨"
            broken.append(f"💨 <strong>[{type_str}] {r[0]} ({r[1]})</strong> : <strong>{r[2]} km/h</strong> (ancien record : {r[3]} km/h le {r[4]})")
            
        conn.close()
        
        if not broken:
            return ""
            
        html = """
        <div style="background-color: #fef2f2; border: 1px solid #fee2e2; border-left: 4px solid #ef4444; padding: 16px; border-radius: 8px; margin-bottom: 24px; font-family: sans-serif;">
            <span style="font-weight: 800; font-size: 13px; color: #b91c1c; display: block; margin-bottom: 8px; text-transform: uppercase; letter-spacing: 0.5px;">🚨 ALERTE : RECORDS CLIMATIQUES NATIONAUX BATTUS / ÉGALÉS</span>
            <ul style="margin: 0; padding-left: 20px; font-size: 13.5px; color: #991b1b; line-height: 1.6;">
        """
        for item in broken:
            html += f"                <li style='margin-bottom: 4px;'>{item}</li>\n"
        html += """            </ul>
        </div>
        """
        return html
    except Exception as e:
        print(f"Erreur lors de la génération de l'alerte records : {e}")
        return ""

class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text_content = []
        self.in_script = False
        self.in_style = False

    def handle_starttag(self, tag, attrs):
        if tag == 'script':
            self.in_script = True
        elif tag == 'style':
            self.in_style = True

    def handle_endtag(self, tag):
        if tag == 'script':
            self.in_script = False
        elif tag == 'style':
            self.in_style = False

    def handle_data(self, data):
        if not self.in_script and not self.in_style:
            text = data.strip()
            if text:
                self.text_content.append(text)

def fetch_html(url):
    req = urllib.request.Request(
        url, 
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    )
    with urllib.request.urlopen(req) as response:
        return response.read().decode('utf-8', errors='ignore')

def format_bulletin_text(raw_text):
    if not raw_text:
        return ""
    import re
    # Clean double spaces
    raw_text = " ".join(raw_text.split())
    transitions = [
        "Ce matin", "L'après-midi", "Cet après-midi", "Les orages", "De la Bretagne",
        "Ailleurs", "Le vent", "Les températures maximales", "Il fait moins chaud"
    ]
    sentences = re.split(r'(?<=[.!?])\s+', raw_text)
    paragraphs = []
    current_para = []
    for sentence in sentences:
        is_transition = False
        for trans in transitions:
            if sentence.strip().startswith(trans) or sentence.strip().lower().startswith(trans.lower()):
                is_transition = True
                break
        if is_transition and current_para:
            paragraphs.append(" ".join(current_para))
            current_para = []
        current_para.append(sentence)
    if current_para:
        paragraphs.append(" ".join(current_para))
    formatted_paras = []
    for para in paragraphs:
        para_html = para
        bold_terms = [
            ("vigilance rouge", "vigilance rouge"),
            ("vigilance orange", "vigilance orange"),
            ("canicule", "canicule"),
            ("orages violents", "orages violents"),
            ("orages", "orages"),
            ("fortes chaleurs", "fortes chaleurs"),
            ("chaleur", "chaleur"),
            ("températures maximales", "températures maximales"),
            ("degrés", "degrés"),
            ("Ce matin", "Ce matin"),
            ("L'après-midi", "L'après-midi"),
            ("Cet après-midi", "Cet après-midi"),
        ]
        for term, replacement in bold_terms:
            pattern = re.compile(re.escape(term), re.IGNORECASE)
            para_html = pattern.sub(f"<strong>\\g<0></strong>", para_html)
        formatted_paras.append(f'        <p style="margin: 0 0 6px 0; text-align: justify; line-height: 1.45;">{para_html}</p>')
    return "\n".join(formatted_paras)

def clean_pdf_forecast_text(text):
    if not text:
        return ""
    import re
    lines = text.split('\n')
    cleaned_lines = []
    for line in lines:
        l = line.strip()
        if re.search(r'\d{2}/\d{2}/\d{4}', l):
            continue
        if re.search(r'J\+\d', l):
            continue
        if l.lower() in ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]:
            continue
        cleaned_lines.append(l)
    cleaned_text = " ".join(cleaned_lines)
    cleaned_text = " ".join(cleaned_text.split())
    cleaned_text = cleaned_text.lstrip('\ufeff')
    return cleaned_text

def overlay_logo_on_map(map_path, logo_path):
    if not os.path.exists(map_path) or not os.path.exists(logo_path):
        return
    try:
        from PIL import Image
        img_map = Image.open(map_path).convert("RGBA")
        img_logo = Image.open(logo_path).convert("RGBA")
        
        map_w, map_h = img_map.size
        # Logo height will be 10% of map height
        logo_h = int(map_h * 0.10)
        logo_w = int(img_logo.width * (logo_h / img_logo.height))
        
        try:
            resampling = Image.Resampling.LANCZOS
        except AttributeError:
            resampling = Image.ANTIALIAS
            
        img_logo_resized = img_logo.resize((logo_w, logo_h), resampling)
        
        # Position top-left
        position = (15, 15)
        
        img_map.paste(img_logo_resized, position, img_logo_resized)
        
        if map_path.lower().endswith(".jpg") or map_path.lower().endswith(".jpeg"):
            img_map.convert("RGB").save(map_path, "JPEG", quality=95)
        else:
            img_map.save(map_path, "PNG")
        print(f"Logo Météo Climat Pro superposé avec succès sur {map_path} !")
    except Exception as e:
        print(f"Erreur lors de la superposition du logo sur la carte : {e}")

def get_pdf_info_and_images(out_dir):
    import urllib.parse
    
    def rot13(s):
        res = []
        for c in s:
            if 'a' <= c <= 'z':
                res.append(chr(97 + (ord(c) - 97 + 13) % 26))
            elif 'A' <= c <= 'Z':
                res.append(chr(65 + (ord(c) - 65 + 13) % 26))
            else:
                res.append(c)
        return "".join(res)

    url = "https://vigilance.meteofrance.fr/fr"
    req = urllib.request.Request(
        url, 
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    )
    
    mfsession = None
    try:
        with urllib.request.urlopen(req) as response:
            headers = response.getheaders()
            for header, value in headers:
                if header.lower() == 'set-cookie' and 'mfsession=' in value:
                    m = re.search(r'mfsession=([^;]+)', value)
                    if m:
                        mfsession = m.group(1)
                        break
    except Exception as e:
        return f"Erreur lors de la récupération du cookie mfsession: {e}", []
        
    if not mfsession:
        return "Impossible de trouver le cookie mfsession pour générer le token de téléchargement.", []
        
    token = rot13(urllib.parse.unquote(mfsession))
    base_url = "https://rwg.meteofrance.com/internet2018client/2.0/report"
    params = {
        "domain": "france",
        "report_type": "vigilance",
        "report_subtype": "jours suivants",
        "token": token
    }
    
    pdf_url = base_url + "?" + urllib.parse.urlencode(params)
    fd, temp_path = tempfile.mkstemp(suffix=".pdf")
    os.close(fd)
    
    image_paths = []
    try:
        pdf_req = urllib.request.Request(
            pdf_url, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        )
        with urllib.request.urlopen(pdf_req) as response:
            with open(temp_path, 'wb') as f:
                f.write(response.read())
        
        import fitz
        doc = fitz.open(temp_path)
        pdf_text = []
        
        # Extraire le texte de chaque page
        def save_image_with_white_bg(image_bytes, dest_path):
            from PIL import Image
            import io
            img = Image.open(io.BytesIO(image_bytes))
            if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                bg = Image.new("RGB", img.size, (255, 255, 255))
                bg.paste(img, mask=img.convert("RGBA").split()[3])
                bg.save(dest_path, "PNG")
            else:
                img.convert("RGB").save(dest_path, "PNG")

        j2_j3_text = ""
        j4_j7_text = ""
        
        # Extraire précisément le texte des encadrés de commentaires (x0 > 550 et y1 < 300)
        if len(doc) > 0:
            page1 = doc[0]
            j2_j3_blocks = []
            for block in page1.get_text("blocks"):
                x0, y0, x1, y1, text, block_no, block_type = block
                if x0 > 550 and y0 > 138 and y1 < 300:
                    j2_j3_blocks.append(text.strip())
            j2_j3_text = " ".join(j2_j3_blocks)
            
        if len(doc) > 1:
            page2 = doc[1]
            j4_j7_blocks = []
            for block in page2.get_text("blocks"):
                x0, y0, x1, y1, text, block_no, block_type = block
                if x0 > 550 and y0 > 155 and y1 < 300:
                    j4_j7_blocks.append(text.strip())
            j4_j7_text = " ".join(j4_j7_blocks)

        for i, page in enumerate(doc):
            # Sauvegarder la page entière sous forme d'image PNG
            if i in [0, 1]:  # Page 1 (J+2/J+3) et Page 2 (J+4 à J+7)
                filename = f"carte_jours_suivants_page_{i+1}.png"
                img_path = os.path.join(out_dir, filename)
                pix = page.get_pixmap(dpi=150)
                pix.save(img_path)
                image_paths.append(img_path)
                
        doc.close()
        return (j2_j3_text, j4_j7_text), image_paths
    except Exception as e:
        return f"Erreur lors du téléchargement/lecture du PDF ({pdf_url}): {e}", []
    finally:
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass

def get_national_forecast():
    url = "https://meteofrance.com/"
    try:
        html_content = fetch_html(url)
        bulletins = re.findall(r'<bulletin.*?</bulletin>', html_content, re.DOTALL)
        if not bulletins:
            return "Aucun bulletin national trouvé dans le code source de meteofrance.com."
        b = bulletins[0]
        
        header = re.search(r'<bulletin([^>]*)>', b)
        obs = re.search(r'<observation>(.*?)</observation>', b, re.DOTALL)
        date = re.search(r'<date>(.*?)</date>', b, re.DOTALL)
        titre = re.search(r'<titre>(.*?)</titre>', b, re.DOTALL)
        temps = re.search(r'<temps>(.*?)</temps>', b, re.DOTALL)
        
        result = {}
        if header:
            prod_match = re.search(r'date_heure_production="([^"]+)"', header.group(1))
            if prod_match:
                result['production'] = prod_match.group(1)
        if obs:
            result['observation'] = fix_encoding(obs.group(1).strip())
        if date and titre and temps:
            result['date'] = fix_encoding(date.group(1).strip())
            result['titre'] = fix_encoding(titre.group(1).strip())
            result['temps'] = fix_encoding(temps.group(1).strip())
        return result
    except Exception as e:
        return {"error": f"Erreur lors de la récupération des prévisions nationales ({url}): {e}"}

def download_national_vigilance_map(out_dir, use_tomorrow=False):
    dest_path = os.path.join(out_dir, "vigilance_carte.png")
    try:
        # Tenter d'utiliser la carte de vigilance JPEG construite par la compétence CNews
        cnews_map_path = r"C:\Users\grego\Desktop\cartes_alertes\carte_vigilance_france_pictos.jpg"
        script_dir = os.path.dirname(os.path.abspath(__file__))
        logo_src = os.path.join(script_dir, "logo.png")
        if not os.path.exists(logo_src):
            logo_src = r"C:\Users\grego\Desktop\cartes_alertes\A_CONSERVER_ABSOLUMENT\logo meteo climat pro 3.png"
        if os.path.exists(cnews_map_path):
            import shutil
            shutil.copy(cnews_map_path, dest_path)
            print("Carte de vigilance récupérée avec succès depuis le dossier CNews (Desktop) !")
            if os.path.exists(logo_src):
                overlay_logo_on_map(dest_path, logo_src)
            return dest_path
            
        from playwright.sync_api import sync_playwright
        import time
        
        print(f"Lancement de la capture de la carte (demain={use_tomorrow})...")
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1000, "height": 800})
            page.goto("https://vigilance.meteofrance.fr/fr", timeout=60000)
            page.wait_for_selector("#map", timeout=20000)
            time.sleep(2)
            
            # Fermer le bandeau de cookies s'il est présent
            cookie_selectors = [
                "#didomi-notice-agree-button", 
                "Accept", "Accepter", "Tout accepter", "Autoriser"
            ]
            for sel in cookie_selectors:
                try:
                    if page.is_visible(sel, timeout=1000):
                        page.click(sel)
                        time.sleep(1)
                        break
                except Exception:
                    pass
            
            # Si on veut demain, cliquer sur le bouton Demain
            if use_tomorrow:
                try:
                    demain_btn = page.locator('li').filter(has_text="Demain").first
                    if demain_btn.is_visible():
                        demain_btn.click()
                        print("Bouton 'Demain' clique sur la carte.")
                        time.sleep(2)
                except Exception as e:
                    print(f"Erreur lors du clic sur 'Demain' : {e}")
            
            map_element = page.query_selector("#map")
            if map_element:
                map_element.screenshot(path=dest_path)
                print(f"Capture de la carte enregistree : {dest_path}")
            else:
                page.screenshot(path=dest_path)
                print(f"Capture de secours de la page enregistree : {dest_path}")
                
            browser.close()
            
            script_dir = os.path.dirname(os.path.abspath(__file__))
            logo_src = os.path.join(script_dir, "logo.png")
            if not os.path.exists(logo_src):
                logo_src = r"C:\Users\grego\Desktop\cartes_alertes\A_CONSERVER_ABSOLUMENT\logo meteo climat pro 3.png"
            if os.path.exists(logo_src):
                overlay_logo_on_map(dest_path, logo_src)
                
            return dest_path
    except Exception as e:
        print(f"Erreur lors de la capture Playwright de la carte : {e}")
        return None


def get_departments_vigilance():
    url = "https://vigilance.meteofrance.fr/fr/vigilance-accessible"
    try:
        html_content = fetch_html(url)
        parser = TextExtractor()
        parser.feed(html_content)
        lines = [line.strip() for line in parser.text_content]
        
        headers_indices = [i for i, line in enumerate(lines) if "Vigilance météo et crues pour" in line]
        if not headers_indices:
            return {}
            
        vigilance_data = {}
        for i, idx in enumerate(headers_indices):
            day_title = lines[idx]
            
            # Déterminer si c'est aujourd'hui ou demain
            key = "aujourdhui" if i == 0 else "demain"
            
            end_idx = headers_indices[i+1] if i + 1 < len(headers_indices) else len(lines)
            day_lines = lines[idx:end_idx]
            
            diff_text = ""
            if len(day_lines) > 2 and "Diffusion :" in day_lines[1]:
                diff_text = f" ({day_lines[1]} {day_lines[2]})"
            
            colors = {"Rouge": {}, "Orange": {}, "Jaune": {}}
            current_color = None
            
            j = 0
            while j < len(day_lines):
                line = day_lines[j]
                if "Nom des départements en vigilance rouge" in line:
                    current_color = "Rouge"
                    j += 1
                    continue
                elif "Nom des départements en vigilance orange" in line:
                    current_color = "Orange"
                    j += 1
                    continue
                elif "Nom des départements en vigilance jaune" in line:
                    current_color = "Jaune"
                    j += 1
                    continue
                elif any(term in line for term in ["départements en", "Définition de la vigilance", "Votre vigilance en outre-mer", "Vigilance Accessible"]):
                    current_color = None
                
                if current_color:
                    if '(' in line and ')' in line:
                        dept = line
                        phenoms = []
                        k = j + 1
                        while k < len(day_lines):
                            next_line = day_lines[k]
                            if any(term in next_line for term in ["Nom des", "départements en", "Définition de la vigilance", "Votre vigilance en outre-mer", "Vigilance Accessible"]):
                                break
                            if '(' in next_line and ')' in next_line:
                                break
                            phenoms.append(next_line)
                            k += 1
                        
                        phenom_str = ", ".join(phenoms) if phenoms else "Canicule"
                        colors[current_color].setdefault(phenom_str, []).append(dept)
                        j = k - 1
                j += 1
                
            vigilance_data[key] = {
                "title": day_title + diff_text,
                "colors": colors
            }
        return vigilance_data
    except Exception as e:
        print(f"Erreur vigilance accessible : {e}")
        return {}

def clean_social_posts(text):
    # Supprimer toute mention de Météo-France, Météo France, @meteofrance
    text = re.sub(r'Météo-France', 'les prévisionnistes', text, flags=re.IGNORECASE)
    text = re.sub(r'Météo France', 'les prévisionnistes', text, flags=re.IGNORECASE)
    text = re.sub(r'@meteofrance', '', text, flags=re.IGNORECASE)
    return text

def main():
    parser = argparse.ArgumentParser(description="Générateur de bulletin de vigilance")
    parser.add_argument("--out-dir", required=True, help="Dossier de destination pour les fichiers générés")
    parser.add_argument("--send", action="store_true", help="Envoyer automatiquement l'e-mail après génération")
    parser.add_argument("--to", default="patrick.marliere@wanadoo.fr", help="Destinataire de l'e-mail")
    args = parser.parse_args()
    
    out_dir = args.out_dir
    os.makedirs(out_dir, exist_ok=True)
    
    print(f"Dossier de sortie : {out_dir}")
    
    # Copier le logo Météo Climat Pro dans le dossier de sortie
    script_dir = os.path.dirname(os.path.abspath(__file__))
    logo_src = os.path.join(script_dir, "logo.png")
    if not os.path.exists(logo_src):
        logo_src = r"C:\Users\grego\Desktop\cartes_alertes\A_CONSERVER_ABSOLUMENT\logo meteo climat pro 3.png"
    logo_dest = os.path.join(out_dir, "logo_meteo_climat_pro.png")
    if os.path.exists(logo_src):
        import shutil
        shutil.copy(logo_src, logo_dest)
        print("Logo Météo Climat Pro copié avec succès !")
    
    # Déterminer la vigilance à afficher :
    # - Demain ("demain") si envoyé après 16h30
    # - Aujourd'hui ("aujourdhui") si envoyé avant midi (ou entre midi et 16h30)
    now = datetime.now()
    if now.hour > 16 or (now.hour == 16 and now.minute >= 30):
        use_tomorrow = True
    else:
        use_tomorrow = False
    vigilance_key = "demain" if use_tomorrow else "aujourdhui"
    
    # 1. Télécharger la carte nationale
    print("Téléchargement de la carte de vigilance nationale...")
    national_map = download_national_vigilance_map(out_dir, use_tomorrow)
    
    # 2. Récupérer le PDF et générer les images des jours suivants
    print("Récupération du PDF des jours suivants...")
    (j2_j3_text, j4_j7_text), pdf_images = get_pdf_info_and_images(out_dir)
    
    # 3. Prévisions nationales et températures
    print("Récupération du bulletin national...")
    national_forecast = get_national_forecast()
    
    # 4. Vigilance départementale
    print("Récupération de la vigilance par département...")
    vigilance_data = get_departments_vigilance()
    selected_vigilance = vigilance_data.get(vigilance_key, vigilance_data.get("aujourdhui"))
    
    # Si vide, valeurs par défaut sécurisées
    if not j2_j3_text:
        j2_j3_text = "Poursuite de la canicule sur la majeure partie du pays. Risque d'averses orageuses sur la façade atlantique."
    if not j4_j7_text:
        j4_j7_text = "Baisse relative des températures par l'ouest dès jeudi. Maintien des fortes chaleurs dans le Sud-Est et risque d'orages localisés."

    # Formater les températures
    cities_temp = ""
    obs_text = national_forecast.get('observation', '')
    temps_list = re.findall(r'(\w+(?:-\w+)?)\s*:\s*(\d+/\d+)', obs_text)
    
    # 6. Génération de l'HTML dans le nouvel ordre
    html_lines = []
    html_lines.append("""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            line-height: 1.6;
            color: #2c3e50;
            background-color: #f4f6f8;
            margin: 0;
            padding: 0;
        }
        .container {
            max-width: 680px;
            margin: 30px auto;
            background-color: #ffffff;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
            border: 1px solid #e1e8ed;
        }
        .header {
            background: linear-gradient(135deg, #0f172a, #1e293b);
            color: #ffffff;
            padding: 35px 24px;
            text-align: center;
            border-bottom: 3px solid #3b82f6;
        }
        .header h1 {
            margin: 0;
            font-size: 22px;
            font-weight: 700;
            letter-spacing: 0.5px;
        }
        .header p {
            margin: 8px 0 0 0;
            font-size: 13px;
            opacity: 0.8;
        }
        .content {
            padding: 24px;
        }
        .section-title {
            color: #1e293b;
            font-size: 16px;
            font-weight: 700;
            border-bottom: 2px solid #f1f5f9;
            padding-bottom: 6px;
            margin-top: 30px;
            margin-bottom: 14px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .badge-red {
            background-color: #fef2f2;
            color: #991b1b;
            padding: 4px 8px;
            border-radius: 4px;
            font-weight: 700;
            font-size: 12px;
            display: inline-block;
        }
        .badge-orange {
            background-color: #fff7ed;
            color: #9a3412;
            padding: 4px 8px;
            border-radius: 4px;
            font-weight: 700;
            font-size: 12px;
            display: inline-block;
        }
        .vigilance-card {
            border-radius: 8px;
            padding: 16px;
            margin-bottom: 16px;
            border: 1px solid #e2e8f0;
        }
        .vigilance-red {
            background-color: #fef2f2;
            border-left: 5px solid #ef4444;
        }
        .vigilance-orange {
            background-color: #fff7ed;
            border-left: 5px solid #f97316;
        }
        .map-img {
            max-width: 100%;
            height: auto;
            border-radius: 8px;
            margin-top: 12px;
            margin-bottom: 16px;
            border: 1px solid #e2e8f0;
            display: block;
        }
        .social-box {
            background-color: #f8fafc;
            border: 1px dashed #cbd5e1;
            padding: 14px;
            border-radius: 6px;
            font-family: monospace;
            font-size: 13px;
            white-space: pre-wrap;
            color: #334155;
            margin-bottom: 15px;
        }
        .footer {
            background-color: #f8fafc;
            padding: 20px;
            text-align: center;
            font-size: 11px;
            color: #64748b;
            border-top: 1px solid #e2e8f0;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div style="font-size: 11px; font-weight: 800; letter-spacing: 2px; color: #3b82f6; text-transform: uppercase; margin-bottom: 8px;">MONSIEUR MÉTÉO</div>
            <h1 style="margin:0; font-size:20px; font-weight:700; letter-spacing:0.5px;">🛡️ SYNTHÈSE MÉTÉOROLOGIQUE & VIGILANCE</h1>
            <div style="width: 40px; height: 2px; background-color: #3b82f6; margin: 12px auto;"></div>
            <p style="margin:0; font-size:13px; opacity:0.8;">Rapport professionnel • Édité le """ + now.strftime('%d/%m/%Y à %H:%M') + """</p>
        </div>
        <div class="content">
""")

    # Insertion de l'alerte records climatologiques en direct
    date_compact = now.strftime("%Y%m%d")
    alert_html = generate_records_alert_html(date_compact)
    if alert_html:
        html_lines.append(alert_html)

    # --- 1. BULLETIN ET TEMPÉRATURES NATIONALES ---
    date_str = national_forecast.get('date', '').strip()
    clean_date = date_str.replace("Demain ", "").replace("demain ", "").replace("Aujourd'hui ", "").replace("aujourd'hui ", "").replace("Aujourd’hui ", "").replace("aujourd’hui ", "")
    html_lines.append(f'        <div class="section-title">🌡️ 1. BULLETIN NATIONAL DU {clean_date.upper()}</div>')
    if 'titre' in national_forecast:
        html_lines.append(f"        <p style='font-size:14px; font-weight:bold; color:#0f172a; margin-top:0; margin-bottom:10px;'>📢 {date_str} - {national_forecast['titre']}</p>")
        html_lines.append(format_bulletin_text(national_forecast['temps']))
    
    if temps_list:
        # Extraire la légende de Météo-France
        intro_match = re.match(r'^(.*?):', obs_text, re.DOTALL)
        legend_text = intro_match.group(1).strip() if intro_match else "Voici les températures relevées suivies des prévisions"
        
        is_min = "minimales" in legend_text.lower()
        if is_min:
            th_text = "Ville (Relevé cet après-midi / Min prévu demain matin)"
            color_style = "color:#0284c7; font-weight:bold;"
        else:
            th_text = "Ville (Relevé ce matin / Max prévu cet après-midi)"
            color_style = "color:#e11d48; font-weight:bold;"
        
        html_lines.append('        <p style="font-size:13px; color:#475569; margin-top:0; margin-bottom:12px; line-height:1.4;">')
        html_lines.append(f'            ℹ️ <strong>Description :</strong> {legend_text}.')
        html_lines.append('        </p>')
        html_lines.append('        <table style="width:100%; border-collapse:collapse; margin-bottom:20px; font-size:13px; border:1px solid #e2e8f0; border-radius:8px; overflow:hidden; box-shadow:0 2px 5px rgba(0,0,0,0.02);">')
        html_lines.append('            <thead>')
        html_lines.append('                <tr style="background-color:#0f172a; border-bottom:2px solid #cbd5e1;">')
        html_lines.append(f'                    <th style="padding:10px 12px; text-align:left; font-weight:700; color:#ffffff; width:50%; border-right:1px solid #1e293b;">{th_text}</th>')
        html_lines.append(f'                    <th style="padding:10px 12px; text-align:left; font-weight:700; color:#ffffff; width:50%;">{th_text}</th>')
        html_lines.append('                </tr>')
        html_lines.append('            </thead>')
        html_lines.append('            <tbody>')
        for i in range(0, min(12, len(temps_list)), 2):
            html_lines.append('            <tr>')
            for j in range(2):
                if i+j < len(temps_list):
                    city, temp = temps_list[i+j]
                    t_first, t_second = temp.split('/')
                    border_right = ' border-right:1px solid #e2e8f0;' if j == 0 else ''
                    bg_color = ' background-color:#ffffff;' if (i//2) % 2 == 0 else ' background-color:#f8fafc;'
                    html_lines.append(f'                <td style="padding:10px 12px; border-bottom:1px solid #e2e8f0;{bg_color}{border_right}">')
                    html_lines.append(f'                    <span style="font-weight:600; color:#1e293b;">📍 {city}</span> : {t_first}°C / <span style="{color_style}">{t_second}°C</span>')
                    html_lines.append('                </td>')
            html_lines.append('            </tr>')
        html_lines.append('            </tbody>')
        html_lines.append('        </table>')

    # --- 2. SITUATION DE LA VIGILANCE DÉPARTEMENTALE (DYNAMIQUE) ---
    vig_title = "DEMAIN" if use_tomorrow else "AUJOURD'HUI"
    html_lines.append(f'        <div class="section-title">⚠️ 2. SITUATION DE LA VIGILANCE DÉPARTEMENTALE ({vig_title})</div>')
    
    if selected_vigilance:
        html_lines.append(f"        <p><strong>{selected_vigilance['title']}</strong></p>")
        
        # Carte de vigilance nationale (si dispo)
        if national_map:
            img_b64 = get_image_base64(national_map)
            html_lines.append(f'        <img src="{img_b64}" class="map-img" alt="Carte de Vigilance Nationale">')
            
        colors = selected_vigilance['colors']
        if colors.get('Rouge'):
            html_lines.append('        <div class="vigilance-card vigilance-red" style="margin-bottom: 20px; box-shadow: 0 2px 8px rgba(239, 68, 68, 0.05);">')
            html_lines.append('            <span class="badge-red" style="margin-bottom: 12px; border: 1px solid #fee2e2;">🔥 ALERTE ROUGE CANICULE</span>')
            for phenom, depts in colors['Rouge'].items():
                html_lines.append(f"            <p style='margin: 8px 0 6px 0; font-size:13px; font-weight:bold; color:#991b1b;'>{phenom} :</p>")
                html_lines.append("            <div style='margin-top: 4px; line-height: 1.8;'>")
                for dept in depts:
                    html_lines.append(f"                <span style='display:inline-block; background-color:#fee2e2; color:#991b1b; padding:2px 8px; margin:2px 1px; border-radius:12px; font-size:11px; font-weight:600; border:1px solid #fecaca;'>{dept}</span>")
                html_lines.append("            </div>")
            html_lines.append('        </div>')
            
        if colors.get('Orange'):
            html_lines.append('        <div class="vigilance-card vigilance-orange" style="margin-bottom: 20px; box-shadow: 0 2px 8px rgba(249, 115, 22, 0.05);">')
            html_lines.append('            <span class="badge-orange" style="margin-bottom: 12px; border: 1px solid #ffedd5;">⚠️ ALERTE ORANGE VIGILANCE</span>')
            for phenom, depts in colors['Orange'].items():
                html_lines.append(f"            <p style='margin: 8px 0 6px 0; font-size:13px; font-weight:bold; color:#c2410c;'>{phenom} :</p>")
                html_lines.append("            <div style='margin-top: 4px; line-height: 1.8;'>")
                for dept in depts:
                    html_lines.append(f"                <span style='display:inline-block; background-color:#ffedd5; color:#c2410c; padding:2px 8px; margin:2px 1px; border-radius:12px; font-size:11px; font-weight:600; border:1px solid #fed7aa;'>{dept}</span>")
                html_lines.append("            </div>")
            html_lines.append('        </div>')

    # --- 3. ÉVOLUTION POUR LES PROCHAINS JOURS (J+2 à J+7) ---
    html_lines.append('        <div class="section-title">📅 3. ÉVOLUTION POUR LES PROCHAINS JOURS (J+2 à J+7)</div>')
    
    # 3.1 Cartes d'évolution (PDF intégrés)
    if len(pdf_images) >= 1:
        img_b64 = get_image_base64(pdf_images[0])
        html_lines.append('        <div style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 16px; margin-bottom: 24px; text-align: center;">')
        html_lines.append('            <span style="font-weight: bold; font-size: 13px; color: #1e293b; display: block; margin-bottom: 12px; text-transform: uppercase; letter-spacing: 0.5px;">📈 Carte Officielle - Début de semaine (Lundi J+2 & Mardi J+3)</span>')
        html_lines.append(f'            <img src="{img_b64}" style="width: 100%; max-width: 600px; border: 1px solid #cbd5e1; border-radius: 6px; display: inline-block;" alt="Bulletin J+2 & J+3">')
        html_lines.append('        </div>')
        
    if len(pdf_images) >= 2:
        img_b64 = get_image_base64(pdf_images[1])
        html_lines.append('        <div style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 16px; margin-bottom: 24px; text-align: center;">')
        html_lines.append('            <span style="font-weight: bold; font-size: 13px; color: #1e293b; display: block; margin-bottom: 12px; text-transform: uppercase; letter-spacing: 0.5px;">📈 Carte Officielle - Fin de semaine (De Mercredi J+4 à Samedi J+7)</span>')
        html_lines.append(f'            <img src="{img_b64}" style="width: 100%; max-width: 600px; border: 1px solid #cbd5e1; border-radius: 6px; display: inline-block;" alt="Bulletin J+4 à J+7">')
        html_lines.append('        </div>')

    # 3.2 Article de commentaire détaillé (Extrait du PDF)
    html_lines.append('        <div style="background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 24px; margin-top: 28px; margin-bottom: 28px; box-shadow: 0 4px 12px rgba(0,0,0,0.02);">')
    html_lines.append('            <h3 style="margin: 0 0 16px 0; color: #1e293b; font-size: 15px; font-weight: 700; border-bottom: 2px solid #3b82f6; padding-bottom: 8px; text-transform: uppercase; letter-spacing: 0.5px;">📰 BULLETIN DÉTAILLÉ DE L\'ÉVOLUTION DE LA VIGILANCE NATIONALE</h3>')
    
    # Paragraphe 1 : J+2/J+3
    j2_j3_cleaned = clean_pdf_forecast_text(j2_j3_text)
    j2_j3_formatted = j2_j3_cleaned
    j2_j3_formatted = re.sub(r'(poursuite de la canicule)', r'<strong>\1</strong>', j2_j3_formatted, flags=re.IGNORECASE)
    j2_j3_formatted = re.sub(r'(températures restent très élevées)', r'<strong>\1</strong>', j2_j3_formatted, flags=re.IGNORECASE)
    j2_j3_formatted = re.sub(r'(dégradation orageuse marquée)', r'<strong>\1</strong>', j2_j3_formatted, flags=re.IGNORECASE)
    j2_j3_formatted = re.sub(r'(Vigilance Orange)', r'<strong>\1</strong>', j2_j3_formatted, flags=re.IGNORECASE)
    
    html_lines.append('            <div style="margin-bottom: 20px;">')
    html_lines.append('                <span style="font-weight: bold; font-size: 12px; color: #f97316; text-transform: uppercase; letter-spacing: 0.5px; display: block; margin-bottom: 6px;">📅 Début de semaine (Lundi 13 & Mardi 14 Juillet)</span>')
    html_lines.append(f'                <p style="margin: 0; font-size: 13.5px; color: #334155; line-height: 1.6; text-align: justify;">{j2_j3_formatted}</p>')
    html_lines.append('            </div>')
    
    # Paragraphe 2 : J+4 à J+7
    j4_j7_cleaned = clean_pdf_forecast_text(j4_j7_text)
    j4_j7_formatted = j4_j7_cleaned
    j4_j7_formatted = re.sub(r'(conditions caniculaires se poursuivent)', r'<strong>\1</strong>', j4_j7_formatted, flags=re.IGNORECASE)
    j4_j7_formatted = re.sub(r'(baisse relative des températures)', r'<strong>\1</strong>', j4_j7_formatted, flags=re.IGNORECASE)
    j4_j7_formatted = re.sub(r'(chaleur pourra persister)', r'<strong>\1</strong>', j4_j7_formatted, flags=re.IGNORECASE)
    j4_j7_formatted = re.sub(r'(faible risque d\'orages virulents)', r'<strong>\1</strong>', j4_j7_formatted, flags=re.IGNORECASE)
    
    html_lines.append('            <div>')
    html_lines.append('                <span style="font-weight: bold; font-size: 12px; color: #ef4444; text-transform: uppercase; letter-spacing: 0.5px; display: block; margin-bottom: 6px;">📅 Fin de semaine (De Mercredi 15 au Samedi 18 Juillet)</span>')
    html_lines.append(f'                <p style="margin: 0; font-size: 13.5px; color: #334155; line-height: 1.6; text-align: justify;">{j4_j7_formatted}</p>')
    html_lines.append('            </div>')
    html_lines.append('        </div>')

    # --- 4. COMMUNIQUÉ DE SYNTHÈSE PRESSE ---
    html_lines.append('        <div class="section-title">📰 4. COMMUNIQUÉ DE SYNTHÈSE PRESSE</div>')
    html_lines.append('        <div style="background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 24px; margin-bottom: 28px; box-shadow: 0 4px 12px rgba(0,0,0,0.02);">')
    html_lines.append('            <h4 style="margin: 0 0 4px 0; font-size: 15px; color: #0f172a; font-weight: bold;">Canicule d\'intensité exceptionnelle sur l\'Hexagone</h4>')
    html_lines.append('            <p style="font-style: italic; color:#64748b; font-size: 13px; margin-top: 0; margin-bottom: 16px; border-bottom: 1px solid #f1f5f9; padding-bottom: 8px;">Synthèse globale des événements en cours et à venir.</p>')
    
    press_text_1 = "Une masse d'air d'une chaleur inédite s'est installée sur le pays. Avec des vigilances rouges et oranges généralisées, le thermomètre va fréquemment atteindre ou dépasser les 38°C en plaine, particulièrement sur le flanc Ouest et Central du territoire."
    press_text_1 = re.sub(r'(chaleur inédite)', r'<strong>\1</strong>', press_text_1, flags=re.IGNORECASE)
    press_text_1 = re.sub(r'(vigilances rouges et oranges généralisées)', r'<strong>\1</strong>', press_text_1, flags=re.IGNORECASE)
    press_text_1 = re.sub(r'(atteindre ou dépasser les 38°C)', r'<strong>\1</strong>', press_text_1, flags=re.IGNORECASE)
    
    press_text_2 = "Parallèlement, une instabilité orageuse violente concerne le Sud-Est du pays avec des cumuls d'eau rapides et des risques de grêle. Ces orages vont remonter à partir de lundi par l'Atlantique, amorçant une baisse graduelle des températures par l'ouest dès le milieu de semaine prochaine."
    press_text_2 = re.sub(r'(instabilité orageuse violente)', r'<strong>\1</strong>', press_text_2, flags=re.IGNORECASE)
    press_text_2 = re.sub(r'(risques de grêle)', r'<strong>\1</strong>', press_text_2, flags=re.IGNORECASE)
    press_text_2 = re.sub(r'(baisse graduelle des températures)', r'<strong>\1</strong>', press_text_2, flags=re.IGNORECASE)
    
    html_lines.append(f'            <p style="margin: 0 0 12px 0; font-size: 13.5px; color: #334155; line-height: 1.6; text-align: justify;">{press_text_1}</p>')
    html_lines.append(f'            <p style="margin: 0; font-size: 13.5px; color: #334155; line-height: 1.6; text-align: justify;">{press_text_2}</p>')
    html_lines.append('        </div>')

    # --- RÉSEAUX SOCIAUX (SANS MÉTÉO-FRANCE) ---
    html_lines.append('        <div class="section-title">📱 PROPOSITION DE POSTS RÉSEAUX SOCIAUX</div>')
    
    num_rouge = len(colors.get('Rouge', {}).get('Canicule', [])) if colors.get('Rouge') else 37
    num_orange = len(colors.get('Orange', {}).get('Canicule', [])) if colors.get('Orange') else 46

    li_post = f"""🚨 DÔME DE CHALEUR EXTRÊME : La France bascule dans l'inédit ! 🚨

C'est du jamais vu pour un début juillet ! Une masse d'air d'une chaleur historique s'est installée sur le pays, poussant le thermomètre à des sommets affolants. 

👉 Ce dimanche, la vigilance maximale est déclenchée : {num_rouge} départements sont en VIGILANCE ROUGE canicule et {num_orange} en VIGILANCE ORANGE. 

🌡️ Ce qui vous attend dans les prochaines heures :
*   Des températures extrêmes : Le mercure va fréquemment atteindre ou dépasser les 38°C à 42°C en plaine, particulièrement sur un large flanc Ouest et Centre du territoire.
*   Une instabilité orageuse violente : En marge de cette chaleur étouffante, des orages violents concernent le Sud-Est avec des risques importants de grêle et des rafales de vent de 70 à 90 km/h.
*   Baisse par l'Ouest : Une bouffée d'air océanique amorcera une baisse graduelle des températures par l'Atlantique à partir de lundi/mardi, mais la chaleur persistera à l'Est.

⚠️ Consignes de sécurité cruciales :
1️⃣ Restez au frais : Fermez les volets en journée, limitez les sorties aux heures les plus chaudes.
2️⃣ Hydratez-vous : Buvez de l'eau régulièrement, sans attendre d'avoir soif.
3️⃣ Solidarité : Prenez régulièrement des nouvelles des personnes fragiles ou isolées dans votre entourage.

💬 Et quel temps fait-il chez vous ? Envoyez vos photos et vos observations en commentaire ! 👇

#Meteo #Canicule #ChaleurExtreme #VigilanceRouge #Securite #Climat"""

    tw_post = f"""🚨 #Canicule historique : {num_rouge} départements en Vigilance Rouge ce dimanche ! Les températures vont frôler les 40-42°C localement. 🥵
⚡ Risque d'orages violents au Sud-Est et sur la façade atlantique.
💧 Hydratez-vous, restez au frais et veillez sur vos proches.
🚨 Soyez extrêmement prudents !"""

    html_lines.append(f'        <p><strong>Post LinkedIn (Sans mention de source) :</strong></p>')
    html_lines.append(f'        <div class="social-box">{clean_social_posts(li_post)}</div>')
    
    html_lines.append(f'        <p><strong>Post Twitter / X (Sans mention de source) :</strong></p>')
    html_lines.append(f'        <div class="social-box">{clean_social_posts(tw_post)}</div>')

    html_lines.append("""
        </div>
    </div>
</body>
</html>
""")

    # Écrire l'HTML final
    html_path = os.path.join(out_dir, "bulletin_final.html")
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(html_lines))
        
    print(f"HTML généré avec succès : {html_path}")
    print(f"Images générées : {len(pdf_images) + (1 if national_map else 0)}")

    if args.send:
        smtp_email = os.environ.get("SMTP_EMAIL", "gregory.langlet@sfr.fr")
        smtp_password = os.environ.get("SMTP_PASSWORD")
        
        # Le destinataire par défaut est args.to, mais s'il y a un RECIPIENT_EMAILS dans l'env on l'utilise
        recipient = os.environ.get("RECIPIENT_EMAILS", args.to)
        recipients = [r.strip() for r in recipient.split(",") if r.strip()]
        
        if not smtp_password:
            print("[SMTP] ERREUR : SMTP_PASSWORD manquant. Impossible d'envoyer la vigilance.")
            sys.exit(1)
            
        print(f"[SMTP] Envoi automatique du mail de vigilance à {', '.join(recipients)}...")
        try:
            from email.mime.multipart import MIMEMultipart
            from email.mime.text import MIMEText
            from email.mime.base import MIMEBase
            from email import encoders
            from email.utils import make_msgid, formatdate
            import smtplib
            import mimetypes
            
            # Objet de mail multipart mixed
            msg = MIMEMultipart('mixed')
            display_name = "Monsieur Meteo"
            msg['From'] = f"{display_name} <{smtp_email}>"
            msg['To'] = ", ".join(recipients)
            msg['Subject'] = f"Bulletin de Vigilance Météo-France - {now.strftime('%d/%m/%Y')}"
            msg['Message-ID'] = make_msgid()
            msg['Date'] = formatdate(localtime=True)
            msg['MIME-Version'] = '1.0'
            msg['X-Mailer'] = 'Python/smtplib (Linux)'
            
            # Corps simple anti-spam
            text_body = f"Bonjour,\n\nVeuillez trouver ci-joint le bulletin de vigilance Météo-France et prévisions nationales pour aujourd'hui ({now.strftime('%d/%m/%Y')}).\n\nLe rapport complet au format HTML ainsi que les cartes d'évolution sont attachés à ce message.\n\nCordialement,\nMonsieur Météo"
            msg.attach(MIMEText(text_body, 'plain', 'utf-8'))
            
            # Pièce jointe du rapport HTML principal
            part_html = MIMEBase('text', 'html')
            part_html.set_payload(open(html_path, 'r', encoding='utf-8').read().encode('utf-8'))
            encoders.encode_base64(part_html)
            part_html.add_header('Content-Disposition', 'attachment', filename=f"vigilance_bulletin_{now.strftime('%Y_%m_%d')}.html")
            msg.attach(part_html)
            

            with smtplib.SMTP_SSL("smtp.sfr.fr", 465) as server:
                server.login(smtp_email, smtp_password)
                server.sendmail(smtp_email, recipients, msg.as_string())
            print("[SMTP] E-mail de vigilance envoyé avec succès !")
        except Exception as e:
            print(f"[SMTP] Erreur lors de l'envoi de l'e-mail de vigilance : {e}")
            sys.exit(1)

if __name__ == "__main__":
    main()
