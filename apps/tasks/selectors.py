from datetime import timedelta

from django.db.models import Avg, Count, F, Max, Q, QuerySet
from django.db.models.functions import Coalesce
from django.utils import timezone

from apps.projects.models import Project
from apps.users.models import User
from core.exceptions import NotFoundError

from .models import Task


def get_by_id(task_id: int) -> Task:
    try:
        return Task.objects.select_related(
            'project', 'creator', 'assignee'
        ).prefetch_related('tags').get(id=task_id)
    except Task.DoesNotExist:
        raise NotFoundError('Задача не найдена')


def get_by_id_for_update(task_id: int) -> Task:
    try:
        return Task.objects.select_for_update().select_related(
            'project', 'creator', 'assignee'
        ).prefetch_related('tags').get(id=task_id)
    except Task.DoesNotExist:
        raise NotFoundError('Задача не найдена')


def filter_by_project(project: Project) -> QuerySet[Task]:
    return Task.objects.filter(
        project=project
    ).select_related('creator', 'assignee').prefetch_related('tags')


def filter_by_project_with_filters(
    project: Project,
    status: str | None = None,
    priority: str | None = None,
    assignee_id: int | None = None,
) -> QuerySet[Task]:
    filters = Q(project=project)

    if status:
        filters &= Q(status=status)
    if priority:
        filters &= Q(priority=priority)
    if assignee_id is not None:
        filters &= Q(assignee_id=assignee_id)

    return Task.objects.filter(filters).select_related(
        'creator', 'assignee'
    ).prefetch_related('tags')


def filter_assigned_to_user(user: User) -> QuerySet[Task]:
    return Task.objects.filter(
        assignee=user
    ).select_related('project', 'creator').prefetch_related('tags')


def exists_task_in_project(project: Project, task_id: int) -> bool:
    return Task.objects.filter(project=project, id=task_id).exists()


def get_max_position(project: Project) -> int:
    result = Task.objects.filter(project=project).aggregate(
        max_position=Max('position')
    )
    return result['max_position'] or 0


# def filter_overdue_tasks(project: Project) -> QuerySet[Task]:
#     now = timezone.now()
#     return Task.objects.filter(
#         Q(project=project)
#         & Q(deadline__lt=now)
#         & ~Q(status__in=[Task.Status.COMPLETED, Task.Status.CANCELLED])
#     ).select_related('creator', 'assignee').prefetch_related('tags').order_by('deadline')


# def filter_user_related_tasks(user: User, project: Project) -> QuerySet[Task]:
#     return Task.objects.filter(
#         Q(project=project) & (Q(creator=user) | Q(assignee=user))
#     ).select_related('project', 'creator', 'assignee').prefetch_related('tags').distinct()


# def get_project_task_stats(project: Project) -> dict:
#     return Task.objects.filter(project=project).aggregate(
#         total=Count('id'),
#         completed=Count('id', filter=Q(status=Task.Status.COMPLETED)),
#         in_progress=Count('id', filter=Q(status=Task.Status.IN_PROGRESS)),
#         overdue=Count(
#             'id',
#             filter=Q(deadline__lt=timezone.now())
#             & ~Q(status__in=[Task.Status.COMPLETED, Task.Status.CANCELLED]),
#         ),
#         avg_position=Avg('position'),
#     )


# def filter_with_deadline_soon(
#     project: Project,
#     days: int = 7,
# ) -> QuerySet[Task]:
#     now = timezone.now()
#     threshold = now + timedelta(days=days)
#     return Task.objects.filter(
#         Q(project=project)
#         & Q(deadline__gte=now)
#         & Q(deadline__lte=threshold)
#         & ~Q(status__in=[Task.Status.COMPLETED, Task.Status.CANCELLED])
#     ).annotate(
#         days_until_deadline=Coalesce(F('deadline'), now) - now
#     ).select_related('creator', 'assignee').prefetch_related('tags').order_by('deadline')
