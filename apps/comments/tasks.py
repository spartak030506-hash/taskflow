import logging

from celery import shared_task

from apps.tasks.models import Task
from apps.users.models import User

from .models import Comment

logger = logging.getLogger(__name__)


@shared_task
def send_comment_notification_to_assignee(
    comment_id: int,
    task_id: int,
    author_id: int,
) -> None:
    try:
        Comment.objects.get(id=comment_id)
        task = Task.objects.select_related("project", "assignee").get(id=task_id)
        author = User.objects.get(id=author_id)
    except (Comment.DoesNotExist, Task.DoesNotExist, User.DoesNotExist):
        logger.warning(
            f"Failed to send comment notification to assignee: "
            f"comment_id={comment_id}, task_id={task_id}, author_id={author_id}"
        )
        return

    if not task.assignee or task.assignee_id == author_id:
        return

    logger.info(
        f"Sending comment notification to assignee {task.assignee.email} "
        f'for comment on task "{task.title}" by {author.email}'
    )


@shared_task
def send_comment_notification_to_creator(
    comment_id: int,
    task_id: int,
    author_id: int,
) -> None:
    try:
        Comment.objects.get(id=comment_id)
        task = Task.objects.select_related("project", "creator", "assignee").get(id=task_id)
        author = User.objects.get(id=author_id)
    except (Comment.DoesNotExist, Task.DoesNotExist, User.DoesNotExist):
        logger.warning(
            f"Failed to send comment notification to creator: "
            f"comment_id={comment_id}, task_id={task_id}, author_id={author_id}"
        )
        return

    if task.creator_id == author_id:
        return

    if task.assignee_id and task.creator_id == task.assignee_id:
        return

    logger.info(
        f"Sending comment notification to creator {task.creator.email} "
        f'for comment on task "{task.title}" by {author.email}'
    )
