#!/bin/bash

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}TaskFlow Production Deployment${NC}"
echo -e "${BLUE}================================${NC}"
echo ""

if [ ! -f ".env" ]; then
    echo -e "${RED}✗ .env файл не найден!${NC}"
    echo -e "${YELLOW}Создай .env файл:${NC}"
    echo "  cp .env.production.example .env"
    echo "  nano .env"
    exit 1
fi

echo -e "${GREEN}✓ .env файл найден${NC}"
echo ""

echo -e "${BLUE}Проверка критичных переменных...${NC}"
check_env() {
    local var_name=$1
    local var_value=$(grep "^${var_name}=" .env | cut -d '=' -f2)

    if [ -z "$var_value" ] || [[ "$var_value" == *"CHANGE_ME"* ]]; then
        echo -e "${RED}✗ ${var_name} не настроен!${NC}"
        return 1
    fi

    echo -e "${GREEN}✓ ${var_name}${NC}"
    return 0
}

errors=0
check_env "SECRET_KEY" || ((errors++))
check_env "DB_PASSWORD" || ((errors++))
check_env "ALLOWED_HOSTS" || ((errors++))

if [ $errors -gt 0 ]; then
    echo ""
    echo -e "${RED}Исправь .env и запусти скрипт снова${NC}"
    exit 1
fi

DEBUG=$(grep "^DEBUG=" .env | cut -d '=' -f2)
if [ "$DEBUG" != "False" ]; then
    echo -e "${YELLOW}⚠ WARNING: DEBUG должен быть False в production!${NC}"
    read -p "Продолжить? (y/N): " confirm
    if [[ ! $confirm =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo ""
echo -e "${BLUE}Шаг 1: Запуск Docker Compose...${NC}"
docker compose -f docker-compose.prod.yml up -d --build

echo ""
echo -e "${BLUE}Шаг 2: Ожидание готовности сервисов...${NC}"
sleep 10

echo ""
echo -e "${BLUE}Шаг 3: Проверка статуса контейнеров...${NC}"
docker compose -f docker-compose.prod.yml ps

if ! docker compose -f docker-compose.prod.yml ps | grep -q "Up"; then
    echo -e "${RED}✗ Некоторые контейнеры не запустились!${NC}"
    echo -e "${YELLOW}Проверь логи:${NC}"
    echo "  docker compose -f docker-compose.prod.yml logs"
    exit 1
fi

echo -e "${GREEN}✓ Все контейнеры запущены${NC}"

echo ""
echo -e "${BLUE}Шаг 4: Применение миграций...${NC}"
docker compose -f docker-compose.prod.yml exec -T web python manage.py migrate

echo ""
echo -e "${BLUE}Шаг 5: Сбор статических файлов...${NC}"
docker compose -f docker-compose.prod.yml exec -T web python manage.py collectstatic --noinput

echo ""
echo -e "${BLUE}Шаг 6: Создание суперпользователя...${NC}"
echo -e "${YELLOW}Введи email и пароль для админа:${NC}"
docker compose -f docker-compose.prod.yml exec web python manage.py createsuperuser

echo ""
echo -e "${BLUE}Шаг 7: Проверка работы API...${NC}"
if curl -s -o /dev/null -w "%{http_code}" http://localhost/api/v1/users/ | grep -q "200\|401"; then
    echo -e "${GREEN}✓ API отвечает!${NC}"
else
    echo -e "${YELLOW}⚠ API не отвечает (возможно нормально)${NC}"
fi

echo ""
echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}✓ Деплой завершён успешно!${NC}"
echo -e "${GREEN}================================${NC}"
echo ""
echo -e "${BLUE}Полезные команды:${NC}"
echo "  Логи всех сервисов:"
echo "    docker compose -f docker-compose.prod.yml logs -f"
echo ""
echo "  Логи Django:"
echo "    docker compose -f docker-compose.prod.yml logs -f web"
echo ""
echo "  Проверка API:"
echo "    curl http://localhost/api/v1/users/"
echo ""
echo "  Админка:"
echo "    http://YOUR_IP/admin/"
echo ""
echo "  Swagger документация:"
echo "    http://YOUR_IP/api/docs/"
echo ""
echo -e "${YELLOW}Для настройки HTTPS запусти:${NC}"
echo "  ./scripts/setup-ssl.sh yourdomain.com"
echo ""
