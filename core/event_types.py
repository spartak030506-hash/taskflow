from enum import Enum


class TaskEvents(str, Enum):
    CREATED = "task.created"
    UPDATED = "task.updated"
    DELETED = "task.deleted"
    STATUS_CHANGED = "task.status_changed"
    ASSIGNED = "task.assigned"
    REORDERED = "task.reordered"
    TAGS_CHANGED = "task.tags_changed"


class CommentEvents(str, Enum):
    CREATED = "comment.created"
    UPDATED = "comment.updated"
    DELETED = "comment.deleted"
