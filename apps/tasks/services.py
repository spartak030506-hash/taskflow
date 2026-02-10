from datetime import datetime

from django.db import transaction
from django.db.models import F

from apps.projects.models import Project
from apps.users.models import User

from . import selectors
from .models import Task
from .tasks import (
    send_task_assigned_email,
    send_task_status_changed_email,
    send_task_unassigned_email,
)


@transaction.atomic
def create_task(
    *,
    project: Project,
    creator: User,
    title: str,
    description: str = '',
    priority: str = Task.Priority.MEDIUM,
    deadline: datetime | None = None,
    assignee: User | None = None,
) -> Task:
    position = selectors.get_max_position(project) + 1

    task = Task.objects.create(
        project=project,
        creator=creator,
        title=title,
        description=description,
        priority=priority,
        deadline=deadline,
        assignee=assignee,
        position=position,
    )

    if assignee:
        _user_id = assignee.id
        _task_id = task.id
        _project_id = project.id
        transaction.on_commit(
            lambda: send_task_assigned_email.delay(_user_id, _task_id, _project_id)
        )

    _task_id = task.id
    _user_id = creator.id
    def _broadcast():
        from apps.websocket.tasks import broadcast_task_created
        broadcast_task_created.delay(_task_id, _user_id)
    transaction.on_commit(_broadcast)

    return task


_UNSET = object()


@transaction.atomic
def update_task(
    *,
    task: Task,
    title: str | None = None,
    description: str | None = None,
    priority: str | None = None,
    deadline: datetime | None | object = _UNSET,
    updated_by: User | None = None,
) -> Task:
    update_fields = ['updated_at']

    if title is not None:
        task.title = title
        update_fields.append('title')

    if description is not None:
        task.description = description
        update_fields.append('description')

    if priority is not None:
        task.priority = priority
        update_fields.append('priority')

    if deadline is not _UNSET:
        task.deadline = deadline
        update_fields.append('deadline')

    task.save(update_fields=update_fields)

    if updated_by:
        _task_id = task.id
        _user_id = updated_by.id
        def _broadcast():
            from apps.websocket.tasks import broadcast_task_updated
            broadcast_task_updated.delay(_task_id, _user_id)
        transaction.on_commit(_broadcast)

    return task


@transaction.atomic
def delete_task(*, task: Task, deleted_by: User | None = None) -> None:
    _task_id = task.id
    _project_id = task.project_id

    task.delete()

    if deleted_by:
        _user_id = deleted_by.id
        def _broadcast():
            from apps.websocket.tasks import broadcast_task_deleted
            broadcast_task_deleted.delay(_task_id, _project_id, _user_id)
        transaction.on_commit(_broadcast)


@transaction.atomic
def change_status(*, task: Task, new_status: str, updated_by: User | None = None) -> Task:
    old_status = task.status

    if old_status == new_status:
        return task

    task.status = new_status
    task.save(update_fields=['status', 'updated_at'])

    if task.assignee:
        _user_id = task.assignee_id
        _task_id = task.id
        _old_status = old_status
        _new_status = new_status
        transaction.on_commit(
            lambda: send_task_status_changed_email.delay(
                _user_id, _task_id, _old_status, _new_status
            )
        )

    if updated_by:
        _task_id = task.id
        _user_id = updated_by.id
        def _broadcast():
            from apps.websocket.tasks import broadcast_task_status_changed
            broadcast_task_status_changed.delay(_task_id, _user_id)
        transaction.on_commit(_broadcast)

    return task


@transaction.atomic
def assign_task(*, task: Task, assignee: User | None, project_name: str, updated_by: User | None = None) -> Task:
    old_assignee_id = task.assignee_id

    if task.assignee == assignee:
        return task

    task.assignee = assignee
    task.save(update_fields=['assignee', 'updated_at'])

    if old_assignee_id:
        _old_user_id = old_assignee_id
        _task_title = task.title
        _project_name = project_name
        transaction.on_commit(
            lambda: send_task_unassigned_email.delay(
                _old_user_id, _task_title, _project_name
            )
        )

    if assignee:
        _new_user_id = assignee.id
        _task_id = task.id
        _project_id = task.project_id
        transaction.on_commit(
            lambda: send_task_assigned_email.delay(
                _new_user_id, _task_id, _project_id
            )
        )

    if updated_by:
        _task_id = task.id
        _user_id = updated_by.id
        def _broadcast():
            from apps.websocket.tasks import broadcast_task_assigned
            broadcast_task_assigned.delay(_task_id, _user_id)
        transaction.on_commit(_broadcast)

    return task


@transaction.atomic
def reorder_task(*, task: Task, new_position: int, updated_by: User | None = None) -> Task:
    old_position = task.position

    if old_position == new_position:
        return task

    project = task.project

    if new_position < old_position:
        Task.objects.filter(
            project=project,
            position__gte=new_position,
            position__lt=old_position,
        ).update(position=F('position') + 1)
    else:
        Task.objects.filter(
            project=project,
            position__gt=old_position,
            position__lte=new_position,
        ).update(position=F('position') - 1)

    task.position = new_position
    task.save(update_fields=['position', 'updated_at'])

    if updated_by:
        _task_id = task.id
        _user_id = updated_by.id
        def _broadcast():
            from apps.websocket.tasks import broadcast_task_reordered
            broadcast_task_reordered.delay(_task_id, _user_id)
        transaction.on_commit(_broadcast)

    return task
