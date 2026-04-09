import feedparser
import random

FEEDS = [
    "https://techcrunch.com/category/artificial-intelligence/feed/",
    "https://www.theverge.com/ai-artificial-intelligence/rss/index.xml",
    "https://venturebeat.com/ai/feed/",
    "https://hnrss.org/frontpage?q=AI+LLM+GPT",
]

def get_top_stories(count=3):
    stories = []
    for feed_url in FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:5]:
                title = entry.get("title", "").strip()
                summary = entry.get("summary", entry.get("description", "")).strip()
                link = entry.get("link", "")
                source = feed.feed.get("title", "AI News")
                if title and len(title) > 20:
                    # Strip HTML tags simply
                    import re
                    summary = re.sub('<[^<]+?>', '', summary)[:300]
                    stories.append({
                        "title": title,
                        "summary": summary,
                        "link": link,
                        "source": source
                    })
        except Exception as e:
            print(f"Error fetching {feed_url}: {e}")

    # Shuffle and return top N unique stories
    random.shuffle(stories)
    seen = set()
    unique = []
    for s in stories:
        if s["title"] not in seen:
            seen.add(s["title"])
            unique.append(s)
        if len(unique) >= count:
            break
    return unique

if __name__ == "__main__":
    stories = get_top_stories(3)
    for i, s in enumerate(stories, 1):
        print(f"\n--- Story {i} ---")
        print(f"Title: {s['title']}")
        print(f"Source: {s['source']}")
        print(f"Summary: {s['summary'][:100]}...")
