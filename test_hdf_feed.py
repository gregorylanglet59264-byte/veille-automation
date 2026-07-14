import urllib.request
import xml.etree.ElementTree as ET

url = "https://www.lemonde.fr/planete/rss_full_page.xml"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
try:
    with urllib.request.urlopen(req, timeout=10) as response:
        xml_data = response.read()
    root = ET.fromstring(xml_data)
    print("Success! Number of items:", len(root.findall(".//item")))
    for item in root.findall(".//item")[:3]:
        print("Title:", item.find("title").text)
        print("Link:", item.find("link").text)
except Exception as e:
    print("Failed:", e)
