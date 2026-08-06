import re
files = [
    'scripts/generate_bulletins_html.py',
    'scripts/meteo_marine_tides.py',
    'run_infoclimat.py',
    'multi_source_enricher.py',
]
all_urls = set()
for fn in files:
    try:
        c = open(fn, encoding='utf-8').read()
        urls = re.findall(r"https?://[^\s\"'\\<>)]+", c)
        for u in urls:
            all_urls.add((fn.split('/')[-1], u))
    except:
        pass
for fn, u in sorted(all_urls):
    print(f"{fn}: {u}")
