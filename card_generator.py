import os
import re
import random
import requests
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont

load_dotenv()

# --- Constants ---
CARD_W, CARD_H = 1080, 1080
BG_COLOR, ACCENT_COLOR = "#0D0D0D", "#FFFFFF"
HEADLINE_COLOR, SUMMARY_COLOR = "#FFFFFF", "#CCCCCC"
SOURCE_COLOR, DIVIDER_COLOR = "#888888", "#333333"

ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")

UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY")
PEXELS_API_KEY      = os.getenv("PEXELS_API_KEY")
GROQ_API_KEY        = os.getenv("GROQ_API_KEY")

# ── Query Generation ──────────────────────────────────────────────────────────

def extract_query_ai(title):
    """Use Groq/LLaMA to generate a unique, visual, specific image search query."""
    if not GROQ_API_KEY:
        return extract_query_fallback(title)
    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{
                "role": "user",
                "content": (
                    "You are helping find a photo for a news card. "
                    "Given the headline below, return ONLY a 3-5 word image search query "
                    "that describes a specific, visual, photographic scene — NOT abstract concepts. "
                    "Think like a photo editor: what would you actually photograph?\n\n"
                    "Rules:\n"
                    "- Be specific and visual (e.g. 'engineer testing robot arm' not 'robotics technology')\n"
                    "- Avoid generic words like 'technology', 'digital', 'futuristic', 'abstract'\n"
                    "- Return ONLY the query, no punctuation, no explanation\n\n"
                    f"Headline: {title}"
                )
            }],
            max_tokens=20,
            temperature=0.9   # higher = more variety per run
        )
        query = response.choices[0].message.content.strip().strip('"').strip("'")
        print(f"  🤖 Groq query: '{query}'")
        return query
    except Exception as e:
        print(f"  ⚠️  Groq query failed: {e} — using fallback")
        return extract_query_fallback(title)


def extract_query_fallback(title):
    """Keyword-based fallback when Groq is unavailable."""
    title_lower = title.lower()

    # More specific keyword map — avoids generic "AI technology" repeats
    keyword_map = {
        "chatgpt":      "person using AI chatbot on laptop",
        "gpt":          "AI language model interface screen",
        "openai":       "tech researcher working at computer",
        "gemini":       "Google AI research lab",
        "deepmind":     "scientist working on neural network",
        "claude":       "AI assistant conversation interface",
        "meta":         "social media AI data center",
        "llama":        "open source AI model code",
        "llm":          "data scientist training language model",
        "robot":        "humanoid robot in warehouse",
        "robotics":     "engineer testing robot arm",
        "autonomous":   "self driving car sensors",
        "self-driving": "autonomous vehicle on highway",
        "chip":         "semiconductor chip manufacturing",
        "nvidia":       "GPU server data center",
        "data center":  "rows of servers data center",
        "quantum":      "quantum computing laboratory",
        "startup":      "tech startup team whiteboard",
        "funding":      "venture capital business meeting",
        "regulation":   "government building policy meeting",
        "copyright":    "legal books gavel courtroom",
        "privacy":      "cybersecurity lock encrypted data",
        "cyber":        "hacker dark room screens",
        "health":       "AI medical diagnosis hospital",
        "drug":         "pharmaceutical lab research",
        "climate":      "renewable energy solar panels",
        "energy":       "wind turbines power grid",
        "image":        "AI image generation art studio",
        "video":        "AI video production studio",
        "voice":        "microphone voice assistant speaker",
        "search":       "person searching on computer",
        "agent":        "AI workflow automation dashboard",
        "model":        "deep learning training visualization",
    }

    for key, value in keyword_map.items():
        if key in title_lower:
            return value

    # Extract meaningful words as last resort
    stopwords = {
        "a","an","the","and","or","for","in","on","of","to","is","with",
        "how","why","what","this","that","are","was","has","will","from",
        "by","as","at","it","be","its","new","says","say","could","would"
    }
    words = [w.strip(".,:-") for w in title_lower.split() if w not in stopwords and len(w) > 3]
    return " ".join(words[:3]) + " technology" if words else "AI research laboratory"


