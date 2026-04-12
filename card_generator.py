"""
card_generator.py  —  generates 1080x1080 news cards
Supports:
  - Pure English cards        (bangla=False)
  - Mixed Bangla+English cards (bangla=True)
    English words / numbers embedded in Bangla text render correctly.

Cross-platform: auto-discovers Latin fonts on Windows, Linux, and macOS.
"""

import os
import re
import glob
from PIL import Image, ImageDraw, ImageFont

# ---------------------------------------------------------------------------
# Canvas & colour constants
# ---------------------------------------------------------------------------

CARD_W = 1080
CARD_H = 1080

BG_COLOR       = "#0D0D0D"
ACCENT_COLOR   = "#FFFFFF"
HEADLINE_COLOR = "#FFFFFF"
SUMMARY_COLOR  = "#CCCCCC"
SOURCE_COLOR   = "#888888"
DIVIDER_COLOR  = "#333333"

ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")


# ---------------------------------------------------------------------------
# Colour helpers
# ---------------------------------------------------------------------------

def hex_to_rgb(hex_color):
    h = hex_color.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def hex_to_rgba(hex_color, alpha=255):
    r, g, b = hex_to_rgb(hex_color)
    return (r, g, b, alpha)


# ---------------------------------------------------------------------------
# Robust cross-platform Latin font loader
# ---------------------------------------------------------------------------

_LATIN_BOLD_PATHS = [
    # Linux
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
    "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf",
    # macOS
    "/Library/Fonts/Arial Bold.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
    # Windows
    "C:/Windows/Fonts/arialbd.ttf",
    "C:/Windows/Fonts/calibrib.ttf",
    "C:/Windows/Fonts/segoeuib.ttf",
    "C:/Windows/Fonts/verdanab.ttf",
    "C:/Windows/Fonts/trebucbd.ttf",
]

_LATIN_REG_PATHS = [
    # Linux
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
    "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
    # macOS
    "/Library/Fonts/Arial.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
    # Windows
    "C:/Windows/Fonts/arial.ttf",
    "C:/Windows/Fonts/calibri.ttf",
    "C:/Windows/Fonts/segoeui.ttf",
    "C:/Windows/Fonts/verdana.ttf",
]

_font_cache = {}


def _discover_latin_font(bold):
    cache_key = "latin_bold" if bold else "latin_reg"
    if cache_key in _font_cache:
        return _font_cache[cache_key]

    # 1. Try explicit priority paths
    for path in (_LATIN_BOLD_PATHS if bold else _LATIN_REG_PATHS):
        if os.path.exists(path):
            _font_cache[cache_key] = path
            return path

    # 2. Glob search across common font directories
    search_patterns = [
        "/usr/share/fonts/**/*.ttf",
        "/usr/local/share/fonts/**/*.ttf",
        os.path.expanduser("~/.fonts/**/*.ttf"),
        "C:/Windows/Fonts/*.ttf",
        os.path.expanduser("~/Library/Fonts/*.ttf"),
        "/Library/Fonts/*.ttf",
    ]

    def is_bold_sans(p):
        n = os.path.basename(p).lower()
        return ("bold" in n or n.endswith("bd.ttf")) and "sans" in n \
               and "mono" not in n and "oblique" not in n and "italic" not in n

    def is_reg_sans(p):
        n = os.path.basename(p).lower()
        return "sans" in n and "mono" not in n and "bold" not in n \
               and "oblique" not in n and "italic" not in n and "light" not in n

    check = is_bold_sans if bold else is_reg_sans
    for pattern in search_patterns:
        for path in glob.glob(pattern, recursive=True):
            if check(path):
                _font_cache[cache_key] = path
                return path

    # 3. Last resort: any TTF at all
    for pattern in search_patterns:
        for path in glob.glob(pattern, recursive=True):
            if path.lower().endswith(".ttf"):
                _font_cache[cache_key] = path
                return path

    raise RuntimeError(
        "No Latin TTF font found on this system.\n"
        "Linux fix:   sudo apt install fonts-dejavu-core\n"
        "Windows fix: fonts like arial.ttf should already be in C:/Windows/Fonts/"
    )


def load_font(size, bold=False):
    """Load a Latin font at the given pixel size. Auto-discovers path."""
    path = _discover_latin_font(bold)
    return ImageFont.truetype(path, size)


