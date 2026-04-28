# Orchestrator Pulse — Automated AI News Facebook Pages

> Daily AI News & Trends — fully automated pipeline that scrapes, translates, designs, and posts AI news cards to **two Facebook pages** (English & Bangla) every 3 hours.

---

## What it does

This project automatically runs 8 times a day via GitHub Actions. Each run:

1. Scrapes the latest AI news from 30+ RSS feeds (TechCrunch, The Verge, OpenAI, DeepMind, arXiv, and more)
2. Fetches a **relevant photo from Unsplash** based on the article topic
3. Generates a branded **English** 1080×1080 image card (headline + Unsplash photo) using Python Pillow
4. Posts the English card to the [Orchestrator Pulse (English)](https://www.facebook.com/profile.php?id=61572118407211) Facebook page
5. Translates the headline and summary into **Bangla** using the Groq API (LLaMA 3.3 70B)
6. Generates a Bangla-language image card using the **same Unsplash photo** — no second API call
7. Posts the Bangla card to the [Orchestrator Pulse (Bangla)](https://www.facebook.com/profile.php?id=61573324778812) Facebook page

No manual work required after setup.


<img width="948" height="945" alt="image" src="https://github.com/user-attachments/assets/3e43cb55-9ce7-4d04-91ee-cd89127399bd" />
<img width="945" height="941" alt="image" src="https://github.com/user-attachments/assets/7d48d589-3101-4482-9f25-d2c46313a789" />
<img width="515" height="759" alt="image" src="https://github.com/user-attachments/assets/3d87484a-a3d8-4909-bc01-7e660d93aca3" />
<img width="1445" height="692" alt="Screenshot 2026-04-10 115348" src="https://github.com/user-attachments/assets/194d7358-b036-40e3-8b23-a8c90f058ef3" />

---

## Project structure
RSS Feeds (30+)
│
▼
scraper.py ──── fetches latest AI stories (parallelised with ThreadPoolExecutor)
│
▼
main.py ──── extract_query(English title)
│
▼
Unsplash API ──── shared_image.jpg (fetched ONCE)
│
├──── card_generator.py (English card + shared image) ──► poster.py ──► English Facebook Page
│
└──── translator.py (Groq / LLaMA 3.3 70B)
│
▼
card_generator.py (Bangla card + same shared image) ──► poster.py ──► Bangla Facebook Page

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

English page
PAGE_ID=your_english_facebook_page_id
PAGE_ACCESS_TOKEN=your_english_page_access_token
Bangla page
BANGLA_PAGE_ID=your_bangla_facebook_page_id
BANGLA_PAGE_ACCESS_TOKEN=your_bangla_page_access_token
Meta App credentials
APP_ID=your_meta_app_id
APP_SECRET=your_meta_app_secret
Groq API (for Bangla translation)
GROQ_API_KEY=your_groq_api_key