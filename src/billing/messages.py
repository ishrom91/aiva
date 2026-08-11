"""Upsell message templates."""

from .tariffs import get_tariff_config

NEXT_TARIFF = {"start": "pro", "pro": "salon", "salon": None}


def build_limit_upsell_message(usage: int, limit: int, current_tariff: str) -> str:
    next_tariff = NEXT_TARIFF.get(current_tariff.lower())
    if not next_tariff:
        return "Вы достигли лимита записей на текущем тарифе."
    cfg = get_tariff_config(next_tariff) or {}
    return (
        f"🎉 У тебя уже {usage} из {limit} записей в этом месяце!\n"
        f"Перейди на '{cfg.get('name', next_tariff)}' — там навык 'Консьерж', "
        f"который вернёт клиентов.\n"
        f"Окупится за неделю! 💰\n\n"
        f"💳 Стоимость: {cfg.get('price', 0)}₽/мес"
    )
