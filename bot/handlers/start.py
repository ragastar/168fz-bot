from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from bot.db import ensure_user
from bot.keyboards.main_menu import get_main_menu

router = Router()

START_TEXT = """
<b>👋 Привет! Я — бот-проверка по 168-ФЗ</b>

С 1 марта 2026 года вступил в силу закон о русском языке. Теперь все вывески, меню, сайты и рекламные материалы должны быть на русском.

<b>Я помогу проверить:</b>
📸 <b>Фото</b> — отправьте фото вывески, меню или ценника
📝 <b>Текст</b> — вставьте текст рекламы или описания
🌐 <b>Сайт</b> — скоро! Пока отправьте скриншот

Выберите действие 👇
""".strip()


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    await ensure_user(
        message.from_user.id,
        message.from_user.username,
        message.from_user.first_name,
    )
    await message.answer(START_TEXT, reply_markup=get_main_menu(), parse_mode="HTML")
