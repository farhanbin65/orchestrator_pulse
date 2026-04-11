import feedparser
import random
import re
import socket
from concurrent.futures import ThreadPoolExecutor, as_completed

# Global timeout for all feed requests
socket.setdefaulttimeout(8)

FEEDS = [
    "https://techcrunch.com/category/artificial-intelligence/feed/",
    "https://www.theverge.com/ai-artificial-intelligence/rss/index.xml",
    "https://venturebeat.com/ai/feed/",
    "https://hnrss.org/frontpage?q=AI+LLM+GPT",
    "https://openai.com/blog/rss.xml",
    "https://deepmind.google/discover/blog/rss.xml",
    "https://ai.googleblog.com/feeds/posts/default",
    "https://blogs.microsoft.com/ai/feed/",
    "https://aws.amazon.com/blogs/machine-learning/feed/",
    "https://bair.berkeley.edu/blog/feed.xml",
    "https://www.marktechpost.com/feed/",
    "https://www.unite.ai/feed/",
    "https://www.artificialintelligence-news.com/feed/",
    "https://www.wired.com/feed/tag/ai/latest/rss",
    "https://www.zdnet.com/topic/artificial-intelligence/rss.xml",
    "https://www.infoworld.com/category/artificial-intelligence/index.rss",
    "https://www.geekwire.com/tag/artificial-intelligence/feed/",
    "https://www.fastcompany.com/section/artificial-intelligence/rss.xml",
    "http://arxiv.org/rss/cs.AI",
    "http://arxiv.org/rss/cs.LG",
    "https://export.arxiv.org/rss/stat.ML",
    "https://machinelearningmastery.com/blog/feed/",
    "https://analyticsvidhya.com/feed/",
    "https://kdnuggets.com/feed",
    "https://towardsdatascience.com/feed",
    "https://pub.towardsai.net/feed",
    "https://www.turing.ac.uk/news/rss.xml",
    "https://www.cam.ac.uk/research/news/category/artificial-intelligence/rss.xml",
    "https://www.silicon.co.uk/e-innovation/artificial-intelligence/rss"
]

def fetch_feed(feed_url):
    """Fetch a single feed and return list of stories."""
    stories = []
    try:
        feed = feedparser.parse(feed_url)
        for entry in feed.entries[:5]:
            title = entry.get("title", "").strip()
            summary = entry.get("summary", entry.get("description", "")).strip()
            link = entry.get("link", "")
            source = feed.feed.get("title", "AI News")
            if title and len(title) > 20:
                summary = re.sub('<[^<]+?>', '', summary)[:300]
                stories.append({
                    "title": title,
                    "summary": summary,
                    "link": link,
                    "source": source
                })
    except Exception as e:
        print(f"⚠️  Skipped {feed_url}: {e}")
    return stories

def get_top_stories(count=3):
    stories = []

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(fetch_feed, url): url for url in FEEDS}
        for future in as_completed(futures, timeout=15):  # ← add timeout=15
            try:
                stories.extend(future.result())
            except Exception as e:
                print(f"⚠️  Feed timed out, skipping...")

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