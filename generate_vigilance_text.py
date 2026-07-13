# -*- coding: utf-8 -*-
"""
generate_vigilance_text.py
Fetches vigilance-accessible from Météo-France, extracts counts & risks for J0/J+1,
and formats the Twitter/X post text according to the user's requested template structure.
"""
import os
import sys
import argparse
import re
import urllib.request
from html.parser import HTMLParser

class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text_content = []
        self.in_script = False
        self.in_style = False

    def handle_starttag(self, tag, attrs):
        if tag in ['script', 'style']:
            setattr(self, f"in_{tag}", True)

    def handle_endtag(self, tag):
        if tag in ['script', 'style']:
            setattr(self, f"in_{tag}", False)

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

def get_departments_vigilance(period):
    url = "https://vigilance.meteofrance.fr/fr/vigilance-accessible"
    try:
        html_content = fetch_html(url)
        parser = TextExtractor()
        parser.feed(html_content)
        lines = [line.strip() for line in parser.text_content]
        
        headers_indices = [i for i, line in enumerate(lines) if "Vigilance météo et crues pour" in line]
        if not headers_indices:
            return None
            
        # Target period (0 for today, 1 for tomorrow)
        idx = headers_indices[period] if period < len(headers_indices) else headers_indices[0]
        day_title = lines[idx]
        
        end_idx = headers_indices[period+1] if period + 1 < len(headers_indices) else len(lines)
        day_lines = lines[idx:end_idx]
        
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
            
        return {
            "title": day_title,
            "colors": colors
        }
    except Exception as e:
        print(f"Error fetching vigilance: {e}", file=sys.stderr)
        return None

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--period", type=int, default=0, help="0 for today, 1 for tomorrow")
    parser.add_argument("--output", required=True, help="Output file path for the text post")
    args = parser.parse_args()

    data = get_departments_vigilance(args.period)
    if not data:
        print("Error: Could not retrieve vigilance data.", file=sys.stderr)
        sys.exit(1)

    title = data["title"] # e.g. "Vigilance météo et crues pour le lundi 13 juillet 2026"
    # Extract date part
    date_match = re.search(r"pour (le\s+.*)$", title, re.IGNORECASE)
    date_str = date_match.group(1).upper() if date_match else "CE JOUR"

    colors = data["colors"]
    
    # Count unique departments in Rouge / Orange and map phenomena to department counts
    rouge_depts = set()
    orange_depts = set()
    
    # Map: phenom -> { "Rouge": [depts], "Orange": [depts] }
    phenom_map = {}
    
    for phenom, depts in colors.get("Rouge", {}).items():
        for d in depts:
            # Clean dept name, e.g. "Nord (59)" -> extract name or code
            m = re.search(r'^(.*?)\s*\(', d)
            dept_name = m.group(1).strip() if m else d
            rouge_depts.add(dept_name)
            phenom_map.setdefault(phenom, {"Rouge": set(), "Orange": set()})["Rouge"].add(dept_name)
            
    for phenom, depts in colors.get("Orange", {}).items():
        for d in depts:
            m = re.search(r'^(.*?)\s*\(', d)
            dept_name = m.group(1).strip() if m else d
            orange_depts.add(dept_name)
            phenom_map.setdefault(phenom, {"Rouge": set(), "Orange": set()})["Orange"].add(dept_name)

    num_rouge = len(rouge_depts)
    num_orange = len(orange_depts)

    # Collect active risks and hashtags
    active_risks = list(phenom_map.keys())
    hashtags = ["#Meteo", "#Vigilance"]
    for r in active_risks:
        hashtag = "#" + "".join(r.split())
        if hashtag not in hashtags:
            hashtags.append(hashtag)

    # Format the header
    header_title = f"⚠️ VIGILANCE MÉTÉOROLOGIQUE - {date_str}"
    
    # Active vigilance summary
    vigilance_summary = []
    
    # Rouge
    rouge_line = f"🔴 {num_rouge} département(s) en vigilance Rouge"
    if num_rouge > 0:
        # Group phenomena
        rouge_p = [p for p, data in phenom_map.items() if data["Rouge"]]
        rouge_line += f" ({', '.join(rouge_p)})"
    vigilance_summary.append(rouge_line)
        
    # Orange
    orange_line = f"orange" # fallback
    orange_line = f"🟠 {num_orange} département(s) en vigilance Orange"
    if num_orange > 0:
        orange_p = [p for p, data in phenom_map.items() if data["Orange"]]
        orange_line += f" ({', '.join(orange_p)})"
    vigilance_summary.append(orange_line)

    # Details of risks
    risk_details = []
    for phenom, data in phenom_map.items():
        r_count = len(data["Rouge"])
        o_count = len(data["Orange"])
        
        detail_parts = []
        if r_count > 0:
            detail_parts.append(f"{r_count} dpt(s) en Rouge")
        if o_count > 0:
            detail_parts.append(f"{o_count} en Orange")
            
        risk_details.append(f"- {phenom} : {', '.join(detail_parts)}")

    if not risk_details:
        risk_details.append("- Pas de vigilance particulière signalée.")

    # Assemble the final tweet text
    tweet_lines = [
        header_title,
        "",
        "La vigilance nationale est active :",
        "\n".join(vigilance_summary),
        "",
        "Détail des risques :",
        "\n".join(risk_details),
        "",
        "Pour plus de détails et pour suivre l'évolution, consultez directement le site officiel :",
        "👉 https://vigilance.meteofrance.fr/fr",
        "",
        " ".join(hashtags)
    ]
    
    tweet_text = "\n".join(tweet_lines)
    
    # Enforce character count warning if > 280 (X standard)
    if len(tweet_text) > 280:
        print(f"Warning: Tweet length is {len(tweet_text)} chars (exceeds 280 standard limit). Truncating details to fit.")
        # If too long, we keep only summary and remove details
        tweet_lines = [
            header_title,
            "",
            "La vigilance nationale est active :",
            "\n".join(vigilance_summary),
            "",
            "Pour plus de détails et pour suivre l'évolution, consultez directement le site officiel :",
            "👉 https://vigilance.meteofrance.fr/fr",
            "",
            " ".join(hashtags)
        ]
        tweet_text = "\n".join(tweet_lines)

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(tweet_text)

    print(f"Vigilance tweet text generated successfully: {args.output}")
    print(tweet_text)

if __name__ == "__main__":
    main()
