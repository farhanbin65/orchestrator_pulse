import os
from dotenv import load_dotenv
from scraper import get_top_stories
from card_generator import generate_card, extract_query, fetch_unsplash_image
from poster import post_card_to_facebook
from translator import translate_to_bangla

load_dotenv()

def run_pipeline():
    print("=" * 50)
    print("Orchestrator Pulse — Pipeline Starting")
    print("=" * 50)

    # 1. Fetch news
    print("\n[1/4] Fetching AI news...")
    stories = get_top_stories(count=1)

    if not stories:
        print("No stories found. Exiting.")
        return

    story = stories[0]

    # Fetch Unsplash image ONCE using English title
    print("\n[🖼️] Fetching Unsplash image...")
    query = extract_query(story["title"])
    print(f"  🔍 Query: '{query}'")
    shared_image_path = fetch_unsplash_image(
        query,
        save_path="output/shared_image.jpg"
    )

    # 2. English card — pass shared image
    print("\n[2/4] Generating English card...")
    try:
        english_card = generate_card(
            story, 0,
            bangla=False,
            article_image_path=shared_image_path  # ← use already-fetched image
        )
    except Exception as e:
        print(f"❌ English card generation failed: {e}")
        return

    # 3. Post English
    print("\n[3/4] Posting English card...")
    success_en = post_card_to_facebook(
        english_card,
        story,
        page_id=os.getenv("PAGE_ID"),
        token=os.getenv("PAGE_ACCESS_TOKEN")
    )

    # 4. Bangla pipeline
    print("\n[4/4] Bangla pipeline...")
    try:
        bangla_story = {
            "title":   translate_to_bangla(story["title"],   is_headline=True),
            "summary": translate_to_bangla(story["summary"], is_headline=False),
            "source":  story["source"],
            "link":    story["link"]
        }

        print("Generating Bangla card...")
        bangla_card = generate_card(
            bangla_story, 1,
            bangla=True,
            article_image_path=shared_image_path  # ← same image, no second fetch
        )

        print("Posting Bangla card...")
        success_bn = post_card_to_facebook(
            bangla_card,
            bangla_story,
            page_id=os.getenv("BANGLA_PAGE_ID"),
            token=os.getenv("BANGLA_PAGE_ACCESS_TOKEN")
        )

    except Exception as e:
        print(f"❌ Bangla pipeline failed: {e}")
        success_bn = False

    print("\n" + "=" * 50)
    print(f"English post: {'✅ Published' if success_en else '❌ Failed'}")
    print(f"Bangla post:  {'✅ Published' if success_bn else '❌ Failed'}")
    print("=" * 50)

if __name__ == "__main__":
    run_pipeline()