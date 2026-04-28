# test_local.py
import os
import re
import requests
import socket
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont

load_dotenv()

# ── Config ────────────────────────────────────────────────────────────────────
UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY")
socket.setdefaulttimeout(8)

CARD_W, CARD_H = 1080, 1080
BG_COLOR      = "#0D0D0D"
ACCENT_COLOR  = "#FFFFFF"
HEADLINE_COLOR = "#FFFFFF"
SOURCE_COLOR  = "#888888"
DIVIDER_COLOR = "#333333"

ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")

FEEDS = [
    "https://techcrunch.com/category/artificial-intelligence/feed/",
    "https://www.theverge.com/ai-artificial-intelligence/rss/index.xml",
    "https://venturebeat.com/ai/feed/",
    "https://hnrss.org/frontpage?q=AI+LLM+GPT",
    "https://openai.com/blog/rss.xml",
    "https://deepmind.google/discover/blog/rss.xml",
    "https://www.marktechpost.com/feed/",
    "https://www.wired.com/feed/tag/ai/latest/rss",
    "https://www.zdnet.com/topic/artificial-intelligence/rss.xml",
]

# ── Helpers ───────────────────────────────────────────────────────────────────
def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

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

def draw_rounded_rect(draw, xy, radius, fill):
    x1, y1, x2, y2 = xy
    c = hex_to_rgb(fill)
    draw.rectangle([x1 + radius, y1, x2 - radius, y2], fill=c)
    draw.rectangle([x1, y1 + radius, x2, y2 - radius], fill=c)
    draw.ellipse([x1, y1, x1+2*radius, y1+2*radius], fill=c)
    draw.ellipse([x2-2*radius, y1, x2, y1+2*radius], fill=c)
    draw.ellipse([x1, y2-2*radius, x1+2*radius, y2], fill=c)
    draw.ellipse([x2-2*radius, y2-2*radius, x2, y2], fill=c)

def wrap_text(text, font, max_width, draw):
    words = text.replace('\n', ' ').split()
    lines, current = [], ""
    for word in words:
        test = f"{current} {word}".strip()
        if draw.textbbox((0, 0), test, font=font)[2] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines

# ── Scraper ───────────────────────────────────────────────────────────────────
def fetch_feed(url):
    import feedparser
    stories = []
    try:
        feed = feedparser.parse(url)
        for entry in feed.entries[:5]:
            title   = entry.get("title", "").strip()
            summary = entry.get("summary", entry.get("description", "")).strip()
            link    = entry.get("link", "")
            source  = feed.feed.get("title", "AI News")
            if title and len(title) > 20:
                summary = re.sub('<[^<]+?>', '', summary)[:300]
                stories.append({"title": title, "summary": summary,
                                 "link": link, "source": source})
    except Exception as e:
        print(f"  ⚠️  Skipped {url}: {e}")
    return stories

from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError

def get_story():
    stories = []

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(fetch_feed, url): url for url in FEEDS}

        try:
            for future in as_completed(futures, timeout=15):
                url = futures[future]
                try:
                    result = future.result(timeout=5)  # per-task timeout
                    if result:
                        stories.extend(result)
                except Exception as e:
                    print(f"  ⚠️  Failed {url}: {e}")

        except TimeoutError:
            print("  ⚠️  Some feeds took too long — continuing with available data...")

    if not stories:
        return None

    random.shuffle(stories)
    return stories[0]
# ── Unsplash ──────────────────────────────────────────────────────────────────
def extract_query(title):
    stopwords = {"a","an","the","and","or","for","in","on","of","to","is",
                 "with","how","why","what","this","that","are","was","has","will"}
    words = [w.strip(".,:-") for w in title.lower().split() if w not in stopwords]
    return " ".join(words[:3])

def extract_query(title):
    title = title.lower()

    # Remove noise words
    stopwords = {
        "a","an","the","and","or","for","in","on","of","to","is",
        "with","how","why","what","this","that","are","was","has",
        "will","from","by","as","at","it","be"
    }

    words = [w.strip(".,:-") for w in title.split() if w not in stopwords]

    # 🔹 Keyword mapping (VERY IMPORTANT)
    keyword_map = {
        "gpt": "artificial intelligence chatbot",
        "chatgpt": "AI chatbot interface",
        "openai": "artificial intelligence technology",
        "google": "google AI technology",
        "deepmind": "AI research lab",
        "meta": "AI social media technology",
        "robot": "humanoid robot",
        "robotics": "robot technology",
        "chip": "AI computer chip",
        "nvidia": "GPU chip technology",
        "llm": "large language model AI",
        "ai": "artificial intelligence",
        "model": "AI neural network",
        "startup": "tech startup office",
        "data": "data center servers",
        "cyber": "cyber security technology",
        "vision": "computer vision AI",
        "voice": "voice AI assistant"
    }

    # 🔹 Try to match meaningful keyword
    for key, value in keyword_map.items():
        if key in title:
            return value

    # 🔹 Fallback: build better generic query
    important_words = [w for w in words if len(w) > 3][:2]

    if important_words:
        return " ".join(important_words) + " technology"

    return "artificial intelligence technology"


