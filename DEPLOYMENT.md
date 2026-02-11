# Production Deployment

## Подготовка

### 1. Создать .env файл

```bash
cp .env.production.example .env
```

Изменить переменные для production:

```bash
SECRET_KEY=<сгенерировать через secrets.token_urlsafe(50)>
DEBUG=False
ALLOWED_HOSTS=grigorenkodanil.ru,www.grigorenkodanil.ru
DJANGO_SETTINGS_MODULE=config.settings.production

DB_NAME=taskflow_prod
DB_USER=taskflow_user
DB_PASSWORD=<strong-password>
DB_HOST=db

REDIS_URL=redis://redis:6379/0

EMAIL_HOST=smtp.gmail.com
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=<app-password>
DEFAULT_FROM_EMAIL=noreply@grigorenkodanil.ru

CORS_ALLOWED_ORIGINS=https://grigorenkodanil.ru
FRONTEND_URL=https://grigorenkodanil.ru

# Опционально
# SENTRY_DSN=https://...
```

### 2. Запустить production

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

### 3. Применить миграции

```bash
docker compose -f docker-compose.prod.yml exec web python manage.py migrate
```

### 4. Собрать статические файлы

```bash
docker compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput
```

### 5. Создать суперпользователя

```bash
docker compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
```

### 6. Проверить health check

```bash
curl http://localhost/api/v1/health/
```

## SSL сертификаты (Let's Encrypt)

**После первого деплоя, когда HTTP работает:**

### 1. Остановить nginx

```bash
docker compose -f docker-compose.prod.yml stop nginx
```

### 2. Установить Certbot

```bash
sudo apt install certbot
```

### 3. Получить сертификат

```bash
sudo certbot certonly --standalone -d grigorenkodanil.ru -d www.grigorenkodanil.ru
```

### 4. Обновить nginx.conf

Добавить SSL блок в `docker/nginx/nginx.conf`:

```nginx
server {
    listen 443 ssl http2;
    server_name grigorenkodanil.ru www.grigorenkodanil.ru;

    ssl_certificate /etc/letsencrypt/live/grigorenkodanil.ru/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/grigorenkodanil.ru/privkey.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Остальная конфигурация (location /, /ws/, /static/, /media/)
}

server {
    listen 80;
    server_name grigorenkodanil.ru www.grigorenkodanil.ru;
    return 301 https://$server_name$request_uri;
}
```

### 5. Монтировать сертификаты

Обновить `docker-compose.prod.yml`:

```yaml
nginx:
  volumes:
    - /etc/letsencrypt:/etc/letsencrypt:ro
```

### 6. Включить SSL в Django

Обновить `.env`:
```bash
ENABLE_SSL=True
```

Перезапустить web:
```bash
docker compose -f docker-compose.prod.yml restart web
```

### 7. Перезапустить nginx

```bash
docker compose -f docker-compose.prod.yml up -d nginx
```

### 8. Автообновление сертификатов

Добавить в crontab:

```bash
0 3 * * * certbot renew --quiet && docker compose -f /path/to/project/docker-compose.prod.yml restart nginx
```

## Мониторинг

### Логи

```bash
# Django (web)
docker compose -f docker-compose.prod.yml logs -f web

# WebSocket
docker compose -f docker-compose.prod.yml logs -f websocket

# Nginx
docker compose -f docker-compose.prod.yml logs -f nginx

# Celery
docker compose -f docker-compose.prod.yml logs -f celery

# Все сервисы
docker compose -f docker-compose.prod.yml logs -f
```

### Метрики

Опционально: Sentry для мониторинга ошибок (требуется `SENTRY_DSN` в `.env`)

## Backup и восстановление БД

### Создать backup

```bash
docker compose -f docker-compose.prod.yml exec db pg_dump -U taskflow_user taskflow_prod > backup_$(date +%Y%m%d_%H%M%S).sql
```

### Восстановить из backup

```bash
docker compose -f docker-compose.prod.yml exec -T db psql -U taskflow_user taskflow_prod < backup_20240101_120000.sql
```

## Обновление

### 1. Остановить сервисы

```bash
docker compose -f docker-compose.prod.yml down
```

### 2. Обновить код

```bash
git pull origin main
```

### 3. Пересобрать и запустить

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

### 4. Применить миграции

```bash
docker compose -f docker-compose.prod.yml exec web python manage.py migrate
```

### 5. Собрать статику (если изменилась)

```bash
docker compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput
```

## Troubleshooting

### Проблема: контейнер web не запускается

```bash
docker compose -f docker-compose.prod.yml logs web
docker compose -f docker-compose.prod.yml exec web python manage.py check --deploy
```

### Проблема: ошибки миграций

```bash
docker compose -f docker-compose.prod.yml exec web python manage.py showmigrations
docker compose -f docker-compose.prod.yml exec web python manage.py migrate --fake <app> <migration>
```

### Проблема: WebSocket не работает

Проверить nginx конфигурацию для `/ws/` location и логи:

```bash
docker compose -f docker-compose.prod.yml logs websocket
docker compose -f docker-compose.prod.yml logs nginx
```
