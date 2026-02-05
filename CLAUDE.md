# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Проект

TaskFlow — REST API платформа для управления проектами и задачами на Django + DRF.

## Быстрый старт

```bash
docker compose up -d
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser
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
│   ├── users/              # ✅ Реализовано
│   │   ├── api/            # API-слой (views, serializers, permissions, urls)
│   │   ├── models.py       # Бизнес-слой
│   │   ├── selectors.py    # Бизнес-слой
│   │   ├── services.py     # Бизнес-слой
│   │   └── tasks.py        # Бизнес-слой (Celery)
│   ├── projects/           # ✅ Реализовано (аналогичная структура)
│   ├── tasks/              # ✅ Реализовано (аналогичная структура)
│   ├── tags/               # ✅ Реализовано (аналогичная структура)
│   └── comments/           # ✅ Реализовано (аналогичная структура)
├── core/                   # Общий код
│   ├── cache.py            # CacheKeys, CacheTTL, функции инвалидации
│   ├── exceptions.py       # BaseServiceError, NotFoundError, PermissionDeniedError, ValidationError, ConflictError
│   ├── mixins.py           # TimestampMixin (created_at, updated_at)
│   └── pagination.py       # StandardPagination
├── .AI-docs/               # Документация по разработке
│   └── 
├── docker/
├── docker-compose.yml
├── pyproject.toml
└── manage.py
```

### Структура приложения

Каждое приложение разделено на **бизнес-слой** и **API-слой**:

```
apps/<app>/
├── models.py              # Бизнес-слой: модели данных
├── selectors.py           # Бизнес-слой: чтение из БД
├── services.py            # Бизнес-слой: бизнес-логика
├── tasks.py               # Бизнес-слой: Celery задачи
├── admin.py               # Django admin
├── apps.py
│
├── api/                   # API-слой
│   ├── __init__.py        # Реэкспорты для удобства
│   ├── views.py           # ViewSets, APIView
│   ├── serializers.py     # DRF сериализаторы
│   ├── permissions.py     # DRF permissions
│   └── urls.py            # URL маршруты
│
└── tests/                 # Тесты
    ├── __init__.py
    ├── conftest.py        # Локальные фикстуры
    ├── factories.py       # Factory Boy
    ├── test_services.py   # Тесты сервисов
    └── test_api.py        # Тесты API
```

**Правила импортов:**

