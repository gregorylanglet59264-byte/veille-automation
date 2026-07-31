import sys
import os

sys.path.append(r'C:\Users\grego\Documents\METEO_CLIMAT\veille-automation')
import multi_source_enricher

today_str = "Vendredi 31 Juillet 2026"
ms_hdf = multi_source_enricher.get_enriched_sources_context("Hauts-de-France")
ms_nat = multi_source_enricher.get_enriched_sources_context("France")

# Read existing forum comments from sources_raw_hdf.txt
with open(r'C:\Users\grego\Documents\METEO_CLIMAT\veille-automation\sources_raw_hdf.txt', 'r', encoding='utf-8', errors='ignore') as f:
    existing = f.read()

comments_part = ""
if "=== DISCUSSIONS APPLICABLES" in existing:
    comments_part = "=== DISCUSSIONS APPLICABLES" + existing.split("=== DISCUSSIONS APPLICABLES")[1]

hdf_full_header = f"""=== REGISTRE COMPLET DES SOURCES ET DONNÉES BRUTES HAUTS-DE-FRANCE ({today_str}) ===

Date actuelle de génération : {today_str}
Saison en France : ÉTÉ

PÉRIODES EXACTES À RESPECTER IMPÉRATIVEMENT :
- SEMAINE 1 PREVISION : Du Lundi 3 au Dimanche 9 Août 2026
- SEMAINE 2 PREVISION : Du Lundi 10 au Dimanche 16 Août 2026

{ms_hdf}

{comments_part}
"""

with open(r'C:\Users\grego\Documents\METEO_CLIMAT\veille-automation\sources_raw_hdf.txt', 'w', encoding='utf-8') as f:
    f.write(hdf_full_header)

os.makedirs(r'C:\Users\grego\Documents\METEO_CLIMAT\veille-automation\public', exist_ok=True)
with open(r'C:\Users\grego\Documents\METEO_CLIMAT\veille-automation\public\sources_hdf.txt', 'w', encoding='utf-8') as f:
    f.write(hdf_full_header)

print("FORCE WRITE FULL HDF SOURCES SUCCESSFUL! SIZE:", len(hdf_full_header))
