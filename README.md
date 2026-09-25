# Game Donat

Web-first game top-up platform.

## Stack
- Frontend: static HTML/CSS/JS (GitHub Pages compatible)
- Backend: FastAPI
- Database: PostgreSQL in production, SQLite for local development
- Bot: python-telegram-bot
- Payments: provider abstraction; Manual Receipt is active first
- Referral rewards: one discounted subscription per confirmed referral, with per-user usage limit

## Games
Wuthering Waves, Punishing Gray Raven, Genshin Impact, Honkai: Star Rail, Zenless Zone Zero, Arknights: Endfield, NTE.

## Run locally
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
cp config/.env.example config/.env
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

Open `web/index.html` through a static server and set `API_BASE_URL`.

Never commit `config/.env`, payment secrets, bot tokens, passwords, CVV, or raw card data.
