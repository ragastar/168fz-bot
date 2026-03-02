import logging
import re

from aiogram import Router, F, Bot
from aiogram.types import Message

from bot.config import settings
from bot.db import ensure_user, save_check, count_recent_checks
from bot.keyboards.report import get_report_keyboard
from bot.keyboards.subscription import get_subscribe_keyboard
from bot.services.subscription import check_access
from bot.texts.subscription import SUBSCRIBE_TEXT, LIMIT_EXHAUSTED_TEXT
from bot.services.llm import analyze_text
from bot.services.parser import detect_url_type, parse_website, parse_vk, parse_telegram
from bot.services.prompts import WEBSITE_PROMPT
from bot.services.report import parse_llm_response, format_report, get_verdict_color

log = logging.getLogger(__name__)
router = Router()

URL_PATTERN = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)

INSTAGRAM_MSG = (
    "📸 Instagram не позволяет автоматически получать содержимое страниц.\n\n"
    "Сделайте <b>скриншот</b> профиля или публикации и отправьте его мне — "
    "я проанализирую текст на соответствие 168-ФЗ."
)


def _normalize_url(url: str) -> str:
    """Ensure URL has a scheme."""
    if url.startswith("www."):
        return "https://" + url
    return url


@router.message(F.text.regexp(URL_PATTERN))
async def handle_url(message: Message, bot: Bot) -> None:
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

    # Extract first URL from message
    match = URL_PATTERN.search(message.text)
    if not match:
        return
    url = _normalize_url(match.group(0))

    url_type = detect_url_type(url)

    # Instagram — suggest screenshot
    if url_type == "instagram":
        await message.answer(INSTAGRAM_MSG, parse_mode="HTML")
        return

    # Rate limiting
    recent = await count_recent_checks(user.id)
    if recent >= settings.rate_limit_per_minute:
        await message.answer(
            "⏳ Слишком много запросов. Подождите минуту и попробуйте снова."
        )
        return

    type_labels = {
        "vk": ("VK-страницу", "🔍 Анализирую VK-страницу..."),
        "telegram": ("Telegram-канал", "🔍 Анализирую Telegram-канал..."),
        "website": ("сайт", "🔍 Анализирую сайт... Это займёт 10-20 секунд."),
    }
    label, wait_text = type_labels.get(url_type, type_labels["website"])
    wait_msg = await message.answer(wait_text)

    try:
        # Parse content
        if url_type == "vk":
            content = await parse_vk(url)
        elif url_type == "telegram":
            content = await parse_telegram(url)
        else:
            content = await parse_website(url)

        if content.startswith("[EMPTY]"):
            await wait_msg.edit_text(
                f"😔 Не удалось извлечь текст с этой страницы.\n\n"
                f"Попробуйте отправить <b>скриншот</b> — я проанализирую его.",
                parse_mode="HTML",
            )
            return

        # Analyze with Claude
        user_text = f"URL: {url}\nТип: {label}\n\nСодержимое страницы:\n{content}"
        raw_response = await analyze_text(WEBSITE_PROMPT, user_text)

        # Parse and format
        data = parse_llm_response(raw_response)
        if data is None:
            await wait_msg.edit_text(
                "😔 Не удалось обработать ответ. Попробуйте ещё раз или отправьте скриншот."
            )
            await save_check(user.id, "url", None, input_data=url)
            return

        report = format_report(data)
        color = get_verdict_color(data)
        await save_check(user.id, "url", color, input_data=url)

        await wait_msg.delete()
        await message.answer(report, reply_markup=get_report_keyboard(), parse_mode="HTML")

    except Exception:
        log.exception("Error analyzing URL %s for user %s", url, user.id)
        await wait_msg.edit_text(
            "😔 Не удалось загрузить страницу. Проверьте ссылку или отправьте скриншот."
        )
