from PIL import Image, ImageDraw, ImageFont
import os, math, random

# ── Config ──────────────────────────────────────────────────────────
W, H = 1080, 1080
OUT = "/Users/sandracranage/linkredirect/marketing/carousels"
FONTS = "/Users/sandracranage/linkredirect/marketing/carousels/fonts"

SFNS        = "/System/Library/Fonts/SFNS.ttf"
ARIAL_BOLD  = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
ARIAL       = "/System/Library/Fonts/Supplemental/Arial.ttf"

font_bold   = lambda sz: ImageFont.truetype(ARIAL_BOLD, sz)
font_medium = lambda sz: ImageFont.truetype(SFNS, sz)
font_reg    = lambda sz: ImageFont.truetype(ARIAL, sz)

# ── Brand palette ────────────────────────────────────────────────────
BLACK      = (10, 10, 18)
DARK_NAVY  = (14, 14, 28)
INDIGO     = (99, 102, 241)
INDIGO_DIM = (67, 56, 202)
WHITE      = (255, 255, 255)
WHITE_70   = (255, 255, 255, 178)
WHITE_40   = (255, 255, 255, 102)
MUTED      = (140, 140, 160)
RED        = (239, 68, 68)
GREEN      = (74, 222, 128)
AMBER      = (251, 191, 36)

# ── Helpers ──────────────────────────────────────────────────────────

def add_grain(img, intensity=18):
    import random
    pixels = img.load()
    for y in range(0, img.height, 2):
        for x in range(0, img.width, 2):
            n = random.randint(-intensity, intensity)
            r, g, b = pixels[x, y][:3]
            pixels[x, y] = (
                max(0, min(255, r + n)),
                max(0, min(255, g + n)),
                max(0, min(255, b + n)),
            )
    return img

def draw_gradient_bg(draw, w, h, top=(10,10,18), bottom=(20,14,40)):
    for y in range(h):
        t = y / h
        r = int(top[0] + (bottom[0]-top[0])*t)
        g = int(top[1] + (bottom[1]-top[1])*t)
        b = int(top[2] + (bottom[2]-top[2])*t)
        draw.line([(0, y), (w, y)], fill=(r, g, b))

def draw_blob(draw, cx, cy, r, color_rgba):
    draw.ellipse([cx-r, cy-r, cx+r, cy+r], fill=color_rgba)

def wrap_text(text, font, max_width, draw):
    words = text.split()
    lines = []
    current = ""
    for word in words:
        test = (current + " " + word).strip()
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines

