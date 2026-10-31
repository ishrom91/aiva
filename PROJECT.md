# 📘 Aiva AI — ПАСПОРТ ПРОЕКТА (PROJECT.md) · MAX-версия

> **ЕДИНСТВЕННЫЙ ИСТОЧНИК ПРАВДЫ.** Новый чат → первым сообщением скорми этот файл целиком,
> затем ставь задачу. Любое новое решение → сначала обнови файл, потом делай.
> Лежит в корне `github.com/ishrom91/aiva`.

---

## 0. Суть, питч, описание для нетехнарей
**Суть:** Aiva AI — Telegram-бот, «цифровой администратор» для мастеров бьюти: сам записывает
клиентов, отвечает на вопросы, напоминает о визитах, возвращает «спящих» — голосом мастера, 24/7,
в 40–50 раз дешевле живого администратора.
**Elevator pitch:** «Aiva AI — цифровой администратор для мастеров красоты в Telegram: записывает
клиентов, отвечает и напоминает 24/7 твоим голосом — за 990 ₽/мес вместо зарплаты 40 000 ₽.»
**Для нетехнарей:** мастер работает 8 часов, а вечером до полуночи отвечает клиентам, ведёт
блокнот, забывает напомнить — теряет деньги и сон. Aiva берёт это на себя: клиент пишет боту —
бот записывает, напоминает, возвращает тех, кто пропал. Мастер просто работает. Настройка — 3 минуты.
**Тезис:** сотни тысяч мастеров без администратора тонут в рутине; LLM-экономика 2025–26 сделала
AI-администратора доступным (990 ₽/мес, маржа >85%); канал — Telegram, где уже мастер и клиент.

## 1. Три типа клиентов
| Тип | Роль | Монетизация |
|-----|------|-------------|
| Мастера (B2B) | настраивают бота | подписка |
| Клиенты мастеров (B2C) | записываются/спрашивают | бесплатно |
| Компании (Enterprise) | обезличенная аналитика | Data API (будущее) |

## 2. Функционал (Фазы 0–2, ВСЁ в коде)
- **Онбординг:** `/start` (регистрация, trial 7 дней, меню), `/help`.
- **Запись:** FSM услуга→дата→время→подтверждение; конфликты (±duration), лимиты, ownership;
  слоты каждые 30 мин в рабочих часах; отмена; no-show.
- **Подписки:** Старт 990 / Профи 1990 / Салон 3990 ₽/мес; аддон «Голос» +990;
  лимиты 50/200/безлимит; до 5 мастеров в «Салон».
- **Апсейл (тексты — бизнес-актив):** limit (≥90%: «🎉 У тебя уже {n} из {limit}… перейди на '{next}'… {price}₽/мес»);
  lost_revenue (раз/мес: «💡 …'Консьерж' вернул бы {sum}₽…»); social_proof (раз/нед: «📊 …на 23% больше…»).
- **AI-FAQ (RAG):** свободные ответы вне FSM; цепочка LLM: YandexGPT → OpenAI → DummyLLM;
  контекст = услуги/цены из БД; keyword-fallback без LLM.
- **Напоминания:** фоновой цикл каждый час, окно 20–28 ч, без повторов (`reminded_at`).
- **Консьерж:** `/winback`, «спящие» >60 дней, rate-limit 30 дней/клиент (`last_winback_at`).
- **Админка:** `/add_service` (FSM), `/services`, `/stats`.
- **Privacy (152-ФЗ):** Fernet (`phone_encrypted`/`name_encrypted`; деривация ключа:
  base64(sha256(key)) если невалиден); event sourcing `interactions` = `client_hash` (SHA-256+salt),
  без PII и текста (только длина); локация до района; флаги `DATA_COLLECTION_ENABLED`,
  `DATA_COLLECTION_LOG_TEXT=false` в проде.

### 2.1 Справочник команд бота
| Команда | Кто | Действие |
|---------|-----|----------|
| `/start` | мастер | регистрация, trial, меню |
| `/help` | все | справка |
| `/book` | мастер/клиент | запись (FSM) |
| `/add_service` | мастер | добавить услугу (FSM) |
| `/services` | мастер | список услуг + удаление |
| `/stats` | мастер | статистика |
| `/subscription` | мастер | тариф, usage, лимиты |
| `/upgrade` | мастер | апгрейд (upsell-триггеры) |
| `/winback` | мастер | возврат «спящих» клиентов |
| свободный текст | клиент | AI-FAQ ответ |

