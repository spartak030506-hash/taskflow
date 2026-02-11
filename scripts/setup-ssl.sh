#!/bin/bash

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

DOMAIN=$1

if [ -z "$DOMAIN" ]; then
    echo -e "${RED}✗ Укажи домен!${NC}"
    echo "Usage: $0 yourdomain.com"
    exit 1
fi

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}TaskFlow SSL Setup${NC}"
echo -e "${BLUE}================================${NC}"
echo ""
echo -e "${BLUE}Домен: ${YELLOW}${DOMAIN}${NC}"
echo ""

echo -e "${YELLOW}⚠ Перед запуском убедись что:${NC}"
echo "  1. DNS настроен (домен → IP VPS)"
echo "  2. HTTP работает (curl http://${DOMAIN}/api/v1/users/)"
echo ""
read -p "Продолжить? (y/N): " confirm
if [[ ! $confirm =~ ^[Yy]$ ]]; then
    exit 0
fi

echo ""
echo -e "${BLUE}Шаг 1: Остановка nginx...${NC}"
docker compose -f docker-compose.prod.yml stop nginx

echo ""
echo -e "${BLUE}Шаг 2: Проверка Certbot...${NC}"
if ! command -v certbot &> /dev/null; then
    echo -e "${YELLOW}Certbot не установлен. Устанавливаю...${NC}"
    sudo apt update
    sudo apt install certbot -y
fi
echo -e "${GREEN}✓ Certbot установлен${NC}"

echo ""
echo -e "${BLUE}Шаг 3: Получение SSL сертификата...${NC}"
echo -e "${YELLOW}Certbot спросит email и согласие с ToS${NC}"
sudo certbot certonly --standalone -d ${DOMAIN} -d www.${DOMAIN}

if [ ! -f "/etc/letsencrypt/live/${DOMAIN}/fullchain.pem" ]; then
    echo -e "${RED}✗ Сертификат не получен!${NC}"
    echo -e "${YELLOW}Проверь:${NC}"
    echo "  1. DNS правильно настроен"
    echo "  2. Порт 80 открыт"
    echo "  3. Домен доступен из интернета"
    exit 1
fi

echo -e "${GREEN}✓ Сертификат получен${NC}"

echo ""
echo -e "${BLUE}Шаг 4: Обновление nginx.conf...${NC}"

NGINX_CONF="docker/nginx/nginx.conf"
NGINX_BACKUP="docker/nginx/nginx.conf.backup"

cp ${NGINX_CONF} ${NGINX_BACKUP}
echo -e "${GREEN}✓ Создан backup: ${NGINX_BACKUP}${NC}"

cat > ${NGINX_CONF} << 'EOF'
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';

    access_log /var/log/nginx/access.log main;

    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;

    gzip on;
    gzip_disable "msie6";
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css text/xml text/javascript application/json application/javascript application/xml+rss application/rss+xml font/truetype font/opentype application/vnd.ms-fontobject image/svg+xml;

    upstream django {
        server web:8000;
    }

    upstream websocket {
        server websocket:8001;
    }

    server {
        listen 80;
        server_name _;
        return 301 https://$host$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name _;
        client_max_body_size 10M;

        ssl_certificate /etc/letsencrypt/live/DOMAIN_PLACEHOLDER/fullchain.pem;
        ssl_certificate_key /etc/letsencrypt/live/DOMAIN_PLACEHOLDER/privkey.pem;

        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_prefer_server_ciphers on;
        ssl_ciphers HIGH:!aNULL:!MD5;

        location / {
            proxy_pass http://django;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        location /ws/ {
            proxy_pass http://websocket;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        location /static/ {
            alias /app/staticfiles/;
            expires 30d;
            add_header Cache-Control "public, immutable";
        }

        location /media/ {
            alias /app/media/;
            expires 30d;
            add_header Cache-Control "public";
        }
    }
}
EOF

