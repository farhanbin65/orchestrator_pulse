# PRODUCTION-READY NEWS CARD GENERATOR (DUAL OUTPUT)
# Generates:
# 1. English Card
# 2. Bangla Card (mixed supported)

import os
from PIL import Image, ImageDraw, ImageFont

CARD_W, CARD_H = 1080, 1080
BG_COLOR = (13, 13, 13)
WHITE = (255, 255, 255)
GRAY = (180, 180, 180)

ASSETS_DIR = "assets"
OUTPUT_DIR = "output"

# ---------------- FONT LOADING ----------------

def load_font(path, size):
    return ImageFont.truetype(path, size)

BN_FONT = load_font(os.path.join(ASSETS_DIR, "NotoSansBengali-Regular.ttf"), 40)
BN_FONT_BOLD = load_font(os.path.join(ASSETS_DIR, "NotoSansBengali-Bold.ttf"), 44)
EN_FONT = load_font(os.path.join(ASSETS_DIR, "NotoSans-Regular.ttf"), 40)
EN_FONT_BOLD = load_font(os.path.join(ASSETS_DIR, "NotoSans-Bold.ttf"), 44)

# ---------------- FONT FALLBACK ----------------

def pick_font(char, bold=False):
    fonts = [BN_FONT_BOLD, EN_FONT_BOLD] if bold else [BN_FONT, EN_FONT]
    for f in fonts:
        try:
            f.getmask(char)
            return f
        except:
            continue
    return EN_FONT

# ---------------- TEXT RENDER ----------------

def draw_text_block(draw, text, x, y, max_width, line_height, color, bold=False, max_lines=None):
    words = text.split(" ")
    lines = []
    current = ""

    for word in words:
        test = current + (" " if current else "") + word
        w = sum(draw.textbbox((0,0), c, font=pick_font(c, bold))[2] for c in test)

        if w <= max_width:
            current = test
        else:
            lines.append(current)
            current = word

    if current:
        lines.append(current)

    if max_lines:
        lines = lines[:max_lines]

    for i, line in enumerate(lines):
        cx = x
        for char in line:
            font = pick_font(char, bold)
            bbox = draw.textbbox((0,0), char, font=font)
            draw.text((cx, y + i * line_height), char, font=font, fill=color)
            cx += bbox[2]

    return len(lines) * line_height

# ---------------- CARD BUILDER ----------------

def build_card(story, index=0, lang="en"):
    img = Image.new("RGB", (CARD_W, CARD_H), BG_COLOR)
    draw = ImageDraw.Draw(img)

    max_w = CARD_W - 120
    y = 200

    # HEADER
    if lang == "bn":
        title_prefix = "অর্কেস্ট্রেটর পালস"
    else:
        title_prefix = "Orchestrator Pulse"

    draw_text_block(draw, title_prefix, 60, 60, max_w, 40, WHITE, bold=True)

    # TITLE
    title = story["title"].replace("|", "•")
    h_used = draw_text_block(draw, title, 60, y, max_w, 55, WHITE, bold=True, max_lines=3)

    y += h_used + 20

    draw.rectangle([60, y, 160, y+4], fill=WHITE)
    y += 30

    # SUMMARY
    summary = story["summary"][:400]
    draw_text_block(draw, summary, 60, y, max_w, 45, GRAY, bold=False, max_lines=7)

    # FOOTER
    if lang == "bn":
        source_text = f"সোর্স: {story['source']}"
    else:
        source_text = f"Source: {story['source']}"

    draw_text_block(draw, source_text, 60, CARD_H-100, max_w, 40, GRAY)

    handle = "@OrchestratorPulse"
    bbox = draw.textbbox((0,0), handle, font=EN_FONT_BOLD)
    draw.text((CARD_W - bbox[2] - 60, CARD_H-100), handle, font=EN_FONT_BOLD, fill=WHITE)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    path = os.path.join(OUTPUT_DIR, f"card_{lang}_{index}.png")
    img.save(path)
    return path

# ---------------- MAIN GENERATOR ----------------

def generate_dual_cards(english_story, bangla_story, index=0):
    en_path = build_card(english_story, index, lang="en")
    bn_path = build_card(bangla_story, index, lang="bn")

    print("Generated:")
    print(en_path)
    print(bn_path)

    return en_path, bn_path

# ---------------- TEST ----------------

if __name__ == "__main__":
    english_story = {
        "title": "OpenAI launches new AI model!",
        "summary": "The new model improves reasoning, speed, and efficiency across multiple domains.",
        "source": "TechCrunch"
    }

    bangla_story = {
        "title": "OpenAI নতুন AI মডেল চালু করেছে!",
        "summary": "এই নতুন মডেলটি যুক্তি, গতি এবং দক্ষতায় বড় উন্নতি এনেছে।",
        "source": "TechCrunch"
    }

    generate_dual_cards(english_story, bangla_story)
