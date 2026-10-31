COMPOSE = docker compose --env-file .env -f docker/docker-compose.yml
TEST_ENV = BOT_TOKEN=000000000:TEST_TOKEN DATABASE_URL=sqlite+aiosqlite:///./test_pytest.db ENCRYPTION_KEY=dGVzdC1rZXktdGVzdC1rZXktdGVzdC1rZXktdGVzdGtleTE= REDIS_URL=

.PHONY: help setup cert deploy up down logs ps config migrate backup maintenance test lint smoke

help:
	@printf '%s\n' 'Aiva commands: setup, cert, deploy, up, down, logs, ps, migrate, backup, test, lint, smoke'

setup:
	bash scripts/setup.sh

cert:
	bash scripts/init-letsencrypt.sh

deploy:
	bash scripts/deploy.sh

up:
	$(COMPOSE) up -d --build

down:
	$(COMPOSE) down

logs:
	$(COMPOSE) logs -f --tail=200

ps:
	$(COMPOSE) ps

config:
	$(COMPOSE) config --quiet

migrate:
	$(COMPOSE) run --rm migrate

backup:
	bash scripts/backup_db.sh

maintenance:
	bash scripts/install_maintenance.sh

test:
	$(TEST_ENV) pytest -q

lint:
	ruff check src tests
	ruff format --check src tests
	mypy src

smoke:
	$(TEST_ENV) python scripts/smoke_test.py