# ── Image Fetchers ────────────────────────────────────────────────────────────

def fetch_unsplash_image(query, save_path):
    if not UNSPLASH_ACCESS_KEY:
        print("  ⚠️  UNSPLASH_ACCESS_KEY not set")
        return None
    try:
        res = requests.get(
            "https://api.unsplash.com/photos/random",
            params={
                "query":          query,
                "orientation":    "squarish",
                "content_filter": "high",
                "count":          10        # fetch 10, pick one randomly → more variety
            },
            headers={"Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}"},
            timeout=8
        )
        res.raise_for_status()
        photos = res.json()

        # photos is a list when count > 1
        if isinstance(photos, list) and photos:
            photo = random.choice(photos)
        elif isinstance(photos, dict):
            photo = photos
        else:
            return None

        img_url   = photo["urls"]["regular"]
        img_bytes = requests.get(img_url, timeout=10).content
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        with open(save_path, "wb") as f:
            f.write(img_bytes)
        print(f"  📷 Unsplash: '{query}'")
        return save_path

    except Exception as e:
        print(f"  ⚠️  Unsplash failed: {e}")
        return None


def fetch_pexels_image(query, save_path):
    if not PEXELS_API_KEY:
        print("  ⚠️  PEXELS_API_KEY not set")
        return None
    try:
        res = requests.get(
            "https://api.pexels.com/v1/search",
            params={
                "query":       query,
                "orientation": "square",
                "per_page":    15,
                "page":        random.randint(1, 5)   # random page = variety
            },
            headers={"Authorization": PEXELS_API_KEY},
            timeout=8
        )
        res.raise_for_status()
        data    = res.json()
        photos  = data.get("photos", [])

        if not photos:
            print(f"  ⚠️  Pexels: no results for '{query}'")
            return None

        photo     = random.choice(photos)
        img_url   = photo["src"]["large"]
        img_bytes = requests.get(img_url, timeout=10).content
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        with open(save_path, "wb") as f:
            f.write(img_bytes)
        print(f"  📷 Pexels: '{query}'")
        return save_path

    except Exception as e:
        print(f"  ⚠️  Pexels failed: {e}")
        return None


def fetch_article_image(query, save_path="output/shared_image.jpg"):
    """
    Randomly picks Unsplash or Pexels as primary source.
    Falls back to the other if primary fails.
    Falls back to a broader query if both fail on specific query.
    """
    os.makedirs(os.path.dirname(save_path), exist_ok=True)

    # Randomly assign primary/fallback so both APIs get used over time
    if random.random() < 0.5:
        primary,  primary_name  = fetch_unsplash_image, "Unsplash"
        fallback, fallback_name = fetch_pexels_image,   "Pexels"
    else:
        primary,  primary_name  = fetch_pexels_image,   "Pexels"
        fallback, fallback_name = fetch_unsplash_image, "Unsplash"

    print(f"  🎲 Trying {primary_name} first...")

    # Try specific query on primary
    result = primary(query, save_path)
    if result:
        return result

    # Try specific query on fallback
    print(f"  🔄 Falling back to {fallback_name}...")
    result = fallback(query, save_path)
    if result:
        return result

    # Both failed on specific query — try broader fallback queries
    broader_queries = [
        "artificial intelligence research",
        "technology innovation",
        "computer science lab",
        "AI data center"
    ]
    for bq in broader_queries:
        print(f"  🔄 Trying broader query: '{bq}'")
        result = primary(bq, save_path)
        if result:
            return result
        result = fallback(bq, save_path)
        if result:
            return result

    print("  ❌ All image sources failed — text-only card")
    return None


# ── extract_query (public API used by main.py) ────────────────────────────────
def extract_query(title):
    """Main entry point — uses Groq if available, falls back to keyword map."""
    return extract_query_ai(title)


# ── Helpers ───────────────────────────────────────────────────────────────────
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
    words = text.replace('\n', ' ').split(" ")
    lines, current_line = [], ""
    for word in words:
        if not word:
            continue
        test_line = f"{current_line} {word}".strip()
        if draw.textbbox((0, 0), test_line, font=font)[2] <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)
    return lines

