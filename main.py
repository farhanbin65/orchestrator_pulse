import os
from dotenv import load_dotenv
from scraper import get_top_stories
from card_generator import generate_card
from poster import post_card_to_facebook

load_dotenv()

def run_pipeline():
    print("=" * 50)
    print("Orchestrator Pulse — Pipeline Starting")
    print("=" * 50)

    # Step 1: Scrape 1 story
    print("\n[1/3] Fetching AI news...")
    stories = get_top_stories(count=1)
    if not stories:
        print("No stories found. Exiting.")
        return

    story = stories[0]
    print(f"Story: {story['title'][:80]}...")

    # Step 2: Generate card
    print("\n[2/3] Generating card...")
    try:
        card_path = generate_card(story, 0)
    except Exception as e:
        print(f"❌ Card generation failed: {e}")
        return

    # Step 3: Post to Facebook
    print("\n[3/3] Posting to Facebook...")
    success = post_card_to_facebook(card_path, story)

    print("\n" + "=" * 50)
    if success:
        print("Pipeline complete! 1 post published.")
    else:
        print("Pipeline finished but post failed.")
    print("=" * 50)

if __name__ == "__main__":
    run_pipeline()
