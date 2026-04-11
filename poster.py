import requests
import os
from dotenv import load_dotenv
from pathlib import Path

# Always load .env from the same folder as this file — works regardless of where you run from
load_dotenv(dotenv_path=Path(__file__).parent / ".env")

def post_card_to_facebook(image_path, story, page_id=None, token=None):
    PAGE_ID    = page_id or os.getenv("PAGE_ID")
    PAGE_TOKEN = token   or os.getenv("PAGE_ACCESS_TOKEN")

    # Catch missing credentials immediately with a clear message
    if not PAGE_ID or PAGE_ID == "0":
        print(f"❌ PAGE_ID is missing or invalid: '{PAGE_ID}' — check your .env file")
        return False
    if not PAGE_TOKEN:
        print("❌ PAGE_ACCESS_TOKEN is missing — check your .env file")
        return False

    caption = (
        f"🤖 {story['title']}\n\n"
        f"{story['summary'][:200]}...\n\n"
        f"📰 Source: {story['source']}\n"
        f"🔗 Read more: {story['link']}\n\n"
        f"#AI #ArtificialIntelligence #AINews #TechNews #OrchestratorPulse"
    )

    try:
        with open(image_path, "rb") as img_file:
            response = requests.post(
                f"https://graph.facebook.com/v21.0/{PAGE_ID}/photos",
                data={
                    "caption":   caption,
                    "published": "true",
                    "access_token": PAGE_TOKEN
                },
                files={"source": img_file}
            )

        result = response.json()

        if "id" in result:
            print(f"✅ Posted successfully! Post ID: {result['id']}")
            return True
        else:
            print(f"❌ Post failed: {result}")
            return False

    except Exception as e:
        print(f"❌ Exception during posting: {e}")
        return False