## 3. Архитектура и стек
```
КЛИЕНТЫ(3) → КАНАЛЫ(Telegram-бот, лендинг) → ЯДРО(единый агент+skills:
handlers→services→repositories→models; [Booking][FAQ][Reminder][Winback][Billing+Upsell];
LLM-абстракция) → ДАННЫЕ(PostgreSQL 11 таблиц + Redis; event sourcing→аналитика→Data API)
→ ИНФРА(VPS+Docker+nginx+HTTPS+CI/CD)
```
- Python 3.11 · Aiogram 3 · FastAPI · SQLAlchemy 2 async · Alembic · pydantic-settings · structlog · Fernet.
- Слои строго: сервисы ходят ТОЛЬКО через repositories.
- `main.py`: lifespan; **polling fallback** при пустом `WEBHOOK_URL`; `/health`.
- Skills — задел Фазы 7 (в MVP handlers напрямую; задокументировано в `skills/base.py`).

### 3.1 HTTP-эндпоинты
| Метод/путь | Назначение |
|------------|-----------|
| GET `/` | статус сервиса |
| GET `/health` | db/redis/uptime/version |
| POST `/webhook` | Telegram webhook (проверка secret-заголовка) |
| GET `/api/v1/market-intelligence` | Data API (coming soon, API-key + rate-limit) |
| GET `/api/v1/price-elasticity` | Data API (coming soon) |
| GET `/api/v1/district-benchmarks` | Data API (coming soon) |

### 3.2 Структура репозитория
```
aiva-ai-bot/
├── src/ (api/ v1/endpoints · billing · handlers · middlewares · models ·
│        repositories · schemas · services(+llm, reminder, retention, faq) ·
│        skills · utils · main.py · config.py · database.py)
├── migrations/versions/ (0001, 0002, 0003)
├── tests/ (test_services · test_billing · test_handlers · test_utils ·
│           test_middlewares · test_main · conftest.py)
├── docker/ (Dockerfile · docker-compose.yml) · nginx/ · scripts/ (setup, deploy,
│        init-letsencrypt, smoke_test.py, backup_db*) · .github/workflows/ (ci, deploy)
├── assets/ (brand/ · bot/) · index.html (лендинг) · PROJECT.md · .env.example
└── (план: DEPLOY.md · Makefile · .env.production.example)
```

## 4. Данные
- **PostgreSQL (11 таблиц):** masters, clients, services, bookings, subscriptions,
  interactions, master_analytics, district_analytics, data_api_clients, api_keys, api_request_logs.
  PK = UUID(String). Миграции: `0001_initial`, `0002_fix_interaction_api_key_schema`,
  `0003_phase2_reminders_winback`.
- **Redis:** FSM/кэш/rate-limit; dev-fallback MemoryStorage при пустом REDIS_URL.
- **SQLite:** только тесты/smoke.
- **Будущее (триггеры спроса):** pgvector (2 хранилища: knowledge_embeddings, memory_embeddings),
  ClickHouse при масштабе. НЕ сейчас.

## 5. Data-moat → Data API
Каждый диалог → interactions → аналитика районов/услуг → инсайты для брендов/сетей.
Заглушки готовы (auth+rate-limit), логика — coming soon Q2-2026.

## 6. Бизнес и рынок
- Выручка: подписки + Data API. Без комиссий с записей.
- Юнит-экономика: ARPU 1500–2200; COGS 150–250 (маржа >85%); CAC <1500; retention >80%/мес; LTV/CAC >5.
- Рынок: TAM ~1 млн СНГ (~18 млрд ₽/год); SAM ~300 тыс РФ; SOM 10 тыс мастеров (~260 млн ₽/год).
- Конкуренты: YClients/Dikidi (CRM, не «сотрудник»); BotHelp/Salebot (конструкторы);
  живой администратор (дорого); маркетплейсы (комиссии).
- GTM: инфлюенсеры, школы, рефералка, QR-визитки; хук «Топ-500 мастеров — 0% комиссии навсегда».
- Пост-запуск: нед 1 бета 10–20 мастеров (оффер: месяц бесплатно за отзыв+созвон; цели ≥50%
  активация, ≥30% D7); нед 2–4 ЮKassa+платящие+кейсы; мес 1–2 рост+инвесторы.

