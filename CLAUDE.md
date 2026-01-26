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
│   └── users/              # ✅ Реализовано
├── core/                   # Общий код
│   ├── exceptions.py       # BaseServiceError, NotFoundError, PermissionDeniedError, ValidationError, ConflictError
│   ├── mixins.py           # TimestampMixin (created_at, updated_at)
│   └── pagination.py       # StandardPagination
├── docker/
├── docker-compose.yml
├── pyproject.toml
└── manage.py
```

### Планируемые приложения

```
apps/
├── users/           ✅ Реализовано
├── projects/        📋 Планируется
├── tasks/           📋 Планируется
├── tags/            📋 Планируется
├── comments/        📋 Планируется
├── attachments/     📋 Планируется
├── notifications/   📋 Планируется
└── activity/        📋 Планируется
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
├── permissions.py
├── admin.py
├── migrations/
└── tests/
    ├── conftest.py
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

## Критические правила

### Обязательно

- `@transaction.atomic` для всех операций записи в сервисах
- `transaction.on_commit()` для Celery задач внутри транзакции
- `select_related`/`prefetch_related` в каждом селекторе
- `update_fields` при `save()` (включая `updated_at` если модель наследует `TimestampMixin`)
- Явный `on_delete` для всех ForeignKey
- Исключения вместо `None` в селекторах
- `select_for_update()` для конкурентного доступа к данным

### Запрещено

- `fields = '__all__'` в сериализаторах
- Бизнес-логика в моделях, views или сериализаторах
- Запись данных в селекторах
- Синхронные задачи (email, внешние API) внутри транзакции
- Возврат `dict` вместо объекта из сервисов
- `FloatField` для денег (только `DecimalField`)

### Паттерны именования

| Слой | Префиксы методов |
|------|------------------|
| Selector | `get_` (один объект), `filter_` (QuerySet), `exists_`, `count_` |
| Service | Глаголы: `create_`, `update_`, `delete_`, `cancel_`, `publish_` |

## Использование исключений

Кастомные исключения из `core/exceptions.py` автоматически обрабатываются в `core/exception_handler.py`:

```python
from core.exceptions import NotFoundError, ValidationError, ConflictError

# В селекторах — бросать NotFoundError вместо возврата None
def get_by_id(user_id: int) -> User:
    try:
        return User.objects.get(id=user_id)
    except User.DoesNotExist:
        raise NotFoundError('Пользователь не найден')

# В сервисах — ValidationError для бизнес-ошибок, ConflictError для дубликатов
def register_user(email: str) -> User:
    if selectors.exists_email(email):
        raise ConflictError('Пользователь с таким email уже существует')
```

| Исключение | HTTP код | Когда использовать |
|------------|----------|-------------------|
| `NotFoundError` | 404 | Объект не найден |
| `ValidationError` | 400 | Бизнес-валидация не пройдена |
| `ConflictError` | 409 | Дубликат, конфликт данных |
| `PermissionDeniedError` | 403 | Нет прав доступа |

## Реализованные приложения

### apps/users

Кастомная модель пользователя с JWT аутентификацией, верификацией email и сбросом пароля.

**Модели:** `User`, `EmailVerificationToken`, `PasswordResetToken`

**API Endpoints:**

| Метод | URL | Описание | Auth |
|-------|-----|----------|------|
| POST | `/api/v1/auth/register/` | Регистрация | — |
| POST | `/api/v1/auth/token/` | Получение JWT (login) | — |
| POST | `/api/v1/auth/token/refresh/` | Обновление access токена | — |
| POST | `/api/v1/auth/verify-email/` | Подтверждение email | — |
| POST | `/api/v1/auth/resend-verification/` | Повторная отправка | JWT |
| POST | `/api/v1/auth/password-reset/` | Запрос сброса пароля | — |
| POST | `/api/v1/auth/password-reset/confirm/` | Подтверждение сброса | — |
| GET | `/api/v1/users/` | Список пользователей | Admin |
| GET | `/api/v1/users/{id}/` | Профиль пользователя | JWT+Owner |
| PATCH | `/api/v1/users/{id}/` | Обновление профиля | JWT+Owner |
| GET | `/api/v1/users/me/` | Текущий пользователь | JWT |
| POST | `/api/v1/users/me/change-password/` | Смена пароля | JWT |

## Документация по слоям

**ВАЖНО**: Перед написанием кода ОБЯЗАТЕЛЬНО прочитай соответствующий файл документации.

### При написании Models

Читай: [common/02-models.md](rules-drf-django/django-rules/common/02-models.md)

Ключевое:
- `TextChoices`/`IntegerChoices` для enum
- `DecimalField` для денег
- Индексы в `Meta.indexes` для частых запросов
- `CheckConstraint`/`UniqueConstraint` для бизнес-правил БД

