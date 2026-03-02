from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_report_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔄 Проверить ещё", callback_data="check_again"),
        ],
        [
            InlineKeyboardButton(
                text="🪧 Заказать вывеску",
                callback_data="cta_sign",
            ),
        ],
        [
            InlineKeyboardButton(
                text="⚖️ Консультация юриста",
                callback_data="cta_lawyer",
            ),
        ],
        [
            InlineKeyboardButton(
                text="🌐 Русификация сайта",
                callback_data="cta_website",
            ),
        ],
    ])
