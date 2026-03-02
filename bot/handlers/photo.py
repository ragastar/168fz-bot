import io
import logging

from aiogram import Router, F, Bot
from aiogram.types import Message

from bot.config import settings
from bot.db import ensure_user, save_check, count_recent_checks
from bot.keyboards.report import get_report_keyboard
from bot.keyboards.subscription import get_subscribe_keyboard
from bot.services.llm import analyze_image
from bot.services.prompts import PHOTO_PROMPT
from bot.services.report import parse_llm_response, format_report, get_verdict_color
from bot.services.subscription import check_access
from bot.texts.subscription import SUBSCRIBE_TEXT, LIMIT_EXHAUSTED_TEXT

log = logging.getLogger(__name__)
router = Router()


@router.message(F.photo)
async def handle_photo(message: Message, bot: Bot) -> None:
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

    # Rate limiting
    recent = await count_recent_checks(user.id)
    if recent >= settings.rate_limit_per_minute:
        await message.answer(
            "⏳ Слишком много запросов. Подождите минуту и попробуйте снова."
        )
        return

    wait_msg = await message.answer("🔍 Анализирую фото... Это займёт 10-20 секунд.")

    try:
        # Download photo (largest size)
        photo = message.photo[-1]
        file = await bot.get_file(photo.file_id)
        buf = io.BytesIO()
        await bot.download_file(file.file_path, buf)
        image_bytes = buf.getvalue()

        # Analyze with Claude Vision
        caption = message.caption or "Проанализируй это изображение на соответствие 168-ФЗ."
        raw_response = await analyze_image(PHOTO_PROMPT, image_bytes, caption)

        # Parse and format
        data = parse_llm_response(raw_response)
        if data is None:
            await wait_msg.edit_text(
                "😔 Не удалось обработать ответ. Попробуйте ещё раз или отправьте другое фото."
            )
            await save_check(user.id, "photo", None, input_data=message.caption)
            return

        report = format_report(data)
        color = get_verdict_color(data)
        await save_check(user.id, "photo", color, input_data=message.caption)

        await wait_msg.delete()
        await message.answer(report, reply_markup=get_report_keyboard(), parse_mode="HTML")

    except Exception:
        log.exception("Error analyzing photo for user %s", user.id)
        await wait_msg.edit_text(
            "😔 Произошла ошибка при анализе. Попробуйте ещё раз чуть позже."
        )