def fetch_unsplash_image(query, save_path="output/article_image.jpg"):
    queries = [
        query,
        query + " technology",
        query + " futuristic",
        "artificial intelligence",
        "AI technology"
    ]

    for q in queries:
        try:
            res = requests.get(
                "https://api.unsplash.com/photos/random",
                params={
                    "query": q,
                    "orientation": "squarish",
                    "content_filter": "high",
                    "order_by": "relevant"
                },
                headers={"Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}"},
                timeout=8
            )
            res.raise_for_status()
            data = res.json()

            img_url = data["urls"]["regular"]
            img_bytes = requests.get(img_url, timeout=10).content

            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            with open(save_path, "wb") as f:
                f.write(img_bytes)

            print(f"  📷 Using query: '{q}'")
            return save_path

        except Exception:
            continue

    print("  ⚠️  Unsplash failed")
    return None
# ── Card Generator ────────────────────────────────────────────────────────────
def generate_card(story, article_image_path=None, index=0):
    img  = Image.new("RGB", (CARD_W, CARD_H), hex_to_rgb(BG_COLOR))
    draw = ImageDraw.Draw(img)
    max_text_w = CARD_W - 120

    # 1. Logo + page name
    logo_path = os.path.join(ASSETS_DIR, "logo.png")
    if os.path.exists(logo_path):
        logo   = Image.open(logo_path).convert("RGBA").resize((90, 90), Image.LANCZOS)
        circle = Image.new("RGBA", (106, 106), (0, 0, 0, 0))
        ImageDraw.Draw(circle).ellipse([0, 0, 106, 106], fill=(255, 255, 255, 255))
        img.paste(circle, (44, 44), circle)
        img.paste(logo,   (52, 52), logo)

    draw.text((160, 58), "Orchestrator Pulse",     font=load_font(28, True), fill=hex_to_rgb(ACCENT_COLOR))
    draw.text((160, 94), "Daily AI News & Trends", font=load_font(18),       fill=hex_to_rgb(SOURCE_COLOR))

    # 2. Badge + divider
    draw_rounded_rect(draw, (60, 190, 170, 226), 8, "#FFFFFF")
    draw.text((76, 198), "AI NEWS", font=load_font(20, True), fill=hex_to_rgb(BG_COLOR))
    draw.rectangle([60, 246, CARD_W - 60, 248], fill=hex_to_rgb(DIVIDER_COLOR))

    y = 280

    # 3. Headline
    font_h = load_font(52, bold=True)
    lines  = wrap_text(story["title"], font_h, max_text_w, draw)[:3]
    for line in lines:
        draw.text((60, y), line, font=font_h, fill=hex_to_rgb(HEADLINE_COLOR))
        y += 65
    y += 20

    # 4. Accent bar
    draw.rectangle([60, y, 160, y + 4], fill=hex_to_rgb(ACCENT_COLOR))
    y += 24

    # 5. Unsplash image — fills space between headline and footer
    FOOTER_H  = 100
    image_top = y
    image_h   = CARD_H - FOOTER_H - image_top - 20

    if article_image_path and os.path.exists(article_image_path):
        try:
            art = Image.open(article_image_path).convert("RGB")
            target_w, target_h = CARD_W - 120, image_h

            # Centre-crop to fit
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

            # Rounded corners
            mask = Image.new("L", (target_w, target_h), 0)
            ImageDraw.Draw(mask).rounded_rectangle(
                [0, 0, target_w, target_h], radius=16, fill=255)
            art  = art.convert("RGBA")
            art.putalpha(mask)
            img.paste(art, (60, image_top), art)

        except Exception as e:
            print(f"  ⚠️  Image embed failed: {e}")

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
    return out_path


# ── Run ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 50)
    print("LOCAL TEST — Scrape → Unsplash → Card")
    print("=" * 50)

    print("\n[1/3] Fetching story...")
    story = get_story()
    if not story:
        print("❌ No stories found."); exit()
    print(f"  ✅ {story['title'][:80]}")
    print(f"  📰 {story['source']}")

    print("\n[2/3] Fetching Unsplash image...")
    query       = extract_query(story["title"])
    print(f"  🔍 Query: '{query}'")
    image_path  = fetch_unsplash_image(query)

    print("\n[3/3] Generating card...")
    card_path = generate_card(story, article_image_path=image_path, index=0)
    print(f"  ✅ Saved → {card_path}")

    print("\n" + "=" * 50)
    print("Done! Open output/card_0.png to preview.")
    print("=" * 50)