### При написании Selectors

Читай: [common/03-selectors.md](rules-drf-django/django-rules/common/03-selectors.md)

Ключевое:
- Всегда `select_related` для FK/OneToOne
- Всегда `prefetch_related` для M2M/reverse FK
- `Prefetch` с фильтрацией для сложных случаев
- `only()`/`defer()` для тяжёлых полей

### При написании Services

Читай: [common/04-services.md](rules-drf-django/django-rules/common/04-services.md)

Ключевое:
- `@transaction.atomic` на каждом методе записи
- `select_for_update()` через селектор для блокировки
- `transaction.on_commit(lambda: task.delay(id))` для Celery
- `bulk_create`/`bulk_update` для массовых операций

### При написании Serializers

Читай: [drf/02-serializers.md](rules-drf-django/django-rules/drf/02-serializers.md)

Ключевое:
- Разные сериализаторы: `*ListSerializer`, `*DetailSerializer`, `*CreateSerializer`
- Явно указывать `fields` и `read_only_fields`
- Валидация в `validate_<field>()` и `validate()`
- Никакой бизнес-логики в `create()`/`update()`

### При написании Views/ViewSets

Читай: [drf/01-viewsets.md](rules-drf-django/django-rules/drf/01-viewsets.md)

Ключевое:
- `get_queryset()` использует селекторы
- `get_serializer_class()` возвращает разные сериализаторы
- `perform_create()`/`perform_update()` вызывают сервисы
- `@action` для кастомных эндпоинтов

### При написании Permissions

Читай: [security/02-permissions.md](rules-drf-django/django-rules/security/02-permissions.md)

Ключевое:
- `has_permission()` — доступ к view
- `has_object_permission()` — доступ к объекту
- Выносить в отдельный `permissions.py`

### При оптимизации запросов

Читай: [optimization/01-database-queries.md](rules-drf-django/django-rules/optimization/01-database-queries.md)

Ключевое:
- `QuerySet.explain()` для анализа
- `exists()` вместо `if queryset`
- `count()` вместо `len(queryset)`
- `values_list('id', flat=True)` для списков ID

### При написании тестов

Читай: [quality/01-testing.md](rules-drf-django/django-rules/quality/01-testing.md)

Ключевое:
- Factory Boy для создания объектов
- `@pytest.mark.django_db` для тестов с БД
- `CaptureQueriesContext` для проверки количества запросов
- `freezegun` для тестов с временем

## Полный список документации

**Архитектура:**
- rules-drf-django/django-rules/architecture/01-layers.md
- rules-drf-django/django-rules/architecture/02-patterns.md

**Основное:**
- rules-drf-django/django-rules/common/01-project-structure.md
- rules-drf-django/django-rules/common/02-models.md
- rules-drf-django/django-rules/common/03-selectors.md
- rules-drf-django/django-rules/common/04-services.md
- rules-drf-django/django-rules/common/05-urls.md
- rules-drf-django/django-rules/common/06-migrations.md
- rules-drf-django/django-rules/common/07-admin.md
- rules-drf-django/django-rules/common/08-signals.md
- rules-drf-django/django-rules/common/09-middleware.md
- rules-drf-django/django-rules/common/10-commands.md
- rules-drf-django/django-rules/common/11-task.md
- rules-drf-django/django-rules/common/12-deployment.md

**DRF:**
- rules-drf-django/django-rules/drf/01-viewsets.md
- rules-drf-django/django-rules/drf/02-serializers.md
- rules-drf-django/django-rules/drf/03-pagination.md
- rules-drf-django/django-rules/drf/04-filtering.md
- rules-drf-django/django-rules/drf/05-versioning.md
- rules-drf-django/django-rules/drf/06-exceptions.md

**Безопасность:**
- rules-drf-django/django-rules/security/01-authentication.md
- rules-drf-django/django-rules/security/02-permissions.md
- rules-drf-django/django-rules/security/03-validation.md
- rules-drf-django/django-rules/security/04-vulnerabilities.md
- rules-drf-django/django-rules/security/05-secrets.md
- rules-drf-django/django-rules/security/06-throttling.md

**Оптимизация:**
- rules-drf-django/django-rules/optimization/01-database-queries.md
- rules-drf-django/django-rules/optimization/02-caching.md
- rules-drf-django/django-rules/optimization/03-indexes.md
- rules-drf-django/django-rules/optimization/04-celery.md

**Качество:**
- rules-drf-django/django-rules/quality/01-testing.md
- rules-drf-django/django-rules/quality/02-code-style.md
- rules-drf-django/django-rules/quality/03-documentation.md
- rules-drf-django/django-rules/quality/04-logging.md
- rules-drf-django/django-rules/quality/05-error-handling.md
