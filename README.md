# Aiva AI Bot

A production-ready Telegram bot for beauty industry professionals.

## Description

Aiva AI is a unified AI assistant in Telegram with a modular skill system, designed for beauty professionals. The bot currently implements a booking skill for scheduling appointments, with architecture designed to support additional skills like retention, marketing, and voice capabilities.

## Quick Start

Two ways to get started:

### A) Locally without Docker:
```bash
python -m venv venv && pip install -r requirements.txt
cp .env.example .env && # Edit .env with your settings
alembic upgrade head && uvicorn src.main:app --reload
```

For local development leave `WEBHOOK_URL` empty to use **polling mode**.

### B) Via Docker:
```bash
cp .env.example .env && # Edit .env with your settings
docker compose -f docker/docker-compose.yml up -d --build
```

> Note: For both options, you'll need Redis and PostgreSQL services running (either locally or via Docker)

## Deployment on VPS

1. Run `setup.sh` to prepare the server
2. Run `init-letsencrypt.sh` to configure SSL
3. Deploy with `deploy.sh` and GitHub Secrets

## Migration Command

To create a new migration:
```bash
alembic revision --autogenerate -m "message" && alembic upgrade head
```

## Architecture

```
UI -> Nginx -> Bot -> {PostgreSQL, Redis} + Data API Layer
```

## Tariffs

| Plan | Price | Bookings/month | Features |
|------|-------|----------------|----------|
| Start | 990₽ | 50 | Basic booking, reminders, FAQ |
| Pro | 1990₽ | 200 | + retention, post-care, AI-FAQ |
| Salon | 3990₽ | Unlimited | + marketing, analytics, multi-master |

## Data Collection & Privacy

We collect anonymized data to improve our service:
- What we collect: Event types, anonymous client hashes, service types, district-level locations
- What we DON'T collect: Names, phone numbers, exact addresses, message texts
- How we protect: SHA-256 hashing, AES encryption, compliance with Russian Federal Law 152-FZ

## Data API

Coming Q2 2026 - API for purchasing anonymized market intelligence.

## Assets

See `assets/README.md` for instructions on uploading images and obtaining file IDs.

## Testing

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
ruff check src/
mypy src/
```

## Contributing

Contributions are welcome! Please follow the code style and submit pull requests.

## License

MIT
