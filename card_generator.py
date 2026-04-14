import os
import re
import glob
from PIL import Image, ImageDraw, ImageFont

# --- Constants ---
CARD_W, CARD_H = 1080, 1080
BG_COLOR, ACCENT_COLOR = "#0D0D0D", "#FFFFFF"
HEADLINE_COLOR, SUMMARY_COLOR = "#FFFFFF", "#CCCCCC"
SOURCE_COLOR, DIVIDER_COLOR = "#888888", "#333333"

ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")

def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def paste_rgba(base, overlay, pos):
    base.paste(overlay, pos, overlay)

def draw_rounded_rect(draw, xy, radius, fill):
    x1, y1, x2, y2 = xy
    c = hex_to_rgb(fill)
    draw.rectangle([x1 + radius, y1, x2 - radius, y2], fill=c)
    draw.rectangle([x1, y1 + radius, x2, y2 - radius], fill=c)
    draw.ellipse([x1, y1, x1+2*radius, y1+2*radius], fill=c)
    draw.ellipse([x2-2*radius, y1, x2, y1+2*radius], fill=c)
    draw.ellipse([x1, y2-2*radius, x1+2*radius, y2], fill=c)
    draw.ellipse([x2-2*radius, y2-2*radius, x2, y2], fill=c)

def wrap_text_latin(text, font, max_width, draw):
    # Improved wrapping to prevent the overlap seen in Unknown-5.jpg
    words = text.replace('\n', ' ').split(" ")
    lines = []
    current_line = ""
    for word in words:
        if not word: continue
        test_line = f"{current_line} {word}".strip()
        if draw.textbbox((0, 0), test_line, font=font)[2] <= max_width:
            current_line = test_line
        else:
            if current_line: lines.append(current_line)
            current_line = word
    if current_line: lines.append(current_line)
    return lines

def load_font(size, bold=False):
    # Using standard safe paths for Linux/Windows/Mac
    paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
        "/System/Library/Fonts/Helvetica.ttc"
    ] if bold else [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc"
    ]
    for path in paths:
        if os.path.exists(path): return ImageFont.truetype(path, size)
    return ImageFont.load_default()

def get_bangla_font_path(bold=False):
    name = "NotoSansBengali-Bold.ttf" if bold else "NotoSansBengali-Regular.ttf"
    return os.path.join(ASSETS_DIR, name)

_BANGLA_CLUSTER_RE = re.compile(r"[\u0980-\u09FF\u0964\u0965][\u0980-\u09FF\u0964\u0965\u200C\u200D]*")

def split_mixed_segments(text):
    segments, last = [], 0
    for m in _BANGLA_CLUSTER_RE.finditer(text):
        if m.start() > last: segments.append(("latin", text[last:m.start()]))
        segments.append(("bangla", m.group()))
        last = m.end()
    if last < len(text): segments.append(("latin", text[last:]))
    return segments or [("latin", text)]

def render_mixed_block(text, bn_path, bn_sz, la_bold, la_reg, col, max_w, spacing=12, bold=False, max_lines=None):
    rgb = hex_to_rgb(col)
    bn_f = ImageFont.truetype(bn_path, bn_sz)
    la_f = la_bold if bold else la_reg
    
    # Text wrapping for mixed content
    words = text.split(" ")
    wrapped, current_line, current_w = [], [], 0
    space_px = ImageDraw.Draw(Image.new("RGBA", (1,1))).textbbox((0,0), " ", font=la_f)[2]

    for word in words:
        ww = sum(ImageDraw.Draw(Image.new("RGBA", (1,1))).textbbox((0,0), c, font=(bn_f if s=="bangla" else la_f))[2] for s,c in split_mixed_segments(word))
        if not current_line or current_w + space_px + ww <= max_w:
            current_line.append(word)
            current_w += (space_px if len(current_line) > 1 else 0) + ww
        else:
            wrapped.append(" ".join(current_line))
            current_line, current_w = [word], ww
    if current_line: wrapped.append(" ".join(current_line))
    if max_lines: wrapped = wrapped[:max_lines]

    line_h = max(bn_sz + 5, 35) # Safe height for Bangla
    out = Image.new("RGBA", (max_w, (line_h + spacing) * len(wrapped)), (0,0,0,0))
    d = ImageDraw.Draw(out)
    curr_y = 0
    for line in wrapped:
        curr_x = 0
        for s, c in split_mixed_segments(line):
            f = bn_f if s == "bangla" else la_f
            d.text((curr_x, curr_y), c, font=f, fill=rgb)
            curr_x += d.textbbox((0,0), c, font=f)[2]
        curr_y += line_h + spacing
    return out

