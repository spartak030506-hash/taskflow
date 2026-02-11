import logging

from celery import shared_task

from apps.comments.models import Comment
from apps.tasks.models import Task
from apps.users.models import User
from core.event_types import CommentEvents, TaskEvents
from core.websocket import send_to_project_group

from .serializers import (
    serialize_comment_deleted_event,
    serialize_comment_event,
    serialize_task_deleted_event,
    serialize_task_event,
)

logger = logging.getLogger(__name__)


@shared_task
def broadcast_task_created(task_id: int, user_id: int):
    try:
        task = (
            Task.objects.select_related("creator", "assignee", "project")
            .prefetch_related("tags")
            .get(id=task_id)
        )
        user = User.objects.get(id=user_id)
    except (Task.DoesNotExist, User.DoesNotExist):
        logger.warning(f"Task or User not found: task={task_id}, user={user_id}")
        return

    event_data = serialize_task_event(task, TaskEvents.CREATED, user)
    send_to_project_group(task.project_id, TaskEvents.CREATED, event_data)


@shared_task
def broadcast_task_updated(task_id: int, user_id: int):
    try:
        task = (
            Task.objects.select_related("creator", "assignee", "project")
            .prefetch_related("tags")
            .get(id=task_id)
        )
        user = User.objects.get(id=user_id)
    except (Task.DoesNotExist, User.DoesNotExist):
        return

    event_data = serialize_task_event(task, TaskEvents.UPDATED, user)
    send_to_project_group(task.project_id, TaskEvents.UPDATED, event_data)


@shared_task
def broadcast_task_deleted(task_id: int, project_id: int, user_id: int):
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return

    event_data = serialize_task_deleted_event(task_id, project_id, user)
    send_to_project_group(project_id, TaskEvents.DELETED, event_data)


@shared_task
def broadcast_task_status_changed(task_id: int, user_id: int):
    try:
        task = (
            Task.objects.select_related("creator", "assignee", "project")
            .prefetch_related("tags")
            .get(id=task_id)
        )
        user = User.objects.get(id=user_id)
    except (Task.DoesNotExist, User.DoesNotExist):
        return

    event_data = serialize_task_event(task, TaskEvents.STATUS_CHANGED, user)
    send_to_project_group(task.project_id, TaskEvents.STATUS_CHANGED, event_data)


@shared_task
def broadcast_task_assigned(task_id: int, user_id: int):
    try:
        task = (
            Task.objects.select_related("creator", "assignee", "project")
            .prefetch_related("tags")
            .get(id=task_id)
        )
        user = User.objects.get(id=user_id)
    except (Task.DoesNotExist, User.DoesNotExist):
        return

    event_data = serialize_task_event(task, TaskEvents.ASSIGNED, user)
    send_to_project_group(task.project_id, TaskEvents.ASSIGNED, event_data)


@shared_task
def broadcast_task_reordered(task_id: int, user_id: int):
    try:
        task = (
            Task.objects.select_related("creator", "assignee", "project")
            .prefetch_related("tags")
            .get(id=task_id)
        )
        user = User.objects.get(id=user_id)
    except (Task.DoesNotExist, User.DoesNotExist):
        return

    event_data = serialize_task_event(task, TaskEvents.REORDERED, user)
    send_to_project_group(task.project_id, TaskEvents.REORDERED, event_data)


@shared_task
def broadcast_task_tags_changed(task_id: int, user_id: int):
    try:
        task = (
            Task.objects.select_related("creator", "assignee", "project")
            .prefetch_related("tags")
            .get(id=task_id)
        )
        user = User.objects.get(id=user_id)
    except (Task.DoesNotExist, User.DoesNotExist):
        return

    event_data = serialize_task_event(task, TaskEvents.TAGS_CHANGED, user)
    send_to_project_group(task.project_id, TaskEvents.TAGS_CHANGED, event_data)


@shared_task
def broadcast_comment_created(comment_id: int, user_id: int):
    try:
        comment = Comment.objects.select_related("author", "task__project").get(id=comment_id)
        user = User.objects.get(id=user_id)
    except (Comment.DoesNotExist, User.DoesNotExist):
        return

    event_data = serialize_comment_event(comment, CommentEvents.CREATED, user)
    send_to_project_group(comment.task.project_id, CommentEvents.CREATED, event_data)


@shared_task
def broadcast_comment_updated(comment_id: int, user_id: int):
    try:
        comment = Comment.objects.select_related("author", "task__project").get(id=comment_id)
        user = User.objects.get(id=user_id)
    except (Comment.DoesNotExist, User.DoesNotExist):
        return

    event_data = serialize_comment_event(comment, CommentEvents.UPDATED, user)
    send_to_project_group(comment.task.project_id, CommentEvents.UPDATED, event_data)


@shared_task
def broadcast_comment_deleted(comment_id: int, task_id: int, project_id: int, user_id: int):
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return

    event_data = serialize_comment_deleted_event(comment_id, task_id, user)
    send_to_project_group(project_id, CommentEvents.DELETED, event_data)