def load_font(size, bold=False):
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
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()

def get_bangla_font_path(bold=False):
    name = "NotoSansBengali-Bold.ttf" if bold else "NotoSansBengali-Regular.ttf"
    return os.path.join(ASSETS_DIR, name)

_BANGLA_CLUSTER_RE = re.compile(
    r"[\u0980-\u09FF\u0964\u0965][\u0980-\u09FF\u0964\u0965\u200C\u200D]*"
)

def split_mixed_segments(text):
    segments, last = [], 0
    for m in _BANGLA_CLUSTER_RE.finditer(text):
        if m.start() > last:
            segments.append(("latin", text[last:m.start()]))
        segments.append(("bangla", m.group()))
        last = m.end()
    if last < len(text):
        segments.append(("latin", text[last:]))
    return segments or [("latin", text)]

def render_mixed_block(text, bn_path, bn_sz, la_bold, la_reg, col, max_w,
                        spacing=12, bold=False, max_lines=None):
    rgb  = hex_to_rgb(col)
    bn_f = ImageFont.truetype(bn_path, bn_sz)
    la_f = la_bold if bold else la_reg
    words = text.split(" ")
    wrapped, current_line, current_w = [], [], 0
    space_px = ImageDraw.Draw(Image.new("RGBA", (1, 1))).textbbox((0, 0), " ", font=la_f)[2]
    for word in words:
        ww = sum(
            ImageDraw.Draw(Image.new("RGBA", (1, 1))).textbbox((0, 0), c,
                font=(bn_f if s == "bangla" else la_f))[2]
            for s, c in split_mixed_segments(word)
        )
        if not current_line or current_w + space_px + ww <= max_w:
            current_line.append(word)
            current_w += (space_px if len(current_line) > 1 else 0) + ww
        else:
            wrapped.append(" ".join(current_line))
            current_line, current_w = [word], ww
    if current_line:
        wrapped.append(" ".join(current_line))
    if max_lines:
        wrapped = wrapped[:max_lines]
    line_h = max(bn_sz + 5, 35)
    out    = Image.new("RGBA", (max_w, (line_h + spacing) * len(wrapped)), (0, 0, 0, 0))
    d      = ImageDraw.Draw(out)
    curr_y = 0
    for line in wrapped:
        curr_x = 0
        for s, c in split_mixed_segments(line):
            f = bn_f if s == "bangla" else la_f
            d.text((curr_x, curr_y), c, font=f, fill=rgb)
            curr_x += d.textbbox((0, 0), c, font=f)[2]
        curr_y += line_h + spacing
    return out


