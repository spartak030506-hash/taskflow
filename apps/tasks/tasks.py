import logging

from celery import shared_task

from apps.projects.models import Project
from apps.users.models import User

from .models import Task

logger = logging.getLogger(__name__)


@shared_task
def send_task_assigned_email(
    user_id: int,
    task_id: int,
    project_id: int,
) -> None:
    try:
        user = User.objects.get(id=user_id)
        task = Task.objects.get(id=task_id)
        project = Project.objects.get(id=project_id)
    except (User.DoesNotExist, Task.DoesNotExist, Project.DoesNotExist):
        logger.warning(
            f'Failed to send task assigned email: '
            f'user_id={user_id}, task_id={task_id}, project_id={project_id}'
        )
        return

    logger.info(
        f'Sending task assigned email to {user.email} '
        f'for task "{task.title}" in project "{project.name}"'
    )


@shared_task
def send_task_unassigned_email(
    user_id: int,
    task_title: str,
    project_name: str,
) -> None:
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        logger.warning(
            f'Failed to send task unassigned email: user_id={user_id}'
        )
        return

    logger.info(
        f'Sending task unassigned email to {user.email} '
        f'for task "{task_title}" in project "{project_name}"'
    )


@shared_task
def send_task_status_changed_email(
    user_id: int,
    task_id: int,
    old_status: str,
    new_status: str,
) -> None:
    try:
        user = User.objects.get(id=user_id)
        task = Task.objects.select_related('project').get(id=task_id)
    except (User.DoesNotExist, Task.DoesNotExist):
        logger.warning(
            f'Failed to send task status changed email: '
            f'user_id={user_id}, task_id={task_id}'
        )
        return

    logger.info(
        f'Sending task status changed email to {user.email} '
        f'for task "{task.title}": {old_status} -> {new_status}'
    )
