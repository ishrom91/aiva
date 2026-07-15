"""
Definition of tariffs and their limitations
"""

TARIFFS = {
    "start": {
        "name": "Старт",
        "price_rub": 990,
        "monthly_bookings_limit": 50,
        "skills": ["booking"],
        "features": [
            "Запись клиентов",
            "Напоминания за 24 часа",
            "Базовый FAQ",
            "До 50 записей в месяц"
        ]
    },
    "pro": {
        "name": "Профи",
        "price_rub": 1990,
        "monthly_bookings_limit": 200,
        "skills": ["booking", "retention", "post_care"],
        "features": [
            "Всё из тарифа 'Старт'",
            "Навык 'Консьерж' (возврат спящих клиентов)",
            "Навык 'Пост-забота'",
            "До 200 записей в месяц"
        ]
    },
    "salon": {
        "name": "Салон",
        "price_rub": 3990,
        "monthly_bookings_limit": -1,  # unlimited
        "skills": ["booking", "retention", "post_care", "marketing", "analytics"],
        "features": [
            "Всё из тарифа 'Профи'",
            "Навык 'Авто-Маркетолог'",
            "Аналитика",
            "До 5 мастеров",
            "Безлимит записей"
        ]
    }
}

VOICE_ADDON = {
    "name": "Голосовой агент",
    "price_rub": 990,
    "skills": ["voice"],
    "features": [
        "Прием входящих звонков",
        "Голосовые напоминания",
        "Интеграция с Алисой"
    ]
}