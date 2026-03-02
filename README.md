# 168-ФЗ Бот

Telegram-бот для проверки вывесок, меню и рекламы на соответствие Федеральному закону 168-ФЗ о русском языке.

## Запуск локально

```bash
cp .env.example .env
# Заполнить .env

pip install -r requirements.txt
python -m bot.main
```

## Запуск в Docker

```bash
cp .env.example .env
# Заполнить .env

docker compose up -d --build
docker compose logs -f
```

## Переменные окружения

| Переменная | Описание |
|-----------|----------|
| `BOT_TOKEN` | Telegram Bot Token от @BotFather |
| `OPENROUTER_API_KEY` | API-ключ OpenRouter |
| `OPENROUTER_MODEL` | Модель (по умолчанию: `anthropic/claude-sonnet-4`) |
| `ADMIN_CHAT_ID` | Telegram ID администратора |
