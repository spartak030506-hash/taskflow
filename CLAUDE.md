# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Проект

TaskFlow — REST API платформа для управления проектами и задачами на Django + DRF.

## Быстрый старт

```bash
docker-compose up -d
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
```

API: `http://localhost:8000/api/v1/`

## Стек

- Python 3.12 + Django 5.1 + DRF 3.15
- PostgreSQL 16
- Redis 7 (кеш + Celery broker)
- Celery 5.4
- Django Channels 4.1 (WebSocket)
- SimpleJWT

## Архитектура

### Clean Architecture (слои)

```
Views/ViewSets  →  Services  →  Selectors  →  Models
    (HTTP)        (логика)     (чтение)     (данные)
```

- **Views** — тонкие, только HTTP
- **Services** — вся бизнес-логика, `@transaction.atomic`
- **Selectors** — только чтение из БД, `select_related`/`prefetch_related`
- **Models** — только структура данных, без логики

### Структура проекта

```
taskflow-drf/
├── config/                 # Конфигурация Django
│   ├── settings/
│   │   ├── base.py
│   │   ├── local.py
│   │   ├── production.py
│   │   └── test.py
│   ├── urls.py
│   └── asgi.py
├── apps/                   # Django-приложения
│   ├── users/
│   ├── projects/
│   ├── tasks/
│   ├── tags/
│   ├── comments/
│   ├── attachments/
│   ├── notifications/
│   └── activity/
├── core/                   # Общий код
│   ├── exceptions.py
│   ├── mixins.py
│   └── pagination.py
├── docker/
├── docker-compose.yml
├── pyproject.toml
└── manage.py
```

### Структура приложения

```
apps/{app}/
├── models.py
├── selectors.py
├── services.py
├── serializers.py
├── views.py
├── urls.py
├── admin.py
├── migrations/
└── tests/
    ├── factories.py
    ├── test_models.py
    ├── test_services.py
    └── test_views.py
```

## Команды

```bash
# Docker
docker-compose up -d
docker-compose down
docker-compose logs -f web
docker-compose exec web bash

# Django
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
docker-compose exec web python manage.py shell_plus

# Тесты
docker-compose exec web pytest
docker-compose exec web pytest apps/users/ -v
docker-compose exec web pytest apps/users/tests/test_services.py::TestUserService::test_create -v
docker-compose exec web pytest --cov=apps

# Локальная установка
pip install -e ".[dev]"
```

## Правила

- Код без комментариев
- Никогда `fields = '__all__'` в сериализаторах
- Явный `on_delete` для ForeignKey
- `@transaction.atomic` для записи в сервисах
- `transaction.on_commit()` для Celery задач
- Исключения вместо `None` в селекторах

## TODO

- [ ] OAuth2 Google авторизация
- [ ] OAuth2 GitHub авторизация
- [ ] Burndown chart
- [ ] Экспорт в Excel

## Ссылки на правила

| Тема | Файл |
|------|------|
| Архитектура слоёв | [architecture/01-layers.md](rules-drf-django/django-rules/architecture/01-layers.md) |
| Паттерны | [architecture/02-patterns.md](rules-drf-django/django-rules/architecture/02-patterns.md) |
| Структура проекта | [common/01-project-structure.md](rules-drf-django/django-rules/common/01-project-structure.md) |
| Модели | [common/02-models.md](rules-drf-django/django-rules/common/02-models.md) |
| Селекторы | [common/03-selectors.md](rules-drf-django/django-rules/common/03-selectors.md) |
| Сервисы | [common/04-services.md](rules-drf-django/django-rules/common/04-services.md) |
| ViewSets | [drf/01-viewsets.md](rules-drf-django/django-rules/drf/01-viewsets.md) |
| Сериализаторы | [drf/02-serializers.md](rules-drf-django/django-rules/drf/02-serializers.md) |
| Аутентификация | [security/01-authentication.md](rules-drf-django/django-rules/security/01-authentication.md) |
| Права доступа | [security/02-permissions.md](rules-drf-django/django-rules/security/02-permissions.md) |
| Оптимизация запросов | [optimization/01-database-queries.md](rules-drf-django/django-rules/optimization/01-database-queries.md) |
| Тестирование | [quality/01-testing.md](rules-drf-django/django-rules/quality/01-testing.md) |