def get_bangla_font_path(bold=False):
    """Return path to NotoSansBengali .ttf — raises FileNotFoundError if missing."""
    filename = "NotoSansBengali-Bold.ttf" if bold else "NotoSansBengali-Regular.ttf"
    path = os.path.join(ASSETS_DIR, filename)
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Bangla font not found: {path}\n"
            "Download from: https://fonts.google.com/noto/specimen/Noto+Sans+Bengali\n"
            "Place the .ttf files inside your assets/ folder."
        )
    return path


# ---------------------------------------------------------------------------
# Drawing helpers
# ---------------------------------------------------------------------------

def draw_rounded_rect(draw, xy, radius, fill):
    x1, y1, x2, y2 = xy
    c = hex_to_rgb(fill)
    draw.rectangle([x1 + radius, y1, x2 - radius, y2], fill=c)
    draw.rectangle([x1, y1 + radius, x2, y2 - radius], fill=c)
    draw.ellipse([x1, y1, x1 + 2*radius, y1 + 2*radius], fill=c)
    draw.ellipse([x2 - 2*radius, y1, x2, y1 + 2*radius], fill=c)
    draw.ellipse([x1, y2 - 2*radius, x1 + 2*radius, y2], fill=c)
    draw.ellipse([x2 - 2*radius, y2 - 2*radius, x2, y2], fill=c)


def paste_rgba(base, overlay, position):
    base.paste(overlay, position, overlay)


def wrap_text_latin(text, font, max_width, draw):
    words, lines, current = text.split(" "), [], ""
    for word in words:
        test = (current + " " + word).strip()
        if draw.textbbox((0, 0), test, font=font)[2] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


# ---------------------------------------------------------------------------
# Mixed-script renderer  (Bangla + English / numbers on the same line)
# ---------------------------------------------------------------------------

_BANGLA_RE = re.compile(r"[\u0980-\u09FF]+")


def split_mixed_segments(text):
    """
    Split text into alternating ('bangla', str) / ('latin', str) tuples.
    e.g. 'ChatGPT মার্কেটিং' -> [('latin','ChatGPT '), ('bangla','মার্কেটিং')]
    """
    segments, last = [], 0
    for m in _BANGLA_RE.finditer(text):
        if m.start() > last:
            chunk = text[last:m.start()]
            if chunk:
                segments.append(("latin", chunk))
        segments.append(("bangla", m.group()))
        last = m.end()
    if last < len(text):
        chunk = text[last:]
        if chunk:
            segments.append(("latin", chunk))
    return segments or [("latin", text)]


