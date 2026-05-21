#!/usr/bin/env python3
import os, subprocess, re

CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
OUT = os.path.expanduser('~/Desktop/LinkGlobe-Posts')
os.makedirs(OUT, exist_ok=True)

FONT = '<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,500;0,600;1,400;1,500;1,600&family=DM+Sans:opsz,wght@9..40,300;9..40,400;9..40,500;9..40,600;9..40,700&display=swap" rel="stylesheet">'

with open('/Users/sandracranage/linkredirect/social-posts.html') as f:
    src = f.read()

css = re.search(r'<style>([\s\S]*?)</style>', src).group(1)

# (filename, element-id, width, height, background, scale)
# scale=2 → passes --force-device-scale-factor=2, doubling physical pixels
posts = [
    # Pinterest Pins  500×750 logical → 1000×1500 physical @2x
    ('Pinterest-Pin-1',        'pin-1',       500, 750,  '#FAF8F4', 2),
    ('Pinterest-Pin-2',        'pin-2',       500, 750,  '#0E0D0C', 2),
    ('Pinterest-Pin-3',        'pin-3',       500, 750,  '#FBF5E6', 2),
    ('Pinterest-Pin-4',        'pin-4',       500, 750,  '#EEF4EE', 2),
    # Main carousel  540×540
    ('Main-1-Cover',           'main-1',      540, 540,  '#FAF8F4', 2),
    ('Main-2-Problem',         'main-2',      540, 540,  '#0E0D0C', 2),
    ('Main-3-Maths',           'main-3',      540, 540,  '#F5F2EB', 2),
    ('Main-4-Fix',             'main-4',      540, 540,  '#181614', 2),
    ('Main-5-Countries',       'main-5',      540, 540,  '#F0EDE6', 2),
    ('Main-6-Follow',          'main-6',      540, 540,  '#EEF4EE', 2),
    ('Main-7-CTA',             'main-7',      540, 540,  '#0E0D0C', 2),
    # Mistakes carousel
    ('Mistakes-1-Hook',        'mistakes-1',  540, 540,  '#FAF0EE', 2),
    ('Mistakes-2-M12',         'mistakes-2',  540, 540,  '#0E0D0C', 2),
    ('Mistakes-3-M34',         'mistakes-3',  540, 540,  '#F5F2EB', 2),
    ('Mistakes-4-M5',          'mistakes-4',  540, 540,  '#FBF5E6', 2),
    ('Mistakes-5-Follow',      'mistakes-5',  540, 540,  '#FAF8F4', 2),
    # Checklist carousel
    ('Checklist-1-Hook',       'checklist-1', 540, 540,  '#EEF4EE', 2),
    ('Checklist-2-Setup',      'checklist-2', 540, 540,  '#F5F2EB', 2),
    ('Checklist-3-Content',    'checklist-3', 540, 540,  '#F0EDE6', 2),
    ('Checklist-4-Growth',     'checklist-4', 540, 540,  '#F5F2EB', 2),
    ('Checklist-5-Follow',     'checklist-5', 540, 540,  '#0E0D0C', 2),
    # 10x Earners carousel
    ('EarnX-1-Hook',           'earnx-1',     540, 540,  '#FAF8F4', 2),
    ('EarnX-2-ThreeThings',    'earnx-2',     540, 540,  '#FBF5E6', 2),
    ('EarnX-3-Numbers',        'earnx-3',     540, 540,  '#F0EDE6', 2),
    ('EarnX-4-ActionPlan',     'earnx-4',     540, 540,  '#F5F2EB', 2),
    ('EarnX-5-Follow',         'earnx-5',     540, 540,  '#181614', 2),
]

def get_block_by_id(src, elem_id):
    """Extract the top-level div with id=elem_id, balanced-bracket aware."""
    # Find the opening tag
    pattern = rf'<div\s+id="{re.escape(elem_id)}"[^>]*>'
    m = re.search(pattern, src)
    if not m:
        return f'<p style="color:red;font-size:20px">NOT FOUND: #{elem_id}</p>'
    start = m.start()
    pos = m.end()
    depth = 1
    while depth > 0 and pos < len(src):
        open_m  = src.find('<div',  pos)
        close_m = src.find('</div>', pos)
        if close_m == -1:
            break
        if open_m != -1 and open_m < close_m:
            depth += 1
            pos = open_m + 4
        else:
            depth -= 1
            pos = close_m + 6
    return src[start:pos].strip()

for name, elem_id, w, h, bg, scale in posts:
    block = get_block_by_id(src, elem_id)
    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
{FONT}
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
html,body{{width:{w}px;height:{h}px;overflow:hidden;background:{bg}}}
{css}
body{{padding:0!important;display:block!important}}
.label{{display:none!important}}
</style>
</head>
<body>
{block}
</body>
</html>"""
    tmp = f'/tmp/lg-post-{name}.html'
    with open(tmp, 'w') as f:
        f.write(html)
    out = f'{OUT}/{name}.png'
    cmd = [
        CHROME, '--headless=new', '--disable-gpu', '--no-sandbox',
        f'--window-size={w},{h}',
        f'--screenshot={out}',
        '--hide-scrollbars',
    ]
    if scale > 1:
        cmd.append(f'--force-device-scale-factor={scale}')
    cmd.append(f'file://{tmp}')
    result = subprocess.run(cmd, capture_output=True)
    size = os.path.getsize(out) if os.path.exists(out) else 0
    status = '✅' if size > 10000 else '❌'
    print(f'{status} {name}.png ({size:,} bytes)')

print(f'\n📁 All posts saved to ~/Desktop/LinkGlobe-Posts')
