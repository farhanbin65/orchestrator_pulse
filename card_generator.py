from PIL import Image, ImageDraw, ImageFont
from bangla_text_renderer import BanglaTextRenderer
import os

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
# Helpers
# ---------------------------------------------------------------------------

def hex_to_rgb(hex_color):
    h = hex_color.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def hex_to_rgba(hex_color, alpha=255):
    r, g, b = hex_to_rgb(hex_color)
    return (r, g, b, alpha)


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


def get_bangla_font_path(bold=False):
    filename = "NotoSansBengali-Bold.ttf" if bold else "NotoSansBengali-Regular.ttf"
    path = os.path.join(ASSETS_DIR, filename)
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Bangla font not found: {path}\n"
            "Download from: https://fonts.google.com/noto/specimen/Noto+Sans+Bengali\n"
            "Place the .ttf files inside your assets/ folder."
        )
    return path


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
    """Word-wrap for Latin fonts using PIL textbbox."""
    words   = text.split(" ")
    lines   = []
    current = ""
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


def paste_rgba(base, overlay, position):
    """Paste an RGBA PIL image onto an RGB base at (x, y)."""
    base.paste(overlay, position, overlay)


# ---------------------------------------------------------------------------
# Bangla text block renderer
# ---------------------------------------------------------------------------

def render_bangla_block(text, font_path, font_size, color_hex, max_width,
                        line_spacing=10, align="left"):
    """
    Render a Bangla text block and return a PIL RGBA image
    sized exactly to its content.
    """
    renderer = BanglaTextRenderer(
        font_path=font_path,
        font_size=font_size,
        color=hex_to_rgba(color_hex),
    )
    # render_text returns a PIL image with transparent background
    img = renderer.render_text(
        text,
        width=max_width,
        line_spacing=line_spacing,
        align=align,
        background=None,          # transparent
    )
    return img.convert("RGBA")


# ---------------------------------------------------------------------------
# Main card generator
# ---------------------------------------------------------------------------

