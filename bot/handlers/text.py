import logging

from aiogram import Router, Bot
from aiogram.types import Message

from bot.config import settings
from bot.db import ensure_user, save_check, count_recent_checks
from bot.keyboards.report import get_report_keyboard
from bot.keyboards.subscription import get_subscribe_keyboard
from bot.services.llm import analyze_text
from bot.services.prompts import TEXT_PROMPT
from bot.services.report import parse_llm_response, format_report, get_verdict_color
from bot.services.subscription import check_access
from bot.texts.subscription import SUBSCRIBE_TEXT, LIMIT_EXHAUSTED_TEXT

log = logging.getLogger(__name__)
router = Router()

MIN_TEXT_LENGTH = 2
MAX_TEXT_LENGTH = 3000


@router.message()
async def handle_text(message: Message, bot: Bot) -> None:
    if not message.text:
        return

    text = message.text.strip()
    if len(text) < MIN_TEXT_LENGTH:
        return

    user = message.from_user
    await ensure_user(user.id, user.username, user.first_name)

    # Access check (subscription / limit)
    access = await check_access(bot, user.id)
    if not access.allowed:
        if access.reason == "not_subscribed":
            await message.answer(SUBSCRIBE_TEXT, reply_markup=get_subscribe_keyboard(), parse_mode="HTML")
        else:
            await message.answer(LIMIT_EXHAUSTED_TEXT, parse_mode="HTML")
        return

    if len(text) > MAX_TEXT_LENGTH:
        await message.answer(
            f"📏 Текст слишком длинный ({len(text)} символов). "
            f"Максимум — {MAX_TEXT_LENGTH}. Сократите текст и отправьте снова."
        )
        return

    # Rate limiting
    recent = await count_recent_checks(user.id)
    if recent >= settings.rate_limit_per_minute:
        await message.answer(
            "⏳ Слишком много запросов. Подождите минуту и попробуйте снова."
        )
        return

    wait_msg = await message.answer("🔍 Анализирую текст... Это займёт несколько секунд.")

    try:
        raw_response = await analyze_text(TEXT_PROMPT, text)

        data = parse_llm_response(raw_response)
        if data is None:
            await wait_msg.edit_text(
                "😔 Не удалось обработать ответ. Попробуйте ещё раз."
            )
            await save_check(user.id, "text", None, input_data=text[:200])
            return

        report = format_report(data)
        color = get_verdict_color(data)
        await save_check(user.id, "text", color, input_data=text[:200])

        await wait_msg.delete()
        await message.answer(report, reply_markup=get_report_keyboard(), parse_mode="HTML")

    except Exception:
        log.exception("Error analyzing text for user %s", user.id)
        await wait_msg.edit_text(
            "😔 Произошла ошибка при анализе. Попробуйте ещё раз чуть позже."
        )
