# Aiva AI - Telegram Bot for Beauty Industry Professionals

Aiva AI is a comprehensive Telegram bot designed specifically for beauty industry professionals to manage client bookings, appointments, and customer relationships.

## 🚀 Features

- **Appointment Booking**: Easy scheduling for clients
- **Client Management**: Track customer preferences and history
- **Service Catalog**: Manage various beauty services
- **Subscription System**: Tiered pricing with different features
- **Data Collection**: Aggregated data for future analytics API
- **Upsell Triggers**: Smart suggestions to upgrade plans
- **Multi-master Support**: Each master can manage their own clients and services
- **Secure Data**: Encrypted storage of sensitive information
- **Web Dashboard**: Monitor bookings and analytics

## 💰 Tiered Pricing System

Aiva AI uses a modular tiered pricing system - masters pay only for what they use.

### "Start" Tier - 990 ₽/month
- Client bookings
- 24-hour reminders
- Basic FAQ
- Up to 50 bookings per month

### "Pro" Tier - 1 990 ₽/month ⭐
- Everything from "Start"
- "Concierge" skill (returns sleeping clients)
- "Post-care" skill
- Up to 200 bookings per month

### "Salon" Tier - 3 990 ₽/month
- Everything from "Pro"
- "Auto-Marketer" skill
- Analytics
- Up to 5 masters
- Unlimited bookings

### Premium Add-on: Voice Agent - +990 ₽/month
- Incoming call handling
- Voice reminders
- Integration with Alice

## 📊 Data Collection & Privacy

Aiva AI collects aggregated data about interactions to improve the service 
and provide analytics to masters.

**What we collect:**
- Service types and popularity
- Average prices by district
- Booking patterns (time, day of week)
- Demand trends

**What we DON'T collect:**
- Personal client data (names, phones)
- Exact addresses (district only)
- Message text (length only)

**How we protect data:**
- All client identifiers are hashed (SHA-256)
- Data is anonymized at the collection level
- Compliance with 152-FZ (personal data law)

Masters can disable data collection in settings (will be added in v2.0).

## 🚀 Data API (Coming Q2 2026)

In the future, we will launch a Data API for selling de-identified analytics:
- Demand trends by district
- Price elasticity
- Benchmarks for salon chains

This is an additional revenue source that doesn't affect core bot functionality.

## 🛠️ Tech Stack

- **Python 3.11**
- **Aiogram 3.3+** (Telegram Bot Framework)
- **FastAPI 0.109+** (Web Framework)
- **SQLAlchemy 2.0+** (ORM)
- **PostgreSQL** (Database)
- **Redis** (Caching & FSM)
- **Docker & Docker Compose**
- **Nginx** (Reverse Proxy)
- **Let's Encrypt** (SSL Certificates)

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Telegram      │    │   Aiva AI Bot   │    │   PostgreSQL    │
│   Platform      │◄──►│   (FastAPI)     │◄──►│   Database      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                       ┌─────────────────┐
                       │     Redis       │
                       │   (Cache/FSM)   │
                       └─────────────────┘
```

The architecture follows a modular skill-based approach where each feature is encapsulated as a separate skill.

## 🚀 Quick Start (Local)

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- PostgreSQL (or Docker)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd aiva-ai-bot
```

2. Create and configure environment:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run with Docker Compose:
```bash
docker-compose -f docker/docker-compose.yml up -d
```

5. Or run locally:
```bash
# Run database migrations
alembic upgrade head

# Start the bot
python -m src.main
```

## 🚢 Deployment

### VPS Deployment

1. Set up a VPS with Docker and Docker Compose
2. Configure domain and DNS
3. Update `.env` with production settings
4. Run the deployment script:
```bash
./scripts/deploy.sh
```

### Environment Variables

Required environment variables in `.env`:

- `BOT_TOKEN`: Your Telegram bot token from [@BotFather](https://t.me/BotFather)
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `ENCRYPTION_KEY`: 32-byte base64-encoded key for encrypting sensitive data
- `WEBHOOK_URL`: Public URL for webhook (optional, leave empty for polling)
- `CLIENT_HASH_SALT`: Salt for hashing client IDs
- `DATA_COLLECTION_ENABLED`: Enable/disable data collection
- `SUBSCRIPTION_CHECK_INTERVAL`: Interval for checking limits

## 🧪 Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=src

# Run specific test file
pytest tests/test_handlers/test_start.py
```

## 🔧 Development

### Running Linters

```bash
# Check code style with ruff
ruff check src/

# Format code with ruff
ruff format src/

# Type checking with mypy
mypy src/
```

### Database Migrations

```bash
# Create new migration after making model changes
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head
```

## 📊 Skills Architecture

Aiva AI follows a modular skill-based architecture:

- **Base Skill**: Abstract base class for all skills
- **Booking Skill**: Handles appointment scheduling
- **Subscription Skill**: Manages tiered pricing
- **Future Skills**: Customer retention, marketing, analytics

Each skill is responsible for:
- Determining if it can handle an event
- Processing the event
- Returning appropriate responses

## 🛡️ Security

- Sensitive data encryption (phone numbers, etc.)
- Environment-based configuration
- Secure session management
- Rate limiting
- Input validation
- Client ID anonymization with hashing

## 📈 Roadmap

- [ ] Customer retention tools
- [ ] Marketing automation
- [ ] Advanced analytics dashboard
- [ ] Payment integration
- [ ] Multi-language support
- [ ] Mobile app companion
- [ ] Advanced scheduling algorithms
- [ ] Data API launch (Q2 2026)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for your changes
5. Run the test suite
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For support, please open an issue in the repository or contact the maintainers.

---

Made with ❤️ for beauty industry professionals