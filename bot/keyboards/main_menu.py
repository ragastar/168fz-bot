from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_main_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📸 Проверить фото", callback_data="check_photo"),
            InlineKeyboardButton(text="📝 Проверить текст", callback_data="check_text"),
        ],
        [
            InlineKeyboardButton(text="🌐 Проверить сайт / соцсети", callback_data="check_url"),
        ],
        [
            InlineKeyboardButton(text="📜 О законе", callback_data="info_law"),
            InlineKeyboardButton(text="💰 Штрафы", callback_data="info_fines"),
        ],
        [
            InlineKeyboardButton(text="✅ Чек-лист", callback_data="info_checklist"),
        ],
    ])
