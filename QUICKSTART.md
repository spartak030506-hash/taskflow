# Quick Start - Деплой на VPS за 5 минут

## 1. На VPS: Клонировать проект

```bash
git clone https://github.com/your-repo/taskflow.git
cd taskflow
```

## 2. Создать .env

```bash
cp .env.production.example .env
nano .env
```

**Обязательно изменить:**

```bash
# Сгенерировать
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(50))")

# Заполнить
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com,YOUR_VPS_IP
DB_PASSWORD=Strong_Pa$$w0rd_Here
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

Сохранить (Ctrl+O, Enter, Ctrl+X).

## 3. Запустить деплой

```bash
./scripts/deploy.sh
```

Скрипт сделает всё сам: Docker, миграции, статику, создаст админа.

**Результат:** API работает на `http://YOUR_VPS_IP/api/v1/`

---

## 4. (Опционально) Настроить HTTPS

### Сначала настроить DNS:

В панели регистратора домена:
```
A запись: yourdomain.com → YOUR_VPS_IP
A запись: www.yourdomain.com → YOUR_VPS_IP
```

Подождать 5-30 минут пока DNS распространится.

### Проверить DNS:

```bash
ping yourdomain.com  # Должен показать YOUR_VPS_IP
```

### Запустить настройку SSL:

```bash
./scripts/setup-ssl.sh yourdomain.com
```

Скрипт получит сертификаты, настроит HTTPS, включит редирект.

**Результат:** API работает на `https://yourdomain.com/api/v1/`

---

## Полезные команды

```bash
# Логи всех сервисов
docker compose -f docker-compose.prod.yml logs -f

# Только Django
docker compose -f docker-compose.prod.yml logs -f web

# Перезапуск
docker compose -f docker-compose.prod.yml restart

# Остановка
docker compose -f docker-compose.prod.yml down
```

---

## Troubleshooting

### Ошибка: "SECRET_KEY не настроен"

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(50))"
# Скопировать результат в .env
nano .env
```

### Контейнер не запускается

```bash
docker compose -f docker-compose.prod.yml logs web
docker compose -f docker-compose.prod.yml logs db
```

### 502 Bad Gateway

```bash
docker compose -f docker-compose.prod.yml logs nginx
docker compose -f docker-compose.prod.yml restart web
```

### SSL не работает

```bash
# Проверить что DNS настроен
ping yourdomain.com

# Проверить что HTTP работает
curl http://yourdomain.com/api/v1/users/

# Запустить setup-ssl.sh снова
./scripts/setup-ssl.sh yourdomain.com
```

---

## Готово! 🚀

Админка: `http(s)://YOUR_IP/admin/`
API: `http(s)://YOUR_IP/api/v1/`
Swagger: `http(s)://YOUR_IP/api/docs/`
