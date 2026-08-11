"""FAQ handler for free-text client questions outside FSM."""

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from ..config import settings
from ..database import get_session
from ..services.faq_service import answer_client_question
from ..services.master_service import get_master_by_telegram_id

router = Router()


@router.message(
    F.text,
    ~F.text.startswith("/"),
    StateFilter(None),
)
async def faq_message_handler(message: Message, state: FSMContext) -> None:
    """Answer free-text questions when user is not in an FSM flow."""
    if not settings.AI_FAQ_ENABLED:
        return

    user = message.from_user
    if not user or not message.text:
        return

    async with get_session() as session:
        master = await get_master_by_telegram_id(session, user.id)
        if not master:
            await message.answer(
                "Привет! Для начала нажмите /start — помогу с записью и вопросами."
            )
            return

        answer = await answer_client_question(session, master.id, message.text)

    await message.answer(answer)
