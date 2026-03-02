from aiogram import Router

from .start import router as start_router
from .info import router as info_router
from .photo import router as photo_router
from .text import router as text_router
from .url import router as url_router
from .callbacks import router as callbacks_router


def get_main_router() -> Router:
    main_router = Router()
    main_router.include_router(start_router)
    main_router.include_router(info_router)
    main_router.include_router(callbacks_router)
    main_router.include_router(photo_router)
    main_router.include_router(url_router)
    main_router.include_router(text_router)  # text last — catches all messages
    return main_router