def generate_card(story, index=0, bangla=False):
    img = Image.new("RGB", (CARD_W, CARD_H), hex_to_rgb(BG_COLOR))
    draw = ImageDraw.Draw(img)
    max_text_w = CARD_W - 120

    # 1. Header (Logo & Name)
    logo_path = os.path.join(ASSETS_DIR, "logo.png")
    if os.path.exists(logo_path):
        logo = Image.open(logo_path).convert("RGBA").resize((90, 90), Image.LANCZOS)
        circle = Image.new("RGBA", (106, 106), (0, 0, 0, 0))
        ImageDraw.Draw(circle).ellipse([0, 0, 106, 106], fill=(255, 255, 255, 255))
        img.paste(circle, (44, 44), circle)
        img.paste(logo, (52, 52), logo)

    if bangla:
        bn_bold = get_bangla_font_path(True)
        lat_28b = load_font(28, True)
        name_img = render_mixed_block("অর্কেস্ট্রেটর পালস", bn_bold, 28, lat_28b, lat_28b, ACCENT_COLOR, max_text_w, bold=True)
        paste_rgba(img, name_img, (160, 58))
        draw.text((160, 94), "Daily AI News & Trends", font=load_font(18), fill=hex_to_rgb(SOURCE_COLOR))
    else:
        draw.text((160, 58), "Orchestrator Pulse", font=load_font(28, True), fill=hex_to_rgb(ACCENT_COLOR))
        draw.text((160, 94), "Daily AI News & Trends", font=load_font(18), fill=hex_to_rgb(SOURCE_COLOR))

    # 2. Badge & Line
    tag_font = load_font(20, bold=True)
    draw_rounded_rect(draw, (60, 190, 170, 226), 8, "#FFFFFF")
    draw.text((76, 198), "AI NEWS", font=tag_font, fill=hex_to_rgb(BG_COLOR))
    draw.rectangle([60, 246, CARD_W - 60, 248], fill=hex_to_rgb(DIVIDER_COLOR))

    y = 280

    # 3. Headline
    if bangla:
        bn_bold = get_bangla_font_path(True)
        lat_h = load_font(44, True)
        title_img = render_mixed_block(story["title"], bn_bold, 44, lat_h, lat_h, HEADLINE_COLOR, max_text_w, spacing=14, bold=True, max_lines=3)
        paste_rgba(img, title_img, (60, y))
        y += title_img.height + 20
    else:
        font_h = load_font(52, bold=True)
        lines = wrap_text_latin(story["title"], font_h, max_text_w, draw)[:3]
        for line in lines:
            draw.text((60, y), line, font=font_h, fill=hex_to_rgb(HEADLINE_COLOR))
            y += 65
        y += 20

    # Accent Bar
    draw.rectangle([60, y, 160, y + 4], fill=hex_to_rgb(ACCENT_COLOR))
    y += 35

    # 4. Summary (FIXED: y increments correctly)
    if bangla:
        bn_reg = get_bangla_font_path(False)
        lat_r = load_font(30, False)
        sum_img = render_mixed_block(story["summary"], bn_reg, 30, lat_r, lat_r, SUMMARY_COLOR, max_text_w, spacing=12, max_lines=6)
        paste_rgba(img, sum_img.crop((0,0,sum_img.width, min(sum_img.height, 400))), (60, y))
    else:
        font_s = load_font(32)
        s_lines = wrap_text_latin(story["summary"], font_s, max_text_w, draw)[:8]
        for line in s_lines:
            draw.text((60, y), line, font=font_s, fill=hex_to_rgb(SUMMARY_COLOR))
            y += 48 # Explicit vertical spacing per line

    # 5. Footer
    footer_y = CARD_H - 90
    draw.text((60, footer_y), f"Source: {story['source']}", font=load_font(24), fill=hex_to_rgb(SOURCE_COLOR))
    handle = "@OrchestratorPulse"
    h_font = load_font(24, bold=True)
    h_w = draw.textbbox((0, 0), handle, font=h_font)[2]
    draw.text((CARD_W - h_w - 60, footer_y), handle, font=h_font, fill=hex_to_rgb(ACCENT_COLOR))
    draw.rectangle([0, CARD_H - 8, CARD_W, CARD_H], fill=hex_to_rgb(ACCENT_COLOR))

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_path = os.path.join(OUTPUT_DIR, f"card_{index}.png")
    img.save(out_path)
    return out_path