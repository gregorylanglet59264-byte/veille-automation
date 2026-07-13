#!/usr/bin/env python3
"""
Meteo France Data Downloader
Downloads real-time bulletins and media files from the Meteo France Meteotel server.
"""

import os
import re
import base64
import urllib.request
from urllib.parse import urljoin
from datetime import datetime

# Server configuration
BASE_URL = "http://www.meteo.fr/test/meteotel/pics/bul_xml@/bulletins/"
USERNAME = "22SPC"
PASSWORD = "Schapi05"

def get_auth_header():
    auth_str = f"{USERNAME}:{PASSWORD}"
    auth_bytes = auth_str.encode('ascii')
    auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
    return {"Authorization": f"Basic {auth_b64}"}

def fetch_directory_links(url):
    try:
        req = urllib.request.Request(url, headers=get_auth_header())
        with urllib.request.urlopen(req, timeout=15) as response:
            html = response.read().decode('utf-8', errors='ignore')
            links = re.findall(r'href="([^"?]+)"', html)
            return [l for l in links if not l.startswith('/') and l not in ['?C=N;O=D', '?C=M;O=A', '?C=S;O=A', '?C=D;O=A']]
    except Exception as e:
        print(f"[ERROR] Failed to list directory {url}: {e}")
        return []

def download_file(url, output_path):
    try:
        req = urllib.request.Request(url, headers=get_auth_header())
        with urllib.request.urlopen(req, timeout=10) as response:
            data = response.read()
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'wb') as f:
                f.write(data)
            print(f"[SUCCESS] Downloaded: {os.path.basename(output_path)}")
            return True
    except Exception as e:
        print(f"[ERROR] Failed to download {url} -> {output_path}: {e}")
        return False

def download_bulletins(category, output_dir):
    dir_url = urljoin(BASE_URL, f"{category}/")
    print(f"\n--- Scanning {category} at {dir_url} ---")
    
    links = fetch_directory_links(dir_url)
    target_files = []
    for link in links:
        if link.startswith('FYZZ') or link == 'defaut.html':
            continue
        if link.startswith('DEPT') or link == 'ANDORRE' or link == 'CHAINE':
            target_files.append(link)
            
    print(f"Found {len(target_files)} active files to download in {category}.")
    
    success_count = 0
    for filename in target_files:
        file_url = urljoin(dir_url, filename)
        dest_path = os.path.join(output_dir, category, filename)
        if download_file(file_url, dest_path):
            success_count += 1
            
    print(f"Completed {category}: {success_count}/{len(target_files)} successfully downloaded.")

def download_flood_reports(output_dir):
    category = "BPSPC"
    dir_url = urljoin(BASE_URL, f"{category}/")
    print(f"\n--- Scanning flood reports ({category}) at {dir_url} ---")
    
    links = fetch_directory_links(dir_url)
    pdf_files = [l for l in links if l.endswith('.pdf') or (l.startswith('bulletin_crue') and l.endswith('.txt'))]
    print(f"Found {len(pdf_files)} active reports.")
    
    success_count = 0
    for filename in pdf_files:
        file_url = urljoin(dir_url, filename)
        dest_path = os.path.join(output_dir, category, filename)
        if download_file(file_url, dest_path):
            success_count += 1
            
    print(f"Completed BPSPC: {success_count}/{len(pdf_files)} successfully downloaded.")

def download_isobar_media(output_dir):
    category = "MEDIA"
    dir_url = urljoin(BASE_URL, f"{category}/")
    print(f"\n--- Scanning isobar maps & data ({category}) at {dir_url} ---")
    
    links = fetch_directory_links(dir_url)
    media_files = []
    for link in links:
        if (link.startswith('C_') or link.startswith('XML_') or link == 'europe.pdf') and (link.endswith('.jpeg') or link.endswith('.xml') or link.endswith('.pdf')):
            media_files.append(link)
            
    print(f"Found {len(media_files)} active maps and XML data files.")
    
    success_count = 0
    for filename in media_files:
        file_url = urljoin(dir_url, filename)
        dest_path = os.path.join(output_dir, category, filename)
        if download_file(file_url, dest_path):
            success_count += 1
            
    print(f"Completed MEDIA: {success_count}/{len(media_files)} successfully downloaded.")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Meteo France Data Downloader")
    parser.add_argument("-o", "--output", default="./meteo_data", help="Output directory for downloaded data")
    parser.add_argument("--dept", action="store_true", help="Download department bulletins (PREV_XML)")
    parser.add_argument("--mont", action="store_true", help="Download mountain bulletins (MONT_XML)")
    parser.add_argument("--cote", action="store_true", help="Download coastal bulletins (COTE2)")
    parser.add_argument("--floods", action="store_true", help="Download flood PDF reports (BPSPC)")
    parser.add_argument("--maps", action="store_true", help="Download isobar maps & data (MEDIA)")
    parser.add_argument("--all", action="store_true", help="Download everything")
    
    args = parser.parse_args()
    
    # If no flags are set, default to department and coastal bulletins
    if not (args.dept or args.mont or args.cote or args.floods or args.maps or args.all):
        args.dept = True
        args.cote = True
        
    start_time = datetime.now()
    print(f"Starting downloader at {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Target Directory: {os.path.abspath(args.output)}")
    
    if args.all or args.dept:
        download_bulletins("PREV_XML", args.output)
    if args.all or args.mont:
        download_bulletins("MONT_XML", args.output)
    if args.all or args.cote:
        download_bulletins("COTE2", args.output)
    if args.all or args.floods:
        download_flood_reports(args.output)
    if args.all or args.maps:
        download_isobar_media(args.output)
        
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    print(f"\nFinished in {duration:.2f} seconds.")
