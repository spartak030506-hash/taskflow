from django.db.models import Max, QuerySet

from apps.projects.models import Project
from apps.users.models import User
from core.exceptions import NotFoundError

from .models import Task


def get_by_id(task_id: int) -> Task:
    try:
        return Task.objects.select_related(
            'project', 'creator', 'assignee'
        ).get(id=task_id)
    except Task.DoesNotExist:
        raise NotFoundError('Задача не найдена')


def get_by_id_for_update(task_id: int) -> Task:
    try:
        return Task.objects.select_for_update().select_related(
            'project', 'creator', 'assignee'
        ).get(id=task_id)
    except Task.DoesNotExist:
        raise NotFoundError('Задача не найдена')


def filter_by_project(project: Project) -> QuerySet[Task]:
    return Task.objects.filter(
        project=project
    ).select_related('creator', 'assignee')


def filter_by_project_with_filters(
    project: Project,
    status: str | None = None,
    priority: str | None = None,
    assignee_id: int | None = None,
) -> QuerySet[Task]:
    queryset = filter_by_project(project)

    if status:
        queryset = queryset.filter(status=status)
    if priority:
        queryset = queryset.filter(priority=priority)
    if assignee_id is not None:
        queryset = queryset.filter(assignee_id=assignee_id)

    return queryset


def filter_assigned_to_user(user: User) -> QuerySet[Task]:
    return Task.objects.filter(
        assignee=user
    ).select_related('project', 'creator')


def exists_task_in_project(project: Project, task_id: int) -> bool:
    return Task.objects.filter(project=project, id=task_id).exists()


def get_max_position(project: Project) -> int:
    result = Task.objects.filter(project=project).aggregate(
        max_position=Max('position')
    )
    return result['max_position'] or 0
