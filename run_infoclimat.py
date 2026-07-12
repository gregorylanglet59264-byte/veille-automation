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

INDEX_URL = "https://forums.infoclimat.fr/f/forum/20-evolution-%C3%A0-plus-long-terme/"
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'

def fetch_url(url):
    req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
    with urllib.request.urlopen(req, timeout=15) as response:
        return response.read().decode('utf-8', errors='ignore')

def call_llm(system_prompt, user_prompt):
    gemini_key = os.environ.get("GEMINI_API_KEY")
    openrouter_key = os.environ.get("OPENROUTER_API_KEY")
    
    if gemini_key:
        gemini_key = gemini_key.replace('\ufeff', '').replace('\ufffe', '').strip()
        print("[LLM] Appel de Gemini API...")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_key}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{
                "parts": [{"text": f"{system_prompt}\n\n{user_prompt}"}]
            }]
        }
        try:
            req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=90) as response:
                res_data = json.loads(response.read().decode("utf-8"))
                text = res_data["candidates"][0]["content"]["parts"][0]["text"]
                return text.replace('\ufeff', '').replace('\ufffe', '')
        except Exception as e:
            print(f"[LLM] Erreur Gemini API: {e}")
            
    if openrouter_key:
        openrouter_key = openrouter_key.replace('\ufeff', '').replace('\ufffe', '').strip()
        print("[LLM] Appel de OpenRouter API (DeepSeek)...")
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {openrouter_key}"
        }
        payload = {
            "model": "deepseek/deepseek-chat",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        }
        try:
            req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=90) as response:
                res_data = json.loads(response.read().decode("utf-8"))
                text = res_data["choices"][0]["message"]["content"]
                return text.replace('\ufeff', '').replace('\ufffe', '')
        except urllib.error.HTTPError as http_err:
            print(f"[LLM] Erreur HTTP OpenRouter API ({http_err.code})")
        except Exception as e:
            print(f"[LLM] Erreur OpenRouter API: {e}")
            
    print("[LLM] ERREUR : Aucune clé API configurée.")
    return None

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
        
    target_topic = clean_topics[0]
    # Extraire un titre propre du sujet à partir de l'URL
    topic_title_slug = target_topic.split('/')[-1]
    topic_title_clean = topic_title_slug.replace('-', ' ').title()
    print(f"Sujet identifié : {topic_title_clean} ({target_topic})")
    
    print("Analyse de la pagination...")
    try:
        html_topic = fetch_url(target_topic)
    except Exception as e:
        print(f"Erreur sujet : {e}")
        sys.exit(1)
        
    pages = re.findall(r'\?page=(\d+)', html_topic)
    last_page = 1
    if pages:
        last_page = max(int(p) for p in pages)
    print(f"Pages détectées : {last_page}")
    
    start_page = max(1, last_page - 2)
    all_comments = []
    all_authors = []
    
    print(f"Chargement des commentaires des pages {start_page} à {last_page}...")
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
            
    # Nettoyer les commentaires pour l'IA
    cleaned_comments_data = []
    for idx, comment in enumerate(all_comments):
        clean_comment = re.sub(r'<br\s*/?>', '\n', comment)
        clean_comment = re.sub(r'<[^>]+>', '', clean_comment).strip()
        clean_comment = re.sub(r'\n\s*\n', '\n', clean_comment)
        author = all_authors[idx] if idx < len(all_authors) else "Membre"
        cleaned_comments_data.append(f"Auteur: {author}\nMessage:\n{clean_comment}")
        
    # Garder les 15 derniers messages pour l'analyse
    recent_messages_text = "\n\n=======================\n\n".join(cleaned_comments_data[-15:])
    
    # Extraire et télécharger les graphiques candidats
    print("Extraction des graphiques...")
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
    # Vider le dossier
    for f in os.listdir("candidates"):
        try: os.remove(os.path.join("candidates", f))
        except: pass
        
    downloaded_images = []
    for idx, (img_url, prio) in enumerate(candidate_imgs[:3]):
        ext = "png"
        if ".gif" in img_url.lower(): ext = "gif"
        elif ".jpg" in img_url.lower() or ".jpeg" in img_url.lower(): ext = "jpg"
        
        dest_file = f"candidates/candidate_{idx+1}.{ext}"
        print(f"Téléchargement graphique {idx+1} : {img_url} -> {dest_file}")
        try:
            req = urllib.request.Request(img_url, headers={'User-Agent': USER_AGENT})
            with urllib.request.urlopen(req, timeout=12) as img_resp:
                with open(dest_file, 'wb') as f_out:
                    f_out.write(img_resp.read())
            downloaded_images.append(dest_file)
        except Exception as e:
            print(f"Erreur téléchargement graphique {idx+1} : {e}")

    # Appeler l'IA pour l'analyse des scénarios et la rédaction du post LinkedIn
    print("Appel de l'IA pour l'analyse des scénarios météo...")
    system_prompt = """Tu es un analyste météorologue senior (Monsieur Météo). Ton rôle est d'analyser les discussions récentes des prévisionnistes du forum Infoclimat pour en extraire la tendance à moyen et long terme sous forme de 3 scénarios (Majoritaire, Médian, Minoritaire) avec leurs probabilités associées.

Tu dois ensuite rédiger un post LinkedIn prêt à copier-coller pour présenter ces prévisions de façon claire et engageante pour des professionnels.

RÈGLES CRITIQUES ET ABSOLUES :
1. RÈGLE CRITIQUE : Ne mentionne JAMAIS le nom du forum 'Infoclimat', ses membres, ni leurs pseudos. Présente les analyses comme "le consensus de la communauté des prévisionnistes", "les analyses des modèles" ou "notre consensus".
2. RÈGLE CRITIQUE : Ne mets AUCUN formatage markdown (comme ** ou * ou # ou `) dans le post LinkedIn. Il doit être en brut propre avec des émojis et des listes à puces.
3. RÈGLE CRITIQUE : Rédige en français uniquement.
4. RÈGLE CRITIQUE : Calcule la probabilité des 3 scénarios en utilisant une pondération logique. Le scénario minoritaire (option extrême/isolée) doit être estimé à moins de 5%.
5. RÈGLE CRITIQUE : Utilise un ton de blogueur météorologue passionné, naturel, direct, avec du storytelling. Évite les phrases trop robotiques d'IA.
6. RÈGLE CRITIQUE : Termine obligatoirement le post LinkedIn par une question d'engagement pour inciter les lecteurs à commenter.

Format de sortie attendu : JSON uniquement avec la structure suivante (sans blocs ```json) :
{
  "subject_title": "Titre propre de la semaine de prévision (ex: Semaine du 13 au 19 juillet)",
  "scenarios": {
    "majoritaire": {"prob": "70%", "desc": "Description du scénario majoritaire avec détails physiques (blocage, masses d'air) et géographiques (moitié nord / moitié sud)"},
    "median": {"prob": "25%", "desc": "Description détaillée du scénario médian"},
    "minoritaire": {"prob": "5%", "desc": "Description détaillée du scénario minoritaire et explication de sa faible probabilité"}
  },
  "linkedin_post": "Texte complet du post LinkedIn propre (sans aucun markdown, avec émojis et retours à la ligne)"
}"""

    user_prompt = f"Discussions récentes des prévisionnistes :\n\n{recent_messages_text}"
    response = call_llm(system_prompt, user_prompt)
    
    if response:
        try:
            response_clean = response.strip().replace("```json", "").replace("```", "").strip()
            data = json.loads(response_clean)
        except Exception as e:
            print(f"Erreur parsing JSON IA : {e}")
            data = None
    else:
        data = None
        
    if not data:
        # Fallback de secours si l'IA échoue
        data = {
            "subject_title": topic_title_clean,
            "scenarios": {
                "majoritaire": {"prob": "70%", "desc": "Poursuite du flux dominant avec des températures saisonnières. Les modèles convergent vers un scénario stable sur la majeure partie du pays."},
                "median": {"prob": "25%", "desc": "Variante humide avec baisse des températures par l'ouest et retour d'une instabilité orageuse localisée."},
                "minoritaire": {"prob": "5%", "desc": "Option caniculaire extrême isolée non confirmée par les modèles d'ensemble."}
            },
            "linkedin_post": "🚨 FOCUS MÉTÉO : Tendances pour les prochains jours !\n\nConsensus des prévisionnistes :\n- Scénario Majoritaire (70%) : Temps de saison.\n- Scénario Médian (25%) : Instabilité orageuse.\n- Scénario Minoritaire (5%) : Canicule isolée.\n\n💬 Et chez vous, quel temps préférez-vous ? 👇\n\n#Meteo #Previsions #Climat"
        }
        
    # Encodage des images téléchargées en base64 pour insertion HTML directe
    html_images_block = ""
    for idx, img_path in enumerate(downloaded_images):
        try:
            with open(img_path, "rb") as f_img:
                img_b64 = base64.b64encode(f_img.read()).decode('ascii')
            ext = img_path.split('.')[-1]
            html_images_block += f"""
            <div style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; padding: 20px; margin-bottom: 28px; text-align: center;">
                <span style="font-weight: bold; font-size: 13px; color: #1e293b; display: block; margin-bottom: 12px; text-transform: uppercase; letter-spacing: 0.5px;">📈 Graphique Météo Candidat {idx+1}</span>
                <img src="data:image/{ext};base64,{img_b64}" style="width: 100%; max-width: 600px; border: 1px solid #cbd5e1; border-radius: 6px; display: inline-block;" alt="Graphique Infoclimat {idx+1}">
            </div>
            """
        except Exception as e:
            print(f"Erreur encodage base64 pour {img_path} : {e}")

    # Nettoyage des posts LinkedIn (remplacer sauts de ligne pour affichage propre dans le box)
    linkedin_post_clean = data["linkedin_post"].replace('<br>', '\n').replace('<br/>', '\n')

    # Génération du HTML
    style = """
    body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #334155; background-color: #f1f5f9; margin: 0; padding: 20px; }
    .container { max-width: 700px; background-color: #ffffff; margin: 0 auto; border-radius: 16px; overflow: hidden; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1); border: 1px solid #e2e8f0; }
    .header { background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%); color: #ffffff; padding: 30px; text-align: center; }
    .header h1 { margin: 0; font-size: 24px; font-weight: 700; }
    .header p { margin: 8px 0 0 0; font-size: 14px; opacity: 0.9; }
    .content { padding: 30px; }
    .section-title { font-size: 15px; font-weight: 800; text-transform: uppercase; letter-spacing: 1px; color: #1e3a8a; margin-top: 30px; margin-bottom: 15px; border-bottom: 2px solid #3b82f6; padding-bottom: 6px; }
    .scenario-card { border-radius: 12px; padding: 20px; margin-bottom: 20px; border: 1px solid #e2e8f0; }
    .sc-major { background-color: #ecfdf5; border-left: 5px solid #10b981; }
    .sc-median { background-color: #fef3c7; border-left: 5px solid #f59e0b; }
    .sc-minor { background-color: #fef2f2; border-left: 5px solid #ef4444; }
    .sc-title { font-size: 16px; font-weight: 700; color: #1e293b; display: flex; justify-content: space-between; margin-bottom: 10px; }
    .sc-prob { font-size: 14px; padding: 2px 8px; border-radius: 20px; color: #ffffff; }
    .bg-major { background-color: #10b981; }
    .bg-median { background-color: #f59e0b; }
    .bg-minor { background-color: #ef4444; }
    .social-box { background-color: #f8fafc; border: 1px dashed #cbd5e1; padding: 20px; border-radius: 8px; font-family: monospace; font-size: 13.5px; white-space: pre-wrap; color: #334155; margin-bottom: 25px; line-height: 1.5; }
    """

    html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Analyses & Tendances - {data['subject_title']}</title>
    <style>{style}</style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div style="font-size: 11px; font-weight: 800; letter-spacing: 2px; text-transform: uppercase; margin-bottom: 8px;">MONSIEUR MÉTÉO</div>
            <h1>📊 ÉVOLUTION & TENDANCES MÉTÉO</h1>
            <p>{data['subject_title']} • Analyse du {datetime.datetime.now().strftime('%d/%m/%Y')}</p>
        </div>
        <div class="content">
            
            <div class="section-title">📰 PROPOSITION DE POST LINKEDIN (SANS MARKDOWN)</div>
            <div class="social-box">{linkedin_post_clean}</div>
            
            <div class="section-title">🔮 LES 3 SCÉNARIOS DE PROBABILITÉS</div>
            
            <div class="scenario-card sc-major">
                <div class="sc-title">
                    <span>🟢 SCÉNARIO MAJORITAIRE</span>
                    <span class="sc-prob bg-major">{data['scenarios']['majoritaire']['prob']}</span>
                </div>
                <p style="margin: 0; font-size: 13.5px; line-height: 1.6; text-align: justify;">{data['scenarios']['majoritaire']['desc']}</p>
            </div>
            
            <div class="scenario-card sc-median">
                <div class="sc-title">
                    <span>🟡 SCÉNARIO MÉDIAN</span>
                    <span class="sc-prob bg-median">{data['scenarios']['median']['prob']}</span>
                </div>
                <p style="margin: 0; font-size: 13.5px; line-height: 1.6; text-align: justify;">{data['scenarios']['median']['desc']}</p>
            </div>
            
            <div class="scenario-card sc-minor">
                <div class="sc-title">
                    <span>🔴 SCÉNARIO MINORITAIRE</span>
                    <span class="sc-prob bg-minor">{data['scenarios']['minoritaire']['prob']}</span>
                </div>
                <p style="margin: 0; font-size: 13.5px; line-height: 1.6; text-align: justify;">{data['scenarios']['minoritaire']['desc']}</p>
            </div>
            
            {html_images_block}
            
        </div>
    </div>
</body>
</html>
"""

    html_path = "bulletin_infoclimat.html"
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html)
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
    subject = f"Analyses & Tendances Meteo - {data['subject_title']}"
    filename = f"analyse_infoclimat_{datetime.datetime.now().strftime('%Y_%m_%d')}.html"
    
    html_b64 = base64.b64encode(html.encode('utf-8')).decode('ascii')
    text_body = f"Bonjour,\n\nVeuillez trouver ci-joint l'analyse des tendances et de l'évolution météo à long terme issue du forum Infoclimat pour : {data['subject_title']}.\n\nLe rapport HTML contenant le post LinkedIn rédigé ainsi que les graphiques joints est attaché à ce message.\n\nCordialement,\nMonsieur Météo"
    text_b64 = base64.b64encode(text_body.encode('utf-8')).decode('ascii')
    boundary = uuid.uuid4().hex
    
    raw_message = (
        f'From: Monsieur Meteo <{sender}>\r\n'
        f'To: {", ".join(recipients)}\r\n'
        f'Subject: {subject}\r\n'
        f'Date: {formatdate(localtime=True)}\r\n'
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