## 7. БРЕНД
### 7.1 НОВАЯ палитра (АКТУАЛЬНА с 03.08.2026) — «cool mint / teal glass»
| Роль | HEX |
|------|-----|
| Фон ice | `#F0F7F5` |
| Текст ink | `#0E332E` |
| Primary teal | `#0F766E` |
| Bright teal | `#14B8A6` |
| Deep teal | `#0B5D54` |
| Mint | `#99F6E4` / `#B9F0E4` |
| Ice cyan | `#A5F3FC` |
| Emerald | `#34D399` |
| Янтарь (звёзды) | `#E8A33D` |
| Градиент кнопок | `135deg,#14B8A6,#0B5D54` |
| Лого-плитка | `135deg,#B9F0E4,#0B5D54` |
| Тени | rgba(15,118,110,…) — без чёрного |
| Семантика | success `#10B981`, pain rose-500 |
Стиль: матовый glassmorphism, белая top-highlight граница, 24px, без неона/глянца.
Шрифты: Unbounded (display) + Manrope (body), кириллица.
### 7.2 СТАРАЯ палитра — DEPRECATED: violet `#8B5CF6`, pink `#EC4899`, cream `#FBF8F5`, ink `#17121F`.
### 7.3 Айдентика
- **Лого:** стеклянная 3D-«A» на teal-плитке (сделан основателем). История: искра-звезда →
  бирюзовая «A» → финальный teal-логотип основателя.
- **Аватар/4 иллюстрации:** созданы в СТАРОЙ палитре → **ОТКРЫТАЯ ЗАДАЧА: перекрасить (§12)**.
- Иллюстрации: welcome / booking_ok / reminder / winback (`assets/bot/`, file_id через Bot API).
- Лендинг `index.html`: navbar→hero(чат-демо: 3 сценария запись/возврат/FAQ + glass-карточки)→stats→
  marquee→pain→solution→skills→how→testimonials→pricing(+addon,toggle)→privacy→faq→cta(прогресс мест)→footer.

## 8. Caption-тексты бота (менять осознанно)
- welcome: «🌸 Привет! Я Aiva — твой цифровой администратор. Пока ты пьёшь кофе, я соберу записи
  на день и отвечу клиентам — твоим голосом. Давай настроим услуги? Это займёт 3 минуты ☕️»
- booking_ok: «Готово! ✅ Записала тебя на пятницу, 18:00. Напомню о визите за день — просто приходи
  и наслаждайся 💕»
- reminder: «Напоминаю 🤍 Завтра в 18:00 тебя ждёт любимый мастер. Если планы изменились — напиши,
  я всё поправлю. До встречи! 🌷»
- winback: «Давно не виделись 💕 Мы соскучились! Есть окошко в субботу в 12:00 — записать на твою
  любимую процедуру?»

## 9. Статус и качество (31.10.2026)
- Код Фаз 0–2 и production-обвязка Фазы 3 готовы: **65 тестов зелёных**, ruff/mypy чистые,
  smoke PASSED (все 5 шагов).
- Production: PostgreSQL+Redis в Compose, миграции перед запуском, Docker non-root healthcheck,
  nginx template по DOMAIN, Let's Encrypt, ежедневные бэкапы (14 дней), deploy с pre-backup и
  post-healthcheck, production env validation, CI на push/PR и CD по push main.
- Карта тестов: services (booking, subscription) · billing (upsell) · handlers (start, booking,
  subscription, admin) · utils (encryption, anonymization) · middlewares (event_logger) ·
  фаза-2 (reminder, faq, retention) · production config · health · main.
- Локально: polling + SQLite/локальный PG. Деплой и проверка реального Docker/VPS — следующий шаг.
- НЕ сделано: деплой VPS; ЮKassa; боевой Telegram-тест; юридика; перекрас ассетов; BotFather.

### 9.1 Локальный запуск
```
venv\Scripts\activate
pip install -r requirements.txt -r requirements-dev.txt
copy .env.example .env   (заполнить BOT_TOKEN, DATABASE_URL, ENCRYPTION_KEY; WEBHOOK_URL пусто=polling)
alembic upgrade head
pytest -q
uvicorn src.main:app --port 8000
python scripts/smoke_test.py
```

## 10. Инфраструктура
- Репозиторий `github.com/ishrom91/aiva`; CI/CD GitHub Actions (ruff/mypy/pytest/docker build; deploy по push main).
- Docker multi-stage non-root; compose: postgres+redis+migrate+bot+nginx+certbot;
  PG на VPS, не Managed для MVP. `DEPLOY.md` + `Makefile` + `.env.production.example` готовы.
- VPS план: 2 vCPU/2–4 GB Ubuntu → setup.sh генерирует секреты и cron → init-letsencrypt.sh →
  deploy.sh. Ручные значения только BOT_TOKEN/DOMAIN/EMAIL; WEBHOOK_URL заполняется автоматически.
