import logging
from dataclasses import dataclass

from aiogram import Bot
from aiogram.enums import ChatMemberStatus

from bot.config import settings
from bot.db import count_total_checks

log = logging.getLogger(__name__)


@dataclass
class AccessResult:
    allowed: bool
    remaining: int = 0
    reason: str = ""
    total_checks: int = 0


async def check_channel_subscription(bot: Bot, user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(settings.channel_id, user_id)
        return member.status in (
            ChatMemberStatus.MEMBER,
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.CREATOR,
        )
    except Exception:
        log.warning("Failed to check subscription for user %s", user_id)
        return False


async def check_access(bot: Bot, user_id: int) -> AccessResult:
    total = await count_total_checks(user_id)

    if total < settings.free_checks:
        return AccessResult(
            allowed=True,
            remaining=settings.free_checks - total,
            total_checks=total,
        )

    if total < settings.subscriber_checks:
        subscribed = await check_channel_subscription(bot, user_id)
        if subscribed:
            return AccessResult(
                allowed=True,
                remaining=settings.subscriber_checks - total,
                total_checks=total,
            )
        return AccessResult(
            allowed=False,
            reason="not_subscribed",
            total_checks=total,
        )

    return AccessResult(
        allowed=False,
        reason="limit_exhausted",
        total_checks=total,
    )
