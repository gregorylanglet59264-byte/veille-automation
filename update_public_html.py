import os
import re

nav_nat = '<div style="background:#0d2f4f; padding:12px 20px; text-align:center; color:white; font-family:Inter, ui-sans-serif, sans-serif; font-size:14px; font-weight:700; border-bottom:3px solid #1ea7c9; display:flex; justify-content:center; align-items:center; gap:8px; flex-wrap:wrap;"><span style="opacity:0.85; font-size:13px; text-transform:uppercase; letter-spacing:0.5px;">🌐 Bulletins :</span><a href="index.html" style="color:white; text-decoration:none; padding:6px 12px; background:#1565d8; border-radius:8px; border:1px solid rgba(255,255,255,0.2);">🇫🇷 Prev Nat</a><a href="hdf.html" style="color:white; text-decoration:none; padding:6px 12px; background:rgba(255,255,255,0.12); border-radius:8px; border:1px solid rgba(255,255,255,0.2);">📍 Prev HDF</a><a href="bulletin_national.html" style="color:white; text-decoration:none; padding:6px 12px; background:#0284c7; border-radius:8px; border:1px solid rgba(255,255,255,0.2); font-weight:800;">🌊 Nat (Terre+Mer+Plages)</a><a href="bulletin_hdf.html" style="color:white; text-decoration:none; padding:6px 12px; background:#0284c7; border-radius:8px; border:1px solid rgba(255,255,255,0.2); font-weight:800;">🌾 HDF (Terre+Mer+Plages)</a><a href="bulletin_npdc.html" style="color:white; text-decoration:none; padding:6px 12px; background:#0284c7; border-radius:8px; border:1px solid rgba(255,255,255,0.2); font-weight:800;">⚓ NPDC (Terre+Mer+Plages)</a><a href="sources_national.md" download style="color:white; text-decoration:none; padding:6px 10px; background:#d97706; border-radius:8px; font-size:12px;">Sources Nat</a><a href="sources_hdf.md" download style="color:white; text-decoration:none; padding:6px 10px; background:#d97706; border-radius:8px; font-size:12px;">Sources HDF</a></div>'

nav_hdf = '<div style="background:#0d2f4f; padding:12px 20px; text-align:center; color:white; font-family:Inter, ui-sans-serif, sans-serif; font-size:14px; font-weight:700; border-bottom:3px solid #1ea7c9; display:flex; justify-content:center; align-items:center; gap:8px; flex-wrap:wrap;"><span style="opacity:0.85; font-size:13px; text-transform:uppercase; letter-spacing:0.5px;">🌐 Bulletins :</span><a href="index.html" style="color:white; text-decoration:none; padding:6px 12px; background:rgba(255,255,255,0.12); border-radius:8px; border:1px solid rgba(255,255,255,0.2);">🇫🇷 Prev Nat</a><a href="hdf.html" style="color:white; text-decoration:none; padding:6px 12px; background:#1565d8; border-radius:8px; border:1px solid rgba(255,255,255,0.2);">📍 Prev HDF</a><a href="bulletin_national.html" style="color:white; text-decoration:none; padding:6px 12px; background:#0284c7; border-radius:8px; border:1px solid rgba(255,255,255,0.2); font-weight:800;">🌊 Nat (Terre+Mer+Plages)</a><a href="bulletin_hdf.html" style="color:white; text-decoration:none; padding:6px 12px; background:#0284c7; border-radius:8px; border:1px solid rgba(255,255,255,0.2); font-weight:800;">🌾 HDF (Terre+Mer+Plages)</a><a href="bulletin_npdc.html" style="color:white; text-decoration:none; padding:6px 12px; background:#0284c7; border-radius:8px; border:1px solid rgba(255,255,255,0.2); font-weight:800;">⚓ NPDC (Terre+Mer+Plages)</a><a href="sources_hdf.md" download style="color:white; text-decoration:none; padding:6px 10px; background:#d97706; border-radius:8px; font-size:12px;">Sources HDF</a><a href="sources_national.md" download style="color:white; text-decoration:none; padding:6px 10px; background:#d97706; border-radius:8px; font-size:12px;">Sources Nat</a></div>'

if os.path.exists('public/index.html'):
    with open('public/index.html', 'r', encoding='utf-8') as f:
        html = f.read()
    html = re.sub(r'<div style="background:#0d2f4f;.*?</div>', nav_nat, html, count=1, flags=re.DOTALL)
    with open('public/index.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print('UPDATED PUBLIC/INDEX.HTML NAVBAR')

if os.path.exists('public/hdf.html'):
    with open('public/hdf.html', 'r', encoding='utf-8') as f:
        html = f.read()
    html = re.sub(r'<div style="background:#0d2f4f;.*?</div>', nav_hdf, html, count=1, flags=re.DOTALL)
    with open('public/hdf.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print('UPDATED PUBLIC/HDF.HTML NAVBAR')
