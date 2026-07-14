import urllib.request
import xml.etree.ElementTree as ET
import base64
import re

url = "https://news.google.com/rss/search?q=meteo&hl=fr&gl=FR&ceid=FR:fr"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req) as response:
    xml_data = response.read()

root = ET.fromstring(xml_data)
for item in root.findall(".//item")[:5]:
    link = item.find("link").text
    print("Original Link:", link)
    
    # Extract base64 part
    # Format: https://news.google.com/rss/articles/CBMi...
    m = re.search(r'/articles/([^?]+)', link)
    if m:
        b64_str = m.group(1)
        # Pad base64 if needed
        padded = b64_str + '=' * (-len(b64_str) % 4)
        try:
            decoded_bytes = base64.b64decode(padded)
            # Try to decode as utf-8 or latin-1
            print("Decoded string (raw):", decoded_bytes[:100])
            # Let's search for http or https in the decoded bytes
            decoded_str = decoded_bytes.decode('utf-8', errors='ignore')
            print("Decoded string (unicode):", decoded_str[:150])
            # Find the actual URL
            url_match = re.search(r'(https?://[^\s\x00-\x1f\x7f-\xff]+)', decoded_str)
            if url_match:
                print("Extracted Real URL:", url_match.group(1))
            else:
                print("No HTTP URL found in decoded bytes.")
        except Exception as e:
            print("Decoding failed:", e)
    print("-" * 50)
