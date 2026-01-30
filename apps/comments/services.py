from django.db import transaction

from apps.tasks.models import Task
from apps.users.models import User

from .models import Comment
from .tasks import (
    send_comment_notification_to_assignee,
    send_comment_notification_to_creator,
)


@transaction.atomic
def create_comment(
    *,
    task: Task,
    author: User,
    content: str,
) -> Comment:
    comment = Comment.objects.create(
        task=task,
        author=author,
        content=content,
    )

    _comment_id = comment.id
    _task_id = task.id
    _author_id = author.id

    if task.assignee_id and task.assignee_id != author.id:
        transaction.on_commit(
            lambda: send_comment_notification_to_assignee.delay(
                _comment_id, _task_id, _author_id
            )
        )

    if task.creator_id != author.id and task.creator_id != task.assignee_id:
        transaction.on_commit(
            lambda: send_comment_notification_to_creator.delay(
                _comment_id, _task_id, _author_id
            )
        )

    return comment


@transaction.atomic
def update_comment(
    *,
    comment: Comment,
    content: str,
) -> Comment:
    comment.content = content
    comment.is_edited = True
    comment.save(update_fields=['content', 'is_edited', 'updated_at'])
    return comment


@transaction.atomic
def delete_comment(*, comment: Comment) -> None:
    comment.delete()
