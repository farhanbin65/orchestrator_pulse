"""
Orchestrator Pulse — Daily AI News Pipeline
Scrapes top AI news → generates branded cards → posts to Facebook
Run manually or via GitHub Actions daily
"""

import os
import time
from dotenv import load_dotenv
from scraper import get_top_stories
from card_generator import generate_card
from poster import post_card_to_facebook

load_dotenv()

def run_pipeline(num_posts=3):
    print("=" * 50)
    print("Orchestrator Pulse — Daily Pipeline Starting")
    print("=" * 50)

    # Step 1: Scrape news
    print("\n[1/3] Fetching top AI news...")
    stories = get_top_stories(num_posts)
    if not stories:
        print("No stories found. Exiting.")
        return
    print(f"Found {len(stories)} stories.")

    # Step 2 & 3: Generate card and post for each story
    for i, story in enumerate(stories):
        print(f"\n[Story {i+1}/{len(stories)}]")
        print(f"Title: {story['title'][:80]}...")

        # Generate card
        print("  Generating card...")
        card_path = generate_card(story, i)

        # Post to Facebook
        print("  Posting to Facebook...")
        success = post_card_to_facebook(card_path, story)

        if success:
            print(f"  Done!")
        else:
            print(f"  Failed to post story {i+1}")

        # Wait 30 seconds between posts to avoid rate limits
        if i < len(stories) - 1:
            print("  Waiting 30s before next post...")
            time.sleep(30)

    print("\n" + "=" * 50)
    print(f"Pipeline complete! Posted {len(stories)} cards.")
    print("=" * 50)

if __name__ == "__main__":
    run_pipeline(num_posts=3)
