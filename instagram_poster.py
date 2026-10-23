import os
import shutil
import subprocess
import time
from pathlib import Path

import requests

GRAPH = "https://graph.facebook.com/v25.0"
REPO = os.getenv("GITHUB_REPOSITORY")          # set automatically in GitHub Actions
BRANCH = os.getenv("GITHUB_REF_NAME", "main")  # set automatically in GitHub Actions
IG_FOLDER = "public_ig"


def build_caption(story):
    # Instagram captions are plain text: links are not clickable.
    return (
        f"{story['title']}\n\n"
        f"{story['summary'][:200]}...\n\n"
        f"Source: {story['source']}\n"
        f"Read more: {story['link']}\n\n"
        f"#AI #ArtificialIntelligence #AINews #TechNews #OrchestratorPulse"
    )[:2200]


def commit_image_to_repo(local_path, lang):
    """Copy the card into the repo under a unique name and push it. Returns the public URL."""
    filename = f"{lang}_{int(time.time())}{Path(local_path).suffix}"
    repo_path = f"{IG_FOLDER}/{filename}"

    Path(IG_FOLDER).mkdir(exist_ok=True)
    shutil.copy(local_path, repo_path)

    subprocess.run(["git", "config", "user.name", "orchestrator-bot"], check=True)
    subprocess.run(["git", "config", "user.email", "bot@users.noreply.github.com"], check=True)
    subprocess.run(["git", "add", repo_path], check=True)
    subprocess.run(["git", "commit", "-m", f"Add Instagram image {filename}"], check=True)
    subprocess.run(["git", "pull", "--rebase", "origin", BRANCH], check=True)
    subprocess.run(["git", "push", "origin", f"HEAD:{BRANCH}"], check=True)

    return f"https://raw.githubusercontent.com/{REPO}/{BRANCH}/{repo_path}"


def wait_until_public(url, timeout=90):
    """Instagram fails if the URL isn't live yet, so wait until it responds."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            if requests.head(url, timeout=10).status_code == 200:
                return True
        except requests.RequestException:
            pass
        time.sleep(5)
    return False


def post_card_to_instagram(image_path, story, ig_user_id, token, lang):
    if not ig_user_id or not token:
        print(f"❌ Instagram {lang}: IG user ID or token missing")
        return False

    try:
        image_url = commit_image_to_repo(image_path, lang)
        if not wait_until_public(image_url):
            print(f"❌ Instagram {lang}: image URL not public yet: {image_url}")
            return False

        # Step 1: create the draft (container)
        r = requests.post(
            f"{GRAPH}/{ig_user_id}/media",
            data={"image_url": image_url, "caption": build_caption(story), "access_token": token},
        )
        result = r.json()
        if "id" not in result:
            print(f"❌ Instagram {lang} container failed: {result}")
            return False
        creation_id = result["id"]

        # Wait until Instagram has processed the draft
        for _ in range(20):
            status = requests.get(
                f"{GRAPH}/{creation_id}",
                params={"fields": "status_code", "access_token": token},
            ).json()
            if status.get("status_code") == "FINISHED":
                break
            if status.get("status_code") == "ERROR":
                print(f"❌ Instagram {lang} processing error: {status}")
                return False
            time.sleep(5)

        # Step 2: publish the draft
        r = requests.post(
            f"{GRAPH}/{ig_user_id}/media_publish",
            data={"creation_id": creation_id, "access_token": token},
        )
        result = r.json()
        if "id" in result:
            print(f"✅ Instagram {lang} published. Post ID: {result['id']}")
            return True

        print(f"❌ Instagram {lang} publish failed: {result}")
        return False

    except Exception as e:
        print(f"❌ Instagram {lang} exception: {e}")
        return False