- Окружение основателя (Windows): Docker Desktop нестабилен; Ростелеком подменяет DNS (→8.8.8.8);
  Telegram API может требовать VPN/proxy (`TELEGRAM_PROXY`); боевой тест — на VPS.

### 10.1 Env (полный список; секреты — только в .env, не коммитить)
```
BOT_TOKEN, ENVIRONMENT, DATABASE_URL, REDIS_URL, WEBHOOK_URL, ENCRYPTION_KEY, LOG_LEVEL,
POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD, CLIENT_HASH_SALT,
DATA_COLLECTION_ENABLED, DATA_COLLECTION_LOG_TEXT, SUBSCRIPTION_CHECK_INTERVAL,
TELEGRAM_WEBHOOK_SECRET, DATA_API_ENABLED, DATA_API_RATE_LIMIT_DEFAULT,
DOMAIN, EMAIL, LETSENCRYPT_STAGING, BOT_ASSET_FILE_IDS,
YANDEX_FOLDER_ID, YANDEX_API_KEY, OPENAI_API_KEY, OPENAI_BASE_URL,
AI_FAQ_ENABLED, REMINDER_HOURS_BEFORE, WINBACK_DAYS, TELEGRAM_PROXY
```

## 11. Дорожная карта
| Фаза | Что | Статус |
|------|-----|--------|
| 0–2 | Ядро + AI-администратор | ✅ |
| 3 | Production-обвязка + деплой VPS → живой бот | код ✅ / VPS ⏳ |
| 4 | Бета + ЮKassa | нед 1–2 |
| 5 | Платящие + кейсы | нед 2–4 |
| 6 | Рост + инвесторы | мес 1–2 |
| 7 | pgvector, рынок ур.2–3, Консьерж-авто, Маркетолог, Голос, Data API | мес 3+ |
Рыночная экспертиза бота: ур.1 (справочник цен/сезонность/советы) — опционален; ур.2–3 — с ростом data-moat.

## 12. ОТКРЫТЫЕ ЗАДАЧИ (не терять!)
1. Влить production-изменения в `main`, запустить CI, затем деплой VPS по `DEPLOY.md`.
2. Боевой Telegram-тест после запуска: `/start`, услуга, запись, FAQ, напоминание, `/health`.
3. ЮKassa. 4. Юридика: ИП/самозанятость, оферта, политика 152-ФЗ (до платежей).
5. Перекрас аватара+4 иллюстраций в новую палитру.
6. BotFather: /setuserpic, /setname «Aiva AI», /setdescription (проверить статус).

## 13. Инвест-сводка
- Pre-seed 5 млн ₽, runway 12–18 мес. Use of funds: 40 рост/CAC · 30 продукт/найм · 20 инфра · 10 юр.
- Раунд покупает: запуск→500+ мастеров→MRR ~0,7 млн→retention >80%→Консьерж live→B2B-пилоты.
- Метрики: активация ≥50%, D30 >60% (бета), MRR, ARPU, no-show↓, NPS >30.
- Риски/митигации: галлюцинации (guardrails+эскалация); спам (согласия/opt-out); 152-ФЗ (анонимизация);
  CRM+AI (скорость/ниша/data-moat); Telegram (polling fallback); solo (AI-leverage, найм при 100 платящих).
- Exit-опциональность: data-moat ценен для M&A (Яндекс/Авито/Dikidi/бренды).

## 14. DECISION LOG
1. UUID PK — distributed-friendly. 2. Repositories — единственный слой БД. 3. Без векторных БД в MVP
(триггеры — §4). 4. Смена палитры на teal (03.08.26, решение основателя); violet/pink deprecated.
5. Glassmorphism пришёл из warm-matte промта, переосмыслен в teal под лого основателя.
6. PG на VPS для MVP (экономия). 7. Polling fallback (dev без домена). 8. Текст сообщений не храним (152-ФЗ).
9. Skills — задел, handlers напрямую в MVP. 10. Лого-путь: искра→бирюза→финал основателя.
11. Production fail-fast для webhook/secrets/PII; `/health` возвращает 503 при недоступных DB/Redis.
12. Приложение использует asyncpg, Alembic — psycopg2; миграции запускаются отдельным одноразовым
контейнером до bot. 13. Секреты генерируются на VPS, ручные поля минимизированы до токена/домена/почты.

## 15. Команда и процесс
- Основатель: Роман (продукт/решения/бренд), код руками не пишет.
- Процесс: архитектор пишет промты → AI-кодер (Cursor/Qoder) реализует → основатель riporta → ревью.
- Бот: **@AivaAI_bot**.

*При изменении продукта — обновляй раздел и дату в §9.*
