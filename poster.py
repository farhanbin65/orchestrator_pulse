import requests
import os
from dotenv import load_dotenv

load_dotenv()

PAGE_ID    = os.getenv("PAGE_ID")
PAGE_TOKEN = os.getenv("PAGE_ACCESS_TOKEN")

def post_card_to_facebook(image_path, story):
    caption = (
        f"🤖 {story['title']}\n\n"
        f"{story['summary'][:200]}...\n\n"
        f"📰 Source: {story['source']}\n"
        f"🔗 Read more: {story['link']}\n\n"
        f"#AI #ArtificialIntelligence #AINews #TechNews #OrchestratorPulse"
    )

    with open(image_path, "rb") as img_file:
        response = requests.post(
            f"https://graph.facebook.com/v19.0/{PAGE_ID}/photos",
            data={
                "caption": caption,
                "published": "true",     
                "no_story": "false",     
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

if __name__ == "__main__":
    test_story = {
        "title": "Test Post from Orchestrator Pulse Pipeline",
        "summary": "This is a test of the automated posting pipeline.",
        "source": "Test",
        "link": "https://facebook.com"
    }
    from card_generator import generate_card
    card_path = generate_card(test_story, 0)
    post_card_to_facebook(card_path, test_story)