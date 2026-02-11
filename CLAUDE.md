# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Проект

TaskFlow — REST API платформа для управления проектами и задачами на Django + DRF.

**Стек:** Python 3.12, Django 5.1, DRF 3.15, PostgreSQL 16, Redis 7, Celery 5.4, Channels 4.1, SimpleJWT

**Документация:**
- [DEVELOPMENT.md](DEVELOPMENT.md) — инструкции для разработки (использует `.env.dev.example`)
- [DEPLOYMENT.md](DEPLOYMENT.md) — инструкции для production (использует `.env.production.example`)

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

### Структура приложения

```
apps/<app>/
├── models.py              # Бизнес-слой
├── selectors.py           # Бизнес-слой
├── services.py            # Бизнес-слой
├── tasks.py               # Бизнес-слой (Celery)
│
├── api/                   # API-слой
│   ├── views.py
│   ├── serializers.py
│   ├── permissions.py
│   └── urls.py
│
└── tests/
```

**Правила импортов:**
- В `api/` импорт бизнес-слоя через `..`
- Межприложенческие импорты API через `.api.`
- Бизнес-слой НИКОГДА не импортирует из `api/`

### Core модули

```
core/
├── api_docs/           # OpenAPI декораторы
├── cache.py            # CacheKeys, CacheTTL, инвалидация
├── event_types.py      # WebSocket события
├── websocket.py        # send_to_project_group
├── middleware.py       # JWTAuthMiddleware
├── exceptions.py       # Кастомные исключения
├── mixins.py           # TimestampMixin
└── pagination.py       # StandardPagination
```

## Критические правила

### Обязательно

- `@transaction.atomic` для всех операций записи в сервисах
- `transaction.on_commit()` для Celery задач и инвалидации кеша
- `select_related`/`prefetch_related` в каждом селекторе
- `update_fields` при `save()` (включая `updated_at`)
- Явный `on_delete` для всех ForeignKey
- Исключения вместо `None` в селекторах
- `select_for_update()` для конкурентного доступа
- Инвалидация кеша при изменении данных

### Запрещено

- `fields = '__all__'` в сериализаторах
- Бизнес-логика в моделях, views или сериализаторах
- Запись данных в селекторах
- Синхронные задачи внутри транзакции
- Возврат `dict` вместо объекта из сервисов
- `FloatField` для денег (только `DecimalField`)
- Кеширование `select_for_update()` селекторов

### Паттерны именования

| Слой | Префиксы |
|------|----------|
| Selector | `get_`, `filter_`, `exists_`, `count_` |
| Service | `create_`, `update_`, `delete_`, `cancel_`, `publish_` |

## Использование исключений

Кастомные исключения из `core/exceptions.py`:

```python
from core.exceptions import NotFoundError, ValidationError, ConflictError

# В селекторах
def get_by_id(user_id: int) -> User:
    try:
        return User.objects.get(id=user_id)
    except User.DoesNotExist:
        raise NotFoundError('Пользователь не найден')

# В сервисах
def register_user(email: str) -> User:
    if selectors.exists_email(email):
        raise ConflictError('Пользователь с таким email уже существует')
```

| Исключение | HTTP | Когда |
|------------|------|-------|
| `NotFoundError` | 404 | Объект не найден |
| `ValidationError` | 400 | Бизнес-валидация |
| `ConflictError` | 409 | Дубликат/конфликт |
| `PermissionDeniedError` | 403 | Нет прав |

## Кеширование (Redis)

**ОБЯЗАТЕЛЬНО использовать обёртки из `core/cache.py`:**

```python
from core.cache import safe_cache_get, safe_cache_set, cache_with_lock
```

❌ **НИКОГДА напрямую:** `from django.core.cache import cache`

**Критические правила:**
1. Кэшировать только `dict`/`list`, НЕ ORM-объекты
2. Использовать sentinel для различия "не в кэше" и "False/None в кэше"
3. Короткий TTL (60s) для негативного кэширования
4. Инвалидация через `transaction.on_commit()`
5. Graceful degradation при падении Redis

**Паттерн:**

