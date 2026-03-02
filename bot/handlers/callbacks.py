from aiogram import Router, F
from aiogram.types import CallbackQuery

from bot.db import ensure_user, save_lead
from bot.keyboards.main_menu import get_main_menu
from bot.texts.law import LAW_TEXT
from bot.texts.fines import FINES_TEXT
from bot.texts.checklist import CHECKLIST_TEXT

router = Router()


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


CTA_TEXTS = {
    "cta_sign": (
        "🪧 <b>Заказ вывески по 168-ФЗ</b>\n\n"
        "Мы подготовим вывеску, полностью соответствующую новым требованиям закона.\n\n"
        "📩 Оставьте заявку: напишите «Хочу вывеску» — мы свяжемся с вами."
    ),
    "cta_lawyer": (
        "⚖️ <b>Юридическая консультация</b>\n\n"
        "Наш юрист проверит все ваши материалы и подготовит заключение.\n\n"
        "📩 Оставьте заявку: напишите «Нужен юрист» — мы свяжемся с вами."
    ),
    "cta_website": (
        "🌐 <b>Русификация сайта</b>\n\n"
        "Полная русификация сайта с учётом требований 168-ФЗ: навигация, описания, метаданные.\n\n"
        "📩 Оставьте заявку: напишите «Русификация сайта» — мы свяжемся с вами."
    ),
}


@router.callback_query(F.data.startswith("cta_"))
async def cb_cta(callback: CallbackQuery) -> None:
    cta_type = callback.data.replace("cta_", "")
    await ensure_user(
        callback.from_user.id,
        callback.from_user.username,
        callback.from_user.first_name,
    )
    await save_lead(callback.from_user.id, cta_type)
    text = CTA_TEXTS.get(callback.data, "Спасибо за интерес! Мы скоро свяжемся.")
    await callback.message.answer(text, parse_mode="HTML")
    await callback.answer()
