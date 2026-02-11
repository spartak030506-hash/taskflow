import logging

from celery import shared_task

from apps.projects.models import Project
from apps.users.models import User

logger = logging.getLogger(__name__)


@shared_task
def send_project_invitation_email(user_id: int, project_id: int, role: str) -> None:
    try:
        user = User.objects.get(id=user_id)
        project = Project.objects.get(id=project_id)
    except (User.DoesNotExist, Project.DoesNotExist):
        logger.warning(
            f"Failed to send invitation email: user_id={user_id}, project_id={project_id}"
        )
        return

    logger.info(
        f"Sending project invitation email to {user.email} "
        f'for project "{project.name}" with role "{role}"'
    )


@shared_task
def send_role_changed_email(user_id: int, project_id: int, new_role: str) -> None:
    try:
        user = User.objects.get(id=user_id)
        project = Project.objects.get(id=project_id)
    except (User.DoesNotExist, Project.DoesNotExist):
        logger.warning(
            f"Failed to send role changed email: user_id={user_id}, project_id={project_id}"
        )
        return

    logger.info(
        f"Sending role changed email to {user.email} "
        f'for project "{project.name}" with new role "{new_role}"'
    )


@shared_task
def send_removed_from_project_email(user_id: int, project_name: str) -> None:
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        logger.warning(f"Failed to send removed from project email: user_id={user_id}")
        return

    logger.info(
        f"Sending removed from project email to {user.email} " f'for project "{project_name}"'
    )
