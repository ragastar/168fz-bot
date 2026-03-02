import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties

from bot.config import settings
from bot.db import get_db, close_db
from bot.handlers import get_main_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger(__name__)


async def main() -> None:
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode="HTML"),
    )
    dp = Dispatcher()
    dp.include_router(get_main_router())

    # Init DB on startup
    await get_db()
    log.info("Database initialized")

    # Set bot commands
    from aiogram.types import BotCommand

    await bot.set_my_commands([
        BotCommand(command="start", description="Главное меню"),
        BotCommand(command="law", description="О законе 168-ФЗ"),
        BotCommand(command="fines", description="Таблица штрафов"),
        BotCommand(command="checklist", description="Чек-лист самопроверки"),
    ])

    log.info("Bot starting (long-polling)...")
    try:
        await dp.start_polling(bot)
    finally:
        await close_db()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