def draw_wrapped_text(draw, text, font, color, max_width, x, y, line_gap=14, center=True):
    lines = wrap_text(text, font, max_width, draw)
    total_h = 0
    rendered = []
    for line in lines:
        bb = draw.textbbox((0, 0), line, font=font)
        lh = bb[3] - bb[1]
        rendered.append((line, lh))
        total_h += lh + line_gap
    total_h -= line_gap
    cy = y - total_h // 2
    for line, lh in rendered:
        if center:
            bb = draw.textbbox((0, 0), line, font=font)
            lw = bb[2] - bb[0]
            draw.text((x - lw // 2, cy), line, font=font, fill=color)
        else:
            draw.text((x, cy), line, font=font, fill=color)
        cy += lh + line_gap
    return total_h

def pill(draw, text, font, color, bg, x, y, pad_x=22, pad_y=10, radius=50):
    bb = draw.textbbox((0, 0), text, font=font)
    tw = bb[2] - bb[0]
    th = bb[3] - bb[1]
    rx0 = x - tw//2 - pad_x
    ry0 = y - th//2 - pad_y
    rx1 = x + tw//2 + pad_x
    ry1 = y + th//2 + pad_y
    draw.rounded_rectangle([rx0, ry0, rx1, ry1], radius=radius, fill=bg)
    draw.text((x - tw//2, ry0 + pad_y), text, font=font, fill=color)

def progress_dots(draw, total, current, cx, y, dot_r=7, gap=20):
    total_w = total * dot_r*2 + (total-1)*gap
    sx = cx - total_w//2
    for i in range(total):
        x = sx + i*(dot_r*2+gap) + dot_r
        col = WHITE if i == current else (60, 60, 80)
        draw.ellipse([x-dot_r, y-dot_r, x+dot_r, y+dot_r], fill=col)

def make_slide_base(style="dark"):
    img = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(img)
    if style == "dark":
        draw_gradient_bg(draw, W, H, (10,10,22), (18,12,38))
        # subtle blob accents
        overlay = Image.new("RGBA", (W, H), (0,0,0,0))
        od = ImageDraw.Draw(overlay)
        od.ellipse([-80, -80, 280, 280], fill=(99,102,241,18))
        od.ellipse([W-200, H-200, W+100, H+100], fill=(99,102,241,12))
        img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    elif style == "light":
        draw_gradient_bg(draw, W, H, (245,243,255), (235,233,252))
        overlay = Image.new("RGBA", (W, H), (0,0,0,0))
        od = ImageDraw.Draw(overlay)
        od.ellipse([-60, -60, 220, 220], fill=(99,102,241,15))
        img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    return img

def add_branding(draw, style="dark"):
    f = font_medium(20)
    col = (100,100,120) if style=="dark" else (160,155,185)
    bb = draw.textbbox((0,0), "linkglobe.co", font=f)
    draw.text((W//2 - (bb[2]-bb[0])//2, H-48), "linkglobe.co", font=f, fill=col)

def save(img, path):
    add_grain(img, 12)
    img.save(path, quality=95)
    print(f"  Saved: {path}")


# ════════════════════════════════════════════════════════════════════
# CAROUSEL 1 — "You're losing commission" (8 slides)
# ════════════════════════════════════════════════════════════════════

def carousel_1():
    folder = f"{OUT}/carousel-1"
    os.makedirs(folder, exist_ok=True)
    n = 8

    slides = [
        # (hook_line, sub, accent_color, note)
        {
            "type": "hook",
            "eyebrow": "AFFILIATE MARKETING",
            "headline": "You're losing\ncommission right now.",
            "sub": "And you don't even know it's happening.",
            "slide": 0,
        },
        {
            "type": "body",
            "number": "01",
            "headline": "Amazon has a\ndifferent store\nfor every country.",
            "sub": "US. UK. Australia. Canada. Germany. Japan.\nEach one is a completely separate program.",
            "slide": 1,
        },
        {
            "type": "body",
            "number": "02",
            "headline": "Your affiliate tag\nonly works in\none of them.",
            "sub": "The store you signed up for.\nEvery other country → £0.",
            "slide": 2,
        },
        {
            "type": "body",
            "number": "03",
            "headline": "So when a UK fan\nclicks your US link...",
            "sub": None,
            "slide": 3,
        },
        {
            "type": "impact",
            "headline": "You earn\nabsolutely\nnothing.",
            "sub": "Every click. Every post. For years.",
            "slide": 4,
        },
        {
            "type": "body",
            "number": "04",
            "headline": "This is happening\nto 20–40% of\nevery post you make.",
            "sub": "That's how many of your followers\naren't from your home country.",
            "slide": 5,
        },
        {
            "type": "body",
            "number": "05",
            "headline": "The fix takes\n10 minutes.",
            "sub": "One geo-smart link that detects each fan's country\nand sends them to their local store — automatically.",
            "slide": 6,
        },
        {
            "type": "cta",
            "headline": "Start earning from\nevery fan.\nEvery country.",
            "sub": "Free to start. No card needed.",
            "pill_text": "linkglobe.co →",
            "slide": 7,
        },
    ]

    for s in slides:
        img = make_slide_base("dark")
        draw = ImageDraw.Draw(img)
        cx, cy = W//2, H//2

        if s["type"] == "hook":
            # eyebrow pill
            pill(draw, s["eyebrow"], font_medium(15), INDIGO, (30,28,55), cx, 200)
            # big headline
            lines = s["headline"].split("\n")
            y = cy - 60
            for line in lines:
                f = font_bold(72)
                bb = draw.textbbox((0,0), line, font=f)
                draw.text((cx-(bb[2]-bb[0])//2, y), line, font=f, fill=WHITE)
                y += (bb[3]-bb[1]) + 10
            # sub
            f_sub = font_reg(26)
            bb = draw.textbbox((0,0), s["sub"], font=f_sub)
            draw.text((cx-(bb[2]-bb[0])//2, y+30), s["sub"], font=f_sub, fill=(160,155,185))

        elif s["type"] == "body":
            # big number watermark
            f_num = font_bold(200)
            bb = draw.textbbox((0,0), s["number"], font=f_num)
            draw.text((cx-(bb[2]-bb[0])//2, cy-160), s["number"], font=f_num, fill=(25,22,50))
            # headline
            lines = s["headline"].split("\n")
            y = cy - 100
            for line in lines:
                f = font_bold(62)
                bb = draw.textbbox((0,0), line, font=f)
                draw.text((cx-(bb[2]-bb[0])//2, y), line, font=f, fill=WHITE)
                y += (bb[3]-bb[1]) + 8
            # sub
            if s["sub"]:
                for subline in s["sub"].split("\n"):
                    f_s = font_reg(24)
                    bb = draw.textbbox((0,0), subline, font=f_s)
                    draw.text((cx-(bb[2]-bb[0])//2, y+20), subline, font=f_s, fill=(160,155,185))
                    y += 36

        elif s["type"] == "impact":
            # accent top bar
            draw.rectangle([cx-30, 180, cx+30, 186], fill=RED)
            # huge text
            lines = s["headline"].split("\n")
            y = cy - 160
            for line in lines:
                sz = 100 if len(line) < 10 else 80
                f = font_bold(sz)
                bb = draw.textbbox((0,0), line, font=f)
                draw.text((cx-(bb[2]-bb[0])//2, y), line, font=f, fill=WHITE)
                y += (bb[3]-bb[1]) + 6
            if s["sub"]:
                f_s = font_medium(26)
                bb = draw.textbbox((0,0), s["sub"], font=f_s)
                draw.text((cx-(bb[2]-bb[0])//2, y+30), s["sub"], font=f_s, fill=(160,155,185))

        elif s["type"] == "cta":
            # indigo glow
            overlay = Image.new("RGBA", (W, H), (0,0,0,0))
            od = ImageDraw.Draw(overlay)
            od.ellipse([cx-300, cy-300, cx+300, cy+300], fill=(99,102,241,28))
            img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
            draw = ImageDraw.Draw(img)

            lines = s["headline"].split("\n")
            y = cy - 160
            for line in lines:
                f = font_bold(66)
                bb = draw.textbbox((0,0), line, font=f)
                draw.text((cx-(bb[2]-bb[0])//2, y), line, font=f, fill=WHITE)
                y += (bb[3]-bb[1]) + 8
            f_s = font_reg(24)
            bb = draw.textbbox((0,0), s["sub"], font=f_s)
            draw.text((cx-(bb[2]-bb[0])//2, y+20), s["sub"], font=f_s, fill=(160,155,185))
            # big pill CTA
            pill(draw, s["pill_text"], font_bold(28), WHITE, INDIGO_DIM, cx, y+110, pad_x=50, pad_y=22, radius=60)

        # progress dots + branding
        progress_dots(draw, n, s["slide"], cx, H-80)
        add_branding(draw)

        save(img, f"{folder}/slide-{s['slide']+1:02d}.jpg")

    print(f"✅ Carousel 1 done — {folder}")


# ════════════════════════════════════════════════════════════════════
# CAROUSEL 2 — "5 Mistakes" (7 slides)
# ════════════════════════════════════════════════════════════════════

def carousel_2():
    folder = f"{OUT}/carousel-2"
    os.makedirs(folder, exist_ok=True)
    n = 7

    mistakes = [
        ("Using a country-specific Amazon link", "Your UK, AU & CA fans click and get nothing."),
        ("Not tagging every Amazon marketplace", "AU, UK, CA, DE are separate — separate money."),
        ("Relying on Linktree for affiliate links", "Linktree doesn't geo-route. Your links are still broken."),
        ("Never checking international click data", "You don't know how much you're losing because you've never looked."),
        ("Keeping the same links for years", "One smart link fixes this for every product. Forever."),
    ]

    # Slide 1 — hook
    img = make_slide_base("dark")
    draw = ImageDraw.Draw(img)
    cx, cy = W//2, H//2
    pill(draw, "AFFILIATE MARKETING", font_medium(15), INDIGO, (30,28,55), cx, 200)
    f = font_bold(76)
    bb = draw.textbbox((0,0), "5 Mistakes", font=f)
    draw.text((cx-(bb[2]-bb[0])//2, cy-120), "5 Mistakes", font=f, fill=WHITE)
    f2 = font_bold(46)
    line2 = "Costing You"
    bb2 = draw.textbbox((0,0), line2, font=f2)
    draw.text((cx-(bb2[2]-bb2[0])//2, cy-30), line2, font=f2, fill=INDIGO)
    line3 = "Commission"
    bb3 = draw.textbbox((0,0), line3, font=f2)
    draw.text((cx-(bb3[2]-bb3[0])//2, cy+30), line3, font=f2, fill=INDIGO)
    f_s = font_reg(24)
    sub = "Swipe to find out if you're making them →"
    bb_s = draw.textbbox((0,0), sub, font=f_s)
    draw.text((cx-(bb_s[2]-bb_s[0])//2, cy+110), sub, font=f_s, fill=(160,155,185))
    progress_dots(draw, n, 0, cx, H-80)
    add_branding(draw)
    save(img, f"{folder}/slide-01.jpg")

    # Slides 2–6 — each mistake
    for i, (title, desc) in enumerate(mistakes):
        img = make_slide_base("dark")
        draw = ImageDraw.Draw(img)

        # Big mistake number
        num_str = f"0{i+1}"
        f_num = font_bold(180)
        bb = draw.textbbox((0,0), num_str, font=f_num)
        draw.text((cx-(bb[2]-bb[0])//2, cy-200), num_str, font=f_num, fill=(22,20,48))

        # ❌ icon area
        draw.text((cx-30, cy-140), "❌", font=font_bold(52), fill=WHITE)

        # Title
        draw_wrapped_text(draw, title, font_bold(52), WHITE, 880, cx, cy, line_gap=10)

        # Desc
        f_desc = font_reg(24)
        draw_wrapped_text(draw, desc, f_desc, (160,155,185), 820, cx, cy+140, line_gap=8)

        progress_dots(draw, n, i+1, cx, H-80)
        add_branding(draw)
        save(img, f"{folder}/slide-{i+2:02d}.jpg")

    # Slide 7 — CTA
    img = make_slide_base("dark")
    overlay = Image.new("RGBA", (W, H), (0,0,0,0))
    od = ImageDraw.Draw(overlay)
    od.ellipse([W//2-280, H//2-280, W//2+280, H//2+280], fill=(99,102,241,30))
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(img)
    cx, cy = W//2, H//2

    f_h = font_bold(64)
    draw_wrapped_text(draw, "All 5 fixed.\nOne tool.", font_bold(72), WHITE, 880, cx, cy-120, line_gap=10)
    draw_wrapped_text(draw, "Free to start. No card needed.", font_reg(26), (160,155,185), 800, cx, cy+60)
    pill(draw, "linkglobe.co →", font_bold(28), WHITE, INDIGO_DIM, cx, cy+160, pad_x=50, pad_y=22, radius=60)
    progress_dots(draw, n, 6, cx, H-80)
    add_branding(draw)
    save(img, f"{folder}/slide-07.jpg")

    print(f"✅ Carousel 2 done — {folder}")


# ════════════════════════════════════════════════════════════════════
# CAROUSEL 3 — "Do the math" (6 slides)
# ════════════════════════════════════════════════════════════════════

def carousel_3():
    folder = f"{OUT}/carousel-3"
    os.makedirs(folder, exist_ok=True)
    n = 6

    def slide(idx, fn):
        img = make_slide_base("dark")
        draw = ImageDraw.Draw(img)
        fn(draw, W//2, H//2)
        progress_dots(draw, n, idx, W//2, H-80)
        add_branding(draw)
        save(img, f"{folder}/slide-{idx+1:02d}.jpg")

    def s0(draw, cx, cy):
        pill(draw, "DO THE MATH", font_medium(15), AMBER, (45,38,12), cx, 200)
        draw_wrapped_text(draw, "How much are you\nactually losing?", font_bold(72), WHITE, 900, cx, cy-60, line_gap=10)
        draw_wrapped_text(draw, "We calculated it for you.", font_reg(26), (160,155,185), 800, cx, cy+120)

    def s1(draw, cx, cy):
        draw_wrapped_text(draw, "Say you have", font_medium(28), (160,155,185), 800, cx, cy-220)
        f_big = font_bold(120)
        bb = draw.textbbox((0,0), "20,000", font=f_big)
        draw.text((cx-(bb[2]-bb[0])//2, cy-170), "20,000", font=f_big, fill=WHITE)
        draw_wrapped_text(draw, "followers", font_medium(36), (160,155,185), 800, cx, cy+60)
        draw_wrapped_text(draw, "Roughly 30% aren't from your country.", font_reg(24), (120,115,150), 800, cx, cy+140)

    def s2(draw, cx, cy):
        draw_wrapped_text(draw, "That's", font_medium(28), (160,155,185), 800, cx, cy-200)
        f_big = font_bold(120)
        bb = draw.textbbox((0,0), "6,000", font=f_big)
        draw.text((cx-(bb[2]-bb[0])//2, cy-150), "6,000", font=f_big, fill=INDIGO)
        draw_wrapped_text(draw, "people clicking your links\nand making you £0.", font_medium(34), WHITE, 860, cx, cy+70, line_gap=10)

    def s3(draw, cx, cy):
        # loss calculation visual
        items = [
            ("60 lost clicks/month", "1% conversion rate"),
            ("× £40 avg order", "typical Amazon basket"),
            ("× 4% commission", "Amazon standard rate"),
        ]
        y = cy - 200
        for item, note in items:
            f_i = font_bold(38)
            bb = draw.textbbox((0,0), item, font=f_i)
            draw.text((cx-(bb[2]-bb[0])//2, y), item, font=f_i, fill=WHITE)
            f_n = font_reg(20)
            bb_n = draw.textbbox((0,0), note, font=f_n)
            draw.text((cx-(bb_n[2]-bb_n[0])//2, y+48), note, font=f_n, fill=(100,95,130))
            y += 120
        # divider
        draw.rectangle([cx-200, y-10, cx+200, y-8], fill=(40,38,70))
        # result
        draw_wrapped_text(draw, "= £96 lost every month", font_bold(44), RED, 860, cx, y+50)

    def s4(draw, cx, cy):
        draw_wrapped_text(draw, "With 100k followers?", font_medium(32), (160,155,185), 800, cx, cy-180)
        f_big = font_bold(110)
        bb = draw.textbbox((0,0), "£480/mo", font=f_big)
        draw.text((cx-(bb[2]-bb[0])//2, cy-130), "£480/mo", font=f_big, fill=RED)
        draw_wrapped_text(draw, "gone. Every month.", font_bold(38), WHITE, 800, cx, cy+80)
        draw_wrapped_text(draw, "£5,760 a year. Just... gone.", font_reg(26), (160,155,185), 800, cx, cy+160)

    def s5(draw, cx, cy):
        overlay = Image.new("RGBA", (W, H), (0,0,0,0))
        od = ImageDraw.Draw(overlay)
        od.ellipse([cx-300, cy-300, cx+300, cy+300], fill=(74,222,128,20))
        img_base = Image.new("RGB", (W, H))
        draw_gradient_bg(ImageDraw.Draw(img_base), W, H, (10,10,22), (18,12,38))
        final = Image.alpha_composite(img_base.convert("RGBA"), overlay).convert("RGB")
        draw2 = ImageDraw.Draw(final)
        draw_wrapped_text(draw2, "Fix it for £15/month.", font_bold(68), GREEN, 900, cx, cy-100, line_gap=10)
        draw_wrapped_text(draw2, "Earn back everything you've been losing.", font_reg(28), WHITE, 860, cx, cy+60)
        pill(draw2, "linkglobe.co →", font_bold(28), WHITE, (30,100,60), cx, cy+170, pad_x=50, pad_y=22, radius=60)
        progress_dots(draw2, n, 5, cx, H-80)
        # branding
        f_b = font_medium(20)
        bb = draw2.textbbox((0,0), "linkglobe.co", font=f_b)
        draw2.text((cx-(bb[2]-bb[0])//2, H-48), "linkglobe.co", font=f_b, fill=(80,120,90))
        save(final, f"{folder}/slide-06.jpg")
        return  # already saved

    slide(0, s0)
    slide(1, s1)
    slide(2, s2)
    slide(3, s3)
    slide(4, s4)
    s5(None, W//2, H//2)  # special handling

    print(f"✅ Carousel 3 done — {folder}")


# ════════════════════════════════════════════════════════════════════
# CAROUSEL 4 — "LinkGlobe vs nothing" comparison (6 slides)
# ════════════════════════════════════════════════════════════════════

def carousel_4():
    folder = f"{OUT}/carousel-4"
    os.makedirs(folder, exist_ok=True)
    n = 6

    # Slide 1 — hook
    img = make_slide_base("dark")
    draw = ImageDraw.Draw(img)
    cx, cy = W//2, H//2
    pill(draw, "WITHOUT vs WITH", font_medium(15), INDIGO, (30,28,55), cx, 200)
    draw_wrapped_text(draw, "Same content.\nDifferent results.", font_bold(72), WHITE, 900, cx, cy-60, line_gap=10)
    draw_wrapped_text(draw, "Here's what changes when you fix your links.", font_reg(26), (160,155,185), 820, cx, cy+120)
    progress_dots(draw, n, 0, cx, H-80)
    add_branding(draw)
    save(img, f"{folder}/slide-01.jpg")

    # Slides 2–5 — comparison rows
    comparisons = [
        ("UK fan clicks your link", "Lands on Amazon US\n→ £0 for you", "Lands on Amazon UK\n→ commission earned ✅"),
        ("AU fan clicks your link", "Lands on Amazon US\n→ £0 for you", "Lands on Amazon AU\n→ commission earned ✅"),
        ("CA fan clicks your link", "Sees wrong products\n→ £0 for you", "Lands on Amazon CA\n→ commission earned ✅"),
        ("You post a new product", "One broken link\nfor most of the world", "One smart link that\nworks in every country"),
    ]

    for i, (scenario, before, after) in enumerate(comparisons):
        img = make_slide_base("dark")
        draw = ImageDraw.Draw(img)
        cx, cy = W//2, H//2

        # Scenario label
        f_sc = font_medium(22)
        bb = draw.textbbox((0,0), scenario, font=f_sc)
        draw.text((cx-(bb[2]-bb[0])//2, 170), scenario, font=f_sc, fill=(160,155,185))

        # Two columns
        pad = 60
        col_w = (W - pad*3) // 2

        # Left — WITHOUT
        lx = pad
        draw.rounded_rectangle([lx, 240, lx+col_w, H-120], radius=20, fill=(30,14,14))
        draw.rounded_rectangle([lx, 240, lx+col_w, 285], radius=10, fill=(60,20,20))
        f_lab = font_bold(18)
        draw.text((lx+18, 252), "WITHOUT", font=f_lab, fill=RED)
        # before text
        for j, line in enumerate(before.split("\n")):
            f_l = font_medium(28) if j==0 else font_reg(24)
            col_t = WHITE if j==0 else (200,100,100)
            bb = draw.textbbox((0,0), line, font=f_l)
            draw.text((lx + (col_w-(bb[2]-bb[0]))//2, 330+j*50), line, font=f_l, fill=col_t)

        # Right — WITH
        rx = pad*2 + col_w
        draw.rounded_rectangle([rx, 240, rx+col_w, H-120], radius=20, fill=(14,30,20))
        draw.rounded_rectangle([rx, 240, rx+col_w, 285], radius=10, fill=(20,55,30))
        draw.text((rx+18, 252), "WITH LINKGLOBE", font=f_lab, fill=GREEN)
        for j, line in enumerate(after.split("\n")):
            f_l = font_medium(28) if j==0 else font_reg(24)
            col_t = WHITE if j==0 else (100,200,130)
            bb = draw.textbbox((0,0), line, font=f_l)
            draw.text((rx + (col_w-(bb[2]-bb[0]))//2, 330+j*50), line, font=f_l, fill=col_t)

        progress_dots(draw, n, i+1, cx, H-80)
        add_branding(draw)
        save(img, f"{folder}/slide-{i+2:02d}.jpg")

    # Slide 6 — CTA
    img = make_slide_base("dark")
    overlay = Image.new("RGBA", (W, H), (0,0,0,0))
    od = ImageDraw.Draw(overlay)
    od.ellipse([W//2-280, H//2-280, W//2+280, H//2+280], fill=(99,102,241,28))
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(img)
    cx, cy = W//2, H//2
    draw_wrapped_text(draw, "Start earning\nfrom every fan.", font_bold(72), WHITE, 900, cx, cy-120, line_gap=10)
    draw_wrapped_text(draw, "Free plan available. No card needed.", font_reg(26), (160,155,185), 820, cx, cy+60)
    pill(draw, "linkglobe.co →", font_bold(28), WHITE, INDIGO_DIM, cx, cy+160, pad_x=50, pad_y=22, radius=60)
    progress_dots(draw, n, 5, cx, H-80)
    add_branding(draw)
    save(img, f"{folder}/slide-06.jpg")

    print(f"✅ Carousel 4 done — {folder}")


# ════════════════════════════════════════════════════════════════════
# CAROUSEL 5 — "How it works in 3 steps" (5 slides)
# ════════════════════════════════════════════════════════════════════

def carousel_5():
    folder = f"{OUT}/carousel-5"
    os.makedirs(folder, exist_ok=True)
    n = 5

    # Slide 1
    img = make_slide_base("dark")
    draw = ImageDraw.Draw(img)
    cx, cy = W//2, H//2
    pill(draw, "SETUP IN 10 MINUTES", font_medium(15), GREEN, (14,38,22), cx, 200)
    draw_wrapped_text(draw, "How to earn from\nevery country.", font_bold(72), WHITE, 900, cx, cy-60, line_gap=10)
    draw_wrapped_text(draw, "3 steps. Done once. Works forever.", font_reg(26), (160,155,185), 820, cx, cy+120)
    progress_dots(draw, n, 0, cx, H-80)
    add_branding(draw)
    save(img, f"{folder}/slide-01.jpg")

    steps = [
        ("01", "Add your affiliate tags.", "Enter your Amazon tag for each country — UK, US, AU, CA, DE.\nYou do this once. It applies to every product forever."),
        ("02", "Paste any product URL.", "Copy any Amazon, ASOS, Charlotte Tilbury or brand link.\nYour geo-smart link is ready in seconds."),
        ("03", "Share it everywhere.", "Put it in your bio, stories, TikTok, Pinterest.\nEvery fan goes to their local store. You earn from all of them."),
    ]

    for i, (num, title, desc) in enumerate(steps):
        img = make_slide_base("dark")
        draw = ImageDraw.Draw(img)
        cx, cy = W//2, H//2

        # Step number — big ghost
        f_g = font_bold(220)
        bb = draw.textbbox((0,0), num, font=f_g)
        draw.text((cx-(bb[2]-bb[0])//2, cy-200), num, font=f_g, fill=(22,20,48))

        # Step indicator pill
        pill(draw, f"STEP {num}", font_medium(18), INDIGO, (30,28,60), cx, cy-140)

        # Title
        f_t = font_bold(58)
        bb = draw.textbbox((0,0), title, font=f_t)
        draw.text((cx-(bb[2]-bb[0])//2, cy-80), title, font=f_t, fill=WHITE)

        # Desc
        for j, line in enumerate(desc.split("\n")):
            f_d = font_reg(24)
            bb = draw.textbbox((0,0), line, font=f_d)
            draw.text((cx-(bb[2]-bb[0])//2, cy+30+j*40), line, font=f_d, fill=(160,155,185))

        progress_dots(draw, n, i+1, cx, H-80)
        add_branding(draw)
        save(img, f"{folder}/slide-{i+2:02d}.jpg")

    # Slide 5 — CTA
    img = make_slide_base("dark")
    overlay = Image.new("RGBA", (W, H), (0,0,0,0))
    od = ImageDraw.Draw(overlay)
    od.ellipse([W//2-300, H//2-300, W//2+300, H//2+300], fill=(99,102,241,28))
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(img)
    cx, cy = W//2, H//2
    draw_wrapped_text(draw, "Free to start.\nNo card needed.", font_bold(72), WHITE, 900, cx, cy-120, line_gap=10)
    draw_wrapped_text(draw, "Set up in 10 minutes.", font_reg(28), (160,155,185), 820, cx, cy+60)
    pill(draw, "linkglobe.co →", font_bold(30), WHITE, INDIGO_DIM, cx, cy+160, pad_x=54, pad_y=24, radius=60)
    progress_dots(draw, n, 4, cx, H-80)
    add_branding(draw)
    save(img, f"{folder}/slide-05.jpg")

    print(f"✅ Carousel 5 done — {folder}")


# ── Run all ─────────────────────────────────────────────────────────
print("Building carousels...")
carousel_1()
carousel_2()
carousel_3()
carousel_4()
carousel_5()
print("\n🎉 All carousels built!")
print(f"📁 Find them at: {OUT}")
