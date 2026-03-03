# Инструкция: что сделать на VPS

## Что уже задеплоено автоматически (CI/CD)
Всё что в папке `landing/` — CI сам копирует на VPS при push to master.
Тебе ничего не нужно делать для:
- SVG-иллюстрации
- HTML-файлы (schema, fonts, meta)
- Новые страницы (/blog/, /o-proekte/, 404.html)
- sitemap.xml

## Что нужно сделать руками: nginx конфиг

### Шаг 1: Открой файл nginx конфига

В VSCode через SSH открой файл:
```
/etc/nginx/sites-enabled/168fz-landing
```

Если файла с таким именем нет, посмотри что лежит в папке:
```
ls /etc/nginx/sites-enabled/
```
Нужен файл в котором есть `server_name xn--b1aaakc4awhjdoz3hm.xn--p1ai`

### Шаг 2: Найди блок server для порта 443

Файл выглядит примерно так:
```nginx
server {
    listen 443 ssl;
    server_name xn--b1aaakc4awhjdoz3hm.xn--p1ai;

    ssl_certificate /etc/letsencrypt/live/.../fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/.../privkey.pem;

    root /var/www/168fz-landing;
    index index.html;

    # ... тут могут быть location блоки ...

    location / {
        try_files $uri $uri/ =404;
    }

    location /admin {
        proxy_pass http://127.0.0.1:8080;
        # ...
    }
}
```

### Шаг 3: Вставь конфиг

Скопируй ВЕСЬ текст ниже и вставь его ПОСЛЕ строки `index index.html;`
и ПЕРЕД первым `location / {`:

```nginx
    # =============================================
    # SEO-фиксы (добавлено 2026-03-03)
    # =============================================

    # 1. GZIP-СЖАТИЕ — страницы будут весить в 3-4 раза меньше
    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_min_length 1000;
    gzip_types
        text/plain
        text/css
        application/json
        application/javascript
        text/xml
        application/xml
        application/xml+rss
        text/javascript
        image/svg+xml;

    # 2. КЕШИРОВАНИЕ СТАТИКИ — CSS, картинки, шрифты кешируются на 30 дней
    location ~* \.(css|js|svg|png|jpg|jpeg|gif|ico|woff|woff2|ttf|eot)$ {
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # 3. ЗАГОЛОВКИ БЕЗОПАСНОСТИ
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header Permissions-Policy "camera=(), microphone=(), geolocation=()" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' https://mc.yandex.ru https://fonts.googleapis.com; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src https://fonts.gstatic.com; img-src 'self' https://mc.yandex.ru data:; connect-src 'self' https://mc.yandex.ru;" always;

    # 4. КАСТОМНАЯ 404
    error_page 404 /404.html;

    # 5. РЕДИРЕКТ /blog → /blog/ (чтобы не было двух URL)
    location = /blog {
        return 301 /blog/;
    }
```

### Шаг 4: Проверь и перезагрузи

Открой терминал в VSCode (Ctrl+`) и выполни:

```bash
sudo nginx -t
```

Если видишь `syntax is ok` и `test is successful` — всё хорошо. Далее:

```bash
sudo systemctl reload nginx
```

### Шаг 5: Проверь что работает

Открой в браузере:
- https://проверьвывеску.рф — должна открыться как обычно
- https://проверьвывеску.рф/blog — должен редиректить на /blog/
- https://проверьвывеску.рф/несуществующая-страница — должна показать красивую 404

### Если что-то сломалось

Убери всё что вставил между комментариями `# SEO-фиксы` и сохрани. Потом:
```bash
sudo nginx -t && sudo systemctl reload nginx
```
Сайт вернётся как было.

## Что это даст

| Метрика | Было | Станет |
|---------|------|--------|
| Размер страницы | 46 KB | ~12 KB |
| Security Score | 15/100 | 90/100 |
| Technical SEO | 62/100 | ~82/100 |
| Повторные визиты | медленно | мгновенно |