def render_mixed_block(text, bangla_font_path, bangla_size,
                       latin_font_bold, latin_font_reg,
                       color_hex, max_width,
                       line_spacing=10, bold=False):
    """
    Render mixed Bangla+Latin text into a transparent RGBA PIL image.

    Each word is split into Bangla/Latin segments; each segment is drawn
    with its correct font side-by-side, so English words inside Bangla
    sentences never show as broken boxes.
    """
    color_rgb = hex_to_rgb(color_hex)
    bn_font   = ImageFont.truetype(bangla_font_path, bangla_size)
    la_font   = latin_font_bold if bold else latin_font_reg

    # measurement probe
    probe     = Image.new("RGBA", (1, 1))
    probe_drw = ImageDraw.Draw(probe)

    def seg_w(script, chunk):
        f = bn_font if script == "bangla" else la_font
        return probe_drw.textbbox((0, 0), chunk, font=f)[2]

    def word_w(word):
        return sum(seg_w(s, c) for s, c in split_mixed_segments(word))

    space_px = probe_drw.textbbox((0, 0), " ", font=la_font)[2]

    # word-wrap
    words, wrapped, cur_words, cur_w = text.split(" "), [], [], 0
    for word in words:
        ww = word_w(word)
        if not cur_words:
            cur_words, cur_w = [word], ww
        elif cur_w + space_px + ww <= max_width:
            cur_words.append(word)
            cur_w += space_px + ww
        else:
            wrapped.append(" ".join(cur_words))
            cur_words, cur_w = [word], ww
    if cur_words:
        wrapped.append(" ".join(cur_words))

    # line height = tallest glyph across both scripts
    bn_h   = probe_drw.textbbox((0, 0), "অ", font=bn_font)[3]
    la_h   = probe_drw.textbbox((0, 0), "Ag", font=la_font)[3]
    line_h = max(bn_h, la_h)
    n      = len(wrapped)
    total_h = max(line_h * n + line_spacing * max(n - 1, 0), 1)

    out  = Image.new("RGBA", (max_width, total_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(out)

    y = 0
    for line in wrapped:
        x = 0
        for script, chunk in split_mixed_segments(line):
            f     = bn_font if script == "bangla" else la_font
            seg_h = draw.textbbox((0, 0), chunk, font=f)[3]
            y_off = (line_h - seg_h) // 2       # vertically centre within line_h
            draw.text((x, y + y_off), chunk, font=f, fill=color_rgb)
            x += draw.textbbox((0, 0), chunk, font=f)[2]
        y += line_h + line_spacing

    return out


# ---------------------------------------------------------------------------
# Main card generator
# ---------------------------------------------------------------------------

def generate_card(story, index=0, bangla=False):
    """
    Generate a 1080x1080 PNG news card and save to OUTPUT_DIR.

    story  : dict  — keys: title, summary, source, link
    index  : int   — used in filename  (card_0.png, card_1.png ...)
    bangla : bool  — True  = Bangla mode (mixed Bangla+English)
                     False = English / Latin only
    """
    img  = Image.new("RGB", (CARD_W, CARD_H), hex_to_rgb(BG_COLOR))
    draw = ImageDraw.Draw(img)

    # logo
    logo_path = os.path.join(ASSETS_DIR, "logo.png")
    logo      = Image.open(logo_path).convert("RGBA").resize((90, 90), Image.LANCZOS)
    circle    = Image.new("RGBA", (106, 106), (0, 0, 0, 0))
    ImageDraw.Draw(circle).ellipse([0, 0, 106, 106], fill=(255, 255, 255, 255))
    img.paste(circle, (44, 44), circle)
    img.paste(logo,   (52, 52), logo)

    max_text_w = CARD_W - 120   # 60 px margin each side

    # =========================================================================
    # BANGLA MODE
    # =========================================================================
    if bangla:
        bn_bold = get_bangla_font_path(bold=True)
        bn_reg  = get_bangla_font_path(bold=False)

        lat_name     = load_font(28, bold=True)
        lat_tagline  = load_font(18, bold=False)
        lat_headline = load_font(52, bold=True)
        lat_summary  = load_font(30, bold=False)
        lat_source   = load_font(24, bold=False)

        # page name
        name_img = render_mixed_block(
            "অর্কেস্ট্রেটর পালস",
            bn_bold, 28, lat_name, lat_name,
            ACCENT_COLOR, max_text_w, line_spacing=6, bold=True,
        )
        paste_rgba(img, name_img, (160, 58))

        # tagline — pure Latin, plain PIL
        draw.text((160, 94), "Daily AI News & Trends",
                  font=lat_tagline, fill=hex_to_rgb(SOURCE_COLOR))

        # AI NEWS badge
        tag_font = load_font(20, bold=True)
        tag_text = "AI NEWS"
        tb       = draw.textbbox((0, 0), tag_text, font=tag_font)
        tag_w, tag_h = tb[2] + 32, tb[3] + 16
        tag_x, tag_y = 60, 190
        draw_rounded_rect(draw, (tag_x, tag_y, tag_x + tag_w, tag_y + tag_h), 8, "#FFFFFF")
        draw.text((tag_x + 16, tag_y + 8), tag_text,
                  font=tag_font, fill=hex_to_rgb(BG_COLOR))
        draw.rectangle(
            [60, tag_y + tag_h + 20, CARD_W - 60, tag_y + tag_h + 22],
            fill=hex_to_rgb(DIVIDER_COLOR),
        )

        y = tag_y + tag_h + 44

        # headline — mixed
        title_img = render_mixed_block(
            story["title"],
            bn_bold, 52, lat_headline, lat_headline,
            HEADLINE_COLOR, max_text_w, line_spacing=14, bold=True,
        )
        if title_img.height > 210:
            title_img = title_img.crop((0, 0, title_img.width, 210))
        paste_rgba(img, title_img, (60, y))
        y += title_img.height + 22      # breathing room after headline

        draw.rectangle([60, y, 160, y + 4], fill=hex_to_rgb(ACCENT_COLOR))
        y += 32                          # breathing room before body

        # summary — mixed
        summary = story["summary"]
        if len(summary) > 400:
            summary = summary[:400] + "..."
        summary_img = render_mixed_block(
            summary,
            bn_reg, 30, lat_summary, lat_summary,
            SUMMARY_COLOR, max_text_w, line_spacing=12, bold=False,
        )
        if summary_img.height > 280:
            summary_img = summary_img.crop((0, 0, summary_img.width, 280))
        paste_rgba(img, summary_img, (60, y))

        # source — mixed (handles "সোর্স: TechCrunch" correctly)
        source_img = render_mixed_block(
            f"সোর্স: {story['source']}",
            bn_reg, 24, lat_source, lat_source,
            SOURCE_COLOR, max_text_w, line_spacing=8, bold=False,
        )
        paste_rgba(img, source_img, (60, CARD_H - 90))

    # =========================================================================
    # ENGLISH MODE  — plain PIL, identical to original working version
    # =========================================================================
    else:
        font_name     = load_font(28, bold=True)
        font_tagline  = load_font(18)
        font_headline = load_font(52, bold=True)
        font_summary  = load_font(30)
        font_source   = load_font(24)

        draw.text((160, 58), "Orchestrator Pulse",
                  font=font_name,    fill=hex_to_rgb(ACCENT_COLOR))
        draw.text((160, 94), "Daily AI News & Trends",
                  font=font_tagline, fill=hex_to_rgb(SOURCE_COLOR))

        tag_font = load_font(20, bold=True)
        tag_text = "AI NEWS"
        tb       = draw.textbbox((0, 0), tag_text, font=tag_font)
        tag_w, tag_h = tb[2] + 32, tb[3] + 16
        tag_x, tag_y = 60, 190
        draw_rounded_rect(draw, (tag_x, tag_y, tag_x + tag_w, tag_y + tag_h), 8, "#FFFFFF")
        draw.text((tag_x + 16, tag_y + 8), tag_text,
                  font=tag_font, fill=hex_to_rgb(BG_COLOR))
        draw.rectangle(
            [60, tag_y + tag_h + 20, CARD_W - 60, tag_y + tag_h + 22],
            fill=hex_to_rgb(DIVIDER_COLOR),
        )

        y = tag_y + tag_h + 44

        for line in wrap_text_latin(story["title"], font_headline, max_text_w, draw)[:3]:
            draw.text((60, y), line, font=font_headline, fill=hex_to_rgb(HEADLINE_COLOR))
            y += 60

        y += 10
        draw.rectangle([60, y, 160, y + 4], fill=hex_to_rgb(ACCENT_COLOR))
        y += 24

        summary = story["summary"]
        if len(summary) > 400:
            summary = summary[:400] + "..."
        for line in wrap_text_latin(summary, font_summary, max_text_w, draw)[:7]:
            draw.text((60, y), line, font=font_summary, fill=hex_to_rgb(SUMMARY_COLOR))
            y += 40

        draw.text((60, CARD_H - 90), f"Source: {story['source']}",
                  font=font_source, fill=hex_to_rgb(SOURCE_COLOR))

    # =========================================================================
    # SHARED — handle & bottom bar  (always Latin, same for both modes)
    # =========================================================================
    handle_font = load_font(24, bold=True)
    handle      = "@OrchestratorPulse"
    hbbox       = draw.textbbox((0, 0), handle, font=handle_font)
    draw.text(
        (CARD_W - hbbox[2] - 60, CARD_H - 90),
        handle, font=handle_font, fill=hex_to_rgb(ACCENT_COLOR),
    )
    draw.rectangle([0, CARD_H - 8, CARD_W, CARD_H], fill=hex_to_rgb(ACCENT_COLOR))

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_path = os.path.join(OUTPUT_DIR, f"card_{index}.png")
    img.save(out_path)
    print(f"Saved -> {out_path}")
    return out_path


# ---------------------------------------------------------------------------
# Quick test  —  python card_generator.py
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("Latin bold font:", _discover_latin_font(bold=True))
    print("Latin reg  font:", _discover_latin_font(bold=False))
    print()

    english_story = {
        "title":   "OpenAI Releases GPT-5 With Breakthrough Reasoning Capabilities",
        "summary": "OpenAI has announced GPT-5, claiming it significantly outperforms previous "
                   "models on complex reasoning tasks, coding benchmarks, and multimodal understanding.",
        "source":  "TechCrunch",
        "link":    "https://techcrunch.com",
    }

    bangla_story = {
        "title":   "ChatGPT মার্কেটিং দলের জন্য নতুন সুযোগ তৈরি করছে",
        "summary": "শিখুন কিভাবে marketing দলগুলি ChatGPT ব্যবহার করে প্রচারাভিযানের পরিকল্পনা "
                   "করতে, বিষয়বস্তু তৈরি করতে, কর্মক্ষমতা বিশ্লেষণ করতে এবং ধারণা থেকে "
                   "বাস্তবায়নে দ্রুত স্থানান্তরিত হতে পারে।",
        "source":  "OpenAI News",
        "link":    "https://openai.com",
    }

    generate_card(english_story, index=0, bangla=False)
    generate_card(bangla_story,  index=1, bangla=True)