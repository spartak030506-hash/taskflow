from django.utils import timezone

from apps.comments.api.serializers import CommentDetailSerializer
from apps.tasks.api.serializers import TaskDetailSerializer
from apps.users.api.serializers import UserListSerializer


def serialize_task_event(task, event_type: str, user) -> dict:
    return {
        "event_type": event_type,
        "timestamp": timezone.now().isoformat(),
        "user": UserListSerializer(user).data,
        "data": TaskDetailSerializer(task).data,
    }


def serialize_comment_event(comment, event_type: str, user) -> dict:
    return {
        "event_type": event_type,
        "timestamp": timezone.now().isoformat(),
        "user": UserListSerializer(user).data,
        "data": CommentDetailSerializer(comment).data,
    }


def serialize_task_deleted_event(task_id: int, project_id: int, user) -> dict:
    return {
        "event_type": "task.deleted",
        "timestamp": timezone.now().isoformat(),
        "user": UserListSerializer(user).data,
        "data": {
            "id": task_id,
            "project_id": project_id,
        },
    }


def serialize_comment_deleted_event(comment_id: int, task_id: int, user) -> dict:
    return {
        "event_type": "comment.deleted",
        "timestamp": timezone.now().isoformat(),
        "user": UserListSerializer(user).data,
        "data": {
            "id": comment_id,
            "task_id": task_id,
        },
    }
