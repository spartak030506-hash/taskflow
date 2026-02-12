# CLAUDE.md

Инструкции для Claude Code при работе с этим проектом.

## О проекте

**TaskFlow** — REST API платформа для управления проектами и задачами.

**Стек технологий:**
- Python 3.12 + Django 5.1 + DRF 3.15
- PostgreSQL 16
- Redis 7 (кеш + Celery broker + Channels)
- Celery 5.4 (асинхронные задачи)
- Channels 4.1 (WebSocket)
- SimpleJWT (JWT аутентификация)

**Документация:**
- `DEPLOYMENT.md` — production deployment
- `.AI-docs/` — детальные правила разработки

---

## Архитектура

### Clean Architecture (слои)

```
Views/ViewSets  →  Services  →  Selectors  →  Models
    (HTTP)        (логика)     (чтение)     (данные)
```

**Принципы:**
- **Views** — тонкие, только HTTP (парсинг, валидация, ответ)
- **Services** — вся бизнес-логика, `@transaction.atomic`
- **Selectors** — только чтение из БД, оптимизация запросов
- **Models** — только структура данных, без логики

### Структура проекта

```
taskflow-drf/
├── config/                     # Django конфигурация
│   ├── settings/
│   │   ├── base.py             # Общие настройки
│   │   ├── local.py            # Локальная разработка
│   │   ├── production.py       # Production
│   │   └── test.py             # Тесты
│   ├── urls.py                 # Главные URL маршруты
│   └── asgi.py                 # ASGI для WebSocket
│
├── apps/                       # Django приложения
│   ├── users/                  # Пользователи, аутентификация
│   ├── projects/               # Проекты, участники
│   ├── tasks/                  # Задачи
│   ├── tags/                   # Теги для задач
│   ├── comments/               # Комментарии к задачам
│   └── websocket/              # WebSocket real-time обновления
│
├── core/                       # Общий код
│   ├── api_docs/               # OpenAPI декораторы
│   ├── cache.py                # Кеширование (Redis)
│   ├── exceptions.py           # Кастомные исключения
│   ├── exception_handler.py    # DRF exception handler
│   ├── event_types.py          # WebSocket события
│   ├── websocket.py            # WebSocket утилиты
│   ├── middleware.py           # JWT middleware для WS
│   ├── mixins.py               # TimestampMixin
│   └── pagination.py           # StandardPagination
│
├── docker/                     # Docker конфигурация
├── pyproject.toml              # Зависимости проекта
└── manage.py
```

### Структура приложения

Каждое приложение разделено на **бизнес-слой** и **API-слой**:

```
apps/<app>/
├── models.py              # Бизнес-слой: модели
├── selectors.py           # Бизнес-слой: чтение из БД
├── services.py            # Бизнес-слой: бизнес-логика
├── tasks.py               # Бизнес-слой: Celery задачи
├── admin.py
│
├── api/                   # API-слой (DRF)
│   ├── views.py           # ViewSets, APIView
│   ├── serializers.py     # Сериализаторы
│   ├── permissions.py     # Permissions
│   └── urls.py            # URL маршруты
│
└── tests/
    ├── conftest.py        # Локальные фикстуры
    ├── factories.py       # Factory Boy фабрики
    ├── test_services.py   # Тесты бизнес-логики
    └── test_api.py        # Тесты API
```

### Правила импортов

**1. Внутри `api/` — импорт бизнес-слоя через `..`:**
```python
# apps/tasks/api/views.py
from .. import selectors, services
from ..models import Task
from .serializers import TaskSerializer
```

**2. Межприложенческие импорты API — через `.api.`:**
```python
# apps/tasks/api/serializers.py
from apps.users.api.serializers import UserListSerializer
from apps.tags.api.serializers import TagMinimalSerializer
```

**3. Бизнес-слой — импортирует только бизнес-слой:**
```python
# apps/tasks/services.py
from apps.projects import selectors as project_selectors
from apps.users.models import User
# ❌ НИКОГДА: from apps.users.api.serializers import ...
```

---

## Core модули

### `core/cache.py`

Централизованное управление кешированием через Redis.

**Константы:**
- `CACHE_VERSION = 'v1'` — версионирование ключей
- `CACHE_NONE_SENTINEL` — для различия `None` в кеше от отсутствия в кеше
- `CACHE_FALSE_SENTINEL` — для различия `False` в кеше от отсутствия в кеше
- `CacheTTL` — класс с константами времени жизни кеша
- `CacheKeys` — класс с шаблонами ключей

**Функции:**
- `safe_cache_get()` — чтение с graceful degradation
- `safe_cache_set()` — запись с graceful degradation
- `cache_with_lock()` — защита от cache stampede

### `core/exceptions.py`

Кастомные исключения для бизнес-логики:
- `NotFoundError` → 404
- `ValidationError` → 400
- `ConflictError` → 409
- `PermissionDeniedError` → 403

Автоматически обрабатываются в `core/exception_handler.py`.

### `core/api_docs/`

