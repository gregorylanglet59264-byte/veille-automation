import re

def md_to_html(md):
    if not md:
        return ""
    lines = md.split('\n')
    out = []
    in_table = False
    table_lines = []
    
    def flush_table(t_lines):
        if not t_lines:
            return ''
        h = '<table class="data-table"><thead>'
        t_lines = [l for l in t_lines if not re.match(r'^\s*\|?\s*:?-+:?\s*\|', l)]
        for idx, line in enumerate(t_lines):
            cells = [c.strip() for c in line.strip('|').split('|')]
            tag = 'th' if idx == 0 else 'td'
            row_html = ''.join(f'<{tag}>{c}</{tag}>' for c in cells)
            if idx == 0:
                h += f'<tr>{row_html}</tr></thead><tbody>'
            else:
                h += f'<tr>{row_html}</tr>'
        h += '</tbody></table>'
        return h

    in_list = False
    for line in lines:
        l = line.strip()
        if l.startswith('|'):
            if in_list:
                out.append('</ul>')
                in_list = False
            table_lines.append(l)
            in_table = True
            continue
        elif in_table:
            out.append(flush_table(table_lines))
            table_lines = []
            in_table = False
            
        if not l:
            if in_list:
                out.append('</ul>')
                in_list = False
            continue
        elif l.startswith('### '):
            if in_list: out.append('</ul>'); in_list = False
            out.append(f'<h3 style="color:var(--primary); margin-top:16px; font-size:1.1em;">{l[4:]}</h3>')
        elif l.startswith('## '):
            if in_list: out.append('</ul>'); in_list = False
            out.append(f'<h2 style="color:var(--text); border-bottom:1px solid var(--border); padding-bottom:6px; margin-top:24px; font-size:1.3em;">{l[3:]}</h2>')
        elif l.startswith('# '):
            if in_list: out.append('</ul>'); in_list = False
            out.append(f'<h1 style="color:var(--primary); margin-bottom:12px; font-size:1.6em;">{l[2:]}</h1>')
        elif l.startswith('> '):
            if in_list: out.append('</ul>'); in_list = False
            txt = l[2:].replace('[!IMPORTANT]', '⚠️').replace('[!NOTE]', 'ℹ️').replace('[!WARNING]', '⚠️')
            out.append(f'<div class="alert-box" style="margin:10px 0;"><p>{txt}</p></div>')
        elif l.startswith('- ') or l.startswith('* '):
            if not in_list:
                out.append('<ul style="padding-left:20px; margin-bottom:12px;">')
                in_list = True
            out.append(f'<li>{l[2:]}</li>')
        else:
            if in_list:
                out.append('</ul>')
                in_list = False
            out.append(f'<p style="margin-bottom:8px; line-height:1.6;">{l}</p>')

    if in_list:
        out.append('</ul>')
    if in_table:
        out.append(flush_table(table_lines))
        
    res = '\n'.join(out)
    res = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', res)
    return res

if __name__ == '__main__':
    with open('Hauts-de-France/bulletin_france_premium.md', encoding='utf-8') as f:
        parsed = md_to_html(f.read())
    print("Length of parsed HTML:", len(parsed))
    print(parsed[:800])