def generate_card(story, index=0, bangla=False):
    # Base canvas — RGB
    img  = Image.new("RGB", (CARD_W, CARD_H), hex_to_rgb(BG_COLOR))
    draw = ImageDraw.Draw(img)

    # --- Logo ---
    logo_path = os.path.join(ASSETS_DIR, "logo.png")
    logo      = Image.open(logo_path).convert("RGBA")
    logo      = logo.resize((90, 90), Image.LANCZOS)

    circle = Image.new("RGBA", (106, 106), (0, 0, 0, 0))
    ImageDraw.Draw(circle).ellipse([0, 0, 106, 106], fill=(255, 255, 255, 255))
    img.paste(circle, (44, 44), circle)
    img.paste(logo,   (52, 52), logo)

    max_text_w = CARD_W - 120   # left margin 60 + right margin 60

    # -----------------------------------------------------------------------
    # BANGLA MODE  — use BanglaTextRenderer for all Bangla strings
    # -----------------------------------------------------------------------
    if bangla:
        bangla_font_bold   = get_bangla_font_path(bold=True)
        bangla_font_reg    = get_bangla_font_path(bold=False)
        page_name          = "অর্কেস্ট্রেটর পালস"

        # Header — page name
        name_img = render_bangla_block(page_name, bangla_font_bold, 28, ACCENT_COLOR, max_text_w)
        paste_rgba(img, name_img, (160, 58))

        # Header — tagline (Latin, no Bangla renderer needed)
        font_tagline = load_font(18)
        draw.text((160, 94), "Daily AI News & Trends", font=font_tagline, fill=hex_to_rgb(SOURCE_COLOR))

        # Tag badge
        tag_font = load_font(20, bold=True)
        tag_text = "AI NEWS"
        tag_bbox = draw.textbbox((0, 0), tag_text, font=tag_font)
        tag_w    = tag_bbox[2] + 32
        tag_h    = tag_bbox[3] + 16
        tag_x, tag_y = 60, 190
        draw_rounded_rect(draw, (tag_x, tag_y, tag_x + tag_w, tag_y + tag_h), 8, "#FFFFFF")
        draw.text((tag_x + 16, tag_y + 8), tag_text, font=tag_font, fill=hex_to_rgb(BG_COLOR))
        draw.rectangle(
            [60, tag_y + tag_h + 20, CARD_W - 60, tag_y + tag_h + 22],
            fill=hex_to_rgb(DIVIDER_COLOR)
        )

        y = tag_y + tag_h + 44

        # Headline
        title     = story["title"]
        title_img = render_bangla_block(title, bangla_font_bold, 52, HEADLINE_COLOR,
                                        max_text_w, line_spacing=12, align="left")
        # Clamp to 3 lines worth of height (≈ 3 * (52 + 12) = 192px)
        max_headline_h = 192
        if title_img.height > max_headline_h:
            title_img = title_img.crop((0, 0, title_img.width, max_headline_h))
        paste_rgba(img, title_img, (60, y))
        y += title_img.height + 10

        draw.rectangle([60, y, 160, y + 4], fill=hex_to_rgb(ACCENT_COLOR))
        y += 24

        # Summary
        summary = story["summary"]
        summary = summary[:400] + "..." if len(summary) > 400 else summary
        summary_img = render_bangla_block(summary, bangla_font_reg, 30, SUMMARY_COLOR,
                                          max_text_w, line_spacing=10, align="left")
        # Clamp to 7 lines worth (≈ 7 * 40 = 280px)
        max_summary_h = 280
        if summary_img.height > max_summary_h:
            summary_img = summary_img.crop((0, 0, summary_img.width, max_summary_h))
        paste_rgba(img, summary_img, (60, y))

        # Footer source (Bangla)
        source_img = render_bangla_block(
            f"Source: {story['source']}", bangla_font_reg, 24, SOURCE_COLOR, max_text_w
        )
        paste_rgba(img, source_img, (60, CARD_H - 90))

    # -----------------------------------------------------------------------
    # ENGLISH / LATIN MODE — plain PIL as before
    # -----------------------------------------------------------------------
    else:
        font_name    = load_font(28, bold=True)
        font_tagline = load_font(18)
        font_headline = load_font(52, bold=True)
        font_summary  = load_font(30)
        font_source   = load_font(24)

        draw.text((160, 58), "Orchestrator Pulse",      font=font_name,    fill=hex_to_rgb(ACCENT_COLOR))
        draw.text((160, 94), "Daily AI News & Trends",  font=font_tagline, fill=hex_to_rgb(SOURCE_COLOR))

        tag_font = load_font(20, bold=True)
        tag_text = "AI NEWS"
        tag_bbox = draw.textbbox((0, 0), tag_text, font=tag_font)
        tag_w    = tag_bbox[2] + 32
        tag_h    = tag_bbox[3] + 16
        tag_x, tag_y = 60, 190
        draw_rounded_rect(draw, (tag_x, tag_y, tag_x + tag_w, tag_y + tag_h), 8, "#FFFFFF")
        draw.text((tag_x + 16, tag_y + 8), tag_text, font=tag_font, fill=hex_to_rgb(BG_COLOR))
        draw.rectangle(
            [60, tag_y + tag_h + 20, CARD_W - 60, tag_y + tag_h + 22],
            fill=hex_to_rgb(DIVIDER_COLOR)
        )

        y = tag_y + tag_h + 44

        for line in wrap_text(story["title"], font_headline, max_text_w, draw)[:3]:
            draw.text((60, y), line, font=font_headline, fill=hex_to_rgb(HEADLINE_COLOR))
            y += 60

        y += 10
        draw.rectangle([60, y, 160, y + 4], fill=hex_to_rgb(ACCENT_COLOR))
        y += 24

        summary = story["summary"]
        summary = summary[:400] + "..." if len(summary) > 400 else summary
        for line in wrap_text(summary, font_summary, max_text_w, draw)[:7]:
            draw.text((60, y), line, font=font_summary, fill=hex_to_rgb(SUMMARY_COLOR))
            y += 40

        draw.text((60, CARD_H - 90), f"Source: {story['source']}",
                  font=font_source, fill=hex_to_rgb(SOURCE_COLOR))

    # --- Handle (always Latin) ---
    handle_font = load_font(24, bold=True)
    handle      = "@OrchestratorPulse"
    hbbox       = draw.textbbox((0, 0), handle, font=handle_font)
    draw.text((CARD_W - hbbox[2] - 60, CARD_H - 90),
              handle, font=handle_font, fill=hex_to_rgb(ACCENT_COLOR))

    # --- Bottom accent bar ---
    draw.rectangle([0, CARD_H - 8, CARD_W, CARD_H], fill=hex_to_rgb(ACCENT_COLOR))

    # --- Save ---
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_path = os.path.join(OUTPUT_DIR, f"card_{index}.png")
    img.save(out_path)
    print(f"Saved → {out_path}")
    return out_path


# ---------------------------------------------------------------------------
# Quick test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    english_story = {
        "title":   "OpenAI Releases GPT-5 With Breakthrough Reasoning Capabilities",
        "summary": "OpenAI has announced GPT-5, claiming it significantly outperforms previous models "
                   "on complex reasoning tasks, coding benchmarks, and multimodal understanding.",
        "source":  "TechCrunch",
        "link":    "https://techcrunch.com",
    }
    bangla_story = {
        "title":   "ওপেনএআই জিপিটি-৫ প্রকাশ করেছে অসাধারণ যুক্তি ক্ষমতা নিয়ে",
        "summary": "ওপেনএআই জিপিটি-৫ ঘোষণা করেছে, যা জটিল যুক্তি কাজ, কোডিং বেঞ্চমার্ক "
                   "এবং মাল্টিমোডাল বোঝাপড়ায় আগের মডেলগুলোকে উল্লেখযোগ্যভাবে ছাড়িয়ে গেছে।",
        "source":  "টেকক্রাঞ্চ",
        "link":    "https://techcrunch.com",
    }

    generate_card(english_story, index=0, bangla=False)
    generate_card(bangla_story,  index=1, bangla=True)