OpenAPI декораторы для документирования API:
- `list_endpoint_schema()`
- `create_endpoint_schema()`
- `retrieve_endpoint_schema()`
- `update_endpoint_schema()`
- `delete_endpoint_schema()`
- `action_endpoint_schema()`

### `core/event_types.py`

Константы для WebSocket событий:
- `TaskEvents` — события задач
- `CommentEvents` — события комментариев

### `core/websocket.py`

Утилиты для WebSocket:
- `send_to_project_group()` — broadcast события в группу проекта

---

## Критические правила

### ✅ Обязательно

- `@transaction.atomic` для всех операций записи в сервисах
- `transaction.on_commit()` для Celery задач и инвалидации кеша
- `select_related`/`prefetch_related` в каждом селекторе
- `update_fields` при `save()` (включая `updated_at`)
- Явный `on_delete` для всех `ForeignKey`
- Исключения вместо `None` в селекторах
- `select_for_update()` для конкурентного доступа
- Инвалидация кеша при изменении данных

### ❌ Запрещено

- `fields = '__all__'` в сериализаторах
- Бизнес-логика в моделях, views или сериализаторах
- Запись данных в селекторах
- Синхронные задачи (email, API) внутри транзакции
- Возврат `dict` вместо объекта из сервисов
- `FloatField` для денег (только `DecimalField`)
- Кеширование `select_for_update()` селекторов

### Паттерны именования

**Selectors:**
- `get_*()` — один объект, бросает исключение если не найден
- `filter_*()` — QuerySet
- `exists_*()` — bool
- `count_*()` — int

**Services:**
- Глаголы: `create_*()`, `update_*()`, `delete_*()`, `cancel_*()`, `publish_*()`

---

## Использование исключений

```python
from core.exceptions import NotFoundError, ValidationError, ConflictError

# В селекторах — NotFoundError вместо None
def get_by_id(user_id: int) -> User:
    try:
        return User.objects.get(id=user_id)
    except User.DoesNotExist:
        raise NotFoundError('Пользователь не найден')

# В сервисах — ValidationError для бизнес-ошибок
def register_user(email: str) -> User:
    if selectors.exists_email(email):
        raise ConflictError('Пользователь с таким email уже существует')
```

| Исключение | HTTP | Применение |
|------------|------|------------|
| `NotFoundError` | 404 | Объект не найден |
| `ValidationError` | 400 | Бизнес-валидация |
| `ConflictError` | 409 | Дубликат/конфликт |
| `PermissionDeniedError` | 403 | Нет прав |

---

## Кеширование (Redis)

### ⚠️ ВАЖНО: Использовать только обёртки

**Правильно:**
```python
from core.cache import safe_cache_get, safe_cache_set, cache_with_lock
```

**Неправильно:**
```python
from django.core.cache import cache  # ❌ НИКОГДА напрямую!
```

### Критические правила кеширования

1. **Кэшировать только `dict`/`list`, НЕ ORM-объекты**
2. **Использовать sentinel для различия "не в кеше" и "False/None в кеше"**
3. **Короткий TTL (60s) для негативного кэширования**
4. **Инвалидация через `transaction.on_commit()`**
5. **Graceful degradation при падении Redis**

### Паттерны кеширования

**Для горячих ключей (detail страницы):**

```python
from core.cache import cache_with_lock, CACHE_NONE_SENTINEL, CacheKeys, CacheTTL

def get_detail(project_id: int) -> dict:
    cache_key = CacheKeys.PROJECT_DETAIL.format(project_id=project_id)

    def fetch_project():
        project = Project.objects.select_related('owner').get(id=project_id)
        return {'id': project.id, 'name': project.name, ...}

    result = cache_with_lock(cache_key, CacheTTL.PROJECT, fetch_project)
    if result == CACHE_NONE_SENTINEL:
        raise NotFoundError('Проект не найден')
    return result
```

**Для Optional[str] (может быть None):**

```python
def get_member_role(project_id: int, user_id: int) -> str | None:
    cached = safe_cache_get(cache_key)

    # 1. СНАЧАЛА проверяем sentinel, 2. ПОТОМ is not None
    if cached == CACHE_NONE_SENTINEL:
        return None
    if cached is not None:
        return cached

    role = ProjectMember.objects.filter(...).values_list('role', flat=True).first()
    ttl = CacheTTL.MEMBERSHIP if role else CacheTTL.NOT_FOUND
    safe_cache_set(cache_key, role or CACHE_NONE_SENTINEL, ttl)
    return role
```

**Для bool:**

```python
def is_admin(project_id: int, user_id: int) -> bool:
    cached = safe_cache_get(cache_key)

    # 1. СНАЧАЛА sentinel, 2. ПОТОМ is not None
    if cached == CACHE_FALSE_SENTINEL:
        return False
    if cached is not None:
        return cached

    is_admin = ProjectMember.objects.filter(...).exists()
    ttl = CacheTTL.MEMBERSHIP if is_admin else CacheTTL.NOT_FOUND
    safe_cache_set(cache_key, is_admin or CACHE_FALSE_SENTINEL, ttl)
    return is_admin
```

**Инвалидация:**

