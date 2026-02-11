# Development Guide

## Быстрый старт

```bash
cp .env.example .env.dev
docker compose up -d
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser
```

API: `http://localhost:8000/api/v1/`

## Переменные окружения

Файл `.env.dev` для локальной разработки (копия `.env.example`).

**Критичные переменные:**
- `DJANGO_SETTINGS_MODULE=config.settings.local`
- `SECRET_KEY` — секретный ключ Django
- `DB_*` — PostgreSQL настройки
- `REDIS_URL` — Redis для кеша, Celery, WebSocket
- `CELERY_BROKER_URL` — Celery broker

## Команды

### Docker

```bash
docker compose up -d
docker compose down
docker compose logs -f web
docker compose exec web bash
```

### Django

```bash
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser
docker compose exec web python manage.py shell_plus
docker compose exec web python manage.py makemigrations
```

### Тесты

```bash
docker compose exec web pytest
docker compose exec web pytest apps/users/ -v
docker compose exec web pytest apps/users/tests/test_services.py::TestCreateUser -v
docker compose exec web pytest --cov=apps
```

### Celery

```bash
docker compose exec web celery -A config worker -l info
docker compose exec web celery -A config beat -l info
```

### Линтеры

```bash
docker compose exec web black .
docker compose exec web ruff check .
docker compose exec web ruff check --fix .
```

### Локальная установка (без Docker)

```bash
pip install -e ".[dev]"
python manage.py runserver
```

## OpenAPI Документация

**URL:**
- Swagger UI: `http://localhost:8000/api/docs/`
- ReDoc: `http://localhost:8000/api/redoc/`
- Schema: `http://localhost:8000/api/schema/`

**Команды:**
```bash
docker compose exec web python manage.py spectacular --validate
docker compose exec web python manage.py spectacular --file openapi.yml
```

**Декораторы для ViewSets:**

```python
from core.api_docs import (
    list_endpoint_schema,
    create_endpoint_schema,
    retrieve_endpoint_schema,
    update_endpoint_schema,
    delete_endpoint_schema,
    action_endpoint_schema,
)

@list_endpoint_schema(
    summary="Краткое описание",
    description="Подробное описание",
    tags=['имя_приложения'],
)
def list(self, request):
    ...
```

**help_text в сериализаторах:**

```python
class CreateSerializer(serializers.Serializer):
    field = serializers.CharField(
        max_length=255,
        help_text="Описание поля для OpenAPI schema"
    )
```

## Проверка кода

```bash
docker compose exec web python -m py_compile apps/**/*.py
docker compose exec web python manage.py check
docker compose exec web python manage.py check --deploy
docker compose exec web python manage.py spectacular --validate
```

## Реализованные приложения

### apps/users

Кастомная модель пользователя с JWT аутентификацией, верификацией email и сбросом пароля.

**Модели:** `User`, `EmailVerificationToken`, `PasswordResetToken`

**URL:** `/api/v1/auth/`, `/api/v1/users/`

### apps/projects

Управление проектами с ролевой моделью доступа.

**Модели:** `Project`, `ProjectMember`

**Роли:** `owner`, `admin`, `member`, `viewer`

**URL:** `/api/v1/projects/`

**Celery задачи:** `send_project_invitation_email`, `send_role_changed_email`, `send_removed_from_project_email`

### apps/tasks

Управление задачами внутри проектов.

**Модели:** `Task` (статусы: pending, in_progress, completed, cancelled)

**URL:** `/api/v1/projects/{project_id}/tasks/`

**Эндпоинты:**
- `POST /tasks/{id}/status/` — смена статуса
- `POST /tasks/{id}/assign/` — назначение исполнителя
- `POST /tasks/{id}/reorder/` — изменение позиции
- `POST /tasks/{id}/tags/` — установить теги

**Celery задачи:** `send_task_assigned_email`, `send_task_unassigned_email`, `send_task_status_changed_email`

### apps/tags

Теги для задач с привязкой к проекту.

**Модели:** `Tag` (name, color)

**URL:** `/api/v1/projects/{project_id}/tags/`

### apps/comments

Комментарии к задачам.

**Модели:** `Comment`

**URL:** `/api/v1/projects/{project_id}/tasks/{task_id}/comments/`

**Celery задачи:** `send_comment_notification_to_assignee`, `send_comment_notification_to_creator`

### apps/websocket

WebSocket для real-time обновлений.

**URL:** `ws://localhost:8000/ws/projects/{project_id}/?token=JWT_TOKEN`

**События:** `task.created`, `task.updated`, `task.deleted`, `comment.created`, etc.
