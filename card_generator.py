"""
card_generator.py  —  generates 1080x1080 news cards
Supports:
  - Pure English cards         (bangla=False)
  - Mixed Bangla+English cards  (bangla=True)

Fixes over v1:
  - English / numbers render correctly in Bangla mode
  - Alignment and spacing fixed
  - Heading and body are properly separated
  - Source renders as text, not boxes

Fixes over v2:
  - Bangla diacritics (া ি ্ etc.) no longer land as boxes — the regex
    now keeps every Unicode combining mark attached to its base letter
  - Heading height is tracked from the CROPPED image, not the original,
    so body text never bleeds into the heading zone
  - Conjunct consonant sequences preserved by splitting only on true
    word-boundaries, not on every Unicode code-point boundary
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
# Cross-platform Latin font loader
# ---------------------------------------------------------------------------

_LATIN_BOLD_PATHS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
    "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf",
    "/Library/Fonts/Arial Bold.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
    "C:/Windows/Fonts/arialbd.ttf",
    "C:/Windows/Fonts/calibrib.ttf",
    "C:/Windows/Fonts/segoeuib.ttf",
]

_LATIN_REG_PATHS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
    "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
    "/Library/Fonts/Arial.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
    "C:/Windows/Fonts/arial.ttf",
    "C:/Windows/Fonts/calibri.ttf",
    "C:/Windows/Fonts/segoeui.ttf",
]

_font_cache = {}


def _discover_latin_font(bold):
    key = "bold" if bold else "reg"
    if key in _font_cache:
        return _font_cache[key]
    for path in (_LATIN_BOLD_PATHS if bold else _LATIN_REG_PATHS):
        if os.path.exists(path):
            _font_cache[key] = path
            return path
    # glob fallback
    patterns = [
        "/usr/share/fonts/**/*.ttf",
        "/usr/local/share/fonts/**/*.ttf",
        os.path.expanduser("~/.fonts/**/*.ttf"),
        "C:/Windows/Fonts/*.ttf",
        os.path.expanduser("~/Library/Fonts/*.ttf"),
        "/Library/Fonts/*.ttf",
    ]
    def ok_bold(p):
        n = os.path.basename(p).lower()
        return ("bold" in n or n.endswith("bd.ttf")) and "sans" in n \
               and "mono" not in n and "italic" not in n
    def ok_reg(p):
        n = os.path.basename(p).lower()
        return "sans" in n and "mono" not in n and "bold" not in n \
               and "italic" not in n and "light" not in n
    check = ok_bold if bold else ok_reg
    for pat in patterns:
        for path in glob.glob(pat, recursive=True):
            if check(path):
                _font_cache[key] = path
                return path
    raise RuntimeError("No Latin TTF font found. Run: sudo apt install fonts-dejavu-core")


def load_font(size, bold=False):
    return ImageFont.truetype(_discover_latin_font(bold), size)


def get_bangla_font_path(bold=False):
    filename = "NotoSansBengali-Bold.ttf" if bold else "NotoSansBengali-Regular.ttf"
    path = os.path.join(ASSETS_DIR, filename)
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Bangla font not found: {path}\n"
            "Download: https://fonts.google.com/noto/specimen/Noto+Sans+Bengali\n"
            "Place .ttf files in your assets/ folder."
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
    draw.ellipse([x1,           y1,           x1+2*radius, y1+2*radius], fill=c)
    draw.ellipse([x2-2*radius,  y1,           x2,          y1+2*radius], fill=c)
    draw.ellipse([x1,           y2-2*radius,  x1+2*radius, y2         ], fill=c)
    draw.ellipse([x2-2*radius,  y2-2*radius,  x2,          y2         ], fill=c)


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

_BANGLA_CLUSTER_RE = re.compile(
    r"[\u0980-\u09FF][\u0980-\u09FF\u200C\u200D]*"
)


def split_mixed_segments(text):
    """
    Split a mixed Bangla+Latin string into typed segments.

    Returns a list of ('bangla', chunk) | ('latin', chunk) tuples.
    Bangla diacritics and ZWJ/ZWNJ stay attached to their base letter —
    they are never the first character of a 'latin' segment.

    Example:
        'ChatGPT মার্কেটিং 2024'
        → [('latin','ChatGPT '), ('bangla','মার্কেটিং'), ('latin',' 2024')]
    """
    segments, last = [], 0
    for m in _BANGLA_CLUSTER_RE.finditer(text):
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


# ---------------------------------------------------------------------------
# Mixed-script block renderer
# ---------------------------------------------------------------------------

def render_mixed_block(text, bangla_font_path, bangla_size,
                       latin_bold_font, latin_reg_font,
                       color_hex, max_width,
                       line_spacing=10, bold=False):
    """
    Render a mixed Bangla+Latin paragraph into a transparent RGBA image.
    Returns a PIL Image sized to the actual content (width=max_width).
    """
    color_rgb = hex_to_rgb(color_hex)
    bn_font   = ImageFont.truetype(bangla_font_path, bangla_size)
    la_font   = latin_bold_font if bold else latin_reg_font

    # ---- measurement helpers (use a 1×1 probe) ----
    probe     = Image.new("RGBA", (1, 1))
    probe_drw = ImageDraw.Draw(probe)

    def seg_width(script, chunk):
        f = bn_font if script == "bangla" else la_font
        return probe_drw.textbbox((0, 0), chunk, font=f)[2]

    space_px = probe_drw.textbbox((0, 0), " ", font=la_font)[2]

    def word_width(word):
        return sum(seg_width(s, c) for s, c in split_mixed_segments(word))

    # ---- word-wrap ----
    words   = text.split(" ")
    wrapped = []
    cur_words, cur_w = [], 0
    for word in words:
        ww = word_width(word)
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

    # ---- line height = tallest glyph across both scripts ----
    bn_h   = probe_drw.textbbox((0, 0), "অ", font=bn_font)[3]
    la_h   = probe_drw.textbbox((0, 0), "Ag", font=la_font)[3]
    line_h = max(bn_h, la_h)

    n       = len(wrapped)
    total_h = max(line_h * n + line_spacing * max(n - 1, 0), 1)

    out  = Image.new("RGBA", (max_width, total_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(out)

    y = 0
    for line in wrapped:
        x = 0
        for script, chunk in split_mixed_segments(line):
            f     = bn_font if script == "bangla" else la_font
            seg_h = draw.textbbox((0, 0), chunk, font=f)[3]
            y_off = (line_h - seg_h) // 2      # vertically centre within line
            draw.text((x, y + y_off), chunk, font=f, fill=color_rgb)
            x += draw.textbbox((0, 0), chunk, font=f)[2]
        y += line_h + line_spacing

    return out


# ---------------------------------------------------------------------------
# Crop helper that also returns the ACTUAL used height
# ---------------------------------------------------------------------------

def crop_block(img, max_h):
    """Crop img to max_h pixels. Returns (cropped_img, actual_height)."""
    actual_h = min(img.height, max_h)
    return img.crop((0, 0, img.width, actual_h)), actual_h


# ---------------------------------------------------------------------------
# Main card generator
# ---------------------------------------------------------------------------

def generate_card(story, index=0, bangla=False):
    """
    Generate a 1080×1080 PNG news card.

    story  : dict  —  title, summary, source, link
    index  : int   —  card_0.png, card_1.png …
    bangla : bool  —  True = Bangla/mixed mode
    """
    img  = Image.new("RGB", (CARD_W, CARD_H), hex_to_rgb(BG_COLOR))
    draw = ImageDraw.Draw(img)

    # ---- logo ----
    logo_path = os.path.join(ASSETS_DIR, "logo.png")
    logo      = Image.open(logo_path).convert("RGBA").resize((90, 90), Image.LANCZOS)
    circle    = Image.new("RGBA", (106, 106), (0, 0, 0, 0))
    ImageDraw.Draw(circle).ellipse([0, 0, 106, 106], fill=(255, 255, 255, 255))
    img.paste(circle, (44, 44), circle)
    img.paste(logo,   (52, 52), logo)

    max_text_w = CARD_W - 120   # 60 px left + 60 px right margin

    # ======================================================================
    # SHARED HEADER  (logo already done above)
    # ======================================================================

    tag_font = load_font(20, bold=True)
    tag_text = "AI NEWS"
    tb       = draw.textbbox((0, 0), tag_text, font=tag_font)
    tag_w, tag_h = tb[2] + 32, tb[3] + 16
    tag_x, tag_y = 60, 190

    if bangla:
        # ---- page name in Bangla ----
        bn_bold = get_bangla_font_path(bold=True)
        bn_reg  = get_bangla_font_path(bold=False)

        lat_28b = load_font(28, bold=True)
        lat_18  = load_font(18, bold=False)
        lat_52b = load_font(52, bold=True)
        lat_30  = load_font(30, bold=False)
        lat_24  = load_font(24, bold=False)

        name_img = render_mixed_block(
            "অর্কেস্ট্রেটর পালস",
            bn_bold, 28, lat_28b, lat_28b,
            ACCENT_COLOR, max_text_w, line_spacing=4, bold=True,
        )
        paste_rgba(img, name_img, (160, 58))
        draw.text((160, 94), "Daily AI News & Trends",
                  font=lat_18, fill=hex_to_rgb(SOURCE_COLOR))
    else:
        font_name    = load_font(28, bold=True)
        font_tagline = load_font(18)
        draw.text((160, 58), "Orchestrator Pulse",
                  font=font_name, fill=hex_to_rgb(ACCENT_COLOR))
        draw.text((160, 94), "Daily AI News & Trends",
                  font=font_tagline, fill=hex_to_rgb(SOURCE_COLOR))

    # ---- AI NEWS badge (shared) ----
    draw_rounded_rect(draw, (tag_x, tag_y, tag_x + tag_w, tag_y + tag_h), 8, "#FFFFFF")
    draw.text((tag_x + 16, tag_y + 8), tag_text,
              font=tag_font, fill=hex_to_rgb(BG_COLOR))
    draw.rectangle(
        [60, tag_y + tag_h + 20, CARD_W - 60, tag_y + tag_h + 22],
        fill=hex_to_rgb(DIVIDER_COLOR),
    )

    # ======================================================================
    # CONTENT AREA  —  y starts just below the divider
    # ======================================================================

    y = tag_y + tag_h + 44   # ~258 px from top

    # ---- HEADLINE ----
    MAX_HEADLINE_H = 210     # hard ceiling for the headline zone

    if bangla:
        title_img = render_mixed_block(
            story["title"],
            bn_bold, 52, lat_52b, lat_52b,
            HEADLINE_COLOR, max_text_w, line_spacing=14, bold=True,
        )
        title_img, title_used_h = crop_block(title_img, MAX_HEADLINE_H)
        paste_rgba(img, title_img, (60, y))
    else:
        font_headline = load_font(52, bold=True)
        title_lines   = wrap_text_latin(story["title"], font_headline, max_text_w, draw)[:3]
        title_used_h  = 0
        for line in title_lines:
            draw.text((60, y + title_used_h), line,
                      font=font_headline, fill=hex_to_rgb(HEADLINE_COLOR))
            title_used_h += 60

    y += title_used_h + 22   # breathing room after headline  ← FIX: use actual height

    # ---- accent bar separating headline from body ----
    draw.rectangle([60, y, 160, y + 4], fill=hex_to_rgb(ACCENT_COLOR))
    y += 32                  # breathing room before body

    # ---- BODY SUMMARY ----
    MAX_SUMMARY_H = 300      # hard ceiling for the body zone

    summary = story["summary"]
    if len(summary) > 400:
        summary = summary[:400] + "..."

    if bangla:
        summary_img = render_mixed_block(
            summary,
            bn_reg, 30, lat_30, lat_30,
            SUMMARY_COLOR, max_text_w, line_spacing=12, bold=False,
        )
        summary_img, _ = crop_block(summary_img, MAX_SUMMARY_H)
        paste_rgba(img, summary_img, (60, y))
    else:
        font_summary = load_font(30)
        for line in wrap_text_latin(summary, font_summary, max_text_w, draw)[:7]:
            draw.text((60, y), line, font=font_summary, fill=hex_to_rgb(SUMMARY_COLOR))
            y += 40

    # ======================================================================
    # FOOTER  — source (left) + handle (right)
    # ======================================================================

    FOOTER_Y = CARD_H - 90

    if bangla:
        source_img = render_mixed_block(
            f"সোর্স: {story['source']}",
            bn_reg, 24, lat_24, lat_24,
            SOURCE_COLOR, max_text_w, line_spacing=6, bold=False,
        )
        paste_rgba(img, source_img, (60, FOOTER_Y))
    else:
        font_source = load_font(24)
        draw.text((60, FOOTER_Y), f"Source: {story['source']}",
                  font=font_source, fill=hex_to_rgb(SOURCE_COLOR))

    # handle — always Latin
    handle_font = load_font(24, bold=True)
    handle      = "@OrchestratorPulse"
    hbbox       = draw.textbbox((0, 0), handle, font=handle_font)
    draw.text(
        (CARD_W - hbbox[2] - 60, FOOTER_Y),
        handle, font=handle_font, fill=hex_to_rgb(ACCENT_COLOR),
    )

    # bottom accent bar
    draw.rectangle([0, CARD_H - 8, CARD_W, CARD_H], fill=hex_to_rgb(ACCENT_COLOR))

    # ---- save ----
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_path = os.path.join(OUTPUT_DIR, f"card_{index}.png")
    img.save(out_path)
    print(f"Saved → {out_path}")
    return out_path


# ---------------------------------------------------------------------------
# Quick test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("Latin bold:", _discover_latin_font(bold=True))
    print("Latin reg: ", _discover_latin_font(bold=False))
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