```python
@transaction.atomic
def update_project(*, project: Project, name: str) -> Project:
    project.name = name
    project.save(update_fields=['name', 'updated_at'])

    _project_id = project.id
    transaction.on_commit(lambda: invalidate_project_cache(_project_id))
    return project
```

---

## Приложения

### `apps/users/`

Пользователи, JWT аутентификация, верификация email, сброс пароля.

**Модели:** `User`, `EmailVerificationToken`, `PasswordResetToken`

**Endpoints:** `/api/v1/auth/` (регистрация, токены), `/api/v1/users/me/` (профиль)

### `apps/projects/`

Проекты с ролевой моделью.

**Модели:** `Project`, `ProjectMember` (роли: `owner`, `admin`, `member`, `viewer`)

**Endpoints:** `/api/v1/projects/` (CRUD), `/api/v1/projects/{id}/members/` (участники)

**Кеширование:** детали проекта (10 мин), роль пользователя (5 мин), проверка прав (5 мин)

### `apps/tasks/`

Задачи внутри проектов.

**Модели:** `Task` (статусы: `pending`, `in_progress`, `completed`, `cancelled`; приоритеты: `low`, `medium`, `high`, `urgent`)

**Endpoints:** `/api/v1/projects/{project_id}/tasks/` (CRUD, статус, назначение)

**Права:**
- Просмотр: все участники
- Создание: member, admin, owner
- Редактирование: creator, assignee, admin, owner

### `apps/tags/`

Теги для задач.

**Модели:** `Tag` (name, color в HEX)

**Endpoints:** `/api/v1/projects/{project_id}/tags/` (CRUD)

**Ограничения:** уникальность имени в проекте, максимум 20 тегов на задачу

### `apps/comments/`

Комментарии к задачам.

**Модели:** `Comment` (task, author, content, is_edited)

**Endpoints:** `/api/v1/projects/{project_id}/tasks/{task_id}/comments/` (CRUD)

**Права:** создание (member+), редактирование (автор), удаление (автор, admin, owner)

### `apps/websocket/`

Real-time обновления через WebSocket.

**URL:** `ws://localhost:8000/ws/projects/{project_id}/?token=JWT_TOKEN`

**События:** `task.*`, `comment.*` (created, updated, deleted)

**Архитектура:** JWT аутентификация, broadcasting через Redis, graceful degradation

---

## Команды разработки

```bash
# Docker
docker compose up -d                                    # Запуск
docker compose logs -f web                              # Логи
docker compose exec web bash                            # Shell

# Django
docker compose exec web python manage.py migrate       # Миграции
docker compose exec web python manage.py createsuperuser
docker compose exec web python manage.py shell_plus
docker compose exec web python manage.py check --deploy

# Тесты
docker compose exec web pytest                          # Все
docker compose exec web pytest apps/users/ -v           # Приложение
docker compose exec web pytest --cov=apps               # С покрытием

# OpenAPI
# Swagger UI: http://localhost:8000/api/docs/
docker compose exec web python manage.py spectacular --validate
```

---

## Документация по слоям

**ВАЖНО:** Перед написанием кода ОБЯЗАТЕЛЬНО прочитай соответствующий файл.

### Models
📖 `.AI-docs/django-rules/common/02-models.md`

- `TextChoices`/`IntegerChoices` для enum
- `DecimalField` для денег
- Индексы для частых запросов
- `CheckConstraint`/`UniqueConstraint` для бизнес-правил

### Selectors
📖 `.AI-docs/django-rules/common/03-selectors.md`

- `select_related` для FK/OneToOne
- `prefetch_related` для M2M/reverse FK
- `Prefetch` для сложных случаев
- `only()`/`defer()` для тяжёлых полей

### Services
📖 `.AI-docs/django-rules/common/04-services.md`

- `@transaction.atomic` на каждом методе записи
- `select_for_update()` для блокировки
- `transaction.on_commit()` для Celery
- `bulk_create`/`bulk_update` для массовых операций

### Serializers
📖 `.AI-docs/django-rules/drf/02-serializers.md`

- Разные сериализаторы: `*List`, `*Detail`, `*Create`
- Явно указывать `fields` и `read_only_fields`
- Валидация в `validate_<field>()` и `validate()`

### Views/ViewSets
📖 `.AI-docs/django-rules/drf/01-viewsets.md`

- `get_queryset()` использует селекторы
- `get_serializer_class()` возвращает разные сериализаторы
- `perform_create()`/`perform_update()` вызывают сервисы

### Permissions
📖 `.AI-docs/django-rules/security/02-permissions.md`

- `has_permission()` — доступ к view
- `has_object_permission()` — доступ к объекту

### Кеширование
📖 `.AI-docs/django-rules/optimization/02-caching.md`

- Обязательные обёртки `safe_cache_get/set`
- Sentinel-значения для `None`/`False`
- Версионирование ключей
- Graceful degradation

### Тестирование
📖 `.AI-docs/django-rules/quality/01-testing.md`

- Factory Boy для фабрик
- `@pytest.mark.django_db(transaction=True)` для тестов с `transaction.on_commit()`
- Freezegun для тестов со временем
