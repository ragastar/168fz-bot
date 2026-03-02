from aiogram import Router, F
from aiogram.types import CallbackQuery

import logging

from bot.db import ensure_user, save_lead, get_setting, get_db
from bot.keyboards.main_menu import get_main_menu
from bot.texts.law import LAW_TEXT
from bot.texts.fines import FINES_TEXT
from bot.texts.checklist import CHECKLIST_TEXT

router = Router()
log = logging.getLogger(__name__)


@router.callback_query(F.data == "check_photo")
async def cb_check_photo(callback: CallbackQuery) -> None:
    await callback.message.answer("📸 Отправьте фото вывески, меню или ценника — я проверю на соответствие 168-ФЗ.")
    await callback.answer()


@router.callback_query(F.data == "check_text")
async def cb_check_text(callback: CallbackQuery) -> None:
    await callback.message.answer("📝 Отправьте текст рекламы, описания или слогана — я проверю на соответствие 168-ФЗ.")
    await callback.answer()


@router.callback_query(F.data == "check_url")
async def cb_check_url(callback: CallbackQuery) -> None:
    await callback.message.answer(
        "🌐 Отправьте ссылку на сайт, VK или Telegram-канал — "
        "я проанализирую текст на соответствие 168-ФЗ.\n\n"
        "Для Instagram отправьте <b>скриншот</b> — автоматический парсинг недоступен.",
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "check_again")
async def cb_check_again(callback: CallbackQuery) -> None:
    await callback.message.answer(
        "Отправьте фото или текст для проверки 👇",
        reply_markup=get_main_menu(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "info_law")
async def cb_info_law(callback: CallbackQuery) -> None:
    await callback.message.answer(LAW_TEXT, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "info_fines")
async def cb_info_fines(callback: CallbackQuery) -> None:
    await callback.message.answer(FINES_TEXT, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "info_checklist")
async def cb_info_checklist(callback: CallbackQuery) -> None:
    await callback.message.answer(CHECKLIST_TEXT, parse_mode="HTML")
    await callback.answer()


CTA_LABELS = {
    "cta_sign": "🪧 Заказ вывески по 168-ФЗ",
    "cta_lawyer": "⚖️ Юридическая консультация",
    "cta_website": "🌐 Русификация сайта",
}

CTA_TEXTS = {
    "cta_sign": (
        "🪧 <b>Заказ вывески по 168-ФЗ</b>\n\n"
        "Мы подготовим вывеску, полностью соответствующую новым требованиям закона.\n\n"
        "✅ <b>Заявка принята!</b> Мы свяжемся с вами в Telegram."
    ),
    "cta_lawyer": (
        "⚖️ <b>Юридическая консультация</b>\n\n"
        "Наш юрист проверит все ваши материалы и подготовит заключение.\n\n"
        "✅ <b>Заявка принята!</b> Мы свяжемся с вами в Telegram."
    ),
    "cta_website": (
        "🌐 <b>Русификация сайта</b>\n\n"
        "Полная русификация сайта с учётом требований 168-ФЗ: навигация, описания, метаданные.\n\n"
        "✅ <b>Заявка принята!</b> Мы свяжемся с вами в Telegram."
    ),
}


@router.callback_query(F.data.startswith("cta_"))
async def cb_cta(callback: CallbackQuery) -> None:
    cta_type = callback.data.replace("cta_", "")
    user = callback.from_user
    await ensure_user(user.id, user.username, user.first_name)
    await save_lead(user.id, cta_type)

    text = CTA_TEXTS.get(callback.data, "✅ <b>Заявка принята!</b> Мы свяжемся с вами в Telegram.")
    await callback.message.answer(text, parse_mode="HTML")
    await callback.answer()

    # Уведомляем о новом лиде — chat_id из настроек БД
    chat_id = await get_setting(f"notify_{cta_type}") or await get_setting("notify_default")
    if chat_id:
        label = CTA_LABELS.get(callback.data, cta_type)
        username = f"@{user.username}" if user.username else f"id:{user.id}"
        name = user.first_name or "—"

        # Подтягиваем контекст последней проверки
        db = await get_db()
        cur = await db.execute(
            "SELECT input_type, input_data FROM checks WHERE user_id = ? ORDER BY created_at DESC LIMIT 1",
            (user.id,),
        )
        last_check = await cur.fetchone()
        context_line = ""
        if last_check and last_check[1]:
            check_type = last_check[0]
            data = last_check[1]
            if check_type == "url":
                context_line = f"\nПроверял: {data}"
            else:
                context_line = f"\nПроверял ({check_type}): {data[:100]}"

        admin_text = (
            f"📥 <b>Новый лид</b>\n\n"
            f"Услуга: {label}\n"
            f"Контакт: {username}\n"
            f"Имя: {name}"
            f"{context_line}"
        )
        try:
            await callback.bot.send_message(
                int(chat_id), admin_text, parse_mode="HTML",
            )
        except Exception:
            log.warning("Failed to notify chat %s about lead from %s", chat_id, user.id)
