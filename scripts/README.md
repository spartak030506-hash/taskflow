# Deployment Scripts

## deploy.sh - Первый деплой на HTTP

Автоматизирует первый деплой проекта без SSL.

### Использование

```bash
chmod +x scripts/deploy.sh
./scripts/deploy.sh
```

### Что делает скрипт

1. ✅ Проверяет наличие `.env` файла
2. ✅ Проверяет критичные переменные (`SECRET_KEY`, `DB_PASSWORD`, `ALLOWED_HOSTS`)
3. ✅ Запускает `docker compose -f docker-compose.prod.yml up -d --build`
4. ✅ Ждёт готовности сервисов (10 секунд)
5. ✅ Проверяет статус контейнеров
6. ✅ Применяет миграции БД
7. ✅ Собирает статические файлы (`collectstatic`)
8. ✅ Создаёт суперпользователя (интерактивно)
9. ✅ Проверяет работу API

### Требования

- `.env` файл должен существовать и быть заполнен
- `SECRET_KEY` не должен содержать "CHANGE_ME"
- `DB_PASSWORD` должен быть задан
- `ALLOWED_HOSTS` должен быть задан
- `DEBUG=False` для production

### После выполнения

API доступен на:
- `http://YOUR_IP/api/v1/`
- `http://YOUR_IP/admin/`
- `http://YOUR_IP/api/docs/`

---

## setup-ssl.sh - Настройка HTTPS

Автоматизирует настройку SSL сертификатов и HTTPS.

### Использование

```bash
chmod +x scripts/setup-ssl.sh
./scripts/setup-ssl.sh yourdomain.com
```

### Что делает скрипт

1. ✅ Останавливает nginx в Docker
2. ✅ Проверяет/устанавливает Certbot
3. ✅ Получает SSL сертификаты через Let's Encrypt
4. ✅ Обновляет `docker/nginx/nginx.conf` для HTTPS
5. ✅ Обновляет `docker-compose.prod.yml` (добавляет порт 443 и volume для сертификатов)
6. ✅ Включает `ENABLE_SSL=True` в `.env`
7. ✅ Перезапускает все сервисы
8. ✅ Проверяет работу HTTPS
9. ✅ Настраивает автообновление сертификатов (cron)

### Требования

**Перед запуском обязательно:**

1. DNS должен быть настроен:
   ```
   A запись: yourdomain.com → IP_VPS
   A запись: www.yourdomain.com → IP_VPS
   ```

2. HTTP должен работать:
   ```bash
   curl http://yourdomain.com/api/v1/users/
   ```

3. Порт 80 должен быть открыт в файрволе

### После выполнения

HTTPS доступен на:
- `https://yourdomain.com/api/v1/`
- `https://yourdomain.com/admin/`
- `https://yourdomain.com/api/docs/`

HTTP автоматически редиректит на HTTPS.

### Backups

Скрипт создаёт backups перед изменениями:
- `docker/nginx/nginx.conf.backup`
- `docker-compose.prod.yml.backup`

Для отката:
```bash
mv docker/nginx/nginx.conf.backup docker/nginx/nginx.conf
mv docker-compose.prod.yml.backup docker-compose.prod.yml
docker compose -f docker-compose.prod.yml up -d
```

---

## Troubleshooting

### deploy.sh не запускается

```bash
# Проверить права
ls -l scripts/deploy.sh

# Сделать исполняемым
chmod +x scripts/deploy.sh
```

### "SECRET_KEY не настроен"

```bash
# Сгенерировать новый SECRET_KEY
python3 -c "import secrets; print(secrets.token_urlsafe(50))"

# Вставить в .env
nano .env
```

### setup-ssl.sh: "Сертификат не получен"

Проверь:
1. DNS настроен правильно:
   ```bash
   dig yourdomain.com
   ping yourdomain.com
   ```

2. Порт 80 открыт:
   ```bash
   sudo ufw status
   sudo ufw allow 80/tcp
   ```

3. Nginx остановлен:
   ```bash
   docker compose -f docker-compose.prod.yml stop nginx
   sudo lsof -i :80  # Не должно быть процессов
   ```

### "HTTPS не отвечает" после setup-ssl.sh

```bash
# Проверить логи nginx
docker compose -f docker-compose.prod.yml logs nginx

# Проверить сертификаты
sudo ls -la /etc/letsencrypt/live/yourdomain.com/

# Проверить nginx.conf
cat docker/nginx/nginx.conf | grep ssl_certificate
```

---

## Полезные команды после деплоя

```bash
# Логи всех сервисов
docker compose -f docker-compose.prod.yml logs -f

# Логи Django
docker compose -f docker-compose.prod.yml logs -f web

# Логи Nginx
docker compose -f docker-compose.prod.yml logs -f nginx

# Перезапуск всех сервисов
docker compose -f docker-compose.prod.yml restart

# Остановка всех сервисов
docker compose -f docker-compose.prod.yml down

# Обновление после git pull
git pull
docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml exec web python manage.py migrate
docker compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput
```
