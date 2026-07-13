# -*- coding: utf-8 -*-
"""
generate_vigilance_twitter.py
Captures the vigilance map from the minisite, styles it with the Monsieur Météo
visual identity (framed header, logo, bottom signature bar, and custom styled alert cards),
and overlays it onto the custom background.
"""
import os
import sys
import time
import base64
from PIL import Image

def log(msg):
    print(f"[VIGILANCE TWITTER] {msg}")

def capture_and_compose_vigilance_twitter(period, output_path):
    url = f"https://minisite-douai.vercel.app/vigilance?period={period}"
    
    log(f"Starting capture for period {period} (URL: {url})...")
    
    # Read and convert logo to Base64 to bypass HTTPS local file loading restriction
    script_dir = os.path.dirname(os.path.abspath(__file__))
    logo_path = os.path.join(script_dir, "logo_mm.png")
    if not os.path.exists(logo_path):
        logo_path = r"C:\Users\grego\Documents\METEO_CLIMAT\meteo cnews 2\logo_mm.png"
    logo_data_url = ""
    if os.path.exists(logo_path):
        try:
            with open(logo_path, "rb") as f:
                logo_base64 = base64.b64encode(f.read()).decode("utf-8")
            logo_data_url = f"data:image/png;base64,{logo_base64}"
            log("Successfully encoded logo to Base64.")
        except Exception as e:
            log(f"Warning: Could not base64 encode logo: {e}")
    else:
        log(f"Warning: Logo file not found at {logo_path}")
        
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        log("Error: Playwright is not installed.")
        return False
        
    temp_png = output_path.replace(".jpg", "_temp.png")
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            # Force landscape viewport (1920x1080)
            page.set_viewport_size({"width": 1920, "height": 1080})
            page.goto(url, wait_until="networkidle")
            
            try:
                page.wait_for_selector(".social-fb-container[data-ready='true']", state="attached", timeout=15000)
            except Exception as e:
                log(f"Warning: Timeout waiting for data-ready: {e}")
                
            time.sleep(1.5)
            
            # Inject our custom Monsieur Météo Visual Identity Layout
            page.evaluate('''({ logoUrl }) => {
                let originalSvg = document.querySelector('svg.fb-svg-map');
                if (originalSvg) {
                    let paths = originalSvg.querySelectorAll('path');
                    paths.forEach(p => {
                        let key = Object.keys(p).find(k => k.startsWith('__reactFiber') || k.startsWith('__reactInternalInstance'));
                        if (key && p[key] && p[key].key) {
                            p.setAttribute('data-dep', p[key].key);
                        }
                    });
                }
                
                let svgContent = originalSvg ? originalSvg.innerHTML : '';
                let svgViewBox = originalSvg ? (originalSvg.getAttribute('viewBox') || '0 0 1100 1100') : '0 0 1100 1100';
                
                let el = document.querySelector('.bulletin-auto-card .bulletin-text-display') || document.querySelector('.region-hub-bulletin pre');
                let rawText = el ? el.innerText : "";
                
                let lines = rawText.split('\\n');
                let dateSub = "VIGILANCE MÉTÉOROLOGIQUE";
                let firstLine = lines[0] || "";
                if (firstLine.includes('📋')) {
                    let cleaned = firstLine.replace('📋 ', '').trim();
                    if (cleaned.includes(' DU ')) {
                        let parts = cleaned.split(' DU ');
                        dateSub = parts[1].trim();
                    }
                }
                
                // Parse risks
                let phenomCards = [];
                const getPhenomIcon = (name) => {
                    let n = name.toLowerCase();
                    if (n.includes('canicule') || n.includes('chaleur')) {
                        return `<svg viewBox="0 0 24 24" width="34" height="34" stroke="currentColor" stroke-width="2.5" fill="none" stroke-linecap="round" stroke-linejoin="round"><path d="M14 4v10.54a4 4 0 1 1-4 0V4a2 2 0 0 1 4 0Z"/><path d="M12 9v2"/><path d="M12 12v.01"/></svg>`;
                    } else if (n.includes('forêt') || n.includes('foret') || n.includes('feux') || n.includes('incendie')) {
                        return `<svg viewBox="0 0 24 24" width="34" height="34" stroke="currentColor" stroke-width="2.5" fill="none" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2c0 4-3 5-3 8a3 3 0 0 0 6 0c0-3-3-4-3-8Z"/><path d="M12 22a4 4 0 0 0 4-4c0-3-2-3-2-5"/></svg>`;
                    } else if (n.includes('orage')) {
                        return `<svg viewBox="0 0 24 24" width="34" height="34" stroke="currentColor" stroke-width="2.5" fill="none" stroke-linecap="round" stroke-linejoin="round"><path d="M19 16.9A5 5 0 0 0 18 7h-1.26a8 8 0 1 0-11.62 9"/><path d="m13 11-4 6h6l-4 6"/></svg>`;
                    } else if (n.includes('pluie') || n.includes('inondation') || n.includes('précipitation') || n.includes('averse')) {
                        return `<svg viewBox="0 0 24 24" width="34" height="34" stroke="currentColor" stroke-width="2.5" fill="none" stroke-linecap="round" stroke-linejoin="round"><path d="M16 13v8"/><path d="M8 13v8"/><path d="M12 15v8"/><path d="M20 16.58A5 5 0 0 0 18 7h-1.26A8 8 0 1 0 4 15.25"/></svg>`;
                    } else if (n.includes('crue') || n.includes('débordement')) {
                        return `<svg viewBox="0 0 24 24" width="34" height="34" stroke="currentColor" stroke-width="2.5" fill="none" stroke-linecap="round" stroke-linejoin="round"><path d="M2 6c.6.5 1.2 1 2.5 1C7 7 7 5 9.5 5c2.6 0 2.4 2 5 2 2.5 0 2.5-2 5-2 1.3 0 1.9.5 2.5 1"/><path d="M2 12c.6.5 1.2 1 2.5 1 2.5 0 2.5-2 5-2 2.6 0 2.4 2 5 2 2.5 0 2.5-2 5-2 1.3 0 1.9.5 2.5 1"/></svg>`;
                    } else if (n.includes('vent') || n.includes('tempête') || n.includes('rafale')) {
                        return `<svg viewBox="0 0 24 24" width="34" height="34" stroke="currentColor" stroke-width="2.5" fill="none" stroke-linecap="round" stroke-linejoin="round"><path d="M17.7 7.7a2.5 2.5 0 1 1 1.8 4.3H2"/><path d="M9.6 4.6A2 2 0 1 1 11 8H2"/><path d="M12.6 19.4A2 2 0 1 0 14 16H2"/></svg>`;
                    } else if (n.includes('neige') || n.includes('verglas') || n.includes('gel')) {
                        return `<svg viewBox="0 0 24 24" width="34" height="34" stroke="currentColor" stroke-width="2.5" fill="none" stroke-linecap="round" stroke-linejoin="round"><path d="M2 12h20"/><path d="M12 2v20"/><path d="m4.93 4.93 14.14 14.14"/><path d="m19.07 4.93-14.14 14.14"/></svg>`;
                    } else if (n.includes('froid')) {
                        return `<svg viewBox="0 0 24 24" width="34" height="34" stroke="currentColor" stroke-width="2.5" fill="none" stroke-linecap="round" stroke-linejoin="round"><path d="M14 4v10.54a4 4 0 1 1-4 0V4a2 2 0 0 1 4 0Z"/><path d="m20 4-4 4"/><path d="m16 4 4 4"/><path d="m20 12-4 4"/><path d="m16 12 4 4"/></svg>`;
                    } else {
                        return `<svg viewBox="0 0 24 24" width="34" height="34" stroke="currentColor" stroke-width="2.5" fill="none" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>`;
                    }
                };

                // Check Rouge
                lines.filter(l => l.includes('🔴 Vigilance ROUGE')).forEach(l => {
                    let parts = l.split('–');
                    if (parts.length >= 2) {
                        let phenomName = parts[1].split(':')[0].trim();
                        let deptsStr = parts[1].split(':')[1] || "";
                        let count = deptsStr.split(/,| et /).filter(s => s.trim().length > 0).length;
                        if (count > 0) {
                            phenomCards.push({
                                level: 'ROUGE', levelLabel: 'VIGILANCE ROUGE',
                                color: '#ef4444', textColor: '#ffffff', themeClass: 'red-theme',
                                phenom: phenomName.toUpperCase(),
                                detail: `${count} DÉPARTEMENT${count > 1 ? 'S' : ''}`,
                                icon: getPhenomIcon(phenomName)
                            });
                        }
                    }
                });

                // Check Orange
                lines.filter(l => l.includes('🟠 Vigilance ORANGE')).forEach(l => {
                    let parts = l.split('–');
                    if (parts.length >= 2) {
                        let phenomName = parts[1].split(':')[0].trim();
                        let deptsStr = parts[1].split(':')[1] || "";
                        let count = deptsStr.split(/,| et /).filter(s => s.trim().length > 0).length;
                        if (count > 0) {
                            phenomCards.push({
                                level: 'ORANGE', levelLabel: 'VIGILANCE ORANGE',
                                color: '#f97316', textColor: '#ffffff', themeClass: 'orange-theme',
                                phenom: phenomName.toUpperCase(),
                                detail: `${count} DÉPARTEMENT${count > 1 ? 'S' : ''}`,
                                icon: getPhenomIcon(phenomName)
                            });
                        }
                    }
                });

                // Check Jaune
                lines.filter(l => l.includes('🟡 Vigilance JAUNE')).forEach(l => {
                    let parts = l.split('–');
                    if (parts.length >= 2) {
                        let summaryStr = parts[1].trim().replace(/\\.$/, '');
                        let subParts = summaryStr.split(/, | et /i).filter(s => s.trim().length > 0);
                        subParts.forEach(part => {
                            part = part.trim();
                            if (part.length === 0) return;
                            let match = part.match(/^(.*?)\s+pour\s+(\d+)\s+département/i);
                            let mainPhenom = match ? match[1].toUpperCase() : part.toUpperCase();
                            let mainCount = match ? `${match[2]} DÉPARTEMENT${parseInt(match[2]) > 1 ? 'S' : ''}` : "";
                            
                            phenomCards.push({
                                level: 'JAUNE', levelLabel: 'VIGILANCE JAUNE',
                                color: '#fbbf24', textColor: '#1e293b', themeClass: 'yellow-theme',
                                phenom: mainPhenom.trim(),
                                detail: mainCount.trim(),
                                icon: getPhenomIcon(mainPhenom.trim())
                            });
                        });
                    }
                });

                if (phenomCards.length === 0) {
                    phenomCards.push({
                        level: 'VERT', levelLabel: 'SITUATION CALME',
                        color: '#10b981', textColor: '#ffffff', themeClass: 'green-theme',
                        phenom: 'PAS DE VIGILANCE PARTICULIÈRE',
                        detail: '',
                        icon: `<svg viewBox="0 0 24 24" width="34" height="34" stroke="currentColor" stroke-width="2.5" fill="none" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>`
                    });
                }

                // Hide everything
                document.querySelectorAll('body > *, #root > *').forEach(e => {
                    e.style.display = 'none';
                });

                // Clear body backgrounds for transparency overlay
                let style = document.createElement('style');
                style.innerHTML = `
                    html, body, #root, .app-layout, .main-content, .vigilance-container, .social-fb-container {
                        background: transparent !important;
                        background-color: transparent !important;
                        background-image: none !important;
                    }
                    svg.fb-svg-map path {
                        stroke: transparent !important;
                    }
                    svg.fb-svg-map path[fill="#34d399"]:not([data-dep="2A"]):not([data-dep="2B"]),
                    svg.fb-svg-map path[fill="#10b981"]:not([data-dep="2A"]):not([data-dep="2B"]),
                    svg.fb-svg-map path[fill="#22c55e"]:not([data-dep="2A"]):not([data-dep="2B"]),
                    svg.fb-svg-map path[fill="#34c759"]:not([data-dep="2A"]):not([data-dep="2B"]) {
                        fill: transparent !important;
                    }
                    svg.fb-svg-map path[data-dep="2A"][fill="#34d399"],
                    svg.fb-svg-map path[data-dep="2A"][fill="#10b981"],
                    svg.fb-svg-map path[data-dep="2A"][fill="#22c55e"],
                    svg.fb-svg-map path[data-dep="2A"][fill="#34c759"],
                    svg.fb-svg-map path[data-dep="2B"][fill="#34d399"],
                    svg.fb-svg-map path[data-dep="2B"][fill="#10b981"],
                    svg.fb-svg-map path[data-dep="2B"][fill="#22c55e"],
                    svg.fb-svg-map path[data-dep="2B"][fill="#34c759"] {
                        fill: #10b981 !important;
                        stroke: #1e293b !important;
                        stroke-width: 1.2px !important;
                    }
                    svg.fb-svg-map path[fill*="ff9"], 
                    svg.fb-svg-map path[fill*="ffa"], 
                    svg.fb-svg-map path[fill*="f97"],
                    svg.fb-svg-map path[fill*="fbc"],
                    svg.fb-svg-map path[fill*="ffc"],
                    svg.fb-svg-map path[fill*="eab"],
                    svg.fb-svg-map path[fill*="f59"],
                    svg.fb-svg-map path[fill*="ef4"],
                    svg.fb-svg-map path[fill*="d32"] {
                        stroke: rgba(0, 0, 0, 0.3) !important;
                        stroke-width: 1.5px !important;
                    }
                `;
                document.head.appendChild(style);

                // Build cards list
                let cardsHtml = `<div style="display: flex; flex-direction: column; gap: 20px; width: 100%;">`;
                phenomCards.forEach(c => {
                    let cleanDetail = c.detail.replace(/^(pour\s+|de\s+)/i, '');
                    cardsHtml += `
                        <div style="background: linear-gradient(135deg, rgba(12, 22, 48, 0.96) 0%, rgba(6, 12, 28, 0.99) 100%); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 20px; padding: 20px 25px; display: flex; align-items: center; gap: 20px; box-shadow: 0 15px 35px rgba(0,0,0,0.55); position: relative; overflow: hidden;">
                            <!-- Top accent bar -->
                            <div style="position: absolute; top: 0; left: 0; right: 0; height: 3px; background: ${c.color};"></div>
                            
                            <!-- Icon -->
                            <div style="width: 60px; height: 60px; border: 2.5px solid ${c.color}; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: ${c.color}; background: rgba(0,0,0,0.4); flex-shrink: 0;">
                                ${c.icon}
                            </div>
                            <!-- Text content -->
                            <div style="flex: 1; display: flex; flex-direction: column; justify-content: center; gap: 4px; font-family: 'Outfit', sans-serif;">
                                <div style="color: ${c.color}; font-weight: 800; font-size: 15px; text-transform: uppercase; letter-spacing: 1px;">
                                    ${c.levelLabel}
                                </div>
                                <div style="color: #ffffff; font-weight: 800; font-size: 24px; line-height: 1.2; text-shadow: 0 2px 4px rgba(0,0,0,0.5);">
                                    <span style="text-transform: uppercase;">${c.phenom}</span>
                                    ${cleanDetail ? ` : <span style="text-transform: uppercase; font-weight: 700; color: #cbd5e1;">${cleanDetail}</span>` : ''}
                                </div>
                            </div>
                        </div>
                    `;
                });
                cardsHtml += `</div>`;

                let container = document.createElement('div');
                container.id = 'tv-studio-container';
                container.style.cssText = `
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 1920px;
                    height: 1080px;
                    background: transparent !important;
                    z-index: 9999999;
                    overflow: hidden;
                    font-family: 'Outfit', sans-serif;
                `;

                // Recreate the layout inside the container
                container.innerHTML = `
                    <!-- Logo container (using dynamic Base64 source) -->
                    <div style="position: absolute; top: 40px; left: 60px; z-index: 9999;">
                        <img src="${logoUrl}" style="height: 95px; filter: drop-shadow(0 4px 15px rgba(0, 210, 255, 0.25)) drop-shadow(0 2px 6px rgba(0,0,0,0.5));">
                    </div>

                    <!-- Framed Header matching Twitter Debrief -->
                    <div style="position: absolute; top: 25px; left: 50%; transform: translateX(-50%); width: 1200px; text-align: center; background: linear-gradient(180deg, rgba(10, 18, 40, 0.95) 0%, rgba(6, 11, 25, 0.98) 100%); border: 1px solid rgba(239, 68, 68, 0.4); border-radius: 20px; padding: 10px 40px; box-shadow: 0 12px 35px rgba(0, 0, 0, 0.65), inset 0 1px 0 rgba(255, 255, 255, 0.05); display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 0px; z-index: 20;">
                        <h1 style="font-size: 46px; font-weight: 800; text-transform: uppercase; letter-spacing: 0.5px; color: #ef4444; text-shadow: 0 2px 10px rgba(0, 0, 0, 0.6); margin: 0; line-height: 1.1;">VIGILANCE MÉTÉO FRANCE</h1>
                        <div style="font-size: 21px; font-weight: 600; color: #00d2ff; text-transform: uppercase; letter-spacing: 3px; text-shadow: 0 1px 4px rgba(0, 0, 0, 0.4); opacity: 0.95; margin-top: 2px;">${dateSub.toUpperCase()}</div>
                    </div>

                    <!-- Map container (positioned on left) -->
                    <div style="position: absolute; left: 30px; top: 120px; width: 950px; height: 950px; display: flex; align-items: center; justify-content: center; z-index: 10;">
                        <svg class="fb-svg-map" viewBox="${svgViewBox}" style="width: 100%; height: 100%; filter: drop-shadow(0 20px 35px rgba(0,0,0,0.75));">
                            ${svgContent}
                        </svg>
                    </div>

                    <!-- Alert Cards container (positioned on right) -->
                    <div style="position: absolute; left: 1040px; top: 180px; width: 820px; display: flex; flex-direction: column; z-index: 20; height: 800px; justify-content: center;">
                        ${cardsHtml}
                    </div>

                    <!-- Signature at the bottom -->
                    <div style="position: absolute; bottom: 0; left: 0; width: 100%; height: 6px; background: linear-gradient(90deg, #ef4444 0%, #f97316 50%, #00d2ff 100%); z-index: 999999;"></div>
                `;

                document.body.appendChild(container);
            }''', {"logoUrl": logo_data_url})
            
            # Save the transparent overlay screenshot
            page.screenshot(path=temp_png, omit_background=True)
            browser.close()
            
        # Composite with PIL on top of the custom background
        script_dir = os.path.dirname(os.path.abspath(__file__))
        custom_bg_path = os.path.join(script_dir, "data", "bg_twitter.png")
        if not os.path.exists(custom_bg_path):
            custom_bg_path = r"C:\Users\grego\.gemini\config\skills\twitter\data\bg_twitter.png"
            if not os.path.exists(custom_bg_path):
                # Fallback to general landscape bg if not copied yet
                custom_bg_path = r"C:\Users\grego\Documents\METEO_CLIMAT\meteo cnews 2\bg_landscape.png"
            
        if os.path.exists(custom_bg_path):
            log(f"Composing overlay on top of custom background: {custom_bg_path}")
            bg = Image.open(custom_bg_path).convert("RGBA").resize((1920, 1080), Image.Resampling.LANCZOS)
        else:
            log("Warning: background not found, using dark fallback")
            bg = Image.new("RGBA", (1920, 1080), (5, 12, 28, 255))
            
        overlay_img = Image.open(temp_png).convert("RGBA")
        final_img = Image.alpha_composite(bg, overlay_img).convert("RGB")
        
        final_img.save(output_path, "JPEG", quality=92)
        log(f"Vigilance map successfully saved to: {output_path}")
        
        # Clean up temp png
        if os.path.exists(temp_png):
            os.remove(temp_png)
            
        return True
    except Exception as e:
        log(f"Error capturing/composing vigilance: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--period", type=int, default=0, help="0=Today, 1=Tomorrow")
    parser.add_argument("--output", type=str, required=True, help="Destination path")
    args = parser.parse_args()
    
    capture_and_compose_vigilance_twitter(args.period, args.output)
