from PIL import Image, ImageDraw, ImageFont
import textwrap
import os

# Card dimensions (good for Facebook)
CARD_W = 1080
CARD_H = 1080

# Colors
BG_COLOR       = "#0D0D0D"   # near black background
ACCENT_COLOR   = "#FFFFFF"   # white
HEADLINE_COLOR = "#FFFFFF"   # white
SUMMARY_COLOR  = "#CCCCCC"   # light grey
SOURCE_COLOR   = "#888888"   # muted grey
TAG_BG         = "#1A1A1A"   # slightly lighter black for tag bg
DIVIDER_COLOR  = "#333333"   # subtle divider

ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")

def hex_to_rgb(hex_color):
    h = hex_color.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def load_font(size, bold=False):
    font_paths = [
        f"/usr/share/fonts/truetype/dejavu/DejaVuSans{'-Bold' if bold else ''}.ttf",
        f"/usr/share/fonts/truetype/liberation/LiberationSans{'-Bold' if bold else '-Regular'}.ttf",
        f"C:/Windows/Fonts/{'arialbd' if bold else 'arial'}.ttf",
    ]
    for path in font_paths:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()

def draw_rounded_rect(draw, xy, radius, fill):
    x1, y1, x2, y2 = xy
    fill_rgb = hex_to_rgb(fill)
    draw.rectangle([x1 + radius, y1, x2 - radius, y2], fill=fill_rgb)
    draw.rectangle([x1, y1 + radius, x2, y2 - radius], fill=fill_rgb)
    draw.ellipse([x1, y1, x1 + 2*radius, y1 + 2*radius], fill=fill_rgb)
    draw.ellipse([x2 - 2*radius, y1, x2, y1 + 2*radius], fill=fill_rgb)
    draw.ellipse([x1, y2 - 2*radius, x1 + 2*radius, y2], fill=fill_rgb)
    draw.ellipse([x2 - 2*radius, y2 - 2*radius, x2, y2], fill=fill_rgb)

def wrap_text(text, font, max_width, draw):
    words = text.split()
    lines = []
    current = ""
    for word in words:
        test = f"{current} {word}".strip()
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

def generate_card(story, index=0):
    img = Image.new("RGB", (CARD_W, CARD_H), hex_to_rgb(BG_COLOR))
    draw = ImageDraw.Draw(img)

    # --- Logo (top left) ---
    logo_path = os.path.join(ASSETS_DIR, "logo.png")
    logo = Image.open(logo_path).convert("RGBA")
    logo_size = 90
    logo = logo.resize((logo_size, logo_size), Image.LANCZOS)
    # White circle background for logo
    circle_pad = 8
    circle_size = logo_size + circle_pad * 2
    circle = Image.new("RGBA", (circle_size, circle_size), (0, 0, 0, 0))
    cd = ImageDraw.Draw(circle)
    cd.ellipse([0, 0, circle_size, circle_size], fill=(255, 255, 255, 255))
    img.paste(circle, (44, 44), circle)
    img.paste(logo, (44 + circle_pad, 44 + circle_pad), logo)

    # --- Page name (top, next to logo) ---
    font_name = load_font(28, bold=True)
    font_tagline = load_font(18)
    draw.text((160, 58), "Orchestrator Pulse", font=font_name, fill=hex_to_rgb(ACCENT_COLOR))
    draw.text((160, 94), "Daily AI News & Trends", font=font_tagline, fill=hex_to_rgb(SOURCE_COLOR))

    # --- AI NEWS tag ---
    tag_font = load_font(20, bold=True)
    tag_text = "AI NEWS"
    tag_bbox = draw.textbbox((0, 0), tag_text, font=tag_font)
    tag_w = tag_bbox[2] + 32
    tag_h = tag_bbox[3] + 16
    tag_x = 60
    tag_y = 200
    draw_rounded_rect(draw, (tag_x, tag_y, tag_x + tag_w, tag_y + tag_h), 8, "#FFFFFF")
    draw.text((tag_x + 16, tag_y + 8), tag_text, font=tag_font, fill=hex_to_rgb(BG_COLOR))

    # --- Divider line ---
    draw.rectangle([60, tag_y + tag_h + 24, CARD_W - 60, tag_y + tag_h + 26],
                   fill=hex_to_rgb(DIVIDER_COLOR))

    # --- Headline ---
    font_headline = load_font(52, bold=True)
    font_summary  = load_font(30)
    font_source   = load_font(24)

    headline = story["title"]
    max_text_w = CARD_W - 120
    y = tag_y + tag_h + 56

    lines = wrap_text(headline, font_headline, max_text_w, draw)
    lines = lines[:3]  # max 3 lines
    for line in lines:
        draw.text((60, y), line, font=font_headline, fill=hex_to_rgb(HEADLINE_COLOR))
        bbox = draw.textbbox((0, 0), line, font=font_headline)
        y += bbox[3] + 10
    y += 20

    # --- Divider ---
    draw.rectangle([60, y, 160, y + 4], fill=hex_to_rgb(ACCENT_COLOR))
    y += 28

    # --- Summary ---
    summary = story["summary"][:220].strip()
    if len(story["summary"]) > 220:
        summary += "..."
    sum_lines = wrap_text(summary, font_summary, max_text_w, draw)
    sum_lines = sum_lines[:4]
    for line in sum_lines:
        draw.text((60, y), line, font=font_summary, fill=hex_to_rgb(SUMMARY_COLOR))
        bbox = draw.textbbox((0, 0), line, font=font_summary)
        y += bbox[3] + 8

    # --- Source tag bottom left ---
    source_text = f"Source: {story['source']}"
    draw.text((60, CARD_H - 80), source_text, font=font_source, fill=hex_to_rgb(SOURCE_COLOR))

    # --- Handle bottom right ---
    handle_font = load_font(24, bold=True)
    handle = "@OrchestratorPulse"
    hbbox = draw.textbbox((0, 0), handle, font=handle_font)
    draw.text((CARD_W - hbbox[2] - 60, CARD_H - 80), handle,
              font=handle_font, fill=hex_to_rgb(ACCENT_COLOR))

    # --- Bottom accent line ---
    draw.rectangle([0, CARD_H - 8, CARD_W, CARD_H], fill=hex_to_rgb(ACCENT_COLOR))

    # Save
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_path = os.path.join(OUTPUT_DIR, f"card_{index}.png")
    img.save(out_path, quality=95)
    print(f"Card saved: {out_path}")
    return out_path

if __name__ == "__main__":
    test_story = {
        "title": "OpenAI Releases GPT-5 With Breakthrough Reasoning Capabilities",
        "summary": "OpenAI has announced the release of GPT-5, claiming it significantly outperforms previous models on complex reasoning tasks, coding benchmarks, and multimodal understanding.",
        "source": "TechCrunch",
        "link": "https://techcrunch.com"
    }
    generate_card(test_story, 0)
    print("Test card generated — check the output folder!")