1. **Внутри api/** — импорт бизнес-слоя через `..`:
   ```python
   # api/views.py
   from .. import selectors, services
   from ..models import Model
   from .serializers import Serializer  # из той же api/
   ```

2. **Межприложенческие импорты API** — через `.api.`:
   ```python
   # apps/tasks/api/serializers.py
   from apps.users.api.serializers import UserListSerializer
   from apps.tags.api.serializers import TagMinimalSerializer
   ```

3. **Бизнес-слой** — импортирует только бизнес-слой (никогда не импортирует из api/):
   ```python
   # apps/tasks/services.py
   from apps.projects import selectors as project_selectors
   from apps.users.models import User
   # ❌ НИКОГДА: from apps.users.api.serializers import ...
   ```

### Приложения

- `users/` — реализовано
- `projects/` — реализовано
- `tasks/` — реализовано
- `tags/` — реализовано
- `comments/` — реализовано
- `attachments/`, `notifications/`, `activity/` — планируется

## Команды

```bash
# Docker
docker compose up -d
docker compose down
docker compose logs -f web
docker compose exec web bash

# Django
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser
docker compose exec web python manage.py shell_plus

# Тесты
docker compose exec web pytest
docker compose exec web pytest apps/users/ -v
docker compose exec web pytest apps/users/tests/test_services.py::TestCreateUser::test_create_user_success -v
docker compose exec web pytest --cov=apps

# Локальная установка
pip install -e ".[dev]"
```

## Критические правила

### Обязательно

- `@transaction.atomic` для всех операций записи в сервисах
- `transaction.on_commit()` для Celery задач и инвалидации кеша
- `select_related`/`prefetch_related` в каждом селекторе
- `update_fields` при `save()` (включая `updated_at` если модель наследует `TimestampMixin`)
- Явный `on_delete` для всех ForeignKey
- Исключения вместо `None` в селекторах
- `select_for_update()` для конкурентного доступа к данным
- Инвалидация кеша при изменении закешированных данных

### Запрещено

- `fields = '__all__'` в сериализаторах
- Бизнес-логика в моделях, views или сериализаторах
- Запись данных в селекторах
- Синхронные задачи (email, внешние API) внутри транзакции
- Возврат `dict` вместо объекта из сервисов
- `FloatField` для денег (только `DecimalField`)
- Кеширование `select_for_update()` селекторов (сломает блокировку)

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

**Базовые URL:** `/api/v1/auth/` (регистрация, токены, верификация), `/api/v1/users/` (CRUD профиля)

### apps/projects

Управление проектами с ролевой моделью доступа.

**Модели:** `Project`, `ProjectMember`

**Роли:** `owner`, `admin`, `member`, `viewer`

**Базовый URL:** `/api/v1/projects/` (CRUD проектов, управление участниками)

**Celery задачи:** `send_project_invitation_email`, `send_role_changed_email`, `send_removed_from_project_email`

**Кеширование (Redis):**

| Селектор | Ключ | TTL |
|----------|------|-----|
| `get_by_id()` | `projects:by_id:{id}` | 10 мин |
| `get_member_role()` | `projects:member_role:{project_id}:{user_id}` | 5 мин |
| `exists_member()` | `projects:exists_member:{project_id}:{user_id}` | 5 мин |
| `is_admin_or_owner()` | `projects:is_admin_or_owner:{project_id}:{user_id}` | 5 мин |

Инвалидация через `transaction.on_commit()` в сервисах.

### apps/tasks

Управление задачами внутри проектов.

**Модели:** `Task` (статусы: pending, in_progress, completed, cancelled; приоритеты: low, medium, high, urgent)

**Базовый URL:** `/api/v1/projects/{project_id}/tasks/`

**Эндпоинты:**
- `GET/POST /tasks/` — список и создание
- `GET/PATCH/DELETE /tasks/{id}/` — детали, обновление, удаление
- `POST /tasks/{id}/status/` — смена статуса
- `POST /tasks/{id}/assign/` — назначение исполнителя
- `POST /tasks/{id}/reorder/` — изменение позиции
- `POST /tasks/{id}/tags/` — установить теги задачи

**Права доступа:**
- Просмотр: все участники проекта
- Создание: member, admin, owner (не viewer)
- Редактирование: creator, assignee, admin, owner
- Удаление: creator, admin, owner

**Celery задачи:** `send_task_assigned_email`, `send_task_unassigned_email`, `send_task_status_changed_email`

### apps/tags

Теги для задач с привязкой к проекту.

**Модели:** `Tag` (name, color — HEX формат #RRGGBB)

**Связь с tasks:** M2M через `Task.tags`

**Базовый URL:** `/api/v1/projects/{project_id}/tags/`

**Эндпоинты:**
- `GET/POST /tags/` — список и создание
- `GET/PATCH/DELETE /tags/{id}/` — детали, обновление, удаление
- `POST /tasks/{id}/tags/` — установить теги задачи

**Права доступа:**
- Просмотр: все участники проекта
- Создание/редактирование/удаление: admin, owner
- Установка тегов задачи: редактор задачи (creator, assignee, admin, owner)

**Ограничения:**
- Уникальность имени тега в рамках проекта (case-insensitive)
- Максимум 20 тегов на задачу
- Валидация HEX-цвета на уровне модели и сериализатора

### apps/comments

Комментарии к задачам с уведомлениями.

**Модели:** `Comment` (task, author, content, is_edited)

**Базовый URL:** `/api/v1/projects/{project_id}/tasks/{task_id}/comments/`

**Эндпоинты:**
- `GET/POST /comments/` — список и создание
- `GET/PATCH/DELETE /comments/{id}/` — детали, обновление, удаление

**Права доступа:**
- Просмотр: все участники проекта
- Создание: member, admin, owner (не viewer)
- Редактирование: только автор
- Удаление: автор, admin, owner

**Celery задачи:** `send_comment_notification_to_assignee`, `send_comment_notification_to_creator`

**Ограничения:**
- Контент: 1-10000 символов
- При редактировании устанавливается флаг `is_edited=True`

## Документация по слоям

**ВАЖНО**: Перед написанием кода ОБЯЗАТЕЛЬНО прочитай соответствующий файл документации.

### При написании Models

Читай: [.AI-docs/django-rules/common/02-models.md](.AI-docs/django-rules/common/02-models.md)

Ключевое:
- `TextChoices`/`IntegerChoices` для enum
- `DecimalField` для денег
- Индексы в `Meta.indexes` для частых запросов
- `CheckConstraint`/`UniqueConstraint` для бизнес-правил БД

### При написании Selectors

Читай: [.AI-docs/django-rules/common/03-selectors.md](.AI-docs/django-rules/common/03-selectors.md)

Ключевое:
- Всегда `select_related` для FK/OneToOne
- Всегда `prefetch_related` для M2M/reverse FK
- `Prefetch` с фильтрацией для сложных случаев
- `only()`/`defer()` для тяжёлых полей

### При написании Services

Читай: [.AI-docs/django-rules/common/04-services.md](.AI-docs/django-rules/common/04-services.md)

Ключевое:
- `@transaction.atomic` на каждом методе записи
- `select_for_update()` через селектор для блокировки
- `transaction.on_commit(lambda: task.delay(id))` для Celery
- `bulk_create`/`bulk_update` для массовых операций

### При написании Serializers

Читай: [.AI-docs/django-rules/drf/02-serializers.md](.AI-docs/django-rules/drf/02-serializers.md)

Ключевое:
- Разные сериализаторы: `*ListSerializer`, `*DetailSerializer`, `*CreateSerializer`
- Явно указывать `fields` и `read_only_fields`
- Валидация в `validate_<field>()` и `validate()`
- Никакой бизнес-логики в `create()`/`update()`

### При написании Views/ViewSets

Читай: [.AI-docs/django-rules/drf/01-viewsets.md](.AI-docs/django-rules/drf/01-viewsets.md)

Ключевое:
- `get_queryset()` использует селекторы
- `get_serializer_class()` возвращает разные сериализаторы
- `perform_create()`/`perform_update()` вызывают сервисы
- `@action` для кастомных эндпоинтов

### При написании Permissions

Читай: [.AI-docs/django-rules/security/02-permissions.md](.AI-docs/django-rules/security/02-permissions.md)

Ключевое:
- `has_permission()` — доступ к view
- `has_object_permission()` — доступ к объекту
- Выносить в отдельный `api/permissions.py`

### При оптимизации запросов

Читай: [.AI-docs/django-rules/optimization/01-database-queries.md](.AI-docs/django-rules/optimization/01-database-queries.md)

Ключевое:
- `QuerySet.explain()` для анализа
- `exists()` вместо `if queryset`
- `count()` вместо `len(queryset)`
- `values_list('id', flat=True)` для списков ID

### При кешировании

Читай: [.AI-docs/django-rules/optimization/02-caching.md](.AI-docs/django-rules/optimization/02-caching.md)

Ключевое:
- Ключи и TTL в `core/cache.py` (`CacheKeys`, `CacheTTL`)
- `CACHE_NONE_SENTINEL` для различия "нет в кеше" и "значение None"
- Инвалидация через `transaction.on_commit()` в сервисах
- `cache.delete_many()` для удаления нескольких ключей
- НЕ кешировать `select_for_update()` селекторы

Пример кеширования в селекторе:
```python
from django.core.cache import cache
from core.cache import CacheKeys, CacheTTL

def get_by_id(project_id: int) -> Project:
    cache_key = CacheKeys.PROJECT_BY_ID.format(project_id=project_id)
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    project = Project.objects.select_related('owner').get(id=project_id)
    cache.set(cache_key, project, CacheTTL.PROJECT)
    return project
```

Пример инвалидации в сервисе:
```python
from core.cache import invalidate_project_cache

@transaction.atomic
def update_project(*, project: Project, name: str) -> Project:
    project.name = name
    project.save(update_fields=['name', 'updated_at'])

    _project_id = project.id
    transaction.on_commit(lambda: invalidate_project_cache(_project_id))
    return project
```

### При написании тестов

Читай: [.AI-docs/django-rules/quality/01-testing.md](.AI-docs/django-rules/quality/01-testing.md)

#### Структура тестов

```
apps/<app>/tests/
├── __init__.py
├── conftest.py       # Локальные фикстуры приложения
├── factories.py      # Factory Boy фабрики
├── test_services.py  # Тесты сервисов
└── test_api.py       # Тесты API эндпоинтов
```

Глобальные фикстуры (`api_client`, `user`, `authenticated_client`) — в корневом `conftest.py`.

#### Паттерны тестирования

**Factory Boy:**
```python
class UserFactory(DjangoModelFactory):
    class Meta:
        model = User
        skip_postgeneration_save = True  # Обязательно для избежания DeprecationWarning

    email = factory.Sequence(lambda n: f'user{n}@example.com')

    @factory.post_generation
    def password(self, create, extracted, **kwargs):
        self.set_password(extracted or 'testpass123')
        if create:
            self.save(update_fields=['password'])
```

**Тесты с `transaction.on_commit()` (Celery задачи, инвалидация кеша):**
```python
@pytest.mark.django_db(transaction=True)  # Обязательно transaction=True!
def test_create_sends_email(self):
    with patch('apps.users.services.send_email.delay') as mock_email:
        services.create_user(...)
    mock_email.assert_called_once()
```

**API тесты с пустыми списками:**
```python
# При отправке пустого списка используй format='json'
response = api_client.post(url, {'tag_ids': []}, format='json')
```

**Пагинированные ответы:**
```python
# API возвращает {'count': N, 'results': [...], 'next': ..., 'previous': ...}
assert response.data['count'] == 3
assert len(response.data['results']) == 3
```

**Freezegun для тестов с временем:**
```python
from freezegun import freeze_time

@freeze_time("2024-01-15 12:00:00")
def test_expired_token(self):
    token = TokenFactory(expires_at=timezone.now() - timedelta(hours=1))
    with pytest.raises(ValidationError):
        services.verify_token(token=token.token)
```

**Параметризация ролей:**
```python
@pytest.mark.parametrize('role,expected_status', [
    (ProjectMember.Role.OWNER, 200),
    (ProjectMember.Role.ADMIN, 200),
    (ProjectMember.Role.MEMBER, 403),
])
def test_permissions(self, role, expected_status, api_client):
    ...
```

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
