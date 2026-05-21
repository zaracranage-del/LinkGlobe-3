from PIL import Image, ImageDraw, ImageFont
import os, random

# ── Config ──────────────────────────────────────────────────────────
W, H = 1000, 1500   # Pinterest standard 2:3
OUT  = "/Users/sandracranage/linkredirect/marketing/pinterest/posts"
os.makedirs(OUT, exist_ok=True)

SFNS       = "/System/Library/Fonts/SFNS.ttf"
ARIAL_BOLD = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
ARIAL      = "/System/Library/Fonts/Supplemental/Arial.ttf"

font_bold   = lambda sz: ImageFont.truetype(ARIAL_BOLD, sz)
font_medium = lambda sz: ImageFont.truetype(SFNS, sz)
font_reg    = lambda sz: ImageFont.truetype(ARIAL, sz)

# ── Palette ─────────────────────────────────────────────────────────
BLACK      = (10, 10, 22)
INDIGO     = (99, 102, 241)
INDIGO_DIM = (67, 56, 202)
INDIGO_DK  = (45, 38, 140)
WHITE      = (255, 255, 255)
MUTED      = (150, 145, 175)
RED        = (239, 68, 68)
GREEN      = (74, 222, 128)
AMBER      = (251, 191, 36)
CREAM      = (248, 246, 240)
DARK_CREAM = (235, 230, 218)

# ── Helpers ─────────────────────────────────────────────────────────

def add_grain(img, intensity=14):
    pixels = img.load()
    for y in range(0, img.height, 2):
        for x in range(0, img.width, 2):
            n = random.randint(-intensity, intensity)
            r, g, b = pixels[x, y][:3]
            pixels[x, y] = (max(0,min(255,r+n)), max(0,min(255,g+n)), max(0,min(255,b+n)))
    return img

def grad_bg(draw, top, bottom):
    for y in range(H):
        t = y / H
        r = int(top[0]+(bottom[0]-top[0])*t)
        g = int(top[1]+(bottom[1]-top[1])*t)
        b = int(top[2]+(bottom[2]-top[2])*t)
        draw.line([(0,y),(W,y)], fill=(r,g,b))

def wrap_text(draw, text, font, max_w):
    words = text.split()
    lines, cur = [], ""
    for w in words:
        test = (cur+" "+w).strip()
        if draw.textbbox((0,0), test, font=font)[2] <= max_w:
            cur = test
        else:
            if cur: lines.append(cur)
            cur = w
    if cur: lines.append(cur)
    return lines

def draw_text_block(draw, text, font, color, cx, y, max_w, gap=12, align="center"):
    lines = wrap_text(draw, text, font, max_w)
    for line in lines:
        bb = draw.textbbox((0,0), line, font=font)
        lw = bb[2]-bb[0]
        lh = bb[3]-bb[1]
        x = cx - lw//2 if align=="center" else cx
        draw.text((x, y), line, font=font, fill=color)
        y += lh + gap
    return y

