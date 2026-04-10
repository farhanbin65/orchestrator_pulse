# Orchestrator Pulse — Automated AI News Facebook Page

> Daily AI News & Trends — fully automated pipeline that scrapes, designs, and posts AI news cards to Facebook every 3 hours.

---

## What it does

This project automatically runs 8 times a day via GitHub Actions. Each run:

1. Scrapes the latest AI news from 30+ RSS feeds (TechCrunch, The Verge, OpenAI, DeepMind, arXiv, and more)
2. Picks a fresh story and generates a branded image card using Python Pillow
3. Posts the card to the [Orchestrator Pulse](https://www.facebook.com/profile.php?id=61572118407211) Facebook page with a caption and hashtags

No manual work required after setup.

<img width="725" height="619" alt="image" src="https://github.com/user-attachments/assets/f28ddb84-e6ba-40b9-8b8d-d1aae88e6c20" />
<img width="515" height="759" alt="image" src="https://github.com/user-attachments/assets/3d87484a-a3d8-4909-bc01-7e660d93aca3" />
<img width="1445" height="692" alt="Screenshot 2026-04-10 115348" src="https://github.com/user-attachments/assets/194d7358-b036-40e3-8b23-a8c90f058ef3" />


---

## Project structure

```
orchestrator-pulse/
│
├── main.py              # Entry point — runs the full pipeline (1 post per run)
├── scraper.py           # Fetches latest stories from 30+ AI RSS feeds
├── card_generator.py    # Generates branded 1080x1080 image cards with Pillow
├── poster.py            # Posts image + caption to Facebook via Graph API
│
├── assets/
│   └── logo.png         # Page logo stamped on every card
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
| Pillow (PIL) | Image card generation |
| requests | Facebook Graph API calls |
| python-dotenv | Environment variable management |
| GitHub Actions | Free daily automation (cron scheduler) |
| Meta Graph API v19 | Facebook Page posting |

---

## News sources (30+ feeds)

**Major tech media**
- TechCrunch AI, The Verge, VentureBeat, Wired, ZDNet, Fast Company, GeekWire

**AI labs & companies**
- OpenAI Blog, DeepMind, Google AI Blog, Microsoft AI, AWS Machine Learning

**Research**
- arXiv (cs.AI, cs.LG, stat.ML), BAIR Berkeley, Alan Turing Institute, Cambridge University

**Community & learning**
- Towards Data Science, KDNuggets, Analytics Vidhya, ML Mastery, Hacker News (AI filter)

---

## Card design

Every card is a 1080x1080px image with:
- Page logo + name in the top left
- `AI NEWS` tag badge
- Bold headline
- Short summary
- Source credit bottom left
- `@OrchestratorPulse` handle bottom right
- White accent bar at the bottom

Dark charcoal background (`#0D0D0D`) with white text — clean, minimal, professional.

---

## Setup (for your own page)

### 1. Clone the repo

```bash
git clone https://github.com/YOUR_USERNAME/orchestrator-pulse.git
cd orchestrator-pulse
```

### 2. Install dependencies

```bash
pip install requests feedparser Pillow python-dotenv
```

### 3. Create your `.env` file

```
PAGE_ID=your_facebook_page_id
PAGE_ACCESS_TOKEN=your_page_access_token
APP_ID=your_meta_app_id
APP_SECRET=your_meta_app_secret
```

> To get these values, follow the [Meta Graph API token guide](https://developers.facebook.com/docs/facebook-login/guides/access-tokens/).

### 4. Add your logo

Place your logo at `assets/logo.png` (square PNG, any size).

### 5. Test locally

```bash
python main.py
```

This will fetch 1 story, generate a card in `output/`, and post it to your page.

### 6. Deploy to GitHub Actions

Add these 4 values as **GitHub Secrets** (repo → Settings → Secrets → Actions):

- `PAGE_ID`
- `PAGE_ACCESS_TOKEN`
- `APP_ID`
- `APP_SECRET`

Push to GitHub — the workflow runs automatically every 3 hours from then on.

---

## Posting schedule

The pipeline runs 8 times per day at these UTC times:

```
12:00 AM · 03:00 AM · 06:00 AM · 09:00 AM
12:00 PM · 03:00 PM · 06:00 PM · 09:00 PM
```

---

## Customisation

| What | Where |
|---|---|
| Change posting frequency | `.github/workflows/daily_post.yml` — edit the cron expression |
| Add/remove news sources | `scraper.py` — edit the `FEEDS` list |
| Change card colours/fonts | `card_generator.py` — edit the colour constants at the top |
| Change number of posts per run | `main.py` — edit `count=` in `get_top_stories()` |

---

## Notes

- The Page Access Token does not expire (permanent token obtained via long-lived exchange)
- The `.env` file and `output/` folder are gitignored — never commit your tokens
- GitHub Actions free tier provides 2,000 minutes/month — more than enough for this pipeline
- Built as part of a final year Computing Systems dissertation project (2025)

---

## Author

**Farhan Bin Hossain**  
Final Year Computing Systems Student  
Facebook Page: [Orchestrator Pulse](https://www.facebook.com/OrchestratorPulse)