sed -i "s/DOMAIN_PLACEHOLDER/${DOMAIN}/g" ${NGINX_CONF}
echo -e "${GREEN}✓ nginx.conf обновлён${NC}"

echo ""
echo -e "${BLUE}Шаг 5: Обновление docker-compose.prod.yml...${NC}"

COMPOSE_FILE="docker-compose.prod.yml"
COMPOSE_BACKUP="docker-compose.prod.yml.backup"

cp ${COMPOSE_FILE} ${COMPOSE_BACKUP}
echo -e "${GREEN}✓ Создан backup: ${COMPOSE_BACKUP}${NC}"

if ! grep -q "/etc/letsencrypt" ${COMPOSE_FILE}; then
    # Добавить volume для сертификатов после media_volume
    awk '/nginx:/{flag=1} flag && /- media_volume:\/app\/media:ro/{print; print "      - /etc/letsencrypt:/etc/letsencrypt:ro"; flag=0; next} 1' ${COMPOSE_FILE} > ${COMPOSE_FILE}.tmp
    mv ${COMPOSE_FILE}.tmp ${COMPOSE_FILE}
    echo -e "${GREEN}✓ Добавлен volume для сертификатов${NC}"
fi

if ! grep -q '"443:443"' ${COMPOSE_FILE}; then
    # Добавить порт 443 после порта 80
    awk '/- "80:80"/{print; print "      - \"443:443\""; next} 1' ${COMPOSE_FILE} > ${COMPOSE_FILE}.tmp
    mv ${COMPOSE_FILE}.tmp ${COMPOSE_FILE}
    echo -e "${GREEN}✓ Добавлен порт 443${NC}"
fi

echo ""
echo -e "${BLUE}Шаг 6: Включение SSL в Django...${NC}"

if grep -q "^ENABLE_SSL=False" .env; then
    sed -i 's/^ENABLE_SSL=False/ENABLE_SSL=True/' .env
    echo -e "${GREEN}✓ ENABLE_SSL=True${NC}"
else
    echo -e "${YELLOW}⚠ ENABLE_SSL уже включен или не найден${NC}"
fi

echo ""
echo -e "${BLUE}Шаг 7: Перезапуск сервисов...${NC}"
docker compose -f docker-compose.prod.yml up -d --build

echo ""
echo -e "${BLUE}Шаг 8: Проверка HTTPS...${NC}"
sleep 5

if curl -s -o /dev/null -w "%{http_code}" https://${DOMAIN}/api/v1/users/ | grep -q "200\|401"; then
    echo -e "${GREEN}✓ HTTPS работает!${NC}"
else
    echo -e "${YELLOW}⚠ HTTPS не отвечает${NC}"
    echo -e "${YELLOW}Проверь логи:${NC}"
    echo "  docker compose -f docker-compose.prod.yml logs nginx"
fi

echo ""
echo -e "${BLUE}Шаг 9: Настройка автообновления сертификатов...${NC}"

PROJECT_DIR=$(pwd)
CRON_JOB="0 3 * * * certbot renew --quiet && cd ${PROJECT_DIR} && docker compose -f docker-compose.prod.yml restart nginx"

if ! sudo crontab -l 2>/dev/null | grep -q "certbot renew"; then
    (sudo crontab -l 2>/dev/null; echo "${CRON_JOB}") | sudo crontab -
    echo -e "${GREEN}✓ Cron job добавлен${NC}"
else
    echo -e "${YELLOW}⚠ Cron job уже существует${NC}"
fi

echo ""
echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}✓ SSL настроен успешно!${NC}"
echo -e "${GREEN}================================${NC}"
echo ""
echo -e "${BLUE}Проверь:${NC}"
echo "  https://${DOMAIN}/api/v1/users/"
echo "  https://${DOMAIN}/admin/"
echo "  https://${DOMAIN}/api/docs/"
echo ""
echo -e "${YELLOW}Backups созданы:${NC}"
echo "  ${NGINX_BACKUP}"
echo "  ${COMPOSE_BACKUP}"
echo ""
