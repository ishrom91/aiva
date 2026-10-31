"""RAG-based FAQ for client questions."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.master import Master
from ..models.service import Service
from ..services.llm import BaseLLM, get_llm


async def build_context(session: AsyncSession, master_id: str) -> str:
    """Build master context: services, prices, district."""
    master = await session.get(Master, master_id)
    if not master:
        return ""

    master_settings = master.settings or {}
    district = (
        master_settings.get("district") or master_settings.get("address") or "не указан"
    )

    result = await session.execute(
        select(Service).where(
            Service.master_id == master_id,
            Service.is_active.is_(True),
        )
    )
    services = result.scalars().all()

    lines = [
        f"Салон: {master.name}",
        f"Район/адрес: {district}",
        f"Рабочие часы: {master.work_start_hour or 9}:00–{master.work_end_hour or 18}:00",
        "Услуги:",
    ]
    for svc in services:
        lines.append(f"- {svc.name}: {svc.price}₽, {svc.duration_minutes} мин")
    if not services:
        lines.append("- прайс пока не заполнен")
    return "\n".join(lines)


def _fallback_by_service_name(question: str, context: str) -> str | None:
    lower_q = question.lower()
    for line in context.splitlines():
        if not line.startswith("- "):
            continue
        service_part = line[2:].split(":")[0].strip().lower()
        if service_part and service_part in lower_q:
            return f"{line[2:]}. Записаться можно командой /book"
    return None


async def answer_client_question(
    session: AsyncSession,
    master_id: str,
    question: str,
    *,
    llm: BaseLLM | None = None,
) -> str:
    """Answer a client FAQ using RAG + LLM with keyword fallback."""
    context = await build_context(session, master_id)

    model = llm or get_llm()
    try:
        answer = await model.answer(question, context)
        if answer:
            return answer
    except Exception:
        pass

    matched = _fallback_by_service_name(question, context)
    if matched:
        return matched

    return "Хороший вопрос! Уточню у мастера и скоро отвечу."


def build_system_prompt(master_name: str) -> str:
    return (
        f"Ты администратор салона {master_name}. Отвечай коротко, дружелюбно, "
        "на русском. Используй ТОЛЬКО факты из контекста. "
        "Если не знаешь — скажи 'уточню у мастера'."
    )