# ── Card Generator ────────────────────────────────────────────────────────────
def generate_card(story, index=0, bangla=False, article_image_path=None):
    """
    Flow: Header → Badge → Headline → Accent bar → Photo → Footer
    article_image_path=None  → auto-fetch via Groq query + Unsplash/Pexels
    article_image_path=path  → reuse already-downloaded image (English + Bangla share one fetch)
    """
    if article_image_path is None:
        query = extract_query(story["title"])
        img_save = os.path.join(OUTPUT_DIR, f"article_image_{index}.jpg")
        article_image_path = fetch_article_image(query, save_path=img_save)

    img  = Image.new("RGB", (CARD_W, CARD_H), hex_to_rgb(BG_COLOR))
    draw = ImageDraw.Draw(img)
    max_text_w = CARD_W - 120

    # 1. Header
    logo_path = os.path.join(ASSETS_DIR, "logo.png")
    if os.path.exists(logo_path):
        logo   = Image.open(logo_path).convert("RGBA").resize((90, 90), Image.LANCZOS)
        circle = Image.new("RGBA", (106, 106), (0, 0, 0, 0))
        ImageDraw.Draw(circle).ellipse([0, 0, 106, 106], fill=(255, 255, 255, 255))
        img.paste(circle, (44, 44), circle)
        img.paste(logo,   (52, 52), logo)

    if bangla:
        bn_bold  = get_bangla_font_path(True)
        lat_28b  = load_font(28, True)
        name_img = render_mixed_block(
            "অর্কেস্ট্রেটর পালস", bn_bold, 28, lat_28b, lat_28b,
            ACCENT_COLOR, max_text_w, bold=True
        )
        paste_rgba(img, name_img, (160, 58))
        draw.text((160, 94), "Daily AI News & Trends",
                  font=load_font(18), fill=hex_to_rgb(SOURCE_COLOR))
    else:
        draw.text((160, 58), "Orchestrator Pulse",
                  font=load_font(28, True), fill=hex_to_rgb(ACCENT_COLOR))
        draw.text((160, 94), "Daily AI News & Trends",
                  font=load_font(18),       fill=hex_to_rgb(SOURCE_COLOR))

    # 2. Badge + divider
    draw_rounded_rect(draw, (60, 190, 170, 226), 8, "#FFFFFF")
    draw.text((76, 198), "AI NEWS", font=load_font(20, bold=True), fill=hex_to_rgb(BG_COLOR))
    draw.rectangle([60, 246, CARD_W - 60, 248], fill=hex_to_rgb(DIVIDER_COLOR))

    y = 280

    # 3. Headline
    if bangla:
        bn_bold   = get_bangla_font_path(True)
        lat_h     = load_font(44, True)
        title_img = render_mixed_block(
            story["title"], bn_bold, 44, lat_h, lat_h,
            HEADLINE_COLOR, max_text_w, spacing=14, bold=True, max_lines=3
        )
        paste_rgba(img, title_img, (60, y))
        y += title_img.height + 20
    else:
        font_h = load_font(52, bold=True)
        lines  = wrap_text_latin(story["title"], font_h, max_text_w, draw)[:3]
        for line in lines:
            draw.text((60, y), line, font=font_h, fill=hex_to_rgb(HEADLINE_COLOR))
            y += 65
        y += 20

    # 4. Accent bar
    draw.rectangle([60, y, 160, y + 4], fill=hex_to_rgb(ACCENT_COLOR))
    y += 24

    # 5. Photo — fills space between headline and footer
    FOOTER_H  = 100
    image_top = y
    image_h   = CARD_H - FOOTER_H - image_top - 20

    if article_image_path and os.path.exists(article_image_path):
        try:
            art      = Image.open(article_image_path).convert("RGB")
            target_w = CARD_W - 120
            target_h = image_h
            src_w, src_h = art.size
            if (src_w / src_h) > (target_w / target_h):
                new_w = int(src_h * target_w / target_h)
                art   = art.crop(((src_w - new_w) // 2, 0,
                                   (src_w - new_w) // 2 + new_w, src_h))
            else:
                new_h = int(src_w * target_h / target_w)
                art   = art.crop((0, (src_h - new_h) // 2,
                                   src_w, (src_h - new_h) // 2 + new_h))
            art  = art.resize((target_w, target_h), Image.LANCZOS)
            mask = Image.new("L", (target_w, target_h), 0)
            ImageDraw.Draw(mask).rounded_rectangle(
                [0, 0, target_w, target_h], radius=16, fill=255
            )
            art = art.convert("RGBA")
            art.putalpha(mask)
            img.paste(art, (60, image_top), art)
            print(f"  🖼️  Image embedded at y={image_top}, h={image_h}px")
        except Exception as e:
            print(f"  ⚠️  Image embed failed: {e}")
    else:
        print("  ℹ️  No image — text-only card")

    # 6. Footer
    footer_y = CARD_H - 90
    draw.text((60, footer_y), f"Source: {story['source']}",
              font=load_font(24), fill=hex_to_rgb(SOURCE_COLOR))
    handle = "@OrchestratorPulse"
    h_font = load_font(24, bold=True)
    h_w    = draw.textbbox((0, 0), handle, font=h_font)[2]
    draw.text((CARD_W - h_w - 60, footer_y), handle,
              font=h_font, fill=hex_to_rgb(ACCENT_COLOR))
    draw.rectangle([0, CARD_H - 8, CARD_W, CARD_H], fill=hex_to_rgb(ACCENT_COLOR))

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_path = os.path.join(OUTPUT_DIR, f"card_{index}.png")
    img.save(out_path)
    print(f"  ✅ Card saved → {out_path}")
    return out_path