from django.db.models import QuerySet

from apps.tasks.models import Task
from core.exceptions import NotFoundError

from .models import Comment


def get_by_id(comment_id: int) -> Comment:
    try:
        return Comment.objects.select_related(
            'task', 'task__project', 'author'
        ).get(id=comment_id)
    except Comment.DoesNotExist:
        raise NotFoundError('Комментарий не найден')


def get_by_id_for_update(comment_id: int) -> Comment:
    try:
        return Comment.objects.select_for_update().select_related(
            'task', 'task__project', 'author'
        ).get(id=comment_id)
    except Comment.DoesNotExist:
        raise NotFoundError('Комментарий не найден')


def filter_by_task(task: Task) -> QuerySet[Comment]:
    return Comment.objects.filter(
        task=task
    ).select_related('author')


def count_by_task(task: Task) -> int:
    return Comment.objects.filter(task=task).count()
