# 168fz-bot — проверьвывеску.рф

## Проект
Telegram-бот для AI-проверки вывесок по 168-ФЗ + лендинг + админка.

## Структура
- `bot/` — aiogram 3.x бот + FastAPI админка
- `landing/` — статический лендинг (HTML/CSS/JS), деплоится в `/var/www/168fz-landing/`
- `.github/workflows/deploy.yml` — CI/CD (push to master → auto-deploy на VPS)

## Деплой
- Push to master → GitHub Actions → SSH на VPS → `git pull` + `cp -r landing/* /var/www/168fz-landing/` + `docker compose up -d --build`
- Bot: Docker container, long-polling
- Landing: nginx static files
- Admin: FastAPI на порту 8080, nginx проксирует `/admin`

## Домен
- проверьвывеску.рф = `xn--b1aaakc4awhjdoz3hm.xn--p1ai`

## SEO (текущая задача)
- **Фундамент DONE:** robots.txt, sitemap.xml, canonical, OG, Twitter Card, JSON-LD, favicon, Метрика (107080742)
- **В процессе:** контентная SEO-стратегия → сбор семантики через yandex-wordstat-mcp
- Стратегия: см. memory/168fz-seo-strategy.md
- Ещё не сделано: Яндекс.Вебмастер, Google Search Console

## Важно
- Landing файлы ОБЯЗАТЕЛЬНО должны быть в `landing/` — CI копирует именно оттуда
- Яндекс OAuth токен для Wordstat MCP хранится в ~/.claude.json (env переменная)

## Workflow
- **Нет issue — нет работы.** Перед началом любой задачи создай issue на GitHub.
- Доска: https://github.com/users/ragastar/projects/2
- Новая задача → issue → добавь на доску → In Progress
- Коммит с `#N` в сообщении
- После завершения → комментарий в issue, карточку в Done, закрой issue
- Язык: русский (коммиты, issues, комментарии)
