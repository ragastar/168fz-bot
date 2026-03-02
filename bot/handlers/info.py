from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.texts.law import LAW_TEXT
from bot.texts.fines import FINES_TEXT
from bot.texts.checklist import CHECKLIST_TEXT

router = Router()


@router.message(Command("law"))
async def cmd_law(message: Message) -> None:
    await message.answer(LAW_TEXT, parse_mode="HTML")


@router.message(Command("fines"))
async def cmd_fines(message: Message) -> None:
    await message.answer(FINES_TEXT, parse_mode="HTML")


@router.message(Command("checklist"))
async def cmd_checklist(message: Message) -> None:
    await message.answer(CHECKLIST_TEXT, parse_mode="HTML")