```python
from core.cache import cache_with_lock, CACHE_NONE_SENTINEL, CacheKeys, CacheTTL

def get_detail(project_id: int) -> dict:
    cache_key = CacheKeys.PROJECT_DETAIL.format(project_id=project_id)

    def fetch_project():
        try:
            project = Project.objects.select_related('owner').get(id=project_id)
        except Project.DoesNotExist:
            safe_cache_set(cache_key, CACHE_NONE_SENTINEL, CacheTTL.NOT_FOUND)
            raise NotFoundError('Проект не найден')

        return {'id': project.id, 'name': project.name, ...}

    result = cache_with_lock(cache_key, CacheTTL.PROJECT, fetch_project)

    if result == CACHE_NONE_SENTINEL:
        raise NotFoundError('Проект не найден')

    return result
```

## Документация по слоям

**ВАЖНО**: Перед написанием кода ОБЯЗАТЕЛЬНО прочитай соответствующий файл.

### При написании Models
Читай: [.AI-docs/django-rules/common/02-models.md](.AI-docs/django-rules/common/02-models.md)

### При написании Selectors
Читай: [.AI-docs/django-rules/common/03-selectors.md](.AI-docs/django-rules/common/03-selectors.md)

### При написании Services
Читай: [.AI-docs/django-rules/common/04-services.md](.AI-docs/django-rules/common/04-services.md)

### При написании Serializers
Читай: [.AI-docs/django-rules/drf/02-serializers.md](.AI-docs/django-rules/drf/02-serializers.md)

### При написании Views/ViewSets
Читай: [.AI-docs/django-rules/drf/01-viewsets.md](.AI-docs/django-rules/drf/01-viewsets.md)

### При написании Permissions
Читай: [.AI-docs/django-rules/security/02-permissions.md](.AI-docs/django-rules/security/02-permissions.md)

### При оптимизации запросов
Читай: [.AI-docs/django-rules/optimization/01-database-queries.md](.AI-docs/django-rules/optimization/01-database-queries.md)

### При кешировании
Читай: [.AI-docs/django-rules/optimization/02-caching.md](.AI-docs/django-rules/optimization/02-caching.md)

### При написании тестов
Читай: [.AI-docs/django-rules/quality/01-testing.md](.AI-docs/django-rules/quality/01-testing.md)

## Полный список документации

**Архитектура:**
- .AI-docs/django-rules/architecture/01-layers.md
- .AI-docs/django-rules/architecture/02-patterns.md

**Основное:**
- .AI-docs/django-rules/common/01-project-structure.md
- .AI-docs/django-rules/common/02-models.md
- .AI-docs/django-rules/common/03-selectors.md
- .AI-docs/django-rules/common/04-services.md
- .AI-docs/django-rules/common/05-urls.md
- .AI-docs/django-rules/common/06-migrations.md
- .AI-docs/django-rules/common/07-admin.md
- .AI-docs/django-rules/common/08-signals.md
- .AI-docs/django-rules/common/09-middleware.md
- .AI-docs/django-rules/common/10-commands.md
- .AI-docs/django-rules/common/11-task.md
- .AI-docs/django-rules/common/12-deployment.md

**DRF:**
- .AI-docs/django-rules/drf/01-viewsets.md
- .AI-docs/django-rules/drf/02-serializers.md
- .AI-docs/django-rules/drf/03-pagination.md
- .AI-docs/django-rules/drf/04-filtering.md
- .AI-docs/django-rules/drf/05-versioning.md
- .AI-docs/django-rules/drf/06-exceptions.md

**Безопасность:**
- .AI-docs/django-rules/security/01-authentication.md
- .AI-docs/django-rules/security/02-permissions.md
- .AI-docs/django-rules/security/03-validation.md
- .AI-docs/django-rules/security/04-vulnerabilities.md
- .AI-docs/django-rules/security/05-secrets.md
- .AI-docs/django-rules/security/06-throttling.md

**Оптимизация:**
- .AI-docs/django-rules/optimization/01-database-queries.md
- .AI-docs/django-rules/optimization/02-caching.md
- .AI-docs/django-rules/optimization/03-indexes.md
- .AI-docs/django-rules/optimization/04-celery.md

**Качество:**
- .AI-docs/django-rules/quality/01-testing.md
- .AI-docs/django-rules/quality/02-code-style.md
- .AI-docs/django-rules/quality/03-documentation.md
- .AI-docs/django-rules/quality/04-logging.md
- .AI-docs/django-rules/quality/05-error-handling.md
