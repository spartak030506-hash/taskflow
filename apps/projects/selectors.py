from django.core.cache import cache
from django.db.models import Count, Q, QuerySet

from apps.users.models import User
from core.cache import (
    CACHE_NONE_SENTINEL,
    CacheKeys,
    CacheTTL,
)
from core.exceptions import NotFoundError

from .models import Project, ProjectMember


def get_by_id(project_id: int) -> Project:
    cache_key = CacheKeys.PROJECT_BY_ID.format(project_id=project_id)
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    try:
        project = Project.objects.select_related('owner').get(id=project_id)
    except Project.DoesNotExist:
        raise NotFoundError('Проект не найден')

    cache.set(cache_key, project, CacheTTL.PROJECT)
    return project


def get_by_id_with_members(project_id: int) -> Project:
    try:
        return Project.objects.select_related('owner').prefetch_related(
            'members__user'
        ).get(id=project_id)
    except Project.DoesNotExist:
        raise NotFoundError('Проект не найден')


def get_by_id_for_update(project_id: int) -> Project:
    try:
        return Project.objects.select_for_update().get(id=project_id)
    except Project.DoesNotExist:
        raise NotFoundError('Проект не найден')


def get_by_id_with_members_count(project_id: int) -> Project:
    try:
        return Project.objects.select_related('owner').annotate(
            members_count=Count('members')
        ).get(id=project_id)
    except Project.DoesNotExist:
        raise NotFoundError('Проект не найден')


def filter_for_user(user: User) -> QuerySet[Project]:
    return Project.objects.filter(
        members__user=user
    ).select_related('owner').distinct()


def filter_for_user_with_members_count(user: User) -> QuerySet[Project]:
    return Project.objects.filter(
        members__user=user
    ).select_related('owner').annotate(
        members_count=Count('members')
    ).distinct()


def get_member(project: Project, user: User) -> ProjectMember:
    try:
        return ProjectMember.objects.select_related('user', 'project').get(
            project=project,
            user=user,
        )
    except ProjectMember.DoesNotExist:
        raise NotFoundError('Участник не найден')


def get_member_role(project: Project, user: User) -> str | None:
    cache_key = CacheKeys.MEMBER_ROLE.format(project_id=project.id, user_id=user.id)
    cached = cache.get(cache_key)
    if cached is not None:
        return None if cached == CACHE_NONE_SENTINEL else cached

    role = ProjectMember.objects.filter(
        project=project,
        user=user,
    ).values_list('role', flat=True).first()

    cache.set(cache_key, role if role is not None else CACHE_NONE_SENTINEL, CacheTTL.MEMBERSHIP)
    return role


def filter_members(project: Project) -> QuerySet[ProjectMember]:
    return ProjectMember.objects.filter(
        project=project
    ).select_related('user').order_by('joined_at')


def exists_member(project: Project, user: User) -> bool:
    cache_key = CacheKeys.EXISTS_MEMBER.format(project_id=project.id, user_id=user.id)
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    exists = ProjectMember.objects.filter(
        project=project,
        user=user,
    ).exists()

    cache.set(cache_key, exists, CacheTTL.MEMBERSHIP)
    return exists


def is_admin_or_owner(project: Project, user: User) -> bool:
    cache_key = CacheKeys.IS_ADMIN_OR_OWNER.format(project_id=project.id, user_id=user.id)
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    is_admin = ProjectMember.objects.filter(
        project=project,
        user=user,
        role__in=[ProjectMember.Role.OWNER, ProjectMember.Role.ADMIN],
    ).exists()

    cache.set(cache_key, is_admin, CacheTTL.MEMBERSHIP)
    return is_admin


def get_project_with_task_stats(project_id: int) -> Project:
    from apps.tasks.models import Task

    try:
        return Project.objects.select_related('owner').annotate(
            total_tasks=Count('tasks'),
            completed_tasks=Count('tasks', filter=Q(tasks__status=Task.Status.COMPLETED)),
            pending_tasks=Count('tasks', filter=Q(tasks__status=Task.Status.PENDING)),
            in_progress_tasks=Count('tasks', filter=Q(tasks__status=Task.Status.IN_PROGRESS)),
            members_count=Count('members', distinct=True),
        ).get(id=project_id)
    except Project.DoesNotExist:
        raise NotFoundError('Проект не найден')