def pill_btn(draw, text, font, color, bg, cx, y, px=36, py=16, r=50):
    bb = draw.textbbox((0,0), text, font=font)
    tw, th = bb[2]-bb[0], bb[3]-bb[1]
    x0,y0 = cx-tw//2-px, y-th//2-py
    x1,y1 = cx+tw//2+px, y+th//2+py
    draw.rounded_rectangle([x0,y0,x1,y1], radius=r, fill=bg)
    draw.text((cx-tw//2, y0+py), text, font=font, fill=color)
    return y1

def divider(draw, cx, y, w=60, col=(60,55,90)):
    draw.rectangle([cx-w//2, y, cx+w//2, y+3], fill=col)

def tag_pill(draw, text, font, color, bg, cx, y, px=18, py=8, r=40):
    bb = draw.textbbox((0,0), text, font=font)
    tw, th = bb[2]-bb[0], bb[3]-bb[1]
    x0,y0 = cx-tw//2-px, y-py
    x1,y1 = cx+tw//2+px, y+th+py
    draw.rounded_rectangle([x0,y0,x1,y1], radius=r, fill=bg)
    draw.text((cx-tw//2, y0+py), text, font=font, fill=color)
    return y1+10

def branding_footer(draw, img, style="dark"):
    # subtle footer bar
    col = (22,20,42) if style=="dark" else (225,220,210)
    draw.rectangle([0, H-80, W, H], fill=col)
    f = font_medium(22)
    text = "linkglobe.co"
    bb = draw.textbbox((0,0), text, font=f)
    tw = bb[2]-bb[0]
    fg = (100,96,140) if style=="dark" else (140,130,110)
    draw.text((W//2-tw//2, H-54), text, font=f, fill=fg)

def save(img, name):
    add_grain(img, 12)
    path = f"{OUT}/{name}"
    img.save(path, quality=95)
    print(f"  ✓ {name}")


# ════════════════════════════════════════════════════════════════════
# PIN 1 — "You're losing commission" (dark dramatic)
# ════════════════════════════════════════════════════════════════════
def pin_1():
    img = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(img)
    grad_bg(draw, (10,10,22), (22,14,46))

    # Indigo glow blob top-right
    ov = Image.new("RGBA",(W,H),(0,0,0,0))
    od = ImageDraw.Draw(ov)
    od.ellipse([W-200,-100,W+200,300], fill=(99,102,241,30))
    od.ellipse([-100,H-200,300,H+100], fill=(67,56,202,20))
    img = Image.alpha_composite(img.convert("RGBA"),ov).convert("RGB")
    draw = ImageDraw.Draw(img)

    cx = W//2
    y = 110

    # Eyebrow tag
    y = tag_pill(draw, "AFFILIATE MARKETING TIP", font_medium(20), INDIGO, (28,26,58), cx, y) + 30

    # Main headline — 3 lines, large
    y = draw_text_block(draw, "You're losing", font_bold(90), WHITE, cx, y, 900, gap=4)
    y = draw_text_block(draw, "commission", font_bold(90), WHITE, cx, y, 900, gap=4)
    y = draw_text_block(draw, "right now.", font_bold(90), INDIGO, cx, y, 900, gap=0)
    y += 40

    divider(draw, cx, y)
    y += 44

    # Body copy
    body = "Your Amazon affiliate link only earns in one country. Every UK, AU and CA fan who clicks? You get £0."
    y = draw_text_block(draw, body, font_reg(30), MUTED, cx, y, 840, gap=10)
    y += 50

    # Stat callout box
    draw.rounded_rectangle([80, y, W-80, y+140], radius=16, fill=(24,22,50), outline=(50,46,90), width=1)
    stat_text = "Up to 40% of your audience\nis losing you money right now."
    sy = y + 24
    for line in stat_text.split("\n"):
        bb = draw.textbbox((0,0), line, font=font_medium(26))
        lw = bb[2]-bb[0]
        draw.text((cx-lw//2, sy), line, font=font_medium(26), fill=(200,196,240))
        sy += 42
    y += 180

    # Secondary copy
    y = draw_text_block(draw, "The fix takes 10 minutes.", font_bold(38), WHITE, cx, y, 840, gap=6)
    y += 30

    # CTA button
    pill_btn(draw, "Free to start → linkglobe.co", font_bold(28), WHITE, INDIGO_DIM, cx, y+30, px=44, py=20, r=60)

    branding_footer(draw, img, "dark")
    save(img, "pin-1-commission.jpg")


# ════════════════════════════════════════════════════════════════════
# PIN 2 — "5 Mistakes" (dark with red accents)
# ════════════════════════════════════════════════════════════════════
def pin_2():
    img = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(img)
    grad_bg(draw, (12,10,22), (28,10,20))

    ov = Image.new("RGBA",(W,H),(0,0,0,0))
    od = ImageDraw.Draw(ov)
    od.ellipse([-50,-50,350,350], fill=(239,68,68,15))
    img = Image.alpha_composite(img.convert("RGBA"),ov).convert("RGB")
    draw = ImageDraw.Draw(img)

    cx = W//2
    y = 100

    y = tag_pill(draw, "5 AFFILIATE MISTAKES", font_medium(20), RED, (40,14,14), cx, y) + 30

    y = draw_text_block(draw, "Costing you", font_bold(82), WHITE, cx, y, 900, gap=6)
    y = draw_text_block(draw, "commission", font_bold(82), RED, cx, y, 900, gap=6)
    y = draw_text_block(draw, "every day.", font_bold(82), WHITE, cx, y, 900, gap=0)
    y += 50

    mistakes = [
        "Using a country-specific Amazon link",
        "Not signing up for every marketplace",
        "Relying on Linktree to fix your links",
        "Never checking international clicks",
        "Keeping the same broken links for years",
    ]

    for i, m in enumerate(mistakes):
        # row bg
        bg_col = (30,14,14) if i%2==0 else (24,12,12)
        draw.rounded_rectangle([60, y, W-60, y+72], radius=12, fill=bg_col)
        # number
        num = font_bold(26)
        draw.text((84, y+20), f"0{i+1}", font=num, fill=(120,60,60))
        # text
        f_m = font_medium(26)
        bb = draw.textbbox((0,0), m, font=f_m)
        draw.text((130, y+22), m, font=f_m, fill=(220,210,210))
        y += 86

    y += 30
    y = draw_text_block(draw, "All 5 fixed in 10 minutes.", font_bold(36), WHITE, cx, y, 840, gap=6)
    y += 30
    pill_btn(draw, "linkglobe.co — free to start", font_bold(26), WHITE, (100,20,20), cx, y+20, px=40, py=18, r=60)

    branding_footer(draw, img, "dark")
    save(img, "pin-2-mistakes.jpg")


# ════════════════════════════════════════════════════════════════════
# PIN 3 — "Do the math" (dark with amber/gold)
# ════════════════════════════════════════════════════════════════════
def pin_3():
    img = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(img)
    grad_bg(draw, (12,10,18), (20,16,10))

    ov = Image.new("RGBA",(W,H),(0,0,0,0))
    od = ImageDraw.Draw(ov)
    od.ellipse([W-250,-100,W+100,350], fill=(251,191,36,18))
    img = Image.alpha_composite(img.convert("RGBA"),ov).convert("RGB")
    draw = ImageDraw.Draw(img)

    cx = W//2
    y = 100

    y = tag_pill(draw, "DO THE MATHS", font_medium(20), AMBER, (40,32,8), cx, y) + 30

    y = draw_text_block(draw, "How much are you", font_bold(66), WHITE, cx, y, 900, gap=6)
    y = draw_text_block(draw, "actually losing?", font_bold(66), AMBER, cx, y, 900, gap=0)
    y += 50

    divider(draw, cx, y, col=(80,70,30))
    y += 44

    # Calculation steps
    steps = [
        ("20,000 followers", "typical mid-size creator"),
        ("× 30% international", "= 6,000 people"),
        ("× 1% click rate", "= 60 lost clicks/month"),
        ("× £40 order × 4%", "= £96 gone every month"),
    ]

    for val, note in steps:
        draw.rounded_rectangle([60,y,W-60,y+90], radius=14, fill=(22,20,12))
        f_v = font_bold(34)
        bb = draw.textbbox((0,0), val, font=f_v)
        draw.text((cx-bb[2]//2+bb[0]//2, y+12), val, font=f_v, fill=WHITE)
        f_n = font_reg(22)
        bb2 = draw.textbbox((0,0), note, font=f_n)
        draw.text((cx-bb2[2]//2+bb2[0]//2, y+52), note, font=f_n, fill=(160,145,80))
        y += 104

    y += 10

    # Big result
    draw.rounded_rectangle([60,y,W-60,y+130], radius=16, fill=(40,32,8), outline=AMBER, width=2)
    f_r = font_bold(58)
    bb = draw.textbbox((0,0),"£96/month lost",font=f_r)
    draw.text((cx-(bb[2]-bb[0])//2, y+18), "£96/month lost", font=f_r, fill=AMBER)
    f_rs = font_reg(24)
    bb2 = draw.textbbox((0,0),"With 100k followers? £480/month.",font=f_rs)
    draw.text((cx-(bb2[2]-bb2[0])//2, y+88), "With 100k followers? £480/month.", font=f_rs, fill=(180,160,80))
    y += 160

    y += 20
    pill_btn(draw, "Fix it free → linkglobe.co", font_bold(26), WHITE, INDIGO_DIM, cx, y+20, px=40, py=18, r=60)

    branding_footer(draw, img, "dark")
    save(img, "pin-3-math.jpg")


# ════════════════════════════════════════════════════════════════════
# PIN 4 — "Without vs With" (split design)
# ════════════════════════════════════════════════════════════════════
def pin_4():
    img = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(img)
    grad_bg(draw, (10,10,22), (18,14,38))

    cx = W//2
    y = 100

    tag_pill(draw, "BEFORE vs AFTER", font_medium(20), WHITE, (35,32,65), cx, y)
    y = 178

    y = draw_text_block(draw, "Same content.", font_bold(74), WHITE, cx, y, 900, gap=6)
    y = draw_text_block(draw, "Different results.", font_bold(74), INDIGO, cx, y, 900, gap=0)
    y += 50

    # Two column comparison
    pad = 40
    cw = (W - pad*3) // 2
    rows = [
        ("UK fan clicks", "£0", "✅ Commission"),
        ("AU fan clicks", "£0", "✅ Commission"),
        ("CA fan clicks", "£0", "✅ Commission"),
        ("DE fan clicks", "£0", "✅ Commission"),
    ]

    # Headers
    lx, rx = pad, pad*2+cw
    draw.rounded_rectangle([lx,y,lx+cw,y+52], radius=10, fill=(50,14,14))
    draw.rounded_rectangle([rx,y,rx+cw,y+52], radius=10, fill=(14,50,28))
    f_h = font_bold(22)
    bb = draw.textbbox((0,0),"WITHOUT",font=f_h)
    draw.text((lx+(cw-(bb[2]-bb[0]))//2, y+14), "WITHOUT", font=f_h, fill=RED)
    bb = draw.textbbox((0,0),"WITH LINKGLOBE",font=f_h)
    draw.text((rx+(cw-(bb[2]-bb[0]))//2, y+14), "WITH LINKGLOBE", font=f_h, fill=GREEN)
    y += 62

    for scenario, before, after in rows:
        row_h = 90
        draw.rounded_rectangle([lx,y,lx+cw,y+row_h], radius=10, fill=(24,12,12))
        draw.rounded_rectangle([rx,y,rx+cw,y+row_h], radius=10, fill=(12,28,18))

        f_sc = font_reg(20)
        bb = draw.textbbox((0,0), scenario, font=f_sc)
        draw.text((lx+(cw-(bb[2]-bb[0]))//2, y+8), scenario, font=f_sc, fill=(160,100,100))
        draw.text((rx+(cw-(bb[2]-bb[0]))//2, y+8), scenario, font=f_sc, fill=(100,160,120))

        f_val = font_bold(32)
        bb = draw.textbbox((0,0), before, font=f_val)
        draw.text((lx+(cw-(bb[2]-bb[0]))//2, y+38), before, font=f_val, fill=RED)
        bb = draw.textbbox((0,0), after, font=f_val)
        draw.text((rx+(cw-(bb[2]-bb[0]))//2, y+38), after, font=f_val, fill=GREEN)

        y += row_h + 8

    y += 30
    y = draw_text_block(draw, "One link. Every country.\nYour full commission.", font_bold(40), WHITE, cx, y, 860, gap=8)
    y += 30
    pill_btn(draw, "Free → linkglobe.co", font_bold(28), WHITE, INDIGO_DIM, cx, y+16, px=44, py=20, r=60)

    branding_footer(draw, img, "dark")
    save(img, "pin-4-comparison.jpg")


# ════════════════════════════════════════════════════════════════════
# PIN 5 — "How it works" (clean steps, light/cream feel with dark top)
# ════════════════════════════════════════════════════════════════════
def pin_5():
    img = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(img)

    # Dark top half, cream bottom
    for y_px in range(H):
        t = y_px / H
        if t < 0.42:
            r,g,b = 10,10,22
        else:
            progress = (t-0.42)/0.58
            r = int(10 + (242-10)*progress)
            g = int(10 + (238-10)*progress)
            b = int(22 + (230-22)*progress)
        draw.line([(0,y_px),(W,y_px)], fill=(r,g,b))

    cx = W//2
    y = 100

    tag_pill(draw, "SETUP GUIDE", font_medium(20), INDIGO, (28,26,58), cx, y)
    y = 172

    y = draw_text_block(draw, "Earn from every", font_bold(74), WHITE, cx, y, 900, gap=6)
    y = draw_text_block(draw, "country in", font_bold(74), WHITE, cx, y, 900, gap=6)
    y = draw_text_block(draw, "3 steps.", font_bold(74), INDIGO, cx, y, 900, gap=0)
    y += 30

    f_sub = font_reg(28)
    y = draw_text_block(draw, "Set up once. Works forever.", f_sub, MUTED, cx, y, 840, gap=0)
    y += 50

    steps = [
        ("01", "Add your affiliate tags", "Enter your Amazon tag for UK, US, AU, CA.\nDone once. Applies to every product forever."),
        ("02", "Paste any product link", "Amazon, ASOS, Charlotte Tilbury — anything.\nYour geo-smart link is ready in seconds."),
        ("03", "Share it everywhere", "Bio, TikTok, Pinterest, Stories.\nEvery fan earns you commission automatically."),
    ]

    for num, title, desc in steps:
        card_h = 190
        card_col = (255,255,255) if y > H//2 else (22,20,46)
        border_col = (220,216,240) if y > H//2 else (38,36,72)
        draw.rounded_rectangle([50,y,W-50,y+card_h], radius=18, fill=card_col, outline=border_col, width=1)

        # Number circle
        draw.ellipse([70,y+20,130,y+80], fill=INDIGO)
        f_n = font_bold(26)
        bb = draw.textbbox((0,0), num, font=f_n)
        draw.text((100-(bb[2]-bb[0])//2, y+34), num, font=f_n, fill=WHITE)

        # Title
        tc = BLACK if y > H//2 else WHITE
        mc = (100,95,130) if y > H//2 else MUTED
        f_t = font_bold(30)
        draw.text((150, y+22), title, font=f_t, fill=tc)

        for j, line in enumerate(desc.split("\n")):
            f_d = font_reg(22)
            draw.text((150, y+66+j*30), line, font=f_d, fill=mc)

        y += card_h + 16

    y += 20
    pill_btn(draw, "Free to start → linkglobe.co", font_bold(26), WHITE, INDIGO_DIM, cx, y+20, px=42, py=20, r=60)

    branding_footer(draw, img, "light")
    save(img, "pin-5-howto.jpg")


# ── Run ─────────────────────────────────────────────────────────────
print("Building Pinterest pins...")
pin_1()
pin_2()
pin_3()
pin_4()
pin_5()
print(f"\n🎉 Done! Pins saved to:\n{OUT}")
