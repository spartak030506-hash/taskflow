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

    def _broadcast():
        from apps.websocket.tasks import broadcast_comment_created
        broadcast_comment_created.delay(_comment_id, _author_id)
    transaction.on_commit(_broadcast)

    return comment


@transaction.atomic
def update_comment(
    *,
    comment: Comment,
    content: str,
    updated_by: User | None = None,
) -> Comment:
    comment.content = content
    comment.is_edited = True
    comment.save(update_fields=['content', 'is_edited', 'updated_at'])

    if updated_by:
        _comment_id = comment.id
        _user_id = updated_by.id
        def _broadcast():
            from apps.websocket.tasks import broadcast_comment_updated
            broadcast_comment_updated.delay(_comment_id, _user_id)
        transaction.on_commit(_broadcast)

    return comment


@transaction.atomic
def delete_comment(*, comment: Comment, deleted_by: User | None = None) -> None:
    _comment_id = comment.id
    _task_id = comment.task_id
    _project_id = comment.task.project_id

    comment.delete()

    if deleted_by:
        _user_id = deleted_by.id
        def _broadcast():
            from apps.websocket.tasks import broadcast_comment_deleted
            broadcast_comment_deleted.delay(
                _comment_id, _task_id, _project_id, _user_id
            )
        transaction.on_commit(_broadcast)
