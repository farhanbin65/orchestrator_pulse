# Orchestrator Pulse — Automated AI News Facebook Pages

> Daily AI News & Trends — fully automated pipeline that scrapes, translates, designs, and posts AI news cards to **two Facebook pages** (English & Bangla) every 3 hours.

---

## What it does

This project automatically runs 8 times a day via GitHub Actions. Each run:

1. Scrapes the latest AI news from 30+ RSS feeds (TechCrunch, The Verge, OpenAI, DeepMind, arXiv, and more)
2. Picks a fresh story and generates a branded **English** image card using Python Pillow
3. Posts the English card to the [Orchestrator Pulse (English)](https://www.facebook.com/profile.php?id=61572118407211) Facebook page
4. Translates the headline and summary into **Bangla** using the Groq API (LLaMA 3.3 70B)
5. Generates a Bangla-language image card with mixed-script rendering support
6. Posts the Bangla card to the [Orchestrator Pulse (Bangla)](https://www.facebook.com/profile.php?id=61573324778812) Facebook page

No manual work required after setup.

<img width="725" height="619" alt="image" src="https://github.com/user-attachments/assets/f28ddb84-e6ba40b9-8b8d-d1aae88e6c20" />
<img width="515" height="759" alt="image" src="https://github.com/user-attachments/assets/3d87484a-a3d8-4909-bc01-7e660d93aca3" />
<img width="1445" height="692" alt="Screenshot 2026-04-10 115348" src="https://github.com/user-attachments/assets/194d7358-b036-40e3-8b23-a8c90f058ef3" />

---

## Project structure

```
orchestrator-pulse/
│
├── main.py              # Entry point — runs the full pipeline (English + Bangla per run)
├── scraper.py           # Fetches latest stories from 30+ AI RSS feeds
├── card_generator.py    # Generates branded 1080x1080 image cards with Pillow (English & Bangla)
├── poster.py            # Posts image + caption to Facebook via Graph API
├── translator.py        # Translates English news to Bangla using Groq API (LLaMA 3.3 70B)
│
├── assets/
│   ├── logo.png                    # Page logo stamped on every card
│   ├── NotoSansBengali-Regular.ttf # Bangla font
│   └── NotoSansBengali-Bold.ttf    # Bangla bold font
│
├── output/              # Generated cards saved here (gitignored)
├── .env                 # Your API tokens (gitignored — never commit this)
├── .gitignore
│
└── .github/
    └── workflows/
        └── daily_post.yml   # GitHub Actions — runs every 3 hours
```

---

## Tech stack

| Tool | Purpose |
|---|---|
| Python 3.11 | Core language |
| feedparser | RSS feed parsing |
| Pillow (PIL) | Image card generation (English & Bangla) |
| requests | Facebook Graph API calls |
| groq | Bangla translation via LLaMA 3.3 70B |
| python-dotenv | Environment variable management |
| GitHub Actions | Free daily automation (cron scheduler) |
| Meta Graph API v19 | Facebook Page posting |

---

## Pipeline overview

```
RSS Feeds (30+)
      │
      ▼
  scraper.py ──── fetches latest AI stories (parallelised with ThreadPoolExecutor)
      │
      ▼
  main.py  ─────┬──── card_generator.py (English card) ──► poster.py ──► English Facebook Page
                │
                └──── translator.py (Groq / LLaMA 3.3 70B)
                            │
                            ▼
                      card_generator.py (Bangla card) ──► poster.py ──► Bangla Facebook Page
```

---



## Setup (for your own pages)

### 1. Clone the repo

```bash
git clone https://github.com/YOUR_USERNAME/orchestrator-pulse.git
cd orchestrator-pulse
```

### 2. Install dependencies

```bash
pip install requests feedparser Pillow python-dotenv groq
```

### 3. Add Bangla fonts

Download and place these fonts in `assets/`:
- [`NotoSansBengali-Regular.ttf`](https://fonts.google.com/noto/specimen/Noto+Sans+Bengali)
- [`NotoSansBengali-Bold.ttf`](https://fonts.google.com/noto/specimen/Noto+Sans+Bengali)

### 4. Create your `.env` file

```
# English page
PAGE_ID=your_english_facebook_page_id
PAGE_ACCESS_TOKEN=your_english_page_access_token

# Bangla page
BANGLA_PAGE_ID=your_bangla_facebook_page_id
BANGLA_PAGE_ACCESS_TOKEN=your_bangla_page_access_token

# Meta App credentials
APP_ID=your_meta_app_id
APP_SECRET=your_meta_app_secret

# Groq API (for Bangla translation)
GROQ_API_KEY=your_groq_api_key
```

> To get Facebook tokens, follow the [Meta Graph API token guide](https://developers.facebook.com/docs/facebook-login/guides/access-tokens/).  
> To get a Groq API key, sign up at [console.groq.com](https://console.groq.com).

### 5. Add your logo

Place your logo at `assets/logo.png` (square PNG, any size).

### 6. Test locally

```bash
python main.py
```

This will fetch 1 story, generate both English and Bangla cards in `output/`, and post to both pages.

### 7. Deploy to GitHub Actions

Add these values as **GitHub Secrets** (repo → Settings → Secrets → Actions):

- `PAGE_ID`
- `PAGE_ACCESS_TOKEN`
- `BANGLA_PAGE_ID`
- `BANGLA_PAGE_ACCESS_TOKEN`
- `APP_ID`
- `APP_SECRET`
- `GROQ_API_KEY`

Push to GitHub — the workflow runs automatically every 3 hours from then on.

---

## Posting schedule

The pipeline runs 8 times per day at these UTC times:

```
12:00 AM · 03:00 AM · 06:00 AM · 09:00 AM
12:00 PM · 03:00 PM · 06:00 PM · 09:00 PM
```

Both the English and Bangla cards are posted in the same run.


## Notes

- Page Access Tokens do not expire (permanent tokens obtained via long-lived exchange)
- The `.env` file and `output/` folder are gitignored — never commit your tokens
- GitHub Actions free tier provides 2,000 minutes/month — more than enough for this pipeline
- Feed fetching is parallelised with `ThreadPoolExecutor` and uses an 8-second socket timeout to prevent hangs on slow feeds
- The Bangla translator strips arXiv metadata (IDs, "Abstract", "Announce Type") to keep cards clean
- Built as part of a final year Computing Systems dissertation project (2025–2026)

---

## Author

**Farhan Bin Hossain**  
Final Year Computing Systems Student  
English Page: [Orchestrator Pulse](https://www.facebook.com/profile.php?id=61572118407211)  
Bangla Page: [Orchestrator Pulse (বাংলা)](https://www.facebook.com/profile.php?id=61573324778812)