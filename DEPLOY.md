# Деплой Aiva AI на VPS

## Что подготовлено автоматически

- PostgreSQL 16 и Redis 7 с постоянными томами;
- миграции перед запуском бота;
- Docker healthcheck и перезапуск сервисов;
- nginx, HTTPS и продление Let's Encrypt;
- ежедневные PostgreSQL-бэкапы с хранением 14 дней;
- проверка здоровья после каждого деплоя;
- генерация криптографических секретов на сервере.

## Первый запуск

Требования: Ubuntu/Debian, 2 vCPU, 2–4 GB RAM, домен с A-записью на IP сервера.

```bash
git clone https://github.com/ishrom91/aiva.git ~/aiva
cd ~/aiva
bash scripts/setup.sh
```

Переподключись к SSH, если текущий пользователь был добавлен в группу `docker`.

Открой `.env` и заполни только:

```dotenv
BOT_TOKEN=токен_от_BotFather
DOMAIN=bot.example.ru
EMAIL=real@example.ru
```

Остальные секреты уже сгенерированы. `WEBHOOK_URL` будет автоматически установлен в `https://DOMAIN/webhook`.

```bash
bash scripts/init-letsencrypt.sh
bash scripts/deploy.sh
```

Проверка:

```bash
curl -f https://bot.example.ru/health
```

Затем открой `@AivaAI_bot` в Telegram и выполни `/start`.

## Обновление

```bash
cd ~/aiva
bash scripts/deploy.sh
```

Скрипт сам получает код, делает преддеплойный бэкап, применяет миграции, пересобирает контейнеры и проверяет `/health`. Не используй `docker compose down` для обычного обновления.

## Полезные команды

```bash
make ps          # состояние сервисов
make logs        # общие логи
make backup      # бэкап сейчас
make config      # проверка Compose
make test        # тесты локально
make smoke       # бизнес-сценарий без Telegram
```

Бэкапы находятся в `backups/`, автоматический запуск — ежедневно в 03:17 UTC. Логи обслуживания — в `logs/`.

## Автодеплой из GitHub

Workflow уже настроен. В GitHub → Settings → Secrets and variables → Actions добавь:

- `HOST` — IP VPS;
- `USERNAME` — SSH-пользователь;
- `SSH_PRIVATE_KEY` — закрытый ключ для деплоя;
- `DEPLOY_PATH` — например `/home/ubuntu/aiva` (если не задан, используется `/opt/aiva`).

На VPS должен существовать клон репозитория и заполненный `.env`. Push в `main` запускает `bash scripts/deploy.sh`.

## Если HTTPS не выпускается

1. Проверь, что A-запись домена указывает на VPS и DNS успел обновиться.
2. Проверь доступность портов 80 и 443 в панели облачного провайдера.
3. Проверь `docker compose --env-file .env -f docker/docker-compose.yml logs nginx certbot`.
4. Для тестовых попыток временно поставь `LETSENCRYPT_STAGING=1`, чтобы не исчерпать лимит Let's Encrypt.

Не коммить `.env`, `certbot/`, `backups/` и реальные Telegram/LLM-